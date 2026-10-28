import pytest
from test_v1425_live_3d import live,gl_page
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


@pytest.mark.parametrize('answer',['save','discard'])
def test_modified_properties_closes_after_decision_and_stays_closed(gl_page,answer):
    p=gl_page
    p.evaluate("()=>{M.pavement_areas=[{id:'p',name:'Original',kind:'pista_nova',points:[{x:500100,y:7800000},{x:500200,y:7800000},{x:500200,y:7800010}]}];sel={key:'pavement_areas',i:0};showProps();psOpenHub('props')}")
    p.locator('#propPanel [data-pp=name]').fill('Modificado')
    p.locator('#propPanel [data-pp=name]').press('Enter')
    p.locator('#rsPanelClose').click();p.locator(f'#rsPanelDecision [data-choice={answer}]').click()
    p.wait_for_function('!RodoviaPanels.opened',timeout=10000);p.wait_for_timeout(500)
    assert p.locator('#rsPanelPopup').is_hidden()
    assert p.locator('#rsPanelDecision').count()==0
    assert p.evaluate('M.pavement_areas[0].name')==('Modificado' if answer=='save' else 'Original')
    screenshot(p,'14214_01_painel_fechado_'+answer)


def test_axis_selection_hides_short_routes_and_refreshes_when_limit_changes(page):
    page.evaluate("()=>{analysis={routes:[{id:'0',direction_key:'0',length_m:19,layer:'MINI'},{id:'1',direction_key:'1',length_m:50,layer:'EIXO'},{id:'2',direction_key:'2',length_m:120,layer:'EIXO'}],layers:[],warnings:[],geometric_length_m:600};cfg.min_route_segment_m=50;$('min_route_segment_m').value='50';showLayers()}")
    assert page.locator('#routes [data-route="0"]').count()==0
    assert page.locator('#routes [data-route="1"]').count()==1
    page.get_by_role('tab',name='Projeto',exact=True).click()
    page.locator('details.rsAdvancedTools > summary').filter(has_text='Parâmetros de apresentação').click()
    page.locator('#min_route_segment_m').select_option('120')
    assert page.locator('#routes [data-route="1"]').count()==0
    assert page.locator('#routes [data-route="2"]').count()==1


def test_discard_closes_even_if_property_refresh_fails(gl_page):
    p=gl_page;p.evaluate("openSection('Configuração')");original=p.locator('#name').input_value()
    p.locator('#name').fill('Descartar');p.locator('#name').dispatch_event('change')
    p.locator('#rsPanelClose').click()
    p.evaluate("()=>{window._oldRefresh=refreshLists;refreshLists=()=>{throw Error('falha simulada na lista')}}")
    p.locator('#rsPanelDecision [data-choice=discard]').click()
    try:
        p.wait_for_function('!RodoviaPanels.opened',timeout=5000)
        assert p.locator('#rsPanelPopup').is_hidden()
        assert p.locator('#name').input_value()==original
        assert not p.evaluate("document.body.classList.contains('rsPanelOpen')")
    finally:p.evaluate('()=>{refreshLists=window._oldRefresh}')


def test_save_modified_text_without_enter_reaches_engine_and_closes(gl_page,live):
    p=gl_page
    p.evaluate("()=>{M.pavement_areas=[{id:'p',name:'Original',kind:'pista_nova',points:[{x:500100,y:7800000},{x:500200,y:7800000},{x:500200,y:7800010}]}];sel={key:'pavement_areas',i:0};showProps();psOpenHub('props')}")
    p.locator('#propPanel [data-pp=name]').fill('Salvo sem Enter')
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=10000)
    assert p.locator('#rsPanelPopup').is_hidden()
    data=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert data['pavement_areas'][0]['name']=='Salvo sem Enter'


def test_expert_guide_teaches_surface_fix_and_can_locate_the_point(page):
    from test_v14213_continuity_ui import present
    from test_v14213_continuity import network,AXIS
    from shapely.geometry import box
    n=network([dict(points=AXIS)],obstacles=[box(290,-20,310,220)])
    segments=present(page,n);target=next(s for s in segments if s['technical_points'])
    page.evaluate('(id)=>{selSeg={id};showSegProps()}',target['id'])
    guide=page.locator('.rsFlowAssistant');guide.locator('summary').click()
    assert 'Em Camadas' in guide.inner_text() and 'sistema' not in guide.locator('h4').inner_text()
    assert guide.locator('[data-assistant-action=layers]').is_visible()
    screenshot(page,'14214_02_assistente_local')
    guide.locator('[data-assistant-action=locate]').click()
    page.wait_for_function('!RodoviaPanels.opened')
    assert page.locator('#rsPanelPopup').is_hidden() and page.locator('#canvas').is_visible()
    page.evaluate('(id)=>{selSeg={id};showSegProps()}',target['id'])
    page.locator('.rsFlowAssistant summary').click()
    page.locator('.rsFlowAssistant [data-assistant-action=layers]').click()
    page.wait_for_function('RodoviaPanels.opened==="hub:layers"')
    page.wait_for_timeout(150)
    assert page.locator('#rsPanelPopup').is_visible()


def test_limit_uses_exact_length_and_preserves_hidden_direction_choices(page):
    page.evaluate("()=>{analysis={routes:[{id:'a',direction_key:'a',length_m:50,length_exact_m:49.999,layer:'EIXO'},{id:'b',direction_key:'b',length_m:120,length_exact_m:120,layer:'EIXO'}],layers:[],warnings:[],geometric_length_m:600};cfg.min_route_segment_m=50;$('min_route_segment_m').value='50';showLayers()}")
    assert page.locator('#routes [data-route=a]').count()==0
    page.evaluate("document.querySelector('#routes [data-route=b]').value='off'")
    page.get_by_role('tab',name='Projeto',exact=True).click()
    page.locator('details.rsAdvancedTools > summary').filter(has_text='Parâmetros de apresentação').click()
    page.locator('#min_route_segment_m').select_option('200')
    assert page.locator('#routes select').count()==0
    page.locator('#min_route_segment_m').select_option('50')
    assert page.locator('#routes [data-route=b]').input_value()=='off'


def test_closed_flow_properties_stays_closed_on_resize_and_can_be_reopened(page):
    seed(page);page.evaluate('()=>{selSeg={id:0};showSegProps()}')
    page.locator('#rsPanelClose').click()
    page.wait_for_function('!RodoviaPanels.opened')
    page.evaluate('resizeCanvas()');page.wait_for_timeout(150)
    assert page.locator('#rsPanelPopup').is_hidden()
    assert page.evaluate('selSeg.id')==0
    page.locator('[data-pshub=props]').click()
    assert page.locator('#rsPanelPopup').is_visible()
