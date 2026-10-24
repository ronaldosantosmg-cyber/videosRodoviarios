"""1.29 (tela): interdição só oferece Parcial/Total e um valor inválido é corrigido antes de salvar; nomes inválidos
recusados; arquivos DXF e KMZ escolhidos separadamente ficam os dois carregados; aparência de taludes, água e
sinalização; faixa de opções (ribbon) e título da janela."""
import os,socket,threading,time
import numpy as np,cv2,pytest
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})
def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_129_ui(junction,tmp_path):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    blk={'id':'b1','name':'Interdição 1','points':[{'x':500100,'y':7799992},{'x':500140,'y':7799992},{'x':500140,'y':7799999}],'mode':'partial'}
    pid=c.post('/api/projects',json=S(name='Trecho Teste',lane_blocks=[blk],highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}]).model_dump()).json()['id']
    (tmp_path/'Projeto rev3.dxf').write_bytes((junction/'input.dxf').read_bytes())
    (tmp_path/'eixo.kml').write_bytes(b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><LineString><coordinates>-45.0,-19.9 -45.001,-19.9</coordinates></LineString></Placemark></kml>')
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof cfg!=="undefined"&&cfg&&pid&&SCHEMA&&cfg.name==="Trecho Teste"&&filesInfo',timeout=20000);ev=page.evaluate
            assert ev('document.title')=='Trecho Teste — Rodovia Studio'
            # Arquivos escolhidos um de cada vez: os dois ficam carregados, com o nome original.
            page.set_input_files('#fileDxf',str(tmp_path/'Projeto rev3.dxf'));page.wait_for_function("filesInfo&&filesInfo.dxf")
            page.set_input_files('#fileKmz',str(tmp_path/'eixo.kml'));page.wait_for_function("filesInfo&&filesInfo.kmz")
            t=page.inner_text('.fileTable');assert 'Projeto rev3.dxf' in t and 'eixo.kml' in t
            assert c.get(f'/api/projects/{pid}').json()['files']=={'dxf':True,'kmz':True}
            j=c.post(f'/api/projects/{pid}/analyze').json()
            for _ in range(300):
                if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
                time.sleep(.2)
            page.reload();page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA',timeout=20000)
            # Interdição: o painel só oferece Parcial/Total; valor inválido é corrigido antes de salvar.
            ev("(()=>{sel={key:'lane_blocks',i:0};selSet=[];showProps()})()")
            opts=ev("[...document.querySelectorAll('#propPanel [data-pp=\"mode\"] option')].map(o=>o.value)");assert opts==['partial','total']
            ev("(()=>{M.lane_blocks[0].mode='deny';scheduleSave()})()");page.wait_for_timeout(1500)
            assert c.get(f'/api/projects/{pid}').json()['config']['lane_blocks'][0]['mode']=='partial' and 'Corrigido antes de salvar' in ev("document.getElementById('message').textContent")
            # Nome inválido recusado no painel; caixa de diálogo não aceita vazio nem só símbolos.
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()")
            page.fill('#propPanel [data-pp="name"]','   ');page.press('#propPanel [data-pp="name"]','Enter');assert ev('M.highlights[0].name')=='Poste' and 'vazio' in ev("document.getElementById('message').textContent")
            page.fill('#propPanel [data-pp="name"]','<<>>');page.press('#propPanel [data-pp="name"]','Enter');assert ev('M.highlights[0].name')=='Poste'
            ev("renameSel();0");page.wait_for_selector('#inputDlg[open]');page.fill('#inputValue','---');assert ev("document.getElementById('inputOk').disabled") and 'letra' in page.inner_text('#inputErr')
            page.fill('#inputValue','Poste 12');page.keyboard.press('Enter');page.wait_for_function("M.highlights[0].name==='Poste 12'")
            # Aparência: água e sinalização pela faixa de opções.
            page.click('#menuBar .mb:has-text("Aparência")');page.click('#menuBar .rb:has-text("Sinalização")');page.wait_for_selector('#surfDlg[open]')
            ev("(()=>{const i=document.getElementById('sd_wear');i.value='0.6';i.dispatchEvent(new Event('input',{bubbles:true}))})()");page.click('#sd_ok')
            page.click('#menuBar .rb:has-text("Água")');page.wait_for_selector('#surfDlg[open]');ev("document.getElementById('sd_wcolor').value='#1f5f8b'");page.click('#sd_ok')
            page.click('#menuBar .rb:has-text("Taludes")');page.wait_for_selector('#surfDlg[open]');assert ev("document.getElementById('sd_scope').value")=='tipo'
            ev("(()=>{const i=document.getElementById('sd_grao');i.value='2';i.dispatchEvent(new Event('input',{bubbles:true}))})()");page.select_option('#sd_look','natural');page.click('#sd_ok')
            page.wait_for_timeout(1500);conf=c.get(f'/api/projects/{pid}').json()['config']
            assert conf['signage_paint']['wear']==.6 and conf['role_colors']['water']=='#1f5f8b' and conf['texture_params']['talude_corte']['grao']==2 and conf['earthwork_look']=='natural'
            # Área do desenho de talude: região com textura própria.
            ev("(()=>{dxfSel={points:[[500100,7799991],[500150,7799991],[500150,7800009],[500100,7800009]],layer:'TALUDE',role:'cut',area_m2:900,perimeter_m:136};openTexDialog();return 0})()")
            page.wait_for_selector('#surfDlg[open]');assert ev("document.getElementById('sd_scope').value")=='area'
            ev("(()=>{const i=document.getElementById('sd_brilho');i.value='-0.2';i.dispatchEvent(new Event('input',{bubbles:true}))})()");page.click('#sd_ok')
            assert ev('M.texture_areas.length')==1 and ev('M.texture_areas[0].surface')=='talude_corte' and ev('M.texture_areas[0].texture.brilho')==-.2
            # Faixa de opções: Arquivo abre o menu; aba Inserir mostra as ferramentas.
            page.click('#menuBar .mb.file');page.wait_for_selector('#menuDrop:not([hidden])');assert 'Salvar' in page.inner_text('#menuDrop');page.keyboard.press('Escape');page.mouse.click(5,600)
            page.click('#menuBar .mb:has-text("Inserir")');assert page.locator('#menuBar .rb:has-text("Pórtico")').count()==1
            page.click('#menuBar .rb:has-text("Pórtico")');assert ev('tool')=='gantry'
            page.click('#menuBar .mb:has-text("Ajuda")');page.click('#menuBar .rb:has-text("Sobre")');page.wait_for_selector('#aboutDlg[open]')
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
