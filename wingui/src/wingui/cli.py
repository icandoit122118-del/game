"""Command-line front end.

Every CLI call is a fresh process, so refs from an earlier call do not carry
over; target elements with --window plus selector flags instead. Agents that
only have a shell (e.g. Codex without MCP configured) can use this directly.

  wingui windows
  wingui tree  --window Notepad
  wingui find  --window Notepad --type Button
  wingui invoke --window "Save As" --name Save --type Button
  wingui set-value --window "Save As" --id 1001 --value C:\\tmp\\a.txt
  wingui menu --window Notepad --path "File > Save As"
  wingui serve            # MCP stdio server
"""

from __future__ import annotations

import argparse
import json
import sys

from .core import Selector, Session, WinGuiError


def _add_target(p: argparse.ArgumentParser, required: bool = True) -> None:
    p.add_argument("--window", "-w", required=required, help="title substring/regex, hwnd:N or pid:N")
    p.add_argument("--name", "-n", help="element name (substring, case-insensitive)")
    p.add_argument("--id", dest="automation_id", help="AutomationId")
    p.add_argument("--type", "-t", dest="control_type", help="control type, e.g. Button, Edit, MenuItem")
    p.add_argument("--class", dest="class_name", help="Win32 class name")
    p.add_argument("--exact", action="store_true", help="exact name match")
    p.add_argument("--index", type=int, default=0, help="n-th match (default 0)")
    p.add_argument("--timeout", type=float, default=0, help="seconds to wait for the element")


def _selector(a: argparse.Namespace) -> Selector:
    return Selector(name=a.name, automation_id=a.automation_id, control_type=a.control_type,
                    class_name=a.class_name, exact=a.exact, index=a.index)


def _target(s: Session, a: argparse.Namespace):
    sel = _selector(a)
    if sel.empty():
        return s.find_window(a.window)
    return s.locate(a.window, sel, timeout=a.timeout)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="wingui", description="Drive Windows apps via UI Automation (no mouse, no screenshots).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="run the MCP stdio server")
    sub.add_parser("windows", help="list top-level windows")

    p = sub.add_parser("launch", help="start a program and wait for its window")
    p.add_argument("command")
    p.add_argument("args", nargs="*")
    p.add_argument("--timeout", type=float, default=15)

    p = sub.add_parser("tree", help="accessibility snapshot of a window or element")
    _add_target(p)
    p.add_argument("--depth", type=int, default=12)
    p.add_argument("--max-nodes", type=int, default=400)
    p.add_argument("--full", action="store_true", help="show anonymous containers too")
    p.add_argument("--offscreen", action="store_true")

    p = sub.add_parser("find", help="list elements matching a selector")
    _add_target(p)
    p.add_argument("--limit", type=int, default=20)

    for cmd, hlp in (("invoke", "press/activate"), ("text", "read text"), ("focus", "focus element/window")):
        _add_target(sub.add_parser(cmd, help=hlp))

    p = sub.add_parser("set-value", help="set text/number through ValuePattern")
    _add_target(p)
    p.add_argument("--value", "-v", required=True)

    p = sub.add_parser("type", help="type literal text with the keyboard")
    _add_target(p, required=False)
    p.add_argument("--text", required=True)
    p.add_argument("--clear", action="store_true")

    p = sub.add_parser("keys", help="send keys, e.g. '{Ctrl}s'")
    _add_target(p, required=False)
    p.add_argument("keys")

    p = sub.add_parser("toggle", help="toggle a checkbox")
    _add_target(p)
    p.add_argument("--state", choices=["on", "off"])

    p = sub.add_parser("expand", help="expand/collapse")
    _add_target(p)
    p.add_argument("--collapse", action="store_true")

    p = sub.add_parser("select", help="select an item in a combo/list/tab")
    _add_target(p)
    p.add_argument("--item", required=True)

    p = sub.add_parser("menu", help="run a menu path, e.g. 'File > Save'")
    p.add_argument("--window", "-w", required=True)
    p.add_argument("--path", "-p", required=True)

    p = sub.add_parser("close", help="close a window")
    p.add_argument("--window", "-w", required=True)

    p = sub.add_parser("wait", help="wait for a window/element to appear (or --gone)")
    _add_target(p)
    p.add_argument("--gone", action="store_true")
    p.set_defaults(timeout=10)
    return ap


def run(a: argparse.Namespace, s: Session) -> str:
    c = a.cmd
    if c == "windows":
        return json.dumps(s.list_windows(), ensure_ascii=False, indent=1)
    if c == "launch":
        return json.dumps(s.launch(a.command, a.args, a.timeout), ensure_ascii=False)
    if c == "tree":
        return s.snapshot(_target(s, a), max_depth=a.depth, max_nodes=a.max_nodes,
                          compact=not a.full, include_offscreen=a.offscreen)
    if c == "find":
        hits = s.find(a.window, _selector(a), limit=a.limit)
        return "\n".join("- " + s.describe(h, s.ref_for(h)) for h in hits) or "no matches"
    if c == "menu":
        return s.menu(a.window, a.path)
    if c == "close":
        return s.close_window(a.window)
    if c == "wait":
        return s.wait_for(a.window, _selector(a), a.timeout, a.gone)
    if c in ("type", "keys") and not a.window:
        target = None
    else:
        target = _target(s, a)
    if c == "invoke":
        return s.invoke(target)
    if c == "text":
        return s.get_text(target)
    if c == "focus":
        return s.focus(target)
    if c == "set-value":
        return s.set_value(target, a.value)
    if c == "type":
        return s.type_text(target, a.text, a.clear)
    if c == "keys":
        return s.send_keys(a.keys, target)
    if c == "toggle":
        return s.toggle(target, None if a.state is None else a.state == "on")
    if c == "expand":
        return s.expand(target, not a.collapse)
    if c == "select":
        return s.select(target, a.item)
    raise WinGuiError(f"unknown command {c}")


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.cmd == "serve":
        from .server import main as serve

        serve()
        return 0
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Korean titles in cp949 consoles
        except Exception:
            pass
    try:
        print(run(a, Session()))
        return 0
    except WinGuiError as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
