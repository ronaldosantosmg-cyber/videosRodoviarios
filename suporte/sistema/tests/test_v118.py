"""1.18: menos setas (sem excesso), camada 0 separada por cor/tipo com avisos de mapeamento suspeito,
km em planta, vão da passarela no editor e acesso rodoviário com tapers de entrada e saída."""
import os,json,socket,threading,time
import numpy as np,ezdxf,pytest,cv2
from shapely.geometry import Polygon,Point,box
from fastapi.testclient import TestClient
from test_workflow import settings,wait
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})

def test_arrows_not_excessive(junction):
    from app.render import Scene
    n={m:len(Scene.light(junction,S(lane_arrow_repeat=m)).network.arrows) for m in ('off','conflicts','all')}
    assert n['off']<=n['conflicts']<n['all']
    net=Scene.light(junction,S()).network
    # Setas no mesmo sentido a menos de 25 m só se forem a repetição por faixa (mesma âncora).
    for i,((p,t),a) in enumerate(zip(net.arrows,net.arrow_anchors)):
        for (q,u),b in list(zip(net.arrows,net.arrow_anchors))[i+1:]:
            if np.linalg.norm(p-q)<25 and float(t@u)>.7:assert np.linalg.norm(np.asarray(a)-np.asarray(b))<1e-6
    wide=Scene.light(junction,S(arrow_min_gap_m=200)).network;assert len(wide.arrows)<len(net.arrows)

@pytest.fixture
def layer0(tmp_path):
    """Tudo na camada 0: eixo (cor 1), pavimento em hachura (cor 8), barreira em linha (cor 2), sinalização (cor 7)."""
    d=ezdxf.new();m=d.modelspace()
    m.add_lwpolyline([(500000,7800000),(500400,7800000)],dxfattribs={'layer':'0','color':1})
    for k in range(12):m.add_line((500000+k*30,7799993),(500020+k*30,7799993),dxfattribs={'layer':'0','color':7})
    h=m.add_hatch(color=8,dxfattribs={'layer':'0'});h.paths.add_polyline_path([(500000,7799991),(500400,7799991),(500400,7800009),(500000,7800009)],is_closed=True)
    for k in range(10):m.add_line((500000+k*40,7800010),(500035+k*40,7800010),dxfattribs={'layer':'0','color':2})
    d.saveas(tmp_path/'input.dxf');return tmp_path

def test_layer0_split_by_color_and_type(layer0):
    from app.geometry import analyze
    with pytest.raises(ValueError):analyze(layer0,S())        # sem mapeamento não há eixo (tudo na camada 0)
    from app.geometry import split_layers,eff_layer,walk
    doc=ezdxf.readfile(layer0/'input.dxf');ents=list(walk(doc.modelspace()))
    sp=split_layers(ents,doc,'auto');assert sp=={'0'}
    names=sorted({eff_layer(e,sp,doc) for e in ents})
    assert names==['0 · cor 1 · LWPOLYLINE','0 · cor 2 · LINE','0 · cor 7 · LINE','0 · cor 8 · HATCH']
    s=S(layers={'axis':['0 · cor 1 · LWPOLYLINE'],'pavement':['0 · cor 8 · HATCH'],'barrier':['0 · cor 2 · LINE'],'sign_h':['0 · cor 7 · LINE']})
    items,axis,ds,axes,rep=analyze(layer0,s)
    roles={e['role'] for e in items};assert {'axis','pavement','barrier','sign_h'}<=roles
    assert any('separada' in w for w in rep['warnings'])
    assert {l['name'] for l in rep['layers']}==set(names)
    # Mapeamento suspeito: linhas como pavimento geram aviso claro.
    bad=S(layers={'axis':['0 · cor 1 · LWPOLYLINE'],'pavement':['0 · cor 8 · HATCH','0 · cor 2 · LINE']})
    w=analyze(layer0,bad)[4]['warnings'];assert any('não tem áreas fechadas' in x for x in w)
    # Desligado: nomes como no DXF.
    assert split_layers(ents,doc,'off')==set()
    from app.render import Scene
    sc=Scene.light(layer0,s);assert sc.network.edges and sc.network.fills is not None
    assert not [1 for (a,b,c),k in zip(sc.network.markings,sc.network.mark_src) if k!=-4 and abs((a[1]+b[1])/2-7799993)<.3]  # DXF substitui a gerada

def test_migration_keeps_existing_layer_names():
    s=Settings.model_validate({'schema_version':16,'km_start_m':0,'km_end_m':100,'layers':{'axis':['EIXO']}})
    assert s.schema_version>=17 and s.layer_split=='off'
    n=Settings.model_validate({'schema_version':16,'km_start_m':0,'km_end_m':100})
    assert n.layer_split=='auto' and n.accesses==[] and n.lane_arrow_repeat=='conflicts'

def access(**kw):
    return {'name':'Acesso Fazenda','points':[{'x':500200,'y':7799991.5},{'x':500200,'y':7799960},{'x':500210,'y':7799930}],**kw}

def test_access_with_tapers_geometry_and_traffic(tmp_path):
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500400,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799991),(500400,7799991),(500400,7800009),(500000,7800009)],is_closed=True)
    d.saveas(tmp_path/'input.dxf')
    from app.geometry import analyze
    items=analyze(tmp_path,S(accesses=[access()]))[0]
    acc=[Polygon(e['points']) for e in items if str(e['layer']).startswith('ACESSO')];assert acc
    g=acc[0] if len(acc)==1 else __import__('shapely.ops',fromlist=['unary_union']).unary_union(acc)
    # Acesso ao sul (lado direito do eixo, que cresce para leste): tráfego para leste; taper de entrada a oeste.
    assert g.intersects(box(500150,7799987,500170,7799991))      # entrada (antes da ligação)
    assert g.intersects(box(500230,7799987,500250,7799991))      # saída (depois)
    assert not g.intersects(box(500100,7799980,500120,7799990))  # nada além do taper (60 m)
    assert g.covers(Point(500205,7799935))                        # pavimento do acesso
    only_in=Polygon(analyze(tmp_path,S(accesses=[access(mode='in')]))[0][-1]['points'])
    assert not only_in.intersects(box(500235,7799987,500250,7799990))
    # Rede de tráfego: há itinerário que usa o acesso.
    from app.render import Scene
    net=Scene.light(tmp_path,S(accesses=[access()])).network
    assert any(e['p'][:,1].min()<7799950 for e in net.edges if not e['disabled'])
    assert any(p['p'][:,1].min()<7799950 for p in net.paths)
    # Primeiro ponto longe do bordo: aviso claro e nada gerado.
    far=analyze(tmp_path,S(accesses=[access(points=[{'x':500200,'y':7799900},{'x':500200,'y':7799850}])]))
    assert not [e for e in far[0] if str(e['layer']).startswith('ACESSO')] and any('bordo da pista' in w for w in far[4]['warnings'])

def test_access_export_roundtrip(junction):
    from app.exporters import features,geojson,_read_geojson,apply_import
    from app.render import Scene
    cfg=S(accesses=[access()]);sc=Scene.light(junction,cfg)
    out,counts=apply_import({},_read_geojson(geojson(features(cfg,sc.stationing),cfg.crs),cfg.crs))
    assert counts.get('accesses')==1 and Settings.model_validate({**cfg.model_dump(),**out}).accesses[0].taper_in_m==60

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_km_span_and_access_tools(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    cfg={**settings().model_dump(),'duration_s':10,'pois':[{'id':'p1','title':'Passarela 1','kind':'passarela','x':500300,'y':7800000}]}
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
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && editor && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500250,y:7800000});view.s=Math.min(60,canvas.width*mpp()/220);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Km digitado no ponto inicial e no final.
            page.click('#toolbar button[data-tool="chain"]');page.fill('#kmHere','325+850');page.mouse.click(*W2C(500150,7800000))
            assert ev('cfg.km_start_m')==325850 and ev("document.getElementById('km_start_m').value")=='325+850'
            page.click('#toolbar button[data-tool="chainend"]');page.fill('#kmHere','326+000');page.mouse.click(*W2C(500350,7800000))
            assert ev('cfg.km_end_m')==326000 and ev('M.chainage.calibrate')
            # Vão da passarela: arrastar a ponta do vão (desde a 1.19 o centro move a passarela) até 30 m do centro = 60 m.
            page.click('#toolbar button[data-tool="span"]');g=ev('spanGeom(M.pois[0])');e0=min(g['a'],g['b'],key=lambda q:q['y']);page.mouse.move(*W2C(e0['x'],e0['y']));page.mouse.down();page.mouse.move(*W2C(500300,7799985),steps=5);page.mouse.move(*W2C(500300,7799970),steps=5);page.mouse.up()
            sp=ev("M.pois[0].bridge_span_m");assert 55<sp<65 and abs(ev("M.pois[0].bridge_angle_deg"))<=5
            ev('undo()');assert ev("M.pois[0].bridge_span_m")!=sp
            # Acesso com taper.
            page.click('#toolbar button[data-tool="access"]');page.fill('#accIn','50')
            for x,y in [(500180,7799991.5),(500180,7799970),(500188,7799955)]:page.mouse.click(*W2C(x,y))
            page.keyboard.press('Enter');assert ev('M.accesses.length')==1 and ev('M.accesses[0].taper_in_m')==50
            ev('save()');page.wait_for_timeout(500)
            conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['accesses'][0]['name']=='Acesso 1' and conf['km_start_m']==325850
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors

def test_lanes_per_direction_shoulder_and_third_lane(junction):
    """Padrão: 2 faixas por sentido e o restante como acostamento (linha contínua de bordo da faixa);
    3ª faixa entre início e fim marcados."""
    from app.render import Scene
    net=Scene.light(junction,S()).network
    k=next(k for k,L in net.lane_info.items() if L is not None and net.raw_info[k]['kind']=='main')
    L=net.lane_info[k];assert set(L['lanes'][L['lanes']>0])=={2}
    mid=[((a+b)/2,col) for (a,b,col),s_ in zip(net.markings,net.mark_src) if s_==k and 500020<(a[0]+b[0])/2<500090]
    ys=sorted({round(float(p[1]),1) for p,_ in mid})
    # Pista de mão única (sentido +x, faixa interna à esquerda = norte): divisória a 3,5 m e bordo da faixa a 7 m do bordo interno.
    top=7800009-.0
    assert any(abs(y-(top-3.5))<.4 for y in ys) and any(abs(y-(top-7.0))<.4 for y in ys) and len(ys)==2
    r={'name':'3ª faixa','start':{'x':500020,'y':7800000},'end':{'x':500150,'y':7800000},'lanes':3}
    net3=Scene.light(junction,S(lane_ranges=[r])).network;L3=net3.lane_info[k]
    ch=net3.chain(L3["q"]);inside=(ch>40)&(ch<130);outside=(ch>1)&(ch<14)
    assert set(L3['lanes'][inside&(L3['lanes']>0)])=={3} and set(L3['lanes'][outside&(L3['lanes']>0)])=={2}
    auto=Scene.light(junction,S(lanes_per_direction=0)).network;La=auto.lane_info[k];assert np.median(La['lanes'][La['lanes']>0])==5
