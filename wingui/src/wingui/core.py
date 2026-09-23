"""Core of wingui: talk to Windows apps through UI Automation (UIA).

Nothing here moves the mouse or reads pixels. Every action goes through a
UIA control pattern (Invoke, Value, Toggle, SelectionItem, ExpandCollapse,
LegacyIAccessible ...), the same interface screen readers use. The only
input-simulation fallback is keyboard text for controls that expose no
Value pattern, and it is always explicit (``type_text`` / ``send_keys``).

A ``Session`` hands out short refs (``w1``, ``e12``) for elements it has shown
in a snapshot so the agent can act on them by ref. All UIA objects are
apartment-bound COM objects: a Session must be created and used on a single
thread.
"""

from __future__ import annotations

import re
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Iterator


class WinGuiError(Exception):
    """Raised for anything the agent should see as a readable tool error."""


def _load_uia() -> Any:
    try:
        import uiautomation  # type: ignore
    except ImportError as ex:  # non-Windows, or package missing
        raise WinGuiError(
            "The 'uiautomation' package is unavailable. wingui must run with a "
            "Windows Python (pip install wingui-mcp on Windows; from WSL call python.exe)."
        ) from ex
    return uiautomation


# Short names used in snapshots -> UIA PatternId attribute names.
_PATTERNS = {
    "invoke": "InvokePattern",
    "value": "ValuePattern",
    "toggle": "TogglePattern",
    "select": "SelectionItemPattern",
    "expand": "ExpandCollapsePattern",
    "range": "RangeValuePattern",
    "text": "TextPattern",
}
_TOGGLE_STATES = {0: "off", 1: "on", 2: "indeterminate"}
_EXPAND_STATES = {0: "collapsed", 1: "expanded", 2: "partial", 3: "leaf"}


def _short_type(ctrl: Any) -> str:
    name = getattr(ctrl, "ControlTypeName", "") or "Unknown"
    return name[:-7] if name.endswith("Control") else name


def _norm_type(t: str | None) -> str | None:
    if not t:
        return None
    t = t.strip()
    return (t[:-7] if t.lower().endswith("control") else t).lower()


def _clip(s: str, n: int = 80) -> str:
    s = s.replace("\r", "").replace("\n", "\\n")
    return s if len(s) <= n else s[: n - 1] + "…"


def _menu_label(s: str) -> str:
    """'&Save As...\tCtrl+Shift+S' -> 'save as...'"""
    return s.split("\t")[0].replace("&", "").strip().lower()


@dataclass
class Selector:
    """Declarative element query. Every set field must match."""

    name: str | None = None  # case-insensitive substring, or exact if exact=True
    automation_id: str | None = None
    control_type: str | None = None  # "Button", "Edit", "ButtonControl" ...
    class_name: str | None = None
    exact: bool = False
    index: int = 0  # pick the n-th match (document order)

    def empty(self) -> bool:
        return not (self.name or self.automation_id or self.control_type or self.class_name)

    def matches(self, ctrl: Any) -> bool:
        if self.automation_id is not None and (ctrl.AutomationId or "") != self.automation_id:
            return False
        if self.control_type and _short_type(ctrl).lower() != _norm_type(self.control_type):
            return False
        if self.class_name is not None and (ctrl.ClassName or "") != self.class_name:
            return False
        if self.name is not None:
            actual = (ctrl.Name or "").lower()
            want = self.name.lower()
            if (actual != want) if self.exact else (want not in actual):
                return False
        return True

    def describe(self) -> str:
        parts = [f"{k}={v!r}" for k, v in (
            ("name", self.name), ("automation_id", self.automation_id),
            ("control_type", self.control_type), ("class_name", self.class_name),
        ) if v]
        return ", ".join(parts) or "<any>"


class Session:
    def __init__(self, uia: Any | None = None, key_interval: float = 0.01):
        self.uia = uia if uia is not None else _load_uia()
        self.key_interval = key_interval
        self._refs: dict[str, Any] = {}
        self._by_rid: dict[tuple, str] = {}
        self._counter = 0

    # ------------------------------------------------------------------ refs
    def ref_for(self, ctrl: Any, prefix: str = "e") -> str:
        try:
            rid = tuple(ctrl.GetRuntimeId() or ())
        except Exception:
            rid = ()
        if rid and rid in self._by_rid:
            ref = self._by_rid[rid]
            self._refs[ref] = ctrl
            return ref
        self._counter += 1
        ref = f"{prefix}{self._counter}"
        self._refs[ref] = ctrl
        if rid:
            self._by_rid[rid] = ref
        return ref

    def resolve(self, target: Any) -> Any:
        """Turn a ref string (or an already-resolved control) into a control."""
        if not isinstance(target, str):
            return target
        ctrl = self._refs.get(target.strip())
        if ctrl is None:
            raise WinGuiError(f"Unknown ref {target!r}. Take a new snapshot to get current refs.")
        if not self._alive(ctrl):
            raise WinGuiError(f"Element {target} no longer exists. Take a new snapshot.")
        return ctrl

    @staticmethod
    def _alive(ctrl: Any) -> bool:
        try:
            ctrl.GetRuntimeId()
            _ = ctrl.ControlTypeName
            return True
        except Exception:
            return False

    # --------------------------------------------------------------- windows
    def _top_level(self) -> list[Any]:
        out = []
        for c in self.uia.GetRootControl().GetChildren():
            try:
                if c.Name or _short_type(c) == "Window":
                    out.append(c)
            except Exception:
                continue
        return out

    def list_windows(self) -> list[dict]:
        rows = []
        for w in self._top_level():
            try:
                rows.append({
                    "ref": self.ref_for(w, "w"),
                    "title": w.Name,
                    "type": _short_type(w),
                    "class": w.ClassName,
                    "pid": w.ProcessId,
                    "hwnd": w.NativeWindowHandle,
                })
            except Exception:
                continue
        return rows

    def find_window(self, query: str | Any) -> Any:
        """ref | 'hwnd:123' | 'pid:456' | title substring | title regex."""
        if not isinstance(query, str):
            return query
        q = query.strip()
        if q in self._refs:
            return self.resolve(q)
        if q.lower().startswith("hwnd:"):
            ctrl = self.uia.ControlFromHandle(int(q[5:], 0))
            if not ctrl:
                raise WinGuiError(f"No window with {q}")
            return ctrl
        wins = self._top_level()
        if q.lower().startswith("pid:"):
            pid = int(q[4:])
            hits = [w for w in wins if w.ProcessId == pid]
        else:
            hits = [w for w in wins if q.lower() in (w.Name or "").lower()]
            if not hits:
                try:
                    rx = re.compile(q, re.I)
                    hits = [w for w in wins if rx.search(w.Name or "")]
                except re.error:
                    pass
        if not hits:
            titles = ", ".join(repr(w.Name) for w in wins if w.Name)
            raise WinGuiError(f"No window matches {query!r}. Open windows: {titles}")
        return hits[0]

    # ------------------------------------------------------------- traversal
    @staticmethod
    def _children(ctrl: Any) -> list[Any]:
        try:
            return ctrl.GetChildren()
        except Exception:
            return []

    def _descendants(self, root: Any, max_depth: int) -> Iterator[Any]:
        """Breadth-first, so shallower (usually more relevant) matches come first."""
        queue = deque((c, 1) for c in self._children(root))
        while queue:
            ctrl, depth = queue.popleft()
            yield ctrl
            if depth < max_depth:
                queue.extend((c, depth + 1) for c in self._children(ctrl))

    def find(self, window: Any, sel: Selector, max_depth: int = 25, limit: int = 20) -> list[Any]:
        root = self.find_window(window)
        hits = []
        for c in self._descendants(root, max_depth):
            try:
                if sel.matches(c):
                    hits.append(c)
                    if len(hits) >= limit:
                        break
            except Exception:
                continue
        return hits

    def locate(self, window: Any, sel: Selector, timeout: float = 0) -> Any:
        deadline = time.monotonic() + timeout
        while True:
            hits = self.find(window, sel, limit=sel.index + 1)
            if len(hits) > sel.index:
                return hits[sel.index]
            if time.monotonic() >= deadline:
                raise WinGuiError(f"No element matches {sel.describe()} (index {sel.index}).")
            time.sleep(0.25)

    # -------------------------------------------------------------- patterns
    def _pattern(self, ctrl: Any, short: str) -> Any:
        pid = getattr(self.uia.PatternId, _PATTERNS[short])
        try:
            return ctrl.GetPattern(pid)
        except Exception:
            return None

    def _legacy(self, ctrl: Any) -> Any:
        try:
            return ctrl.GetPattern(self.uia.PatternId.LegacyIAccessiblePattern)
        except Exception:
            return None

    def describe(self, ctrl: Any, ref: str) -> str:
        parts = [f"{_short_type(ctrl)}"]
        name = ctrl.Name or ""
        if name:
            parts.append(f'"{_clip(name)}"')
        parts.append(f"[{ref}]")
        if ctrl.AutomationId:
            parts.append(f"#{_clip(ctrl.AutomationId, 40)}")
        actions = []
        for short in _PATTERNS:
            p = self._pattern(ctrl, short)
            if p is None:
                continue
            actions.append(short)
            try:
                if short == "value":
                    parts.append(f'value="{_clip(p.Value or "")}"' + (" readonly" if p.IsReadOnly else ""))
                elif short == "toggle":
                    parts.append(_TOGGLE_STATES.get(p.ToggleState, "?"))
                elif short == "select" and p.IsSelected:
                    parts.append("selected")
                elif short == "expand":
                    state = _EXPAND_STATES.get(p.ExpandCollapseState)
                    if state in ("collapsed", "expanded"):
                        parts.append(state)
                elif short == "range":
                    parts.append(f"range={p.Value}[{p.Minimum}..{p.Maximum}]")
            except Exception:
                pass
        if not ctrl.IsEnabled:
            parts.append("disabled")
        if getattr(ctrl, "HasKeyboardFocus", False):
            parts.append("focused")
        if actions:
            parts.append("{" + ",".join(actions) + "}")
        return " ".join(parts)

    def snapshot(self, window: Any, max_depth: int = 12, max_nodes: int = 400,
                 compact: bool = True, include_offscreen: bool = False) -> str:
        """Indented accessibility tree of one window, one element per line.

        compact=True hides anonymous structural containers (no name, no id, no
        actionable pattern) and lifts their children up a level.
        """
        root = self.find_window(window)
        lines: list[str] = []
        truncated = False

        def interesting(c: Any) -> bool:
            if c.Name or c.AutomationId:
                return True
            return any(self._pattern(c, s) is not None for s in ("invoke", "value", "toggle", "select", "expand"))

        def walk(ctrl: Any, depth: int, indent: int) -> None:
            nonlocal truncated
            for child in self._children(ctrl):
                if len(lines) >= max_nodes:
                    truncated = True
                    return
                try:
                    if not include_offscreen and child.IsOffscreen and _short_type(child) != "MenuItem":
                        continue
                    show = not compact or interesting(child)
                    if show:
                        lines.append("  " * indent + "- " + self.describe(child, self.ref_for(child)))
                    if depth < max_depth:
                        walk(child, depth + 1, indent + 1 if show else indent)
                except Exception:
                    continue

        header = self.describe(root, self.ref_for(root, "w"))
        walk(root, 1, 1)
        if truncated:
            lines.append(f"  … truncated at {max_nodes} nodes; snapshot a sub-element ref or raise max_nodes")
        return "- " + header + "\n" + "\n".join(lines)

    def snapshot_element(self, target: Any, **kw: Any) -> str:
        return self.snapshot(self.resolve(target), **kw)

    # --------------------------------------------------------------- actions
    def invoke(self, target: Any) -> str:
        """Activate an element the way its UIA patterns allow (no mouse)."""
        ctrl = self.resolve(target)
        if not ctrl.IsEnabled:
            raise WinGuiError(f"{_short_type(ctrl)} {ctrl.Name!r} is disabled.")
        if (p := self._pattern(ctrl, "invoke")) is not None:
            p.Invoke()
            return "invoked"
        if (p := self._pattern(ctrl, "toggle")) is not None:
            p.Toggle()
            return f"toggled -> {_TOGGLE_STATES.get(p.ToggleState, '?')}"
        if (p := self._pattern(ctrl, "select")) is not None:
            p.Select()
            return "selected"
        if (p := self._pattern(ctrl, "expand")) is not None:
            if p.ExpandCollapseState == 1:
                p.Collapse()
                return "collapsed"
            p.Expand()
            return "expanded"
        if (p := self._legacy(ctrl)) is not None and p.DefaultAction:
            action = p.DefaultAction
            p.DoDefaultAction()
            return f"default action '{action}'"
        raise WinGuiError(
            f"{_short_type(ctrl)} {ctrl.Name!r} exposes no invokable pattern. "
            "Try send_keys (e.g. focus + {Enter}/{Space}) or act on its parent/child."
        )

    def set_value(self, target: Any, value: str) -> str:
        ctrl = self.resolve(target)
        if (p := self._pattern(ctrl, "value")) is not None and not p.IsReadOnly:
            p.SetValue(value)
            return f'value="{_clip(p.Value or "")}"'
        if (p := self._pattern(ctrl, "range")) is not None:
            try:
                p.SetValue(float(value))
                return f"range value={p.Value}"
            except ValueError:
                raise WinGuiError(f"{value!r} is not numeric; this control only takes a number.")
        raise WinGuiError(
            f"{_short_type(ctrl)} {ctrl.Name!r} has no writable Value pattern. Use type_text instead."
        )

    def type_text(self, target: Any | None, text: str, clear: bool = False) -> str:
        """Type literal text into the element via keyboard (Unicode, IME-independent)."""
        ctrl = self.resolve(target) if target is not None else None
        if ctrl is not None:
            ctrl.SetFocus()
        if clear:
            self.uia.SendKeys("{Ctrl}a{Delete}", interval=self.key_interval, waitTime=0.05)
        for ch in text.replace("\r\n", "\n"):
            if ch == "\n":
                self.uia.SendKeys("{Enter}", waitTime=0)
            elif ch == "\t":
                self.uia.SendKeys("{Tab}", waitTime=0)
            else:
                self.uia.SendUnicodeChar(ch)
            time.sleep(self.key_interval)
        return f"typed {len(text)} chars"

    def send_keys(self, keys: str, target: Any | None = None) -> str:
        """uiautomation SendKeys syntax, e.g. '{Ctrl}s', '{Alt}{F4}', '{Enter}'."""
        if target is not None:
            self.resolve(target).SetFocus()
        self.uia.SendKeys(keys, interval=self.key_interval, waitTime=0.1)
        return f"sent {keys}"

    def toggle(self, target: Any, on: bool | None = None) -> str:
        ctrl = self.resolve(target)
        p = self._pattern(ctrl, "toggle")
        if p is None:
            raise WinGuiError(f"{_short_type(ctrl)} {ctrl.Name!r} is not toggleable.")
        if on is None:
            p.Toggle()
        else:
            want = 1 if on else 0
            for _ in range(3):  # three-state checkboxes may need two hops
                if p.ToggleState == want:
                    break
                p.Toggle()
        return _TOGGLE_STATES.get(p.ToggleState, "?")

    def expand(self, target: Any, expand: bool = True) -> str:
        ctrl = self.resolve(target)
        p = self._pattern(ctrl, "expand")
        if p is None:
            raise WinGuiError(f"{_short_type(ctrl)} {ctrl.Name!r} cannot expand/collapse.")
        p.Expand() if expand else p.Collapse()
        return _EXPAND_STATES.get(p.ExpandCollapseState, "?")

    def select(self, target: Any, item: str) -> str:
        """Pick an item by name inside a ComboBox / List / Tab / Tree."""
        ctrl = self.resolve(target)
        exp = self._pattern(ctrl, "expand")
        if exp is not None:
            try:
                exp.Expand()
            except Exception:
                pass
        # Some combo boxes accept the text directly.
        want = item.lower()
        candidates = []
        for c in self._descendants(ctrl, 6):
            try:
                if self._pattern(c, "select") is None:
                    continue
                name = (c.Name or "").lower()
                if name == want:
                    candidates.insert(0, c)
                elif want in name:
                    candidates.append(c)
            except Exception:
                continue
        if not candidates:
            if (vp := self._pattern(ctrl, "value")) is not None and not vp.IsReadOnly:
                vp.SetValue(item)
                return f'value="{item}"'
            raise WinGuiError(f"No selectable item named {item!r} under {ctrl.Name!r}.")
        chosen = candidates[0]
        try:
            self._pattern(chosen, "select").Select()
        finally:
            if exp is not None:
                try:
                    exp.Collapse()
                except Exception:
                    pass
        return f"selected {chosen.Name!r}"

    def get_text(self, target: Any, max_chars: int = 20000) -> str:
        ctrl = self.resolve(target)
        if (p := self._pattern(ctrl, "text")) is not None:
            try:
                return p.DocumentRange.GetText(max_chars)
            except Exception:
                pass
        if (p := self._pattern(ctrl, "value")) is not None:
            return (p.Value or "")[:max_chars]
        if (p := self._legacy(ctrl)) is not None:
            try:
                if p.Value:
                    return p.Value[:max_chars]
            except Exception:
                pass
        # Fall back to the concatenated names of text descendants.
        texts = [ctrl.Name or ""]
        for c in self._descendants(ctrl, 8):
            try:
                if _short_type(c) in ("Text", "Edit", "Document", "ListItem", "DataItem") and c.Name:
                    texts.append(c.Name)
            except Exception:
                continue
        return "\n".join(t for t in texts if t)[:max_chars]

    def focus(self, target: Any) -> str:
        ctrl = self.find_window(target)
        if _short_type(ctrl) == "Window" and hasattr(ctrl, "SetActive"):
            ctrl.SetActive()
        else:
            ctrl.SetFocus()
        return f"focused {ctrl.Name!r}"

    def close_window(self, window: Any) -> str:
        w = self.find_window(window)
        title = w.Name
        try:
            wp = w.GetPattern(self.uia.PatternId.WindowPattern)
        except Exception:
            wp = None
        if wp is None:
            raise WinGuiError(f"{title!r} has no Window pattern; try send_keys('{{Alt}}{{F4}}').")
        wp.Close()
        return f"close requested for {title!r} (check for a save prompt)"

    def menu(self, window: Any, path: str) -> str:
        """Walk a menu path like 'File > Save As' by expanding and invoking items."""
        w = self.find_window(window)
        pid = w.ProcessId
        steps = [s for s in re.split(r"\s*(?:>|/|->)\s*", path) if s]
        if not steps:
            raise WinGuiError("Empty menu path.")
        scope = [w]
        for i, step in enumerate(steps):
            item = self._find_menu_item(scope, step, pid)
            last = i == len(steps) - 1
            exp = self._pattern(item, "expand")
            if not last and exp is not None:
                exp.Expand()
            else:
                self.invoke(item)
            time.sleep(0.15)
            # Sub-menus usually appear as new top-level popups of the same process.
            scope = [item] + [c for c in self._top_level() if c.ProcessId == pid] + [w]
        return f"menu {' > '.join(steps)} done"

    def _find_menu_item(self, scopes: list[Any], label: str, pid: int, timeout: float = 2.0) -> Any:
        want = _menu_label(label)
        deadline = time.monotonic() + timeout
        while True:
            for scope in scopes:
                prefix = None
                for c in self._descendants(scope, 8):
                    try:
                        if _short_type(c) != "MenuItem":
                            continue
                        got = _menu_label(c.Name or "")
                        if got == want:
                            return c
                        if prefix is None and got.startswith(want):
                            prefix = c
                    except Exception:
                        continue
                if prefix is not None:
                    return prefix
            if time.monotonic() >= deadline:
                raise WinGuiError(f"Menu item {label!r} not found.")
            time.sleep(0.2)
            scopes = scopes + [c for c in self._top_level() if c.ProcessId == pid]

    # ---------------------------------------------------------------- launch
    def launch(self, command: str, args: list[str] | None = None, timeout: float = 15.0,
               cwd: str | None = None) -> dict:
        """Start a program and return the first new top-level window it opens."""
        before = {w.NativeWindowHandle for w in self._top_level()}
        try:
            proc = subprocess.Popen([command, *(args or [])], cwd=cwd)
            pid = proc.pid
        except (FileNotFoundError, OSError):
            # App aliases / UWP / documents / shell verbs go through `start`.
            subprocess.Popen(["cmd", "/c", "start", "", command, *(args or [])], cwd=cwd)
            pid = None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(0.3)
            fresh = [w for w in self._top_level() if w.NativeWindowHandle not in before]
            if fresh:
                fresh.sort(key=lambda w: w.ProcessId != pid)  # prefer our own pid
                w = fresh[0]
                return {"ref": self.ref_for(w, "w"), "title": w.Name, "pid": w.ProcessId,
                        "hwnd": w.NativeWindowHandle}
        raise WinGuiError(
            f"Started {command!r} but no new window appeared within {timeout}s "
            "(it may have reused an existing window; call list_windows)."
        )

    def wait_for(self, window: Any, sel: Selector | None = None, timeout: float = 10.0,
                 gone: bool = False) -> str:
        """Wait until a window (and optionally an element in it) appears or disappears."""
        deadline = time.monotonic() + timeout
        while True:
            try:
                found = self.find_window(window)
                if sel is not None and not sel.empty():
                    hits = self.find(found, sel, limit=sel.index + 1)
                    found = hits[sel.index] if len(hits) > sel.index else None
            except WinGuiError:
                found = None
            if gone and found is None:
                return "gone"
            if not gone and found is not None:
                return "found " + self.describe(found, self.ref_for(found))
            if time.monotonic() >= deadline:
                what = sel.describe() if sel else str(window)
                raise WinGuiError(f"Timed out after {timeout}s waiting for {what} to {'disappear' if gone else 'appear'}.")
            time.sleep(0.25)
