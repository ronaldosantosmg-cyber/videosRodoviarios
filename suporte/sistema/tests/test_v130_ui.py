"""1.30 (tela): abrir projeto (Ctrl+O), renomear, modelos; rota de veículos com trecho de pista dupla; grupos
recolhíveis no painel de propriedades; gerenciador de camadas (edição final); pincel de textura até Esc."""
import os,socket,threading,time
import numpy as np,cv2,pytest
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})
def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_130_ui(junction,tmp_path):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pav=lambda x0,name,tex=None:{'id':name,'name':name,'kind':'pavement','material':'auto','points':[{'x':x0,'y':7799992},{'x':x0+30,'y':7799992},{'x':x0+30,'y':7800008},{'x':x0,'y':7800008}],'source':'drawn','enabled':True,'texture':tex}
    pid=c.post('/api/projects',json=S(name='Trecho UI 130',fps=30,highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}],
        pavement_areas=[pav(500020,'Origem',{'grao':1.8,'tom':.7,'remendos':1,'fissuras':1,'brilho':-.1}),pav(500300,'Destino')]).model_dump()).json()['id']
    other=c.post('/api/projects',json=S(name='Outro 130 xq').model_dump()).json()['id']
    (tmp_path/'p.dxf').write_bytes((junction/'input.dxf').read_bytes())
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)+' '+str(getattr(e,'stack','') or '')[:600]))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof cfg!=="undefined"&&cfg&&pid&&SCHEMA&&cfg.name==="Trecho UI 130"&&filesInfo',timeout=20000);ev=page.evaluate
            page.set_input_files('#fileDxf',str(tmp_path/'p.dxf'));page.wait_for_function("filesInfo&&filesInfo.dxf")
            j=c.post(f'/api/projects/{pid}/analyze').json()
            for _ in range(300):
                if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
                time.sleep(.2)
            page.reload();page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA',timeout=20000)
            # ---- Abrir projeto (Ctrl+O), procurar, renomear e abrir outro ----
            page.click('canvas');page.keyboard.press('Control+o');page.wait_for_selector('#openDlg[open]')
            assert page.locator(f'#opGrid [data-op="{pid}"].cur').count()==1 and page.locator(f'#opGrid [data-op="{other}"]').count()==1
            shot=lambda n:page.screenshot(path=os.path.join(os.environ['SHOTS'],n+'.png')) if os.environ.get('SHOTS') else None
            shot('abrir')
            page.fill('#opSearch','130 XQ');assert page.locator('#opGrid .prjCard').count()==1
            page.click('#opGrid .prjCard');page.click('#opRename');page.wait_for_selector('#inputDlg[open]')
            page.fill('#inputValue','Trecho UI 130');assert ev("document.getElementById('inputOk').disabled")   # nome já usado
            page.fill('#inputValue','Outro 130 xq km 12');page.keyboard.press('Enter');page.wait_for_function("document.querySelector('#opGrid').innerText.includes('km 12')")
            assert c.get(f'/api/projects/{other}').json()['config']['name']=='Outro 130 xq km 12'
            page.dblclick('#opGrid .prjCard');page.wait_for_function(f"pid==='{other}'");assert ev('document.title')=='Outro 130 xq km 12 — Rodovia Studio'
            # Volta pelo menu Arquivo › Abrir projeto…
            page.click('#menuBar .mb.file');page.click('#menuDrop .it:has-text("Abrir projeto")');page.wait_for_selector('#openDlg[open]')
            page.click(f'#opGrid [data-op="{pid}"]');page.click('#opOpen');page.wait_for_function(f"pid==='{pid}'&&typeof geo!=='undefined'&&geo&&ready()",timeout=20000)
            # ---- Modelos: salvar o projeto como modelo e criar um projeto a partir dele ----
            ev("openTplSave();0");page.wait_for_selector('#tplSaveDlg[open]');page.fill('#tsName','Padrão 30 fps UI130');page.click('#tsOk')
            page.wait_for_function("!document.getElementById('tplSaveDlg').open")
            assert 'Padrão 30 fps UI130' in [m['name'] for m in c.get('/api/modelos').json()]
            ev("openTemplates();0");page.wait_for_selector('#tplDlg[open]');page.click('#tplRows tr[data-tpl]:has-text("UI130")');page.click('#tplNewPrj');page.wait_for_selector('#inputDlg[open]')
            page.fill('#inputValue','Trecho do modelo 130');page.keyboard.press('Enter');page.wait_for_function("cfg&&cfg.name==='Trecho do modelo 130'")
            assert ev('cfg.fps')==30 and ev('M.pavement_areas.length')==0
            ev(f"openProjectId('{pid}');0");page.wait_for_function(f"pid==='{pid}'&&ready()",timeout=20000)
            # ---- Rota de veículos: pista simples com trecho de pista dupla ----
            ev("setTool('route')");assert ev("document.getElementById('rtType')!==null")
            ev("(()=>{click({x:500030,y:7800000});click({x:500370,y:7800000});return finishDraft()})()")
            page.wait_for_function("M.route_alignments.length===1&&routeLanes.length===2")
            ev("setTool('routesec')");ev("document.getElementById('rsType').value='dupla';document.getElementById('rsType').dispatchEvent(new Event('change'))")
            ev("(()=>{click({x:500130,y:7800000.5});click({x:500250,y:7799999.5})})()")
            assert ev('M.route_alignments[0].sections.length')==1 and ev('M.route_alignments[0].sections[0].type')=='dupla' and abs(ev('M.route_alignments[0].sections[0].start_m')-100)<.01
            page.wait_for_function("routeLanes.length===4")
            ev("fitView()");shot('rota');page.keyboard.press('Escape');assert ev('tool')=='pan'
            # Propriedades da rota: tabela de trechos; trocar o tipo pelo painel.
            ev("(()=>{sel={key:'route_alignments',i:0};selSet=[];showProps()})()")
            assert 'Trechos da rota' in page.inner_text('#propPanel') and page.locator('#propPanel [data-rs="0:type"]').count()==1
            page.select_option('#propPanel [data-rs="0:type"]','unico');assert ev('M.route_alignments[0].sections[0].type')=='unico'
            ev("undo()");assert ev('M.route_alignments[0].sections[0].type')=='dupla'
            page.wait_for_timeout(1500);conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['route_alignments'][0]['sections'][0]['type']=='dupla'
            # ---- Painel de propriedades: grupos recolhíveis ----
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()")
            assert page.locator('#propPanel .ppGrp').count()>=2 and ev("document.querySelector('#propPanel .ppGrp[data-grp=\"ident\"]').open")
            shot('grupos');page.click('#propPanel [data-ppall="0"]');assert ev("[...document.querySelectorAll('#propPanel .ppGrp')].every(d=>!d.open)")
            ev("showProps()");assert not ev("document.querySelector('#propPanel .ppGrp[data-grp=\"ident\"]').open")   # lembrado
            page.click('#propPanel [data-ppall="1"]');assert ev("[...document.querySelectorAll('#propPanel .ppGrp')].every(d=>d.open)")
            ev("clearSelection()")
            # ---- Gerenciador de camadas: congelar as demais (edição final) e desfazer ----
            ev("openLayerManager()");page.wait_for_selector('#layerDlg[open]')
            names=ev("[...document.querySelectorAll('#lmRows [data-lmn]')].map(t=>t.dataset.lmn)");assert {'EIXO','PAVIMENTO'}<=set(names)
            shot('camadas');page.fill('#lmSearch','PAV*');assert ev("document.querySelectorAll('#lmRows [data-lmn]').length")==1
            page.check('#lmAll');page.click('#layerDlg [data-lm="final"]')
            assert set(ev('cfg.frozen_layers'))==set(names)-{'PAVIMENTO'} and ev('cfg.hidden_layers')==[]
            page.click('#lmUndo');assert ev('cfg.frozen_layers')==[]
            page.fill('#lmSearch','');ev("document.querySelector('#lmRows [data-lmn=\"PAVIMENTO\"] [data-lmv]').click()");assert ev('cfg.hidden_layers')==["PAVIMENTO"]
            page.click('#layerDlg [data-lm="reset"]');assert ev('cfg.hidden_layers')==[] and ev('cfg.frozen_layers')==[]
            page.click('#lmClose')
            # ---- Pincel: copia a textura da origem e aplica em várias áreas até Esc ----
            ev("(()=>{sel={key:'pavement_areas',i:0};selSet=[]})()");ev("startBrush()");assert ev('tool')=='brush' and ev('brush.src.texture.grao')==1.8
            ev("brushClick({x:500315,y:7800000})");page.wait_for_function("brush.n===1")
            assert ev('M.pavement_areas[1].texture.grao')==1.8 and ev('M.pavement_areas[1].texture.tom')==.7
            ev("brushClick({x:500200,y:7800060})");page.wait_for_function("brush.n===2")
            assert ev('M.pavement_areas.length')==3 and ev('M.pavement_areas[2].texture.grao')==1.8 and ev('M.pavement_areas[2].source')=='picked'
            ev("canvas.focus()");page.keyboard.press('Escape');assert ev('tool')=='pan' and 'Pincel encerrado: 2' in ev("document.getElementById('message').textContent")
            ev("undo()");assert ev('M.pavement_areas.length')==2
            # Comandos novos e faixa de opções.
            ev("runCommand('CAMADAS')");page.wait_for_selector('#layerDlg[open]');page.click('#lmClose')
            page.click('#menuBar .mb:has-text("Fluxos")');assert page.locator('#menuBar .rb:has-text("Rota de veículos")').count()==1
            page.click('#menuBar .mb:has-text("Editar")');page.click('#menuBar .rb:has-text("Pincel de textura")');assert ev('tool')=='brush';ev("setTool('pan')")
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
