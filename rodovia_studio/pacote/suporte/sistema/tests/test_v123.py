"""1.23: iniciador Rodovia Studio.exe (código separado do programa) e campos obrigatórios vazios no editor."""
import os,re,sys,json,socket,threading,time,subprocess
from pathlib import Path
import numpy as np,pytest,cv2
from test_workflow import settings
from test_v110 import junction

ROOT=Path(__file__).resolve().parents[1]

def test_launcher_source_is_csharp5_and_complete():
    src=(ROOT/'iniciador'/'RodoviaStudio.cs').read_text(encoding='utf-8-sig')
    code=re.sub(r'//[^\n]*','',re.sub(r'"(?:\\.|[^"\\])*"','""',src))      # sem comentários e textos
    # O csc.exe do .NET Framework 4 só aceita C# 5: nada de $"...", ?., nameof, membros com =>, out var.
    assert '$""' not in code and '?.' not in code and 'nameof(' not in code and not re.search(r'\)\s*=>',code) and 'out var' not in code
    assert code.count('{')==code.count('}') and code.count('(')==code.count(')')
    for must in ('RODOVIA_NO_BROWSER','RODOVIA_PORT_FILE','-PrepararApenas','atualizar.ps1','--app=','taskkill','/api/health','Version = "'):
        assert must in src,must
    cmd=(ROOT/'raiz_extra'/'COMPILAR INICIADOR.cmd').read_bytes()
    assert b'\r\n' in cmd and b'/codepage:65001' in cmd and b'/target:winexe' in cmd and b'v4.0.30319' in cmd
    cmd.decode('ascii')
    assert (ROOT/'iniciador'/'RodoviaStudio.cs').read_bytes()[:3]==b'\xef\xbb\xbf'

def test_iniciar_ps1_prepare_only_switch():
    s=(ROOT/'iniciar.ps1').read_text(encoding='utf-8')
    assert s.startswith('param([switch]$PrepararApenas)') and "if ($PrepararApenas) { Write-Host 'Preparacao concluida.'; exit 0 }" in s
    assert s.index('$PrepararApenas) {') < s.index("Join-Path $PSScriptRoot 'run.py'")

def test_run_py_port_file_and_no_browser(tmp_path,monkeypatch):
    port_file=tmp_path/'logs'/'porta.txt'
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    env=dict(os.environ,RODOVIA_NO_BROWSER='1',RODOVIA_PORT_FILE=str(port_file),RODOVIA_PORT=str(port),RODOVIA_DATA=str(tmp_path/'dados'))
    p=subprocess.Popen([sys.executable,str(ROOT/'run.py')],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    try:
        import httpx
        for _ in range(150):
            if port_file.exists():
                try:
                    if httpx.get(f'http://127.0.0.1:{int(port_file.read_text())}/api/health').json()['status']=='ok':break
                except Exception:pass
            time.sleep(.2)
        assert int(port_file.read_text())==port
        # Segunda instância: encontra a primeira, informa a porta e encerra com 0 sem abrir navegador.
        port_file.unlink()
        r=subprocess.run([sys.executable,str(ROOT/'run.py')],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
        assert r.returncode==0 and int(port_file.read_text())==port and 'já está aberto' in r.stdout
    finally:
        p.terminate();p.wait(timeout=20)

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_rejects_empty_required_fields(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    cfg={**settings().model_dump(),'duration_s':10,'crosswalks':[{'id':'c1','name':'Faixa 1','a':{'x':500300,'y':7799991},'b':{'x':500300,'y':7800009},'width_m':4}]}
    pid=c.post('/api/projects',json=cfg).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1200})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500300,y:7800000});view.s=Math.min(240,canvas.width*mpp()/120);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            page.locator('#canvas').scroll_into_view_if_needed()
            q=ev('W2C({x:500300,y:7800000})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()')
            page.mouse.click(R[0]+q[0]*R[2],R[1]+q[1]*R[2]);assert ev('sel&&sel.key')=='crosswalks'
            n=page.locator('#propPanel input[data-pp="name"]');n.fill('');n.press('Enter')
            assert ev('M.crosswalks[0].name')=='Faixa 1' and 'não pode ficar vazio' in ev("document.getElementById('message').textContent")
            w=page.locator('#propPanel input[data-pp="width_m"]');w.fill('');w.press('Enter');assert ev('M.crosswalks[0].width_m')==4
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
