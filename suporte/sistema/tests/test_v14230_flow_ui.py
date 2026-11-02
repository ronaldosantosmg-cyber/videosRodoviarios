import json
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def open_policy(p):
    p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    p.evaluate('RodoviaFlowPolicy.open()');d=p.locator('#rsFlowPolicy');d.wait_for(state='visible');return d


def test_independent_controls_vdm_fleet_and_entry_are_saved(gl_page,live):
    p=gl_page;p.set_viewport_size({'width':760,'height':820});d=open_policy(p)
    assert d.locator('[data-number=traffic_entry_inset_m]').input_value()=='5'
    d.locator('[data-policy=heavy_shoulder_overtake]').check()
    d.locator('[data-policy=traffic_route_only]').check()
    assert d.locator('[data-policy=traffic_respect_signals]').is_checked() and d.locator('[data-policy=traffic_prevent_collisions]').is_checked()
    d.locator('[data-vdm]').fill('12000');d.locator('[data-number=traffic_forward_share_pct]').fill('60');d.locator('[data-fleet]').select_option('engenharia')
    screenshot(p,'14230_regras_controles_vdm_frota')
    assert d.evaluate('e=>e.getBoundingClientRect().right<=innerWidth')
    d.locator('[data-save]').click();p.wait_for_function("!document.querySelector('#rsFlowPolicy')",timeout=30000)
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert cfg['traffic_entry_inset_m']==5 and cfg['traffic_route_only'] and cfg['traffic_respect_signals'] and cfg['traffic_prevent_collisions']
    assert cfg['traffic_vdm']==12000 and cfg['traffic_forward_share_pct']==60 and cfg['vehicle_mix']=='engenharia' and cfg['traffic_model']=='simulado'
    assert cfg['traffic_demand_vphpl'] is None and cfg['heavy_shoulder_overtake']


def test_apply_and_calculate_delivers_vdm_and_controls_to_real_engine(gl_page,live):
    p=gl_page;d=open_policy(p);d.locator('[data-vdm]').fill('5000')
    d.locator('[data-policy=traffic_route_only]').check()
    d.locator('[data-policy=traffic_respect_signals]').check();d.locator('[data-policy=traffic_prevent_collisions]').check()
    d.locator('[data-calculate]').click();p.wait_for_function("!document.querySelector('#rsFlowPolicy')",timeout=30000)
    p.wait_for_function("""async()=>{const r=await fetch('/api/projects/'+pid);const data=await r.json();return data.analysis?.traffic_simulation?.distribution?.vdm===5000}""",timeout=120000)
    data=p.request.get(live[0]+'/api/projects/'+live[1]).json();sim=data['analysis']['traffic_simulation']
    assert sim['route_only'] and sim['entry_inset_m']==5 and sim['signals_respected'] and sim['collision_prevention']


def test_discard_does_not_apply_controls_or_route_authorizations(gl_page,live):
    p=gl_page;before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];d=open_policy(p)
    d.locator('[data-policy=traffic_respect_signals]').uncheck();d.locator('[data-number=traffic_entry_inset_m]').fill('9')
    d.get_by_role('button',name='Cancelar',exact=True).click();p.get_by_role('button',name='Descartar',exact=True).click()
    assert not d.is_visible()
    after=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];assert before==after


def test_editing_density_exits_vdm_in_ui_and_saved_configuration(gl_page,live):
    p=gl_page;p.evaluate("psOpenHub('video')");p.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    p.locator('#traffic_density').fill('3');p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=30000)
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];assert cfg['traffic_vdm'] is None and cfg['traffic_density']==3


def test_disconnected_deletion_requires_selection_and_confirmation(gl_page,live):
    p=gl_page;p.evaluate("async()=>{await start('analyze');const s=editor.segments.find(s=>s.origin_key&&!s.disabled);window.testRemovedOrigin=s.origin_key;s.technical_message='Trecho sem itinerário utilizável; revise as ligações.';s.technical_status='problem'}")
    d=open_policy(p);details=d.locator('details').filter(has=p.locator('[data-disconnected]')).first;details.locator('summary').click()
    boxes=d.locator('[data-disconnected]');assert boxes.count()>0 and not boxes.first.is_checked();boxes.first.check()
    old=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['flow_overrides']
    d.locator('[data-save]').click();q=p.get_by_role('dialog',name='Confirmar exclusão da circulação',exact=True);q.wait_for()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['flow_overrides']==old
    q.get_by_role('button',name='Excluir da circulação',exact=True).click();p.wait_for_function("!document.querySelector('#rsFlowPolicy')",timeout=30000)
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];assert any(o['action']=='disable' and o['target_key']==p.evaluate('testRemovedOrigin') for o in cfg['flow_overrides'])
    assert p.evaluate('undoStack.length')>0
