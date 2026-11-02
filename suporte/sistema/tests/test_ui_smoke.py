"""Verificação da interface no navegador (executada quando Playwright + Chromium estão disponíveis)."""
import os,threading,time,socket,json
import pytest
pw=pytest.importorskip('playwright.sync_api')
from test_workflow import drawing,settings,wait

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_tools_in_browser(drawing):
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start()
    base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    from app.models import Settings
    pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/preview').json()
    for _ in range(300):
        st=c.get('/api/jobs/'+j['id']).json()
        if st['state'] in ('done','failed'):break
        time.sleep(.2)
    assert st['state']=='done',st
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None)
            page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            # 1.9: o editor abre sobre a imagem web; aqui os ladrilhos são simulados (sem internet no teste).
            import cv2,numpy as np;tile=cv2.imencode('.jpg',np.full((256,256,3),80,np.uint8))[1].tobytes()
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof meta!=="undefined" && meta && baseImage',timeout=20000)
            box=page.locator('#canvas').bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
            ev=page.evaluate
            s0=ev('view.s');page.mouse.move(cx,cy);page.mouse.wheel(0,-400);page.wait_for_timeout(100);assert ev('view.s')>s0
            ev('fitView()')
            def tool(t):page.click(f'#toolbar button[data-tool="{t}"]')
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            tool('chain');page.mouse.click(*W2C(500080,7800000));assert ev('M.chainage.start')['x']==pytest.approx(500080,abs=.5)
            assert 'Início do km' in page.inner_text('#toolHint') or 'Início do km' in page.inner_text('#toolbar button.active')
            ev('undo()');assert ev('M.chainage.start') is None;ev('redo()');assert ev('M.chainage.start') is not None
            tool('dir');a=W2C(500100,7799995);b2=W2C(500160,7799995);page.mouse.move(*a);page.mouse.down();page.mouse.move(*b2,steps=5);page.mouse.up()
            assert ev('M.direction_marks.length')==1
            tool('exvert')
            for x,y in [(500100,7799980),(500140,7799980),(500140,7799990)]:page.mouse.click(*W2C(x,y))
            page.keyboard.press('Enter');assert ev('M.exclusions.length')==1
            tool('exlasso');pts=[W2C(500200+10*__import__('math').cos(t/6),7799980+10*__import__('math').sin(t/6)) for t in range(38)]
            page.mouse.move(*pts[0]);page.mouse.down()
            for q in pts[1:]:page.mouse.move(*q)
            page.mouse.up();assert ev('M.exclusions.length')==2
            tool('exedit');v=ev('M.exclusions[0][0]');page.mouse.move(*W2C(v['x'],v['y']))
            page.mouse.down();page.mouse.move(*W2C(v['x']-5,v['y']-5),steps=3);page.mouse.up()
            assert ev('M.exclusions[0][0].x')==pytest.approx(v['x']-5,abs=.6)
            tool('flowrev');seg=ev('editor.segments[0].mid');page.mouse.click(*W2C(*seg));assert ev('M.flow_overrides.length')==1
            page.mouse.click(*W2C(*seg));assert ev('M.flow_overrides.length')==0  # clicar de novo desfaz
            tool('flowoff');page.mouse.click(*W2C(*seg));assert ev("M.flow_overrides[0].action")=='disable'
            tool('oae');page.mouse.click(*W2C(500100,7800000));page.mouse.click(*W2C(500150,7800000));assert ev('M.oae_marks.length')==1
            tool('noconn');page.mouse.click(*W2C(500200,7800000));assert ev('M.no_connection_zones.length')==1
            tool('flowadd');page.mouse.click(*W2C(500050,7800005));page.mouse.click(*W2C(500050,7800040));page.keyboard.press('Enter')
            page.wait_for_function("document.getElementById('message').textContent.includes('rejeitado')",timeout=10000)
            assert ev('M.traffic_paths.length')==0
            ev('draft=null');page.mouse.click(*W2C(500020,7800005));page.mouse.click(*W2C(500200,7800005));page.keyboard.press('Enter')
            page.wait_for_function('M.traffic_paths.length===1',timeout=10000)
            tool('pair');page.mouse.click(*W2C(500000,7800000));page.mouse.click(*W2C(500002,7799999));assert ev('M.dxf_alignment.pairs.length')==1
            page.click('#markList button[data-act="del"][data-list="oae_marks"]');assert ev('M.oae_marks.length')==0
            # 1.8: início do km com arraste (sentido), fim do km, destaque com caixa arrastada.
            tool('chain');a=W2C(500200,7800000);b2=W2C(500120,7800000);page.mouse.move(*a);page.mouse.down();page.mouse.move(*b2,steps=6);page.mouse.up()
            assert ev('M.chainage.mode')=='manual' and ev('M.chainage.direction')==-1
            tool('chainend');page.mouse.click(*W2C(500050,7800000));assert ev('M.chainage.end')['x']==pytest.approx(500050,abs=1.5)
            assert ev('station().dir')==-1 and ev('Math.round(station().kmEndGeo)')==pytest.approx(150,abs=2)
            tool('highlight');page.select_option('#hlCat','poste');page.fill('#hlName','Poste 7')
            a=W2C(500150,7800012);b2=W2C(500190,7800030);page.mouse.move(*a);page.mouse.down();page.mouse.move(*b2,steps=6);page.mouse.up()
            h=ev('M.highlights[0]');assert h['name']=='Poste 7' and h['category']=='poste' and h['label']['x']==pytest.approx(500190,abs=1.5)
            ev('undo()');assert ev('M.highlights.length')==0;ev('redo()');assert ev('M.highlights.length')==1
            # Ajuda: botão Como usar e dicas nos campos.
            assert ev("document.querySelectorAll('.help').length")>30
            page.hover('label:has(#crs) .help');page.wait_for_timeout(100);assert 'EPSG' in page.inner_text('#tip')
            page.click('#helpBtn');page.wait_for_selector('#helpDialog[open]');assert 'Como usar' in page.inner_text('#helpBody');page.click('#helpDialog button')
            # Tela cheia (tecla F): o editor ocupa a tela e o canvas cresce; L esconde o painel lateral.
            h0=ev('canvas.getBoundingClientRect().height');page.locator('#canvas').focus();page.keyboard.press('f');page.wait_for_timeout(400)
            if ev('!!document.fullscreenElement'):
                assert ev('document.fullscreenElement.id')=='editorSection' and ev('canvas.getBoundingClientRect().height')>h0
                if os.environ.get('UI_SHOT_FS'):page.screenshot(path=os.environ['UI_SHOT_FS'])
                w0=ev('canvas.getBoundingClientRect().width');page.keyboard.press('l');page.wait_for_timeout(200);assert ev('canvas.getBoundingClientRect().width')>w0
                page.keyboard.press('l');page.keyboard.press('f');page.wait_for_timeout(300);assert not ev('!!document.fullscreenElement')
            assert ev("document.getElementById('refInfo').textContent").startswith('Vídeo TH57 aprovado') and not ev("document.getElementById('reference')")
            page.wait_for_timeout(2500)
            if os.environ.get('UI_SHOT'):page.locator('#editorSection').screenshot(path=os.environ['UI_SHOT'])
            cfg=c.get(f'/api/projects/{pid}').json()['config']
            assert len(cfg['direction_marks'])==1 and len(cfg['exclusions'])==2 and len(cfg['traffic_paths'])==1 and cfg['flow_overrides'][0]['action']=='disable'
            assert cfg['highlights'][0]['name']=='Poste 7' and cfg['chainage']['end'] is not None
            assert cfg['oae_marks']==[] and len(cfg['no_connection_zones'])==1 and len(cfg['dxf_alignment']['pairs'])==1 and cfg['chainage']['start'] is not None
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
