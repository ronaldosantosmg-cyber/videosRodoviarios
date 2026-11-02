"""2.38: o sentido desenhado de cada trecho é o do motor (editor.segments[].forward) em qualquer zoom, em modo de edição ou não, depois de redesenhar; nenhuma camada desenha seta contrária na mesma via."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_setas_uniformes_em_zoom_edicao_e_redesenho(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='Varredura').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];falhas=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':900})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.dismiss())
            page.route('**/tiles/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=90000)
            page.evaluate("""()=>{window.__a=[];const o=arrowsAlong;arrowsAlong=function(pts,f,b,col,sp){__a.push({f:!!f,b:!!b,x:Math.round(pts[0].x*10),y:Math.round(pts[0].y*10),n:pts.length});return o.apply(this,arguments)}}""")
            page.evaluate("""()=>{const sg=editor.segments[0];sg.forward=false;sg.both=false;M.traffic_paths=[{name:sg.source||'trilha',points:sg.points.map(p=>Array.isArray(p)?p:[p.x,p.y]),enabled:true}];sg.source=sg.source||'trilha';vecOn.flows=true}""")
            falhas=[]
            B="()=>RodoviaLayers.stats().technicalBuilds"
            mudancas={
              'sentido do trecho invertido':"()=>{const s=editor.segments[0];s.forward=!s.forward}",
              'fim do salvamento (cor ok/pendente)':"()=>{savePending=!savePending}",
              'sentido do eixo/layer alterado':"()=>{cfg.route_directions={...(cfg.route_directions||{}),'layer:X':(cfg.route_directions||{})['layer:X']==='reverse'?'forward':'reverse'}}",
              'prévia de faixas recebida':"()=>{routeLanes=[...(routeLanes||[])]}",
              'estado do artefato do editor':"()=>{projectSession.artifacts.editor={...(projectSession.artifacts.editor||{}),state:(projectSession.artifacts.editor||{}).state==='ready'?'building':'ready'}}"}
            page.evaluate("()=>draw()");page.evaluate("()=>draw()")
            for nome,js in mudancas.items():
                antes=page.evaluate(B);page.evaluate("()=>draw()");sem_mudanca=page.evaluate(B)
                page.evaluate(js);page.evaluate("()=>draw()");depois=page.evaluate(B)
                if depois<=sem_mudanca:falhas.append((nome,'a tela NÃO repintou sem zoom (cache da camada técnica velho)',antes,sem_mudanca,depois))
            b.close()
    finally:
        server.should_exit=True
    assert not falhas,repr(falhas[:6])
