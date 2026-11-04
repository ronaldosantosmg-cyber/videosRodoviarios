import os,sys,time,socket,tempfile,subprocess,json,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
r=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 with socket.socket() as sock:
  sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 data=Path(tmp)/'dados';base=f'http://127.0.0.1:{port}'
 env={**os.environ,'RODOVIA_DATA':str(data),'RODOVIA_NO_BROWSER':'1','RODOVIA_PORT':str(port)}
 with (Path(tmp)/'server.log').open('w') as log:
  proc=subprocess.Popen([sys.executable,str(r/'suporte/sistema/run.py')],env=env,stdout=log,stderr=log)
  try:
   for _ in range(100):
    try:
     urllib.request.urlopen(base+'/api/health',timeout=1);break
    except OSError:time.sleep(.1)
   else:raise RuntimeError('Servidor indisponível')
   req=urllib.request.Request(base+'/api/projects',data=b'{}',headers={'Content-Type':'application/json'})
   project=json.load(urllib.request.urlopen(req))['id']
   (data/project/'editor.json').write_text('{"engine_revision":"antiga"}')
   with sync_playwright() as p:
    options={'executable_path':os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']} if os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') else {}
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**options)
    page=browser.new_page();page.add_init_script("localStorage.setItem('rodovia_base',JSON.stringify({mode:'none',ta:1,va:1}))");errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda q:requests.append(q.url))
    page.goto(base);page.wait_for_function('typeof load === "function" && window.Rodovia3D')
    assert page.evaluate('(id)=>load(id)',project) is not False
    page.wait_for_function('window.RodoviaRuntime && document.getElementById("health").textContent.includes("política de exportação conferida")')
    page.evaluate('RodoviaRuntime.open()')
    page.locator('#rsRuntimeIdentity').wait_for(state='visible')
    assert 'loaded_code_sha256' in page.locator('#rsRuntimeIdentity').inner_text()
    page.locator('#rsRuntimeIdentity footer button').click()
    assert 'Verificar instalação' in page.evaluate("RodoviaRuntime.status({version:'3.23',ffmpeg:true})")
    assert 'Verificar instalação' in page.evaluate("RodoviaRuntime.status({version:'3.23',ffmpeg:true,runtime:{disk_changed:null,policy:{probe:{ok:true}}}})")
    assert page.evaluate("RodoviaMenus.definitions().find(m=>m.t==='Cenas e Vídeo').sub.slice(0,3).map(i=>i.t)")==['Preparar Rodovia Studio','Gerar vídeo','Dia e noite']
    assert 'Preparar Rodovia Studio' in page.locator('#analyze').inner_text(),page.locator('#analyze').inner_text()
    assert 'primary' not in (page.locator('#render').get_attribute('class') or '').split()
    page.evaluate("async()=>{M.gantries=[{id:'f',name:'FreeFlow',kind:'portico',a:{x:0,y:0},b:{x:30,y:0},height_m:6,beam_width_m:.8},{id:'s',name:'Sacrifício',kind:'portico',a:{x:0,y:50},b:{x:40,y:50},height_m:6,beam_width_m:.8}];await save();await load(pid);await COMANDOS.get('AUDITARMEDIDAS')()}")
    page.locator('#rsDimensionAudit [data-span="0"]').fill('12')
    page.locator('#rsDimensionAudit [data-span="1"]').fill('18')
    page.locator('#rsDimensionAudit [data-save]').click()
    page.locator('#rsDimensionAudit').wait_for(state='detached')
    dimensions=page.evaluate("async()=>await api(`/api/projects/${pid}/dimension-audit`)")
    assert [round(g['crossing_m'],6) for g in dimensions['gantries']]==[12,18]
    assert [round(g['support_axis_distance_m'],6) for g in dimensions['gantries']]==[12.9,18.9]
    for mode in ['off','transition','night']:
     page.evaluate('RodoviaLighting.open()')
     page.locator('#rsDayNight [data-mode]').select_option(mode)
     page.locator('#rsDayNight [data-apply]').click()
     page.wait_for_function('(mode)=>cfg.day_night===mode && !document.querySelector("#rsDayNight[aria-busy]")',arg=mode)
     assert page.request.get(base+'/api/projects/'+project).json()['config']['day_night']==mode
     assert page.locator('#rsDayNight').is_visible()
     page.locator('#rsDayNight [data-save]').click()
     page.locator('#rsDayNight').wait_for(state='detached')
     page.evaluate('(id)=>load(id)',project)
     assert page.evaluate('cfg.day_night')==mode
    # Cancelar uma escolha diferente não modifica o modo já confirmado.
    page.evaluate('RodoviaLighting.open()')
    page.locator('#rsDayNight [data-mode]').select_option('off')
    page.locator('#rsDayNight footer [data-close]').click()
    page.locator('[data-draft-choice="discard"]').click()
    page.locator('#rsDayNight').wait_for(state='detached')
    assert page.request.get(base+'/api/projects/'+project).json()['config']['day_night']=='night'
    # Um comando com conteúdo extenso mantém cabeçalho/rodapé abaixo dos menus.
    page.set_viewport_size({'width':760,'height':620})
    page.evaluate('RodoviaLighting.open()')
    page.evaluate("()=>{const tall=document.createElement('div');tall.style.height='2000px';document.querySelector('#rsDayNight>section').append(tall)}")
    model=page.locator('#rsDayNight').bounding_box();bar=page.locator('#menuBar').bounding_box()
    assert model['y']>=bar['y']+bar['height'] and model['y']+model['height']<=620-8,(model,bar)
    page.locator('#rsDayNight footer [data-close]').click()
    page.locator('#rsDayNight').wait_for(state='detached')
    def menus_visible():
     result=page.evaluate('''()=>[...document.querySelectorAll('[data-rs-menu]')].map(b=>{
      const r=b.getBoundingClientRect(),e=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
      return {name:b.textContent.trim(),visible:r.width>0&&r.height>0&&r.x>=0&&r.right<=innerWidth&&r.y>=0&&r.bottom<=innerHeight,clickable:!!e&&(e===b||b.contains(e))};
     })''')
     assert len(result)==7 and all(m['visible'] and m['clickable'] for m in result),result
    def bounds():
     return page.locator('#canvas').bounding_box()
    def same(before):
     page.wait_for_timeout(100)
     after=bounds()
     assert max(abs(before[k]-after[k]) for k in before)<1, (before,after)
    for w,h in [(1920,1080),(1366,768),(1024,768),(760,620)]:
     page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
     menus_visible()
     baseline=bounds();view=page.evaluate('JSON.stringify(view)')
     titles=page.evaluate('pnItens.map(x=>x.t)')
     for title in titles:
      page.evaluate('(title)=>openSection(title)',title)
      page.locator('#rsPanelPopup').wait_for(state='visible');same(baseline)
      menus_visible()
      page.locator('[data-rs-menu="4"]').click()
      assert page.get_by_role('menuitem',name='Dia e noite',exact=True).is_visible()
      page.evaluate('RodoviaMenus.close()')
      page.locator('#rsPanelClose').click();page.locator('#rsPanelPopup').wait_for(state='hidden');same(baseline)
     assert page.evaluate('JSON.stringify(view)')==view
     page.evaluate("setTool('oae')");same(baseline)
     assert page.locator('#toolOptions').is_visible()
     page.evaluate("setTool('pan')");same(baseline)
     page.locator('#dwCmdLauncher').click();same(baseline)
     page.locator('#dwCommandDrawer [data-dwc=close]').click();same(baseline)
    page.set_viewport_size({'width':1366,'height':768});page.wait_for_timeout(120);baseline=bounds()
    page.evaluate("openSection('Configuração')")
    page.locator('#name').fill('Aplicado sem deslocar')
    page.locator('#rsPanelApply').click()
    page.wait_for_function("document.getElementById('rsPanelStatus').textContent.includes('aplicadas')")
    assert page.locator('#rsPanelPopup').is_visible();same(baseline)
    assert page.request.get(base+'/api/projects/'+project).json()['config']['name']=='Aplicado sem deslocar'
    page.locator('#name').fill('Alteração descartada')
    page.locator('[data-rs-menu="4"]').click()
    assert page.locator('#rsPanelPopup').is_visible()
    assert page.locator('#rsPanelDecision').count()==0
    page.get_by_role('menuitem',name='Dia e noite',exact=True).click()
    page.locator('#rsPanelDecision [data-choice="continue"]').click()
    assert page.locator('#rsPanelPopup').is_visible()
    assert page.locator('#name').input_value()=='Alteração descartada'
    assert page.locator('#rsDayNight').count()==0
    page.evaluate('RodoviaMenus.close()')
    page.locator('#rsPanelDiscard').click();page.locator('#rsPanelPopup').wait_for(state='hidden');same(baseline)
    assert page.request.get(base+'/api/projects/'+project).json()['config']['name']=='Aplicado sem deslocar'
    page.evaluate("openSection('Configuração')")
    header=page.locator('#rsPanelPopup>header').bounding_box()
    page.mouse.move(header['x']+40,header['y']+15);page.mouse.down();page.mouse.move(header['x']+75,header['y']+35);page.mouse.up();same(baseline)
    header=page.locator('#rsPanelPopup>header').bounding_box()
    page.mouse.move(header['x']+40,header['y']+15);page.mouse.down();page.mouse.move(header['x']+40,0);page.mouse.up();same(baseline)
    menus_visible()
    page.set_viewport_size({'width':760,'height':620});page.wait_for_timeout(150)
    menus_visible()
    popup=page.locator('#rsPanelPopup').bounding_box()
    assert popup['y']+popup['height']<=620-7,popup
    page.set_viewport_size({'width':1366,'height':768});page.wait_for_timeout(150)
    page.locator('#rsPanelCancel').click();page.locator('#rsPanelPopup').wait_for(state='hidden');same(baseline)
    assert not errors,errors
    # Cria resultados válidos em um projeto temporário para conferir a reabertura sem novo trabalho.
    setup = r"""
import sys,json
from pathlib import Path
import ezdxf
from PIL import Image
sys.path.insert(0,sys.argv[1])
from app import store
from app.models import Settings
from app.render import Scene
from app.artifacts import begin,finish
from app.webmap import write_vectors
folder=Path(sys.argv[2]);config=json.loads((folder/'config.json').read_text())
config.update(imagery='neutral',hydrography=False,traffic=False,width=1280,duration_s=3,layers={'axis':['EIXO']},route_directions={'layer:EIXO':'forward'})
s=Settings.model_validate(config);store.write_json(folder/'config.json',s.model_dump())
doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799993),(500300,7799993),(500300,7800007),(500000,7800007)],is_closed=True)
doc.saveas(folder/'input.dxf');ticket=begin(folder,'cenario','refresh',s)
scene=Scene(folder,s);im,meta=scene.frame(0,overview=True);Image.fromarray(im).save(folder/'preview.png')
store.write_json(folder/'preview.json',meta);store.write_json(folder/'editor.json',scene.editor_data());store.write_json(folder/'analysis.json',scene.report)
write_vectors(folder,scene.items,scene.axis,s.crs);finish(folder,ticket)
"""
    subprocess.run([sys.executable,'-c',setup,str(r/'suporte/sistema'),str(data/project)],env=env,check=True,timeout=45,capture_output=True)
    page.evaluate('(id)=>load(id,{resultsOnly:true,syncConfig:true})',project)
    before_cfg=page.request.get(base+'/api/projects/'+project).json()
    client_cfg=page.evaluate('collect()')
    differences={k:[client_cfg[k],before_cfg['config'].get(k)] for k in client_cfg if client_cfg[k]!=before_cfg['config'].get(k)}
    assert not differences,differences
    requests.clear()
    page.evaluate('(id)=>load(id)',project)
    assert not any(url.endswith('/refresh') or url.endswith('/analyze') for url in requests),requests
    assert page.request.get(base+'/api/projects/'+project).json()['artifacts']['preview']['state']=='ready'
    assert not errors,errors
    times=page.evaluate("""()=>{const original=structuredClone(cfg);fill({...original,duration_s:3,preview_time_s:1.25});const short=collect().preview_time_s;fill({...original,duration_s:202,preview_time_s:30});const long=collect().preview_time_s;fill(original);return [short,long]}""")
    assert times==[1.25,30],times
    browser.close()
   print('Janelas: 4 resoluções, 9 painéis, ferramentas e linha de comando sem deslocar o canvas; aplicar, descartar, cancelar e arrastar verificados.')
  finally:
   proc.terminate();proc.wait(timeout=10)
