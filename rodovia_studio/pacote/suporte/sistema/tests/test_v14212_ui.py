import io,json
import numpy as np
import tifffile
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot


def test_automatic_job_does_not_close_a_panel_opened_while_save_is_pending(gl_page):
    p=gl_page
    result=p.evaluate('''async()=>{
      const original=save;let release;save=()=>new Promise(r=>release=r);
      try{
        const pending=start('analyze',undefined,{automatic:true});
        psOpenHub('video');const opened=RodoviaPanels.opened;
        release();const completed=await pending;
        return {completed,opened,after:RodoviaPanels.opened,pending:taskRequestPending};
      }finally{save=original}
    }''')
    assert result==dict(completed=False,opened='hub:video',after='hub:video',pending=False)
    assert p.locator('#rsPanelPopup').is_visible()


def upload_image(page,live):
    pixels=np.full((256,256,3),100,np.uint8);pixels[20:95,25:85]=[205,65,35];pixels[120:220,20:100]=[30,145,30];pixels[30:210,170:235]=[25,65,180]
    data=io.BytesIO();keys=(1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,31983)
    tifffile.imwrite(data,pixels,photometric='rgb',extratags=[(33550,'d',3,(4.,4.,0.),False),(33922,'d',6,(0.,0.,0.,499738.,7800512.,0.),False),(34735,'H',len(keys),keys,False)])
    response=page.request.post(live[0]+'/api/projects/'+live[1]+'/imagery',multipart={'files':{'name':'aerea.tif','mimeType':'image/tiff','buffer':data.getvalue()},'mode':'replace'})
    assert response.ok,response.text();page.evaluate('(id)=>load(id)',live[1]);page.wait_for_function('!task && !taskRequestPending',timeout=60000)
    page.evaluate('RodoviaImageContext.refresh()');page.wait_for_selector('#rsToolPanel0 [data-rs-command=IMAGEMCONTORNOS]',state='visible')


def test_image_tool_only_appears_after_local_image_and_runs_real_background_job(gl_page,live):
    p=gl_page
    assert not p.locator('#rsToolPanel0 [data-rs-command=IMAGEMCONTORNOS]').is_visible()
    upload_image(p,live);p.locator('#rsToolPanel0 [data-rs-command=IMAGEMCONTORNOS]').click();p.wait_for_selector('#rsImageContext')
    p.locator('#rsImageContext [name=pixels]').select_option('512')
    p.locator('#rsImageContext [data-analyze]').click()
    p.wait_for_selector('#rsImageContext[open] [data-feature]',timeout=60000)
    result=p.request.get(live[0]+'/api/projects/'+live[1]+'/image_context').json()
    assert result['features'] and result['job_id']
    assert not any(f['reviewed'] for f in result['features'])
    screenshot(p,'14212_01_contornos_sugeridos_grupos')
    # Confirma um objeto e verifica que seu estado chega à configuração real.
    building=next(f for f in result['features'] if f['role']=='building')
    row=p.locator(f'#rsImageContext [data-feature="{building["id"]}"]');row.locator('summary').click()
    row.locator('[data-field=role]').select_option('building')
    row=p.locator(f'#rsImageContext [data-feature="{building["id"]}"]')
    if not row.get_attribute('open'):row.locator('summary').click()
    row.locator('[data-field=name]').fill('Edificação revisada');row.locator('[data-field=height_m]').fill('8');row.locator('[data-field=reviewed]').check();row.locator('[data-field=height_m]').blur()
    p.locator('#rsImageContext footer [data-save]').click()
    try:p.wait_for_selector('#rsImageContext',state='detached',timeout=15000)
    except Exception:raise AssertionError(p.locator('#rsImageContext [data-error]').inner_text())
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert any(f['reviewed'] and f['height_m']==8 and f['name']=='Edificação revisada' for f in config['image_features'])
    p.reload(wait_until='networkidle');p.wait_for_function('M.image_features?.some(f=>f.name==="Edificação revisada")',timeout=15000)
    screenshot(p,'14212_02_contornos_persistentes')
    # Proveniência: transformação da imagem invalida as sugestões anteriores.
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];config['local_imagery']['shift_x']=1
    assert p.request.put(live[0]+'/api/projects/'+live[1]+'/config',data=config).ok
    assert p.request.get(live[0]+'/api/projects/'+live[1]+'/image_context').status==409


def test_sections_dialog_applies_asymmetric_bands_to_the_actual_engine(gl_page,live):
    p=gl_page;p.evaluate("async()=>{M.route_alignments=[{id:'section-route',name:'Eixo das seções',points:[{x:500050,y:7800000},{x:500450,y:7800000}],type:'simples',lanes:1,median_m:0,lane_width_m:3.5,taper_m:40,enabled:true,level:0,sections:[]}];changed();await save();RodoviaSections.open(0)}")
    p.locator('#rsRoadSections [name=template]').select_option('simples3');p.locator('#rsRoadSections [name=rightCount]').select_option('3')
    p.locator('#rsRoadSections [data-right] select').nth(2).select_option('acostamento');p.locator('#rsRoadSections [data-right] input[type=number]').nth(2).fill('2.5')
    p.locator('#rsRoadSections [data-add-section]').click();screenshot(p,'14212_03_secoes_assimetricas')
    p.locator('#rsRoadSections footer [data-calculate]').click();p.wait_for_selector('#rsRoadSections',state='detached',timeout=15000)
    try:p.wait_for_function('!task && !taskRequestPending && !!editor',timeout=60000)
    except Exception:raise AssertionError(str(p.evaluate('({task,taskRequestPending,message:document.getElementById("message").textContent,editor:!!editor})'))+' | '+(live[2]/live[1]/'analysis.json').read_text()[-3500:])
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];section=config['route_alignments'][0]['cross_sections'][0]
    assert len(section['left'])==1 and len(section['right'])==3 and section['right'][2]['kind']=='acostamento'
    assert len([s for s in p.evaluate('editor.segments') if s.get('route')=='section-route'])==3
    assert p.evaluate('editor.itineraries')>=3


def test_new_small_dialog_closing_offers_save_discard_or_continue(gl_page):
    p=gl_page;p.set_viewport_size({'width':1024,'height':720})
    p.evaluate("M.route_alignments=[{id:'r',name:'Rascunho',points:[{x:500050,y:7800000},{x:500450,y:7800000}],type:'simples',lanes:1,enabled:true,sections:[]}];RodoviaSections.open(0)")
    p.locator('#rsRoadSections [name=start]').fill('5');footer=p.locator('#rsRoadSections footer').bounding_box()
    assert footer['y']+footer['height']<=720
    p.locator('#rsRoadSections header [data-close]').click();p.get_by_role('button',name='Continuar editando',exact=True).click()
    assert p.locator('#rsRoadSections').is_visible()
    p.locator('#rsRoadSections header [data-close]').click();screenshot(p,'14212_04_janela_salvar_descartar')
    p.get_by_role('button',name='Descartar',exact=True).click();assert p.locator('#rsRoadSections').count()==0


def test_coordinates_km_and_existing_section_edit_use_the_same_stations(gl_page,live):
    p=gl_page;p.evaluate("async()=>{M.route_alignments=[{id:'limits',name:'Limites por coordenadas',points:[{x:500050,y:7800000},{x:500450,y:7800000}],type:'simples',lanes:1,enabled:true,sections:[]}];changed();await save();RodoviaSections.open(0)}")
    d=p.locator('#rsRoadSections');d.locator('[name=reference]').select_option('coordinates')
    for name,value in [('startX','500100'),('startY','7800000'),('endX','500200'),('endY','7800000')]:d.locator('[name='+name+']').fill(value)
    d.locator('[data-add-section]').click();d.locator('[name=origin]').fill('284+000');d.locator('[name=reference]').select_option('km');d.locator('[name=start]').fill('284+150');d.locator('[name=end]').fill('284+250');d.locator('[data-add-section]').click()
    d.locator('[data-edit-section="0"]').click();d.locator('[name=start]').fill('40');d.locator('[data-add-section]').click()
    d.locator('footer [data-save]').click();p.wait_for_selector('#rsRoadSections',state='detached',timeout=15000)
    result=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['route_alignments'][0]
    assert [(round(s['start_m']),round(s['end_m'])) for s in result['cross_sections']]==[(40,150),(150,250)]
    assert result['km_origin_m']==284000


def test_failed_save_keeps_dialog_and_discard_restores_the_model(gl_page,live):
    p=gl_page;p.evaluate("async()=>{M.route_alignments=[{id:'save-error',name:'Teste de gravação',points:[{x:500050,y:7800000},{x:500450,y:7800000}],type:'simples',lanes:1,enabled:true,sections:[]}];changed();await save();RodoviaSections.open(0)}")
    p.locator('#rsRoadSections [data-add-section]').click()
    pattern='**/api/projects/'+live[1]+'/config'
    p.route(pattern,lambda route:route.fulfill(status=422,content_type='application/json',body='{"detail":"Falha de gravação controlada para teste."}') if route.request.method=='PUT' else route.continue_())
    p.locator('#rsRoadSections footer [data-save]').click();p.wait_for_function("document.querySelector('#rsRoadSections [data-error]').textContent.includes('Falha de gravação')")
    assert p.evaluate('(M.route_alignments[0].cross_sections||[]).length')==0
    p.locator('#rsRoadSections header [data-close]').click();p.get_by_role('button',name='Descartar',exact=True).click()
    assert not p.locator('#rsRoadSections').count()
    p.unroute(pattern)
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert not config['route_alignments'][0]['cross_sections']


def test_image_only_project_can_analyze_and_show_its_georeferenced_capture(gl_page,live):
    from app.models import Settings
    p=gl_page;response=p.request.post(live[0]+'/api/projects',data=Settings(name='Somente imagem',imagery='local').model_dump());assert response.status==201,response.text()
    pid=response.json()['id'];other=(live[0],pid,live[2]);upload_image(p,other)
    assert p.locator('[data-rs-tool=imagesample]').count()==0
    p.locator('#rsToolPanel0 [data-rs-command=IMAGEMCONTORNOS]').click();p.wait_for_selector('#rsImageContext')
    p.locator('#rsImageContext [name=pixels]').select_option('512');p.locator('#rsImageContext [data-analyze]').click()
    p.wait_for_selector('#rsImageContext[open] [data-feature]',timeout=60000)
    assert p.evaluate('ready() && meta.context_capture && !geo')
    assert p.evaluate('C2W(...W2C({x:500250,y:7800000}))')=={'x':500250,'y':7800000}
    screenshot(p,'14212_07_imagem_sem_dxf')
    p.locator('#rsImageContext header [data-close]').click();p.get_by_role('button',name='Descartar',exact=True).click()
    result=p.request.get(live[0]+'/api/projects/'+pid+'/image_context').json();file=live[2]/pid/'contexto_imagem/fontes'/result['capture'];before=file.read_bytes()
    file.write_bytes(before[:-1]+bytes([before[-1]^1]))
    assert p.request.get(live[0]+'/api/projects/'+pid+'/image_context/capture.png').status==409
    file.write_bytes(before)
