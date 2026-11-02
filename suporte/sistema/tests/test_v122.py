"""1.22: edição tipo CAD — seleção com grips, propriedades com Enter, linha de comando (MOVER, APAGAR, DIST, ID,
coordenadas absolutas e relativas), snap, alinhamento por cliques, salvar e salvar como."""
import os,json,socket,threading,time
import numpy as np,pytest,cv2
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})

def test_custom_axis_from_clicks(junction):
    from app.geometry import analyze,custom_axis_points
    from app.models import CustomAxis
    ca=CustomAxis(points=[{'x':500000,'y':7800001},{'x':500200,'y':7800004},{'x':500400,'y':7800001}])
    p=custom_axis_points(ca)
    assert np.allclose(p[0],[500000,7800001]) and np.allclose(p[-1],[500400,7800001])
    assert any(np.allclose(q,[500200,7800004]) for q in p)          # passa exatamente pelos pontos clicados
    assert p[:,1].max()>7800004-1e-6 and np.max(np.linalg.norm(np.diff(p,axis=0),axis=1))<=1.01
    straight=custom_axis_points(CustomAxis(points=ca.points,smooth=False));assert len(straight)==3
    _,axis,ds,_,rep=analyze(junction,S(custom_axis=ca.model_dump()))
    assert np.allclose(axis[0],[500000,7800001]) and abs(ds[-1]-400.1)<1 and any('Eixo de referência' in w for w in rep['warnings'])
    _,axis2,_,_,_=analyze(junction,S(custom_axis={**ca.model_dump(),'enabled':False}));assert np.allclose(axis2[0],[500000,7800000])
    assert Settings.model_validate({'schema_version':20,'km_start_m':0,'km_end_m':100}).custom_axis is None

def test_save_as_copies_project(junction):
    from app.server import app
    import app.store as store
    with TestClient(app) as c:
        pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10,'signs':[{'id':'s1','code':'R-1','point':{'x':500200,'y':7800005}}]}).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
        (store.ROOT/pid/'cache_detalhe').mkdir(exist_ok=True)
        r=c.post(f'/api/projects/{pid}/save_as',json={'name':'Cópia TH'});assert r.status_code==201
        nid=r.json()['id'];d=store.ROOT/nid
        assert (d/'input.dxf').exists() and not (d/'cache_detalhe').exists()
        conf=c.get(f'/api/projects/{nid}').json()['config'];assert conf['name']=='Cópia TH' and conf['signs'][0]['code']=='R-1'
        assert nid in [p['id'] for p in c.get('/api/projects').json()] and pid in [p['id'] for p in c.get('/api/projects').json()]
        assert c.post(f'/api/projects/{pid}/save_as',json={'name':''}).status_code==422

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_cad_tools(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    cfg={**settings().model_dump(),'duration_s':10,'signs':[{'id':'s1','code':'R-1','point':{'x':500200,'y':7800005}}],
         'crosswalks':[{'id':'c1','name':'Faixa 1','a':{'x':500300,'y':7799991},'b':{'x':500300,'y':7800009},'width_m':4}]}
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
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500250,y:7800000});view.s=Math.min(240,canvas.width*mpp()/220);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            page.locator('#canvas').scroll_into_view_if_needed()
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Seleção: clique na placa mostra grips e propriedades.
            page.mouse.click(*W2C(500200,7800005));assert ev('sel&&sel.key')=='signs' and ev("!document.getElementById('propPanel').hidden")
            # Coordenada digitada no grip com precisão milimétrica, confirmada com Enter.
            gx=page.locator('#propPanel input[data-grip="0"][data-ax="x"]');gx.fill('500201.237');gx.press('Enter')
            assert abs(ev('M.signs[0].point.x')-500201.237)<1e-9
            # Propriedade (texto) com Enter; desfazer volta.
            t=page.locator('#propPanel input[data-pp="text"]');t.fill('60');t.press('Enter');assert ev('M.signs[0].text')=='60'
            ev('undo()');assert ev('M.signs[0].text')==''
            # Arrastar o grip da faixa de pedestre (o snap pode atrair para o eixo/vértices: usa ponto livre).
            ev("document.getElementById('snapOn').checked=false")
            page.mouse.click(*W2C(500300,7800000));assert ev('sel.key')=='crosswalks'
            page.mouse.move(*W2C(500300,7799991));page.mouse.down();page.mouse.move(*W2C(500306,7799993),steps=6);page.mouse.up()
            a=ev('M.crosswalks[0].a');assert abs(a['x']-500306)<.3 and abs(a['y']-7799993)<.3
            # MOVER pela linha de comando com ponto base e deslocamento relativo.
            cl=page.locator('#cmdLine');cl.fill('M');cl.press('Enter');cl.fill('0,0');cl.press('Enter');cl.fill('@1.5,-0.25');cl.press('Enter')
            assert abs(ev('M.crosswalks[0].b.x')-500301.5)<1e-9 and abs(ev('M.crosswalks[0].b.y')-7800008.75)<1e-9
            # DIST e APAGAR (tecla Delete).
            cl.fill('DIST');cl.press('Enter');cl.fill('500100,7800000');cl.press('Enter');cl.fill('@3.5,0');cl.press('Enter')
            assert 'Distância 3.500 m' in ev("document.getElementById('message').textContent")
            m=ev('({x:(M.crosswalks[0].a.x+M.crosswalks[0].b.x)/2,y:(M.crosswalks[0].a.y+M.crosswalks[0].b.y)/2})');page.mouse.click(*W2C(m['x'],m['y']));assert ev('sel&&sel.key')=='crosswalks';page.keyboard.press('Delete');assert ev('M.crosswalks.length')==0
            # Snap a vértice do DXF durante um comando de desenho.
            ev("document.getElementById('snapOn').checked=true");page.click('#toolbar button[data-tool="pavarea"]')
            page.mouse.move(*W2C(500190.4,7800009.3));assert ev('snapMark&&snapMark.kind')=='vértice' and abs(ev('lastWorld.x')-500190)<1e-6
            page.keyboard.press('Escape');page.wait_for_selector('#confirmDlg[open]');page.keyboard.press('Enter')  # 1.24: Esc pede confirmação
            # Alinhamento por cliques (comando AL), Enter conclui; letras digitadas na tela vão para a linha de comando.
            page.focus('#canvas');page.keyboard.type('AL');assert ev("document.getElementById('cmdLine').value")=='AL';page.keyboard.press('Enter');assert ev('tool')=='align'
            ev("document.getElementById('snapOn').checked=false")
            for x in (500160,500250,500340):page.mouse.click(*W2C(x,7800000))
            page.focus('#canvas');page.keyboard.press('Enter');assert ev('M.custom_axis.points.length')==3 and ev('tool')=='align'  # 1.34: a ferramenta continua
            page.keyboard.press('Enter');assert ev('tool')=='pan'   # Enter sem pontos encerra
            # Salvar (Ctrl+S).
            page.keyboard.press('Control+s');page.wait_for_timeout(700)
            conf=c.get(f'/api/projects/{pid}').json()['config'];assert len(conf['custom_axis']['points'])==3 and conf['signs'][0]['point']['x']==500201.237 and conf['crosswalks']==[]
            assert ev("document.querySelectorAll('#toolbar button[data-tool=align] svg').length")==1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
