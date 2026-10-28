from test_v142_visual import page
from test_v1422_layout import seed
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_markings_open_as_a_wide_popup_on_a_small_screen(page):
    page.set_viewport_size({'width':1024,'height':720});page.evaluate("()=>{const points=[{x:0,y:0},{x:100,y:0},{x:100,y:20},{x:0,y:20}];M.lane_blocks=[{id:'b',name:'Pista em obras',mode:'total',speed_kmh:20,start_s:0,end_s:null,points}];M.pavement_areas=[{id:'p',name:'Pista nova',kind:'pista_nova',material:'flexivel',source:'picked',points}];refreshLists();abrirAba('marc',true)}")
    pane=page.locator('#rsPanelPopup');assert pane.is_visible()
    box=pane.bounding_box();assert box['width']>900 and box['x']>=0 and box['y']>=0 and box['y']+box['height']<=721
    assert page.locator('#rsPanelBody').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
    for field in ['chainage.mode','blk.0.speed_kmh','blk.0.end_s','pav.0.material']:
        control=page.locator(f'#rsPanelPopup [data-f="{field}"]');assert control.is_visible()
        rect=control.bounding_box();assert rect['x']+rect['width']<=box['x']+box['width']
    page.locator('#rsPanelSave').focus();page.keyboard.press('Tab');assert page.evaluate('document.activeElement.id')=='rsPanelClose'
    screenshot(page,'1428_05_marcacoes_popup_1024')
    page.locator('#rsPanelClose').click();assert pane.is_hidden()


def test_popup_discard_restores_form_and_preserves_previous_pending_edits(gl_page):
    p=gl_page;original=p.locator('#name').input_value();p.evaluate("openSection('Configuração')")
    assert p.locator('#rsPanelPopup').is_visible()
    p.locator('#name').fill('Nome a descartar');p.locator('#name').dispatch_event('change')
    p.wait_for_timeout(1100);assert p.evaluate('savePending')
    p.locator('#rsPanelClose').click();assert p.locator('#rsPanelDecision').is_visible()
    p.locator('[data-choice=continue]').click();assert p.locator('#rsPanelPopup').is_visible()
    p.locator('#rsPanelClose').click();p.locator('[data-choice=discard]').click()
    assert p.locator('#name').input_value()==original
    assert not p.evaluate('savePending')
    assert p.locator('#name').is_enabled()
    screenshot(p,'1428_06_popup_descartar')


def test_popup_save_reaches_the_real_api_and_restores_enabled_controls(gl_page,live):
    p=gl_page;p.evaluate("openSection('Configuração')");p.locator('#name').fill('Configuração da janela salva');p.locator('#name').dispatch_event('change')
    p.locator('#rsPanelClose').click();p.locator('[data-choice=save]').click()
    p.wait_for_function('!RodoviaPanels.opened',timeout=60000)
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']=='Configuração da janela salva'
    assert p.locator('#name').is_enabled() and not p.evaluate('savePending')


def test_presentation_selector_restores_map_local_and_combination(gl_page,live):
    p=gl_page
    # Desde 1.42.24, os campos ficam na expansão de apresentação da aba Projeto.
    p.locator('.rsPresentationExpansion > summary').click()
    assert p.locator('#rsPresentationBase').is_visible() and p.locator('#rsPresentationImages').is_visible()
    # Um mosaico já validado pode ser selecionado sem trocar sua identidade ou apagar fontes.
    p.evaluate("cfg.local_imagery={...cfg.local_imagery,image:'ortofoto.tif',name:'Ortofoto'}")
    for mode,expected,detail in [('mixed','esri',True),('local','local',True),('map','esri',False),('neutral','neutral',False)]:
        p.locator('#rsPresentationBase').select_option(mode)
        assert p.evaluate('cfg.imagery')==expected
        assert p.evaluate('cfg.local_imagery.detail') is detail and p.evaluate('cfg.local_imagery.editor') is detail
        assert p.evaluate('cfg.local_imagery.image')=='ortofoto.tif'
    p.evaluate('save()')
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];assert saved['imagery']=='neutral' and saved['local_imagery']['image']=='ortofoto.tif'
    screenshot(p,'1428_07_imagem_apresentacao')



def test_failed_save_keeps_the_popup_and_the_previous_server_configuration(gl_page,live):
    p=gl_page;before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']
    p.evaluate("openSection('Configuração')");p.locator('#name').fill('');p.locator('#rsPanelSave').click()
    try:p.wait_for_function('document.querySelector("#rsPanelStatus").textContent.startsWith("Não foi salvo:")',timeout=5000)
    except Exception:raise AssertionError(p.evaluate('()=>({status:document.querySelector("#rsPanelStatus").textContent,message:document.querySelector("#message").textContent,popup:RodoviaPanels.opened,name:document.querySelector("#name").value,pending:savePending})'))
    assert p.locator('#rsPanelPopup').is_visible() and p.locator('#name').is_enabled()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']==before
    p.locator('#rsPanelClose').click();p.locator('[data-choice=discard]').click()



def test_discard_keeps_edits_that_existed_before_opening_the_popup(gl_page):
    p=gl_page
    p.evaluate("()=>{$('name').value='Alteração anterior à janela';projectSession.epoch++;savePending=true;clearTimeout(saveTimer);openSection('Configuração')}")
    p.locator('#name').fill('Mudança somente da janela');p.locator('#rsPanelClose').click();p.locator('[data-choice=discard]').click()
    assert p.locator('#name').input_value()=='Alteração anterior à janela' and p.evaluate('savePending')
    p.evaluate('save()');assert not p.evaluate('savePending')



def test_ctrl_s_saves_popup_data_instead_of_claiming_a_deferred_save(gl_page,live):
    p=gl_page;p.evaluate("openSection('Configuração')");p.locator('#name').fill('Salvo pelo atalho da janela');p.keyboard.press('Control+s')
    p.wait_for_function('!RodoviaPanels.opened',timeout=60000)
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']=='Salvo pelo atalho da janela'
    assert not p.evaluate('savePending')


def test_local_selection_generates_a_real_preview_and_preserves_the_geotiff(gl_page,live,tmp_path):
    import hashlib,io
    import numpy as np
    from PIL import Image
    import tifffile
    p=gl_page;source=tmp_path/'ortofoto.tif';pixels=np.full((512,512,3),(35,125,185),dtype=np.uint8)
    keys=[1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,31983]
    tifffile.imwrite(source,pixels,photometric='rgb',extratags=[(33550,'d',3,(4.,4.,0.),False),(33922,'d',6,(0.,0.,0.,499226.,7801024.,0.),False),(34735,'H',len(keys),keys,False)])
    raw=source.read_bytes();url=live[0]+'/api/projects/'+live[1]
    response=p.request.post(url+'/imagery',multipart={'files':{'name':source.name,'mimeType':'image/tiff','buffer':raw},'mode':'replace'})
    assert response.ok,response.text()
    p.evaluate('(id)=>load(id)',live[1]);p.locator('.rsPresentationExpansion > summary').click();p.locator('#rsPresentationBase').select_option('local')
    p.evaluate("async()=>{$('imagery_pixels').value='2048';$('imagery_detail').value='off';$('traffic').checked=false;await start('preview')}")
    job=p.request.get(live[0]+'/api/jobs/'+p.evaluate('lastPolled')).json();assert job['state']=='done',job
    response=p.request.get(url+'/preview.png');assert response.ok,response.text()
    image=np.asarray(Image.open(io.BytesIO(response.body())).convert('RGB'),dtype=int)
    assert np.mean((image[:,:,2]>image[:,:,0]+50)&(image[:,:,2]>image[:,:,1]+20))>.4
    saved=live[2]/live[1]/'imagem_local'/source.name
    assert hashlib.sha256(saved.read_bytes()).digest()==hashlib.sha256(raw).digest()
    screenshot(p,'1428_08_ortofoto_local_real')



def test_discard_restores_flow_diagnostics_and_does_not_rewrite_the_camera(page):
    seed(page);page.evaluate("editor.segments[0].mid=[0,0];selSeg={id:0};showSegProps();previewStale=false")
    before=page.evaluate('JSON.stringify(cfg)');page.locator('#propPanel [data-seg=reverse]').click();page.wait_for_timeout(2800)
    assert page.evaluate('RodoviaFlowStudy.stale') and page.evaluate('M.flow_overrides.length')==1
    assert page.evaluate('JSON.stringify(cfg)')==before
    page.locator('#rsPanelClose').click();page.locator('[data-choice=discard]').click()
    assert not page.evaluate('RodoviaFlowStudy.stale') and page.evaluate('M.flow_overrides.length')==0
    assert not page.evaluate('savePending')
