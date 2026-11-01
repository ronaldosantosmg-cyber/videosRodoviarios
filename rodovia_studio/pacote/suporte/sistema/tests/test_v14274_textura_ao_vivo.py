"""2.43: trocar o TIPO de textura/material/representação repinta o editor 2D na hora, sem zoom e sem salvar: o desenho muda e o cache técnico reconstrói."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

HASH="()=>{const c=document.querySelector('canvas#cv')||canvas;const g=c.getContext('2d');const w=c.width,h=c.height;const d=g.getImageData(Math.floor(w*.3),Math.floor(h*.3),Math.floor(w*.4),Math.floor(h*.4)).data;let a=0,b=0;for(let i=0;i<d.length;i+=4){a=(a*31+d[i]+d[i+1]*3+d[i+2]*7)>>>0;b+=d[i]}return a+':'+b}"
def test_tipo_de_textura_repinta_na_hora(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    server_thread=threading.Thread(target=server.run,daemon=True);server_thread.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='TexturaViva').model_dump()).json()['id']
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
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.dismiss())
            page.route('**/tiles/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=90000)
            # zoom forte sobre a pista (ladrilho da textura >= 14 px) e liga a camada de pavimento
            page.evaluate("""()=>{const a=axisData().a;const m=a[Math.floor(a.length/2)];const mpx=geo.R0/geo.k;view.s=Math.max(view.s,20/(4/mpx));const [cx,cy]=W2C(m);view.ox+=canvas.width/2-cx;view.oy+=canvas.height/2-cy;vecOn.pavement=true;draw()}""")
            page.wait_for_timeout(300)
            B="()=>RodoviaLayers.stats().technicalBuilds"
            def muda(rotulo,js):
                h0=page.evaluate(HASH);b0=page.evaluate(B)
                page.evaluate(js);page.wait_for_timeout(250)
                h1=page.evaluate(HASH);b1=page.evaluate(B)
                if h1==h0:falhas.append((rotulo,'o desenho NÃO mudou na hora'))
                if b1<=b0:falhas.append((rotulo,'o cache técnico não reconstruiu'))
            ev=lambda id,v:"""()=>{const e=document.getElementById('%s');e.value='%s';e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}"""%(id,v)
            muda('pista nova: flexível → rígido (concreto)',ev('pavement_material','rigido'))
            muda('pista nova: rígido → flexível',ev('pavement_material','flexivel'))
            muda('representação técnica (sem textura procedural)',ev('style_profile','tecnico'))
            muda('representação artística de volta',ev('style_profile','padrao'))
            muda('ajuste de grão da textura (arrastando, sem soltar)',"""()=>{window.RodoviaAparencia.rascunho.tp={pista_nova:{grao:2,tom:2,remendos:2,fissuras:2,brilho:.5}};window.RodoviaAparencia.repintar()}""")
            muda('estilo de representação da pista (hachura cruzada)',"""()=>{cfg.pavement_styles={pavement:{pattern:'cruzada',fill:'#223344',hatch:'#ffcc00',spacing_m:2,angle_deg:30,line_m:.2}};window.RodoviaAparencia.rascunho.tp={};window.RodoviaAparencia.repintar()}""")
            b.close()
    finally:
        server.should_exit=True;server_thread.join(timeout=15);assert not server_thread.is_alive()
    assert not errors,errors
    assert not falhas,repr(falhas)


def test_zoom_afastado_pinta_cor_media_do_tipo(junction,tmp_path,monkeypatch):
    """2.54: com a pista pequena na tela (ladrilho < 14 px) trocar o material AINDA muda o desenho (antes ficava sem textura)."""
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    server_thread=threading.Thread(target=server.run,daemon=True);server_thread.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='TexturaLonge').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];res={}
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':900})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.dismiss())
            page.route('**/tiles/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=90000)
            page.evaluate("""()=>{const mpx=geo.R0/geo.k;view.s=Math.min(view.s,6/(4/mpx));const a=axisData().a;const m=a[Math.floor(a.length/2)];const [cx,cy]=W2C(m);view.ox+=canvas.width/2-cx;view.oy+=canvas.height/2-cy;vecOn.pavement=true;draw()}""")
            res['pxTile']=page.evaluate("()=>{const mpx=geo.R0/geo.k;return 4/mpx*view.s}")
            h0=page.evaluate(HASH)
            page.evaluate("""()=>{const e=document.getElementById('pavement_material');e.value='rigido';e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}""");page.wait_for_timeout(300)
            res['mudou']=page.evaluate(HASH)!=h0
            res['flex']=page.evaluate("()=>RodoviaTexturasVivas.corMedia('pista_nova',{},false)")
            res['rig']=page.evaluate("()=>RodoviaTexturasVivas.corMedia('pista_nova',{},true)")
            b.close()
    finally:
        server.should_exit=True;server_thread.join(timeout=15);assert not server_thread.is_alive()
    assert not errors,errors
    assert res['pxTile']<14 and res['flex']!=res['rig'] and res['mudou'],res
