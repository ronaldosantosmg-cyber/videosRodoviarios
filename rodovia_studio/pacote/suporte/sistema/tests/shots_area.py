"""1.33: capturas da área de trabalho (barra em abas, recolhida, janela flutuante, área máxima, rodapé, menu Vídeo).
Uso: SHOTS=<pasta> python -m pytest tests/shots_area.py (não faz parte da bateria)."""
import os,threading,time
import numpy as np,cv2,pytest
from test_workflow import settings
from test_v110 import junction
from test_v132 import S
from shots_dialogs import free_port

def test_capture_area(junction,tmp_path,monkeypatch):
    out=os.environ.get('SHOTS');pw=pytest.importorskip('playwright.sync_api')
    if not out:pytest.skip('defina SHOTS')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='Trecho Área',highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}]).model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes();errs=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':int(os.environ.get('LARG','1850')),'height':1000})
            page.on('pageerror',lambda e:errs.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA',timeout=20000);ev=page.evaluate
            if not ev("document.body.classList.contains('wide')"):ev("$('layoutWide').click()")
            page.wait_for_timeout(600);sh=lambda n:(page.wait_for_timeout(400),page.screenshot(path=os.path.join(out,n+'.png')))
            sh('1_tela')
            ev("abrirAba('avisos')");sh('2_avisos')
            ev("recolherDock(true)");sh('3_recolhida')
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()");sh('4_selecao_reabre')
            ev("(()=>{sel=null;selSet=[];showProps();return 0})()");sh('5_selecao_fim')
            ev("alternarAreaMax(true)");sh('6_area_max')
            ev("destacar('marc')");sh('7_flutuante')
            ev("encaixar('marc');alternarAreaMax(false)")
            ev("$('progress').value=.42;marcarTarefa(true);msg('Montando quadros: 1200 de 2850 · falta ~95 s')");page.wait_for_timeout(1200);sh('8_tarefa')
            page.locator('#bottomBar').screenshot(path=os.path.join(out,'8b_rodape.png'))
            ev("marcarTarefa(false)")
            ev("document.querySelector('#menuBar [data-mb]:nth-child(6)')?.click()");page.locator('#menuBar .mb',has_text='Vídeo').click();sh('9_menu_video')
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errs,errs
