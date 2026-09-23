"""MCP server (stdio) exposing wingui to Claude Code, Codex, or any MCP client."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server
    from mcp.server.fastmcp.exceptions import ToolError

from .core import Selector, Session, WinGuiError

INSTRUCTIONS = """\
Operate Windows desktop apps through the UI Automation accessibility tree - no
screenshots, no mouse coordinates.

Loop: list_windows / launch -> snapshot(window) -> act on [refs] -> snapshot again to verify.
- Each snapshot line: Type "Name" [ref] #AutomationId state {actions}.
  {actions} tells you what works on the element: invoke, value, toggle, select, expand, range, text.
- Prefer set_value over type_text, invoke over send_keys. Use menu() for menu paths.
- Refs stay valid while the element exists; after big UI changes take a fresh snapshot.
- Use wait_for after actions that open dialogs or load content.
- Custom-drawn UIs (games, canvases, some Electron/Java apps) may expose little;
  then fall back to send_keys on the focused window.
"""

mcp = _Server("wingui", instructions=INSTRUCTIONS)

# UIA objects are bound to the COM apartment that created them, so every call
# runs on this one worker thread, which also owns the Session.
_session: Session | None = None
_com_init: Any = None


def _init_worker() -> None:
    global _com_init
    try:
        import uiautomation

        _com_init = uiautomation.UIAutomationInitializerInThread()
    except ImportError:
        pass


_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="uia", initializer=_init_worker)


def _get_session() -> Session:
    global _session
    if _session is None:
        _session = Session()
    return _session


async def _run(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    def call() -> Any:
        return fn(_get_session(), *args, **kwargs)

    # Only ToolError messages are forwarded to the client verbatim.
    try:
        return await asyncio.get_running_loop().run_in_executor(_executor, call)
    except WinGuiError as ex:
        raise ToolError(str(ex)) from ex
    except Exception as ex:  # COM errors etc.
        raise ToolError(f"{type(ex).__name__}: {ex}") from ex


def _sel(name: str | None, automation_id: str | None, control_type: str | None,
         class_name: str | None, exact: bool, index: int) -> Selector:
    return Selector(name=name, automation_id=automation_id, control_type=control_type,
                    class_name=class_name, exact=exact, index=index)


@mcp.tool()
async def list_windows() -> str:
    """List top-level windows (ref, title, pid, hwnd). Window refs start with 'w'."""
    return json.dumps(await _run(Session.list_windows), ensure_ascii=False, indent=1)


@mcp.tool()
async def launch(command: str, args: list[str] | None = None, timeout: float = 15.0) -> str:
    """Start a program (exe name/path, app alias, or document) and return its new window ref."""
    return json.dumps(await _run(Session.launch, command, args, timeout), ensure_ascii=False)


@mcp.tool()
async def snapshot(window: str, max_depth: int = 12, max_nodes: int = 400,
                   compact: bool = True, include_offscreen: bool = False) -> str:
    """Accessibility tree of a window or element.

    window: window ref ('w3'), element ref ('e12') to zoom into a subtree,
    'hwnd:0x1234', 'pid:5678', or a title substring/regex.
    """
    return await _run(Session.snapshot, window, max_depth=max_depth, max_nodes=max_nodes,
                      compact=compact, include_offscreen=include_offscreen)


@mcp.tool()
async def find(window: str, name: str | None = None, automation_id: str | None = None,
               control_type: str | None = None, class_name: str | None = None,
               exact: bool = False, limit: int = 20) -> str:
    """Search a window for elements (name is a case-insensitive substring unless exact)."""
    def do(s: Session) -> str:
        sel = _sel(name, automation_id, control_type, class_name, exact, 0)
        hits = s.find(window, sel, limit=limit)
        return "\n".join("- " + s.describe(c, s.ref_for(c)) for c in hits) or "no matches"
    return await _run(do)


@mcp.tool()
async def invoke(ref: str) -> str:
    """Activate an element: press button, toggle checkbox, select item, expand/collapse node."""
    return await _run(Session.invoke, ref)


@mcp.tool()
async def set_value(ref: str, value: str) -> str:
    """Set an Edit/ComboBox text (ValuePattern) or a slider/spinner number (RangeValuePattern)."""
    return await _run(Session.set_value, ref, value)


@mcp.tool()
async def type_text(text: str, ref: str | None = None, clear: bool = False) -> str:
    """Type literal text via keyboard into ref (or the focused element). Use when set_value is unsupported."""
    return await _run(Session.type_text, ref, text, clear)


@mcp.tool()
async def send_keys(keys: str, ref: str | None = None) -> str:
    """Send key strokes, uiautomation syntax: '{Ctrl}s', '{Alt}{F4}', '{Enter}', '{Ctrl}{Shift}n'."""
    return await _run(Session.send_keys, keys, ref)


@mcp.tool()
async def toggle(ref: str, on: bool | None = None) -> str:
    """Toggle a checkbox/toggle button, or force it on/off when `on` is given."""
    return await _run(Session.toggle, ref, on)


@mcp.tool()
async def expand(ref: str, collapse: bool = False) -> str:
    """Expand (or collapse) a tree node, combo box, or menu."""
    return await _run(Session.expand, ref, not collapse)


@mcp.tool()
async def select(ref: str, item: str) -> str:
    """Choose an item by name inside a ComboBox, List, Tab, or Tree element."""
    return await _run(Session.select, ref, item)


@mcp.tool()
async def menu(window: str, path: str) -> str:
    """Run a menu command by path, e.g. 'File > Save As'."""
    return await _run(Session.menu, window, path)


@mcp.tool()
async def get_text(ref: str, max_chars: int = 20000) -> str:
    """Read the text/value of an element (documents, edits, labels, lists)."""
    return await _run(Session.get_text, ref, max_chars)


@mcp.tool()
async def focus(target: str) -> str:
    """Bring a window to the foreground or focus an element."""
    return await _run(Session.focus, target)


@mcp.tool()
async def close_window(window: str) -> str:
    """Politely close a window through its Window pattern."""
    return await _run(Session.close_window, window)


@mcp.tool()
async def wait_for(window: str, name: str | None = None, automation_id: str | None = None,
                   control_type: str | None = None, timeout: float = 10.0, gone: bool = False) -> str:
    """Wait for a window (and optionally an element in it) to appear, or disappear if gone=True."""
    sel = _sel(name, automation_id, control_type, None, False, 0)
    return await _run(Session.wait_for, window, sel, timeout, gone)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
