import pytest
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_update_progress_share_snap_row_and_live_coordinates_follow_continuous_mouse(page):
    seed(page)
    assert page.locator('#bottomBar #rsUpdateMode').count()==1 and page.locator('#bottomBar #progCard').count()==1
    assert page.locator('#rsStudyFooter #rsActiveTool').is_hidden() and page.locator('#rsStudyFooter .dwCursor').is_hidden()
    rect=page.locator('#canvas').bounding_box();page.mouse.move(rect['x']+rect['width']*.3,rect['y']+rect['height']*.5)
    page.wait_for_timeout(100);before=page.locator('#rsLiveCoordinates').inner_text()
    # Coleta durante a movimentação, sem aguardar a parada/debounce do mouse.
    page.mouse.move(rect['x']+rect['width']*.7,rect['y']+rect['height']*.5,steps=30)
    page.wait_for_timeout(30);after=page.locator('#rsLiveCoordinates').inner_text()
    assert before!=after and 'X ' in after and 'Y ' in after
    assert page.locator('#rsLiveCoordinates').get_attribute('title')
    snap=page.locator('#statusBar span').filter(has_text='SNAP').bounding_box();update=page.locator('#rsUpdateProject').bounding_box()
    assert abs((snap['y']+snap['height']/2)-(update['y']+update['height']/2))<8
    screenshot(page,'14224_rodape_unico_coordenadas')


def test_video_advanced_tools_expand_inline_and_retract(page):
    page.get_by_role('tab',name='Vídeo',exact=True).click();panel=page.locator('[data-activity="Vídeo"]');advanced=panel.locator('.rsAdvancedTools')
    advanced.locator('summary').click();assert advanced.get_attribute('open') is not None
    assert advanced.get_by_role('button',name='Vídeos gerados',exact=True).is_visible()
    assert page.evaluate("getComputedStyle(document.querySelector('[data-activity=\"Vídeo\"] .rsInlineExpansion')).display")=='flex'
    screenshot(page,'14224_video_ferramentas_expandidas')
    advanced.get_by_role('button',name='Recolher ferramentas',exact=True).click();assert advanced.get_attribute('open') is None


def test_project_presentation_fields_stay_inside_expansion_after_reload(page):
    page.get_by_role('tab',name='Projeto',exact=True).click();d=page.locator('.rsPresentationExpansion');d.locator('summary').click()
    page.evaluate('psSyncActivities()')
    assert page.locator('.rsPresentationExpansion #rsTechnicalOptions').count()==1
    assert page.locator('#rsPresentationBase').is_visible()
    boxes=page.evaluate("[...document.querySelectorAll('#rsTechnicalOptions label')].map(x=>{const r=x.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})")
    for i,a in enumerate(boxes):
        assert a['h']>=25
        for b in boxes[i+1:]:assert min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x'])<=1 or min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y'])<=1
    screenshot(page,'14224_parametros_apresentacao')
