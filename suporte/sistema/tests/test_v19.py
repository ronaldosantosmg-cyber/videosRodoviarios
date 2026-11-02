"""1.9: editor sobre imagem web (ladrilhos Esri com cache) e vetores simplificados do DXF/KMZ."""
import json,os,socket,threading,time
import numpy as np,cv2,pytest
from pyproj import Transformer
from fastapi.testclient import TestClient
from test_workflow import drawing,settings,wait
from app import webmap,store
from app.server import app

def jpeg(color=(40,120,60)):
    im=np.zeros((256,256,3),np.uint8);im[:]=color;cv2.putText(im,'T',(100,150),cv2.FONT_HERSHEY_SIMPLEX,3,(255,255,255),5)
    return cv2.imencode('.jpg',im)[1].tobytes()

@pytest.mark.parametrize('crs,b',[('EPSG:31983',[[600000,7790000],[620000,7800000]]),('EPSG:31983',[[500000,7800000],[500300,7800030]]),('EPSG:31982',[[180000,8300000],[230000,8330000]])])
def test_fit_crs_to_web_mercator_is_millimetric(crs,b):
    g=webmap.fit(crs,b);tr=Transformer.from_crs(crs,3857,always_xy=True)
    rng=np.random.default_rng(1);x=rng.uniform(b[0][0],b[1][0],300);y=rng.uniform(b[0][1],b[1][1],300)
    mx,my=webmap.to_merc(g,x,y);ex,ey=tr.transform(x,y);assert np.hypot(mx-ex,my-ey).max()<.005
    bx,by=webmap.to_crs(g,ex,ey);assert np.hypot(bx-x,by-y).max()<.005
    assert g['err_fwd_m']<.005 and g['err_inv_m']<.005 and 1<g['k']<1.2 and g['img_w']>0 and g['mpp_crs']==pytest.approx(.25/g['k'])

def test_tile_cache_and_validation(tmp_path):
    calls=[]
    def fake(z,y,x):calls.append((z,y,x));return jpeg()
    a=webmap.tile(tmp_path,15,100,200,fetch=fake);b=webmap.tile(tmp_path,15,100,200,fetch=fake)
    assert a==b and a[:3]==b'\xff\xd8\xff' and len(calls)==1 and (tmp_path/'esri/15/100/200.jpg').exists()
    with pytest.raises(ValueError):webmap.tile(tmp_path,15,1,1,fetch=lambda *a:b'<html>erro</html>')
    assert not (tmp_path/'esri/15/1/1.jpg').exists()
    with pytest.raises(ValueError):webmap.tile(tmp_path,3,0,8,fetch=fake)

def test_tile_endpoint_offline_and_cached(monkeypatch):
    with TestClient(app) as c:
        def offline(*a,**k):raise OSError('sem rede')
        monkeypatch.setattr('urllib.request.urlopen',offline)
        assert c.get('/tiles/esri/16/1000/2000').status_code==404
        assert c.get('/tiles/esri/2/0/9').status_code==422
        f=store.ROOT/'_ladrilhos/esri/16/1000/2001.jpg';f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(jpeg())
        r=c.get('/tiles/esri/16/1000/2001');assert r.status_code==200 and r.headers['content-type']=='image/jpeg' and r.content==f.read_bytes()

def test_geo_and_vectors_after_analysis(drawing):
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
        assert c.get(f'/api/projects/{pid}/geo').status_code==409 and c.get(f'/api/projects/{pid}/vectors.json').status_code==404
        j=wait(c,c.post(f'/api/projects/{pid}/analyze').json()['id']);assert j['state']=='done',j
        g=c.get(f'/api/projects/{pid}/geo').json();v=c.get(f'/api/projects/{pid}/vectors.json').json()
        assert g['err_fwd_m']<.005 and 'Esri' in g['attribution']
        L=v['layers'];assert L['pavement'] and L['median'] and len(L['domain'])==2 and L['cut']
        ax=np.array(v['axis_main']);assert np.hypot(*np.diff(ax,axis=0).T).sum()==pytest.approx(180+np.hypot(120,30),abs=.5)
        assert sum(len(r['p']) for r in L['cut'])<60  # arco simplificado (tolerância 0,25 m)
        assert c.get(f'/api/projects/{pid}/geo').json()['key']==g['key']  # cache
        # O ajuste DXF aplicado desloca os vetores (reanálise basta, sem prévia).
        conf=c.get(f'/api/projects/{pid}').json()['config'];conf['dxf_alignment']={'mode':'translation','pairs':[{'id':'a','dxf':{'x':500000,'y':7800000},'image':{'x':500003,'y':7800001},'enabled':True}],'applied':True}
        c.put(f'/api/projects/{pid}/config',json=conf);wait(c,c.post(f'/api/projects/{pid}/analyze').json()['id'])
        v2=c.get(f'/api/projects/{pid}/vectors.json').json();d=np.array(v2['axis_main'][0])-np.array(v['axis_main'][0]);assert d==pytest.approx([3,1],abs=.01)
        # DXF original intacto.
        assert (store.directory(pid)/'input.dxf').read_bytes()==(drawing/'input.dxf').read_bytes()

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_map_editor_in_browser_without_preview(drawing):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        st=c.get('/api/jobs/'+j['id']).json()
        if st['state'] in ('done','failed'):break
        time.sleep(.2)
    assert st['state']=='done'
    errors=[];served=[]
    tile=jpeg((30,90,150))
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None)
            page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('response',lambda r:errors.append('HTTP %s %s'%(r.status,r.url)) if r.status>=400 else None)
            def route(r):served.append(r.request.url);r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'})
            page.route('**/tiles/esri/**',route)
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && ready()',timeout=20000)
            ev=page.evaluate
            assert ev('useGeo()') and not ev('meta') and ev("document.getElementById('baseMode').value")=='map'
            page.wait_for_function('tileState.ok>0',timeout=10000);assert served and all('/tiles/esri/' in u for u in served)
            # Coordenadas: ida e volta CRS -> tela -> CRS e conferência com o pyproj.
            back=ev('(()=>{const q=W2C({x:500123.4,y:7800011.1});return C2W(q[0],q[1])})()');assert back['x']==pytest.approx(500123.4,abs=.002) and back['y']==pytest.approx(7800011.1,abs=.002)
            mx,my=Transformer.from_crs('EPSG:31983',3857,always_xy=True).transform(500123.4,7800011.1);assert ev('toMerc(500123.4,7800011.1)')==pytest.approx([mx,my],abs=.005)
            # Afastar o zoom troca o nível dos ladrilhos (o desenho de teste já abre no nível máximo).
            z0=ev('tileZoom()');box=page.locator('#canvas').bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
            for _ in range(4):page.mouse.wheel(0,500);page.wait_for_timeout(60)
            assert ev('tileZoom()')<z0
            ev('fitView()')
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            def tool(t):page.click(f'#toolbar button[data-tool="{t}"]')
            # Eixo disponível só com a análise: início do km com sentido, destaque, OAE e par de controle.
            tool('chain');a=W2C(500150,7800000);b2=W2C(500080,7800000);page.mouse.move(*a);page.mouse.down();page.mouse.move(*b2,steps=6);page.mouse.up()
            assert ev('M.chainage.start')['x']==pytest.approx(500150,abs=.6) and ev('M.chainage.direction')==-1
            tool('oae');page.mouse.click(*W2C(500100,7800000));page.mouse.click(*W2C(500140,7800000));assert ev('M.oae_marks.length')==1
            tool('highlight');page.fill('#hlName','Edifício X');a=W2C(500200,7800020);b2=W2C(500230,7800040);page.mouse.move(*a);page.mouse.down();page.mouse.move(*b2,steps=5);page.mouse.up()
            assert ev('M.highlights[0].point.x')==pytest.approx(500200,abs=.6)
            tool('pair');page.mouse.click(*W2C(500000,7800009));page.mouse.click(*W2C(500001.5,7800010));pr=ev('M.dxf_alignment.pairs[0]')
            assert pr['dxf']['x']==pytest.approx(500000,abs=.3) and pr['image']['x']==pytest.approx(500001.5,abs=.3)
            assert 'km' in page.inner_text('#cursor')
            # Camadas: desligar o pavimento e trocar para “Só vetores”.
            page.click('.vlist summary');page.uncheck('input[data-vrole="pavement"]');assert ev('vecOn.pavement')==False
            page.select_option('#baseMode','none');assert ev('baseMode')=='none' and ev('useGeo()')
            n=len(served);ev('draw()');assert len(served)==n
            page.select_option('#baseMode','map')
            if os.environ.get('UI_SHOT_MAP'):page.locator('#editorSection').screenshot(path=os.environ['UI_SHOT_MAP'])
            # Depois da prévia: troca de fundo mantém o mesmo ponto no centro.
            ev("start('preview')");page.wait_for_function('meta && baseImage',timeout=60000);page.wait_for_timeout(300)
            assert ev('useGeo()')  # continua na imagem web
            c0=ev('C2W(canvas.width/2,canvas.height/2)');page.select_option('#baseMode','preview');assert not ev('useGeo()')
            c1=ev('C2W(canvas.width/2,canvas.height/2)');assert np.hypot(c1['x']-c0['x'],c1['y']-c0['y'])<.5
            assert ev('M.highlights.length')==1
            page.wait_for_timeout(1200)
            cfg=c.get(f'/api/projects/{pid}').json()['config']
            assert cfg['highlights'][0]['name']=='Edifício X' and len(cfg['oae_marks'])==1 and len(cfg['dxf_alignment']['pairs'])==1 and cfg['chainage']['direction']==-1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
