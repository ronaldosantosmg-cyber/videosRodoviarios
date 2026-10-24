"""Capturas de todas as janelas (diálogos) para revisão visual. Uso: SHOTS=<pasta> python -m pytest tests/shots_dialogs.py
(não faz parte da bateria; o nome não começa com test_)."""
import os,socket,threading,time
import numpy as np,cv2,pytest
from test_workflow import settings
from test_v110 import junction
from test_v132 import make_mp4,S

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_capture_dialogs(junction,tmp_path,monkeypatch):
    out=os.environ.get('SHOTS');pw=pytest.importorskip('playwright.sync_api')
    if not out:pytest.skip('defina SHOTS')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    from app import store,videos
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='Trecho Revisão',highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}]).model_dump()).json()['id']
    c.post('/api/projects',json={'name':'Outro trecho'})
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    c.post(f'/api/projects/{pid}/modelo',json={'name':'Padrão NOVA 381','description':'vídeo 30 fps, sinalização limpa'})
    d=store.ROOT/pid;make_mp4(d/'video.mp4');info={'width':1920,'height':1080,'fps':30,'duration_s':95,'frames':2850,'encoder':'libx264'}
    for _ in range(3):videos.archive(d,pid,S(name='Trecho Revisão'),info,120)
    tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':950})
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA',timeout=20000);ev=page.evaluate
            def shot(name,sel):
                page.wait_for_timeout(350);page.locator(sel).screenshot(path=os.path.join(out,name+'.png'))
            def close(sel):ev(f"document.querySelector('{sel}').close()")
            for name,js,sel in [
                ('abrir',"openProjectDialog();0",'#openDlg'),('modelos',"openTemplates();0",'#tplDlg'),('salvar_modelo',"openTplSave();0",'#tplSaveDlg'),
                ('camadas',"openLayerManager();0",'#layerDlg'),('videos',"openVideos();0",'#videosDlg'),('limpar',"openCleanup();0",'#cleanDlg'),
                ('atualizar',"openUpdate();0",'#updDlg'),('sobre',"openAbout();0",'#aboutDlg'),('nome',"inputBox('Renomear projeto','Novo nome do projeto:','Trecho Revisão');0",'#inputDlg'),
                ('confirmar',"confirmBox('Excluir o projeto “Outro trecho” da lista? A pasta vai para “_lixeira”.','Excluir','Cancelar');0",'#confirmDlg'),
                ('agua',"openSurfDialog('agua');0",'#surfDlg'),('sinalizacao',"openSurfDialog('sin');0",'#surfDlg'),('taludes',"openSurfDialog('tex',{surface:'talude_corte',scope:'tipo'});0",'#surfDlg'),
                ('registros',"openLogs('execucao');0",'#logDlg'),('comandos',"runCommand('?');0",'#cmdHelpDlg')]:
                ev(js);page.wait_for_selector(sel+'[open]',timeout=5000);shot(name,sel);close(sel)
            # Textura de área de pista e opções de ferramenta / menu de contexto.
            ev("(()=>{M.pavement_areas.push({id:'p1',name:'Faixa 1',kind:'pavement',material:'auto',points:[{x:500100,y:7799992},{x:500140,y:7799992},{x:500140,y:7800008},{x:500100,y:7800008}],source:'drawn',enabled:true,texture:null});sel={key:'pavement_areas',i:0};selSet=[];showProps();openTexDialog();return 0})()")
            page.wait_for_selector('#texDlg[open]');shot('textura','#texDlg');close('#texDlg')
            ev("setTool('route')");page.wait_for_timeout(300);shot('opcoes_rota','#toolOptions');ev("setTool('pan')")
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()");shot('propriedades','#propPanel')
            page.screenshot(path=os.path.join(out,'tela.png'))
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
