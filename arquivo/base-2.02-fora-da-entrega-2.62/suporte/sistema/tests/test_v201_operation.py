"""Regressões 2.01: vista, confirmação e pintura sem iniciar cálculos."""
import pytest
from test_v1425_live_3d import live, gl_page
from visual_harness import screenshot


def settled(p):
    p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=180000)


def test_resize_preserves_world_center_and_css_scale(gl_page):
    p=gl_page;settled(p)
    p.evaluate('view.s*=1.7;view.ox-=57;view.oy+=23;draw()')
    before=p.evaluate('({...captureProjectView(),dpr:devicePixelRatio})')
    p.set_viewport_size({'width':1024,'height':650});p.wait_for_timeout(250)
    after=p.evaluate('({...captureProjectView(),dpr:devicePixelRatio})')
    assert after['center']['x']==pytest.approx(before['center']['x'],abs=.01)
    assert after['center']['y']==pytest.approx(before['center']['y'],abs=.01)
    assert after['scale']/after['dpr']==pytest.approx(before['scale']/before['dpr'],rel=.001)
    screenshot(p,'201_vista_estavel_1024')


def test_apply_rebases_discard_and_close_without_extra_question(gl_page,live):
    p=gl_page;settled(p);p.evaluate("psOpenHub('video')")
    p.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    original=p.locator('#traffic_density').input_value()
    p.locator('#traffic_density').fill('1.7');p.locator('#traffic_density').dispatch_event('change')
    p.locator('#rsPanelApply').click();p.wait_for_function('!savePending&&!RodoviaPanels.pending')
    assert p.locator('#rsPanelPopup').is_visible()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['traffic_density']==1.7
    p.locator('#traffic_density').fill('2.2');p.locator('#traffic_density').dispatch_event('change')
    p.locator('#rsPanelDiscard').click()
    assert p.locator('#rsPanelPopup').is_hidden() and p.evaluate('collect().traffic_density')==1.7
    p.evaluate("psOpenHub('video')");p.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    p.locator('#traffic_density').fill(original);p.locator('#traffic_density').dispatch_event('change')
    p.locator('#rsPanelApply').click();p.wait_for_function('!savePending&&!RodoviaPanels.pending')
    p.locator('#rsPanelClose').click()
    assert p.locator('#rsPanelPopup').is_hidden() and not p.locator('#rsPanelDecision').count()


def test_failed_apply_keeps_draft_and_allows_retry(gl_page,live):
    p=gl_page;settled(p);p.evaluate("psOpenHub('video')")
    p.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['traffic_density']
    p.locator('#traffic_density').fill('2.4');p.locator('#traffic_density').dispatch_event('change')
    pattern='**/api/projects/'+live[1]+'/config'
    p.route(pattern,lambda r:r.fulfill(status=503,json={'detail':'Falha controlada'}))
    p.locator('#rsPanelApply').click();p.wait_for_function("$('rsPanelStatus').textContent.includes('Não foi salvo')")
    assert p.locator('#rsPanelPopup').is_visible() and not p.locator('#rsPanelApply').is_disabled()
    assert p.locator('#traffic_density').input_value()=='2.4'
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['traffic_density']==before
    p.unroute(pattern);p.locator('#rsPanelApply').click();p.wait_for_function('!savePending&&!RodoviaPanels.pending')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['traffic_density']==2.4
    p.locator('#traffic_density').fill(str(before));p.locator('#traffic_density').dispatch_event('change')
    p.locator('#rsPanelApply').click();p.wait_for_function('!savePending&&!RodoviaPanels.pending');p.locator('#rsPanelClose').click()


def test_model_invalid_input_does_not_call_save_or_leave_busy(gl_page):
    p=gl_page;settled(p)
    p.evaluate("window.rs201Calls=0;RodoviaModelDialog.open({id:'rs201Form',title:'Teste de validação',html:'<label>Comprimento<input name=length type=number required min=1></label>',save:async()=>{window.rs201Calls++;return true}})")
    p.locator('#rs201Form [data-save]').click()
    assert p.evaluate('rs201Calls')==0 and p.locator('#rs201Form').is_visible()
    assert not p.locator('#rs201Form [data-save]').is_disabled()
    p.locator('#rs201Form [name=length]').fill('5');p.locator('#rs201Form [data-save]').click()
    assert p.evaluate('rs201Calls')==1 and p.locator('#rs201Form').count()==0


def test_layer_list_is_alphabetical_without_mutating_catalog(gl_page):
    p=gl_page;settled(p)
    result=p.evaluate("""()=>{const original=sourceLayerCatalog;try{sourceLayerCatalog={source:'input.dxf',layers:['Zeta','Água','eixo 10','Eixo 2'].map(name=>({name,count:1}))};showLayers();return {shown:[...document.querySelectorAll('#layers select')].map(e=>e.dataset.layer),source:sourceLayerCatalog.layers.map(l=>l.name)}}finally{sourceLayerCatalog=original;showLayers()}}""")
    assert result['shown']==['Água','Eixo 2','eixo 10','Zeta']
    assert result['source']==['Zeta','Água','eixo 10','Eixo 2']


def test_materials_appear_locally_without_calculation_or_background_rebuild(gl_page):
    p=gl_page;settled(p)
    requests=[]
    p.on('request',lambda r:requests.append(r.url) if r.method=='POST' and '/api/projects/' in r.url and any(r.url.endswith('/'+kind) for kind in ('analyze','preview','refresh','render','scene3d','rebuild')) else None)
    original=p.evaluate("$('natural_materials_only').checked")
    try:
        p.evaluate("$('natural_materials_only').checked=false;RodoviaLayers.invalidate('technical');draw()")
        before=p.evaluate('canvas.toDataURL()')
        p.evaluate("$('natural_materials_only').checked=true;$('natural_materials_only').dispatchEvent(new Event('change',{bubbles:true}));draw()")
        p.wait_for_function("[...vectorMaterials.values()].some(i=>i.complete&&i.naturalWidth>0)")
        p.wait_for_timeout(150)
        assert p.evaluate('canvas.toDataURL()')!=before
        assert not requests
        assert p.evaluate("[...Object.values(vecPaths)].some(v=>v.surfaces?.size>0)")
        stats=p.evaluate('RodoviaLayers.stats()')
        p.evaluate("$('texture_style').value='artistico';$('texture_style').dispatchEvent(new Event('change',{bubbles:true}));draw()")
        after=p.evaluate('RodoviaLayers.stats()')
        assert after['backgroundBuilds']==stats['backgroundBuilds']
        screenshot(p,'201_materiais_locais')
    finally:
        p.evaluate("value=>{$('natural_materials_only').checked=value;RodoviaLayers.invalidate('technical');draw()}",original)
