from test_v142_visual import page
from test_v1422_layout import seed


def test_cancelled_drag_restores_geometry_and_releases_cursor(page):
    seed(page)
    original=page.evaluate('JSON.stringify(M)')
    page.evaluate("()=>{checkpoint();M.pavement_areas[0].points[0].x+=50;drag={type:'grip',moved:true};canvas.style.cursor='move';canvas.dispatchEvent(new PointerEvent('pointercancel',{pointerId:1,bubbles:true}))}")
    assert page.evaluate('JSON.stringify(M)')==original
    assert page.evaluate('drag===null && sb===null')
    assert page.locator('#canvas').evaluate("e=>e.style.cursor")=='grab'


def test_blur_ends_pan_without_changing_geometry(page):
    seed(page);original=page.evaluate('JSON.stringify(M)')
    page.evaluate("drag={type:'pan'};canvas.style.cursor='grabbing';window.dispatchEvent(new Event('blur'))")
    assert page.evaluate('drag===null')
    assert page.evaluate('JSON.stringify(M)')==original
    assert page.locator('#canvas').evaluate("e=>e.style.cursor")=='grab'
