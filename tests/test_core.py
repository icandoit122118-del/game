"""Tests against a fake UIA tree so the logic runs on any OS."""

from __future__ import annotations

import itertools
import types

import pytest

from wingui.cli import build_parser, run
from wingui.core import Selector, Session, WinGuiError

PatternId = types.SimpleNamespace(
    InvokePattern=1, ValuePattern=2, TogglePattern=3, SelectionItemPattern=4,
    ExpandCollapsePattern=5, RangeValuePattern=6, TextPattern=7,
    LegacyIAccessiblePattern=8, WindowPattern=9,
)
_ids = itertools.count(1)


class Invoke:
    def __init__(self, log):
        self.log = log

    def Invoke(self):
        self.log.append("invoke")


class Value:
    def __init__(self, value="", readonly=False):
        self.Value, self.IsReadOnly = value, readonly

    def SetValue(self, v):
        self.Value = v


class Toggle:
    def __init__(self, state=0):
        self.ToggleState = state

    def Toggle(self):
        self.ToggleState = (self.ToggleState + 1) % 2


class SelItem:
    def __init__(self):
        self.IsSelected = False

    def Select(self):
        self.IsSelected = True


class Expand:
    def __init__(self):
        self.ExpandCollapseState = 0

    def Expand(self):
        self.ExpandCollapseState = 1

    def Collapse(self):
        self.ExpandCollapseState = 0


class WindowPat:
    def __init__(self, log):
        self.log = log

    def Close(self):
        self.log.append("close")


class Ctrl:
    def __init__(self, type_, name="", aid="", children=(), patterns=None, pid=100, enabled=True):
        self.ControlTypeName = type_ + "Control"
        self.Name, self.AutomationId, self.ClassName = name, aid, ""
        self.children = list(children)
        self.patterns = patterns or {}
        self.ProcessId, self.IsEnabled = pid, enabled
        self.IsOffscreen = self.HasKeyboardFocus = False
        self.NativeWindowHandle = next(_ids)
        self.rid = [42, self.NativeWindowHandle]
        self.focused = False

    def GetChildren(self):
        return self.children

    def GetRuntimeId(self):
        return self.rid

    def GetPattern(self, pid):
        return self.patterns.get(pid)

    def SetFocus(self):
        self.focused = True

    SetActive = SetFocus


class FakeUia:
    PatternId = PatternId

    def __init__(self, root):
        self.root, self.keys = root, []

    def GetRootControl(self):
        return self.root

    def ControlFromHandle(self, h):
        return None

    def SendKeys(self, keys, interval=0.01, waitTime=0.1):
        self.keys.append(keys)

    def SendUnicodeChar(self, ch):
        self.keys.append(ch)


@pytest.fixture
def app():
    log = []
    edit = Ctrl("Edit", "Text Editor", "15", patterns={PatternId.ValuePattern: Value("hello")})
    ok = Ctrl("Button", "OK", "btnOk", patterns={PatternId.InvokePattern: Invoke(log)})
    off = Ctrl("Button", "Disabled", patterns={PatternId.InvokePattern: Invoke(log)}, enabled=False)
    chk = Ctrl("CheckBox", "Word wrap", patterns={PatternId.TogglePattern: Toggle()})
    items = [Ctrl("ListItem", n, patterns={PatternId.SelectionItemPattern: SelItem()}) for n in ("UTF-8", "ANSI")]
    combo = Ctrl("ComboBox", "Encoding", children=[Ctrl("List", children=items)],
                 patterns={PatternId.ExpandCollapsePattern: Expand()})
    save = Ctrl("MenuItem", "&Save\tCtrl+S", patterns={PatternId.InvokePattern: Invoke(log)})
    file_ = Ctrl("MenuItem", "File", children=[save], patterns={PatternId.ExpandCollapsePattern: Expand()})
    bar = Ctrl("MenuBar", "Application", children=[file_])
    pane = Ctrl("Pane", children=[edit, ok, off, chk, combo])  # anonymous container
    win = Ctrl("Window", "Untitled - Notepad", children=[bar, pane],
               patterns={PatternId.WindowPattern: WindowPat(log)})
    other = Ctrl("Window", "Calculator", pid=200)
    root = Ctrl("Pane", "Desktop", children=[win, other])
    uia = FakeUia(root)
    return types.SimpleNamespace(s=Session(uia, key_interval=0), uia=uia, log=log, win=win,
                                 edit=edit, ok=ok, chk=chk, combo=combo, items=items)


def ref_of(snapshot: str, needle: str) -> str:
    line = next(l for l in snapshot.splitlines() if needle in l)
    return line.split("[", 1)[1].split("]", 1)[0]


def test_list_and_find_window(app):
    titles = [w["title"] for w in app.s.list_windows()]
    assert titles == ["Untitled - Notepad", "Calculator"]
    assert app.s.find_window("notepad") is app.win
    assert app.s.find_window("pid:200").Name == "Calculator"
    assert app.s.find_window(r"^Calc") .Name == "Calculator"
    with pytest.raises(WinGuiError, match="Open windows"):
        app.s.find_window("Photoshop")


def test_snapshot_compacts_anonymous_containers(app):
    snap = app.s.snapshot("Notepad")
    lines = snap.splitlines()
    assert lines[0].startswith('- Window "Untitled - Notepad" [w')
    assert not any("- Pane" in l for l in lines)  # anonymous pane hidden
    assert '  - Edit "Text Editor"' in snap and 'value="hello"' in snap and "#15" in snap
    assert "disabled" in next(l for l in lines if "Disabled" in l)
    assert "off {toggle}" in next(l for l in lines if "Word wrap" in l)
    full = app.s.snapshot("Notepad", compact=False)
    assert "- Pane" in full


def test_refs_are_stable_across_snapshots(app):
    a = ref_of(app.s.snapshot("Notepad"), "OK")
    b = ref_of(app.s.snapshot("Notepad"), "OK")
    assert a == b


def test_invoke_set_value_toggle(app):
    snap = app.s.snapshot("Notepad")
    assert app.s.invoke(ref_of(snap, '"OK"')) == "invoked"
    assert app.log == ["invoke"]
    with pytest.raises(WinGuiError, match="disabled"):
        app.s.invoke(ref_of(snap, "Disabled"))
    assert app.s.set_value(ref_of(snap, "Text Editor"), "안녕") == 'value="안녕"'
    chk = ref_of(snap, "Word wrap")
    assert app.s.invoke(chk) == "toggled -> on"
    assert app.s.toggle(chk, on=True) == "on"
    assert app.s.toggle(chk, on=False) == "off"


def test_select_in_combo(app):
    ref = ref_of(app.s.snapshot("Notepad"), "Encoding")
    assert app.s.select(ref, "ansi") == "selected 'ANSI'"
    assert app.items[1].patterns[PatternId.SelectionItemPattern].IsSelected
    assert app.combo.patterns[PatternId.ExpandCollapsePattern].ExpandCollapseState == 0


def test_menu_path(app):
    assert app.s.menu("Notepad", "File > Save") == "menu File > Save done"
    assert app.log == ["invoke"]


def test_type_text_and_keys(app):
    ref = ref_of(app.s.snapshot("Notepad"), "Text Editor")
    app.s.type_text(ref, "a{b\n", clear=True)
    assert app.edit.focused
    assert app.uia.keys == ["{Ctrl}a{Delete}", "a", "{", "b", "{Enter}"]


def test_unknown_ref(app):
    with pytest.raises(WinGuiError, match="new snapshot"):
        app.s.invoke("e999")


def test_close_and_wait(app):
    assert "close requested" in app.s.close_window("Notepad")
    assert app.log == ["close"]
    assert app.s.wait_for("Notepad", Selector(name="OK"), timeout=0).startswith("found Button")
    with pytest.raises(WinGuiError, match="Timed out"):
        app.s.wait_for("Notepad", Selector(name="Nope"), timeout=0)


def test_cli_selector_targets(app):
    p = build_parser()
    out = run(p.parse_args(["invoke", "-w", "Notepad", "--name", "ok", "--type", "Button"]), app.s)
    assert out == "invoked"
    out = run(p.parse_args(["set-value", "-w", "Notepad", "--id", "15", "-v", "x"]), app.s)
    assert out == 'value="x"'
    out = run(p.parse_args(["find", "-w", "Notepad", "-t", "button"]), app.s)
    assert out.count("- Button") == 2
