"""Motor, API e interface reais no mesmo projeto, sem imagens externas."""
import threading
import time
import socket
import httpx
import uvicorn
from playwright.sync_api import sync_playwright
from test_workflow import drawing,settings,wait
from visual_harness import chromium_path,screenshot


def test_engine_diagnostics_reach_live_editor_and_update(drawing):
    import ezdxf
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    m.add_lwpolyline([(500050,7800000),(500450,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799980),(500500,7799980),(500500,7800020),(500000,7800020)],is_closed=True)
    doc.saveas(drawing/'input.dxf')
    from app.server import app
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start()
    base=f'http://127.0.0.1:{port}'
    try:
        with httpx.Client(base_url=base,trust_env=False,timeout=60) as client:
            for _ in range(100):
                try:
                    if client.get('/api/health').status_code==200:break
                except httpx.ConnectError:pass
                time.sleep(.1)
            r=client.post('/api/projects',json=settings().model_dump());assert r.status_code==201,r.text
            pid=r.json()['id']
            r=client.post(f'/api/projects/{pid}/files',files={'file':('trecho.dxf',(drawing/'input.dxf').read_bytes())});assert r.status_code==200,r.text
            job=client.post(f'/api/projects/{pid}/analyze').json();result=wait(client,job['id']);assert result['state']=='done',result
            data=client.get(f'/api/projects/{pid}/editor.json').json()
            assert data['segments'] and any(s['technical_status']=='ok' for s in data['segments'])
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_path(),args=['--no-sandbox','--disable-gpu'])
                page=browser.new_page(viewport={'width':1440,'height':900});errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
                page.route('**/tiles/**',lambda r:r.fulfill(status=204,body=''))
                page.goto(base,wait_until='domcontentloaded')
                page.wait_for_function("typeof editor!=='undefined'&&editor?.segments?.length>0",timeout=20000)
                states=page.evaluate("editor.segments.map(s=>({status:s.technical_status,color:flowStudyColor(s)}))")
                assert any(s['color']=='#22c55e' for s in states)
                page.evaluate("selSeg=editor.segments.find(s=>s.technical_status==='ok');showSegProps();draw()")
                assert 'Fluxo presente nos itinerários calculados.' in page.inner_text('#propPanel')
                screenshot(page,'142_11_motor_editor_real')
                # Desativa o trecho e recalcula pelo fluxo real da aplicação.
                page.evaluate("async()=>{const s=selSeg;M.flow_overrides.push({id:'teste-fluxo',x:s.mid[0],y:s.mid[1],action:'disable',enabled:true});changed('Fluxo desativado para teste.');await start('analyze')}")
                assert page.evaluate("editor.segments.some(s=>s.disabled&&flowStudyColor(s)==='#ef4444')")
                screenshot(page,'142_12_motor_editor_fluxo_problema')
                assert not errors,errors
                browser.close()
    finally:
        server.should_exit=True;th.join(timeout=15)
        assert not th.is_alive()
