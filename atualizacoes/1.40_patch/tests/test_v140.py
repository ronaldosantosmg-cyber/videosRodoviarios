from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (BASE / rel).read_text(encoding="utf-8")


def test_v140_desktop_workspace_files():
    js = read("app/js/50_desktop_workspace.js")
    css = read("app/desktop140.css")

    assert "Desktop Workspace" in js
    assert "RodoviaDesktopWorkspace" in js
    assert "ResizeObserver" in js
    assert "dwCommandDrawer" in js
    assert "dwProjectFocus" in js
    assert "Ctrl+Espaço" in js

    assert ".dwCommandDrawer" in css
    assert ".dwProjectFocus" in css
    assert "position:relative" in css
    assert "prefers-reduced-motion" in css


def test_command_drawer_is_docked_not_overlay():
    css = read("app/desktop140.css")
    drawer = css.split(".dwCommandDrawer{", 1)[1].split("}", 1)[0]
    assert "position:relative" in drawer
    assert "position:fixed" not in drawer
    assert "position:absolute" not in drawer


def test_panels_are_forced_into_layout_flow():
    css = read("app/desktop140.css")
    js = read("app/js/50_desktop_workspace.js")
    assert "position:static!important" in css
    assert "forceDockedPanels" in js
    assert "pnEstado.fixado=true" in js
    assert "dockState.fixada=true" in js


def test_workspace_has_keyboard_and_accessibility_guards():
    js = read("app/js/50_desktop_workspace.js")
    assert "isEditableTarget" in js
    assert "aria-expanded" in js
    assert "aria-controls" in js
    assert "focus-visible" in read("app/desktop140.css")


def test_workspace_engine_isolation():
    js = read("app/js/50_desktop_workspace.js")
    forbidden = ["analyze_road", "render_video", "traffic_flows", "dxf", "dwg"]
    assert not any(token in js for token in forbidden)
