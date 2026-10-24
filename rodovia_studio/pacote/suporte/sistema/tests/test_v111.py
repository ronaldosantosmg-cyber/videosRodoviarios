"""1.11: ícone GeoRas, detalhe em alta resolução (imagem e texturas), OAE por vértices com sentido,
fluxos e sinalização no editor sem prévia e imagem web direta no navegador."""
import json,os,socket,threading,time,pickle
from pathlib import Path
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import drawing,settings,wait
from test_v110 import junction
from app.models import Settings
from app.server import app
from app import store

def S(**kw):return settings(**kw)
V=((500150,7800000),80)

def sharp_edge(im,scene):
    """Largura (px) da transição de cor na borda do pavimento (y=+9 m), medida numa coluna central."""
    q=scene.screen(np.array([[500150,7800009]]),np.array(V[0]),V[1])[0].astype(int)
    col=im[q[1]-25:q[1]+25,q[0]].astype(float).mean(1);g=np.abs(np.diff(col))
    return int((g>g.max()*.25).sum())

def test_detail_textures_are_sharper_and_off_reproduces_previous(drawing):
    from app.render import Scene
    on=Scene(drawing,S(traffic=False));off=Scene(drawing,S(traffic=False,imagery_detail='off',detail_textures=False))
    assert on.detail.weight(V[1]/on.W)==1 and off.detail.weight(V[1]/off.W)==0
    a=on.frame(0,view=V)[0];b=off.frame(0,view=V)[0]
    assert not np.array_equal(a,b)
    # Nitidez do desenho do projeto: energia de alta frequência do alfa do overlay (detalhe x mosaico base).
    m=V[1]/on.W;cam=np.array(V[0]);cp=on.worldpx(cam[None])[0];dx=np.array([on.right[0],-on.right[1]])*m/on.px;dy=np.array([-on.up[0],on.up[1]])*m/on.px
    mat=np.column_stack([dx,dy,cp-dx*on.W/2-dy*on.H/2]).astype(np.float32)
    base_ov=cv2.warpAffine(on.overlay,mat,(on.W,on.H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
    _,_,det_ov,_=on.detail.compose(cam,V[1],False,True)
    hf=lambda a:float(np.abs(cv2.Laplacian(a[:,:,3].astype(np.float32),cv2.CV_32F)).mean())
    assert hf(det_ov)>1.25*hf(base_ov)  # aqui o mosaico base já tem 0,34 m/px; no TH57 (0,87 m/px) a diferença é maior
    # Desligado = exatamente o caminho anterior (sem camada de detalhe).
    off.detail=None;c=off.frame(0,view=V)[0];off2=Scene(drawing,S(traffic=False,imagery_detail='off',detail_textures=False));assert np.array_equal(off2.frame(0,view=V)[0],c)
    # Vista aberta: mosaico base (peso 0), sem custo extra.
    assert on.detail.weight(on.overview/on.W)==0
    # Cache em disco: uma segunda cena reaproveita os ladrilhos.
    files=list((drawing/'cache_detalhe').rglob('ov_*.png'));assert files
    again=Scene(drawing,S(traffic=False));assert np.array_equal(again.frame(0,view=V)[0],a)

def test_detail_crossfade_between_base_and_detail(drawing):
    from app.render import Scene
    sc=Scene(drawing,S(traffic=False));px=sc.detail.base_px
    w=[sc.detail.weight(f*px) for f in (1.,.9,.8,.7,.6,.5)]
    assert w[0]==0 and w[1]==0 and 0<w[2]<w[3]<1 and w[4]==1 and w[5]==1

def test_detail_imagery_with_fake_tiles(drawing):
    from app.render import Scene
    from app import detail as D
    from pyproj import Transformer
    sc=Scene(drawing,S(traffic=False))
    sc.detail.enabled_imagery=True;sc.detail.esri_ok=True  # 1.17: Esri só quando o fundo é Esri (aqui forçado)
    P=(500123.0,7800011.0);mx,my=Transformer.from_crs('EPSG:31983',3857,always_xy=True).transform(*P)
    calls=[]
    def fake(z,y,x):
        calls.append((z,y,x));im=np.zeros((256,256,3),np.uint8);im[:]=(40,110,60)
        scale=256*2**z/(2*D.MERC);px=(mx+D.MERC)*scale-x*256;py=(D.MERC-my)*scale-y*256
        if 0<=px<256 and 0<=py<256:cv2.circle(im,(int(px),int(py)),2,(0,0,255),-1)
        return cv2.imencode('.png',im)[1].tobytes()
    sc.detail.fetch=fake;sc.detail.tile_root=drawing/'_lad'
    S_=D.T*D.R;i=int((P[0]-sc.detail.x0)//S_);j=int((sc.detail.y1-P[1])//S_)
    img=sc.detail.imagery_tile(i,j);assert img is not None and calls and all(c[0]==19 for c in calls)
    red=(img[:,:,0]>150)&(img[:,:,1]<90)
    ys,xs=np.nonzero(red);c=np.array([xs.mean(),ys.mean()])
    want=sc.detail.worldpx(i,j)(np.array([P]))[0];assert np.linalg.norm(c-want)<1.5  # 0,3 m
    # Ladrilho "sem dados" do Esri cai para o nível anterior.
    gray=np.full((256,256,3),228,np.uint8);cv2.putText(gray,'Map data not yet available',(5,128),cv2.FONT_HERSHEY_SIMPLEX,.4,(120,120,120),1)
    assert D.placeholder(gray) and not D.placeholder(np.full((256,256,3),(40,110,60),np.uint8))
    sc.detail.fetch=lambda z,y,x:cv2.imencode('.png',gray)[1].tobytes() if z==19 else fake(z,y,x)
    (drawing/'_lad').exists() and __import__('shutil').rmtree(drawing/'_lad')
    calls.clear();img2=sc.detail.imagery_tile(i,j);assert img2 is not None and any(c[0]==18 for c in calls)

def test_offline_detail_imagery_gives_up_fast_and_frame_renders(drawing):
    from app.render import Scene
    sc=Scene(drawing,S(traffic=False));sc.detail.enabled_imagery=True;sc.detail.esri_ok=True  # 1.17: Esri só quando o fundo é Esri (aqui forçado)
    def boom(z,y,x):raise OSError('sem rede')
    sc.detail.fetch=boom;t=time.time();n=sc.detail.prefetch([(np.array(V[0]),V[1])])
    assert sc.detail.offline and time.time()-t<5
    im=sc.frame(0,view=V)[0];assert im.shape==(720,1280,3)

def test_snapshot_keeps_detail_layer(drawing,tmp_path):
    from app.render import Scene
    sc=Scene(drawing,S(traffic=False));a=sc.frame(0,view=V)[0]
    sc.snapshot(tmp_path/'snap');b=Scene.load_snapshot(tmp_path/'snap')
    assert b.detail.sc is b and np.array_equal(b.frame(0,view=V)[0],a)

QUAD=[{'x':500095,'y':7799990},{'x':500140,'y':7799988},{'x':500145,'y':7800010},{'x':500092,'y':7800012}]

def test_oae_polygon_geometry_direction_and_validation(drawing):
    from app.render import Scene
    from app.markup import deck_geometry,oae_direction_marks
    g,line,width,rails,heads=deck_geometry([(p['x'],p['y']) for p in QUAD])
    assert abs(g.area-1056)<60 and 18<width<26 and len(rails)==2 and len(heads)==2
    assert abs(line[0][0]-500093.5)<4 and abs(line[-1][0]-500142.5)<4
    with pytest.raises(ValueError):Settings.model_validate({**S().model_dump(),'oae_marks':[{'name':'X','start':QUAD[0],'end':QUAD[1],'polygon':QUAD[:3]}]})
    m={'name':'Ponte A','start':QUAD[0],'end':QUAD[2],'polygon':QUAD,'level_m':7,'direction':'decreasing'}
    sc=Scene(drawing,S(traffic=False,chainage={'mode':'auto'},km_start_m=1000,km_end_m=1400,oae_marks=[m]))
    o=sc.oae[0];assert o.get('polygon') and o['km_start_m']<o['km_end_m'] and abs(o['km_start_m']-1093)<5
    marks=oae_direction_marks(sc.oae,sc.stationing);assert len(marks)==1 and marks[0][1]==-sc.stationing.direction  # decrescente: contra o km
    # O tabuleiro desenhado segue o polígono (não o eixo): pixel dentro do polígono e fora da faixa padrão de 14 m.
    q=sc.screen(np.array([[500118,7799992]]),np.array(V[0]),V[1])[0].astype(int)
    base=Scene(drawing,S(traffic=False)).frame(0,view=V)[0]
    assert np.abs(sc.frame(0,view=V)[0][q[1],q[0]].astype(int)-base[q[1],q[0]]).max()>0

def test_oae_direction_forces_traffic_on_deck(junction):
    from app.render import Scene
    quad=[{'x':500095,'y':7799991},{'x':500140,'y':7799991},{'x':500140,'y':7800009},{'x':500095,'y':7800009}]
    def flows(direction):
        sc=Scene.light(junction,S(chainage={'mode':'auto'},oae_marks=[{'name':'P','start':quad[0],'end':quad[1],'polygon':quad,'direction':direction}]))
        out=[]
        for r in sc.network.raw_info:
            p=r['points'];on=np.flatnonzero((p[:,0]>500095)&(p[:,0]<500140)&(np.abs(p[:,1]-7800000)<9))
            if len(on)<10 or abs(p[on[-1]][0]-p[on[0]][0])<=2:continue
            dx=p[on[-1]][0]-p[on[0]][0];out.append((r['both'],(1 if dx>0 else -1)*(1 if r['forward'] else -1)))
        return out
    both=flows('both');grow=flows('growing');dec=flows('decreasing')
    assert both
    assert grow and all(not b and s==1 for b,s in grow) and dec and all(not b and s==-1 for b,s in dec)

def test_oae_polygon_export_reimport(drawing):
    from app.render import Scene
    from app import exporters
    m={'id':'p1','name':'Ponte A','start':QUAD[0],'end':QUAD[2],'polygon':QUAD,'direction':'growing'}
    s=S(oae_marks=[m]);sc=Scene(drawing,s);feats=exporters.features(s,sc.stationing,sc.axes,sc.network.raw_info,sc.oae)
    back=exporters.read_any(exporters.geojson(feats,s.crs,True).encode(),'m.geojson',s.crs);cfg,_=exporters.apply_import({},back)
    o=Settings.model_validate({**s.model_dump(),**cfg}).oae_marks[0]
    assert len(o.polygon)==4 and o.direction=='growing' and abs(o.polygon[1].x-500140)<.01

def test_analyze_writes_editor_flows_and_signage(junction):
    drawing=junction
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
        assert c.get(f'/api/projects/{pid}').json()['editor_ready'] is False
        j=wait(c,c.post(f'/api/projects/{pid}/analyze').json()['id']);assert j['state']=='done',j
        r=c.get(f'/api/projects/{pid}').json();assert r['editor_ready'] and 'preview' not in r
        e=c.get(f'/api/projects/{pid}/editor.json').json()
        assert e['segments'] and e['markings'] and e['arrows'] and e['paths'] and len(e['markings'][0])==5 and len(e['axis'])>=2
        assert c.get('/favicon.ico').status_code==200 and c.get('/marca/georas.png').content[:4]==b'\x89PNG'
        from PIL import Image
        import io
        assert Image.open(io.BytesIO(c.get('/favicon.ico').content)).size==(256,256)

def test_schema_v10():
    s=Settings.model_validate({'schema_version':9,'km_start_m':0,'km_end_m':100})
    assert s.schema_version>=10 and s.imagery_detail=='auto' and s.detail_textures

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_oae_polygon_signage_and_direct_tiles(drawing):
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
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes();direct=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' and '404' not in m.text else None)
            # Servidor local sem acesso ao Esri (404): o navegador busca direto no Esri (simulado).
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=404,body='x'))
            def esri(r):direct.append(r.request.url);r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'})
            page.route('https://server.arcgisonline.com/**',esri)
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && editor && ready()',timeout=20000)
            page.wait_for_function('tileState.direct>0',timeout=10000);assert direct and '/MapServer/tile/' in direct[0]
            ev=page.evaluate;ev('fitView()')
            assert ev('!!(vecPaths.signage && vecPaths.arrows)') and ev('editor.markings.length')>10 and not ev('meta')
            page.wait_for_function("document.querySelector('.appicon').complete && document.querySelector('.dev img').complete",timeout=10000)
            assert ev("document.querySelector('.appicon').naturalWidth")==256 and ev("document.querySelector('.dev img').naturalWidth")>100
            page.click('.vlist summary');assert page.locator('input[data-vrole="signage"]').count()==1 and page.locator('input[data-vrole="flows"]').count()==1
            page.uncheck('input[data-vrole="arrows"]');assert ev('vecOn.arrows')==False
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            def tool(t):page.click(f'#toolbar button[data-tool="{t}"]')
            tool('oaepoly');page.select_option('#oaeDir','growing')
            for v in QUAD:page.mouse.click(*W2C(v['x'],v['y']))
            page.keyboard.press('Enter')
            o=ev('M.oae_marks[0]');assert len(o['polygon'])==4 and o['direction']=='growing' and abs(o['start']['x']-500093)<6 and abs(o['end']['x']-500143)<6
            tool('exedit');v=o['polygon'][1];page.mouse.move(*W2C(v['x'],v['y']));page.mouse.down();page.mouse.move(*W2C(v['x']+3,v['y']-2),steps=3);page.mouse.up()
            assert ev('M.oae_marks[0].polygon[1].x')==pytest.approx(v['x']+3,abs=.8)
            ev('undo()');assert ev('M.oae_marks[0].polygon[1].x')==pytest.approx(v['x'],abs=.01);ev('redo()')
            page.select_option('select[data-f="oae.0.direction"]','decreasing');assert ev('M.oae_marks[0].direction')=='decreasing'
            page.click('#updFlows');page.wait_for_function("document.getElementById('message').textContent.includes('atualizados')",timeout=60000)
            cfg=c.get(f'/api/projects/{pid}').json()['config'];oc=cfg['oae_marks'][0]
            assert len(oc['polygon'])==4 and oc['direction']=='decreasing' and cfg['schema_version']>=10
            e=c.get(f'/api/projects/{pid}/editor.json').json();assert e['oae'][0]['polygon'] and e['oae'][0]['direction']=='decreasing'
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
