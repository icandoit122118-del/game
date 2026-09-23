# Agent guide: operating Windows GUI apps

This repo provides `wingui`, which exposes Windows apps through the UI Automation (UIA)
accessibility tree. Do not take screenshots and do not click by coordinates.

## With the MCP server (`wingui` tools)

1. `list_windows` or `launch("notepad")` → get a window ref (`w3`).
2. `snapshot("w3")` → a tree of lines like
   `- Button "Save" [e12] #1 {invoke}` or `- Edit "File name:" [e7] value="" {value}`.
3. Act on refs: `set_value(e7, "...")`, `invoke(e12)`, `toggle`, `select(ref, item)`,
   `expand`, `menu("w3", "File > Save As")`, `get_text(ref)`.
4. `wait_for(...)` when a dialog or content should appear, then snapshot again to verify.

Rules of thumb:
- `set_value` beats `type_text`; `invoke` beats `send_keys`.
- If the tree is huge, `snapshot` an element ref to zoom into a subtree, or use `find`.
- An element without `{actions}` usually has an actionable parent or child.
- If an app shows almost nothing (games, canvases), use `send_keys` on the focused window.

## Shell only (no MCP)

Each call is a new process, so use selectors instead of refs:

```
wingui windows
wingui tree   -w Notepad
wingui find   -w Notepad -t Button
wingui set-value -w "Save As" --id 1001 -v "C:\\temp\\a.txt"
wingui invoke -w "Save As" -n Save -t Button --exact
wingui menu   -w Notepad -p "File > Save As"
wingui text   -w Notepad -t Document
```

Exit code 1 plus `error: ...` on stderr means the target was not found or the action is not supported.

## Development

```
pip install -e .[dev]
pytest            # uses a fake UIA tree, runs on any OS
```
