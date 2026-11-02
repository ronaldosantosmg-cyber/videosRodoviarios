"""1.10: sinalização limpa, setas por km/conflito, áreas sem sinalização, marcos de km, seta de sentido,
grama do canteiro, cidades próximas e proteção contra entradas degeneradas (divisão por zero / vazio)."""
import json,os,socket,threading,time,tempfile
from pathlib import Path
import numpy as np,ezdxf,pytest
from fastapi.testclient import TestClient
from test_workflow import drawing,settings,wait
from app.models import Settings
from app.server import app
from app import store

def S(**kw):return settings(**{'signage_detail':'basic',**kw})  # 1.15: estes testes cobrem a sinalização da 1.10 (modo básico)

@pytest.fixture
def junction(tmp_path):
    """Pista principal com ramo em T e uma alça curta: gera junções onde a pintura antiga se cruzava."""
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO','CANTEIRO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500400,7800000)],dxfattribs={'layer':'EIXO'})
    for pts in [[(500000,7799991),(500400,7799991),(500400,7800009),(500000,7800009)],
                [(500190,7800009),(500210,7800009),(500210,7800120),(500190,7800120)],
                [(500100,7799991),(500112,7799991),(500135,7799960),(500123,7799960)]]:
        h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path(pts,is_closed=True)
    d.saveas(tmp_path/'input.dxf');return tmp_path

def crossings(net):
    A=np.array([m[0] for m in net.markings]);B=np.array([m[1] for m in net.markings]);src=np.array(net.mark_src)
    from shapely.geometry import LineString
    from scipy.spatial import cKDTree
    M=(A+B)/2;bad=0
    for i,j in cKDTree(M).query_pairs(3.2):
        if src[i]==src[j]:continue
        u=(B[i]-A[i])/max(np.linalg.norm(B[i]-A[i]),1e-9);v=(B[j]-A[j])/max(np.linalg.norm(B[j]-A[j]),1e-9)
        if abs(float(u@v))<.906 and LineString([A[i],B[i]]).distance(LineString([A[j],B[j]]))<.8:bad+=1
    return bad

def test_clean_signage_removes_crossings_and_short_spurs(junction):
    from app.render import Scene
    old=Scene(junction,S(signage_style='previous',flow_arrows='dense'));new=Scene(junction,S())
    assert len(new.network.markings)<len(old.network.markings)
    assert crossings(new.network)==0 and crossings(old.network)>0
    rep=new.report['traffic_network']['signage'];assert rep['clean'] and rep['mode']=='km_conflicts'

def test_flow_arrows_modes(junction):
    from app.render import Scene
    dense=Scene(junction,S(flow_arrows='dense')).network.arrows;smart=Scene(junction,S()).network.arrows
    off=Scene(junction,S(flow_arrows='off')).network.arrows;tight=Scene(junction,S(flow_arrow_spacing_m=100)).network.arrows
    assert off==[] and 0<len(smart)<len(dense) and len(tight)>=len(smart)
    # Nenhuma seta duplicada a menos de 12 m no mesmo sentido.
    for i,(p,t) in enumerate(smart):
        for q,u in smart[i+1:]:assert np.linalg.norm(p-q)>=12 or float(t@u)<.7

def test_clean_areas_remove_paint_and_arrows_only_inside(junction):
    from app.render import Scene
    area=[{'x':500150,'y':7799985},{'x':500260,'y':7799985},{'x':500260,'y':7800130},{'x':500150,'y':7800130}]
    a=Scene(junction,S(flow_arrows='dense'));b=Scene(junction,S(flow_arrows='dense',clean_areas=[area]))
    from shapely.geometry import Polygon,Point
    poly=Polygon([(p['x'],p['y']) for p in area])
    inside=lambda net:sum(poly.contains(Point(*(m[0]+m[1])/2)) for m in net.markings)
    assert inside(a.network)>0 and inside(b.network)==0
    assert not any(poly.contains(Point(*p)) for p,_ in b.network.arrows)
    assert len(b.network.markings)-0>=len(a.network.markings)-inside(a.network)-5  # fora da área nada some
    assert np.array_equal(a.surface,b.surface)  # o pavimento continua
    with pytest.raises(ValueError):S(clean_areas=[area[:2]])

def test_schema_v9_migration_defaults():
    old=Settings.model_validate({'schema_version':8,'km_start_m':0,'km_end_m':100})
    from app.migration import SCHEMA_VERSION
    assert old.schema_version==SCHEMA_VERSION and old.signage_style=='clean' and old.flow_arrows=='km_conflicts' and old.km_markers and old.cities==[]
    with pytest.raises(ValueError):Settings.model_validate({'schema_version':SCHEMA_VERSION+1})

def test_km_markers_badge_cities_and_grass_are_drawn(drawing):
    from app.render import Scene
    from app import annotations
    v=((500150,7800000),160)
    base=dict(chainage={'mode':'auto'},km_start_m=2000,km_end_m=2300,traffic=False)
    on=Scene(drawing,S(**base,cities=[{'name':'Vila Teste','point':{'x':500150,'y':7800030}},{'name':'Longe','point':{'x':500150,'y':7803000}}]))
    off=Scene(drawing,S(**base,km_markers=False,direction_badge=False,cities_show=False,median_grass=False))
    items=annotations.km_marker_items(on);assert [i['tag'] for i in items]==['Início','Fim'] and 'km 2+000' in items[0]['name']
    fa=on.frame(0,view=v)[0].astype(int);fb=off.frame(0,view=v)[0].astype(int);diff=np.abs(fa-fb).max(2)>8
    hdr=int(157*on.scale)
    assert diff[hdr:hdr+int(90*on.scale),on.W//2-150:on.W//2+150].mean()>.2  # seta de sentido no topo
    q=on.screen(np.array([[500150,7800030]]),np.array(v[0]),v[1])[0].astype(int);assert diff[q[1]-6:q[1]+6,q[0]:q[0]+60].any()  # nome da cidade
    m=on.screen(np.array([on._km_items[0]['xy']]),np.array(v[0]),v[1])[0].astype(int)
    if 0<m[0]<on.W:assert diff[m[1]-8:m[1]+8,m[0]-8:m[0]+8].any()  # marco do km inicial
    # Cidade fora do quadro: indicador de borda (parte de cima, abaixo da seta de sentido).
    assert diff[hdr+int(84*on.scale):hdr+int(200*on.scale)].any()
    # Grama do canteiro (qualidade aprimorada): o canteiro muda, o pavimento não.
    g1=Scene(drawing,S(traffic=False,km_markers=False,direction_badge=False)).frame(0,view=v)[0].astype(int)
    g0=Scene(drawing,S(traffic=False,km_markers=False,direction_badge=False,median_grass=False)).frame(0,view=v)[0].astype(int)
    md=on.screen(np.array([[500100,7800000]]),np.array(v[0]),v[1])[0].astype(int);pv=on.screen(np.array([[500100,7800005]]),np.array(v[0]),v[1])[0].astype(int)
    assert np.abs(g1-g0)[md[1]-1:md[1]+2,md[0]-20:md[0]+20].max()>0 and np.abs(g1-g0)[pv[1]-1:pv[1]+2,pv[0]-20:pv[0]+20].max()==0

OSM={'elements':[
    {'type':'node','lat':-19.76,'lon':-43.035,'tags':{'place':'town','name':'Cidade Perto','population':'18.000'}},
    {'type':'node','lat':-19.70,'lon':-43.30,'tags':{'place':'city','name':'Cidade Grande','population':'90000'}},
    {'type':'node','lat':-19.7605,'lon':-43.0345,'tags':{'place':'village','name':'Povoado Perto'}},
    {'type':'node','lat':-19.95,'lon':-43.2,'tags':{'place':'village','name':'Povoado Longe'}},
    {'type':'node','lat':-19.76,'lon':-43.04,'tags':{'place':'town'}},
    {'type':'node','lat':-19.76,'lon':-43.04,'tags':{'place':'town','name':'Cidade Perto'}}]}

def test_cities_from_osm_with_cache(tmp_path):
    from app.cities import nearby
    from pyproj import Transformer
    x,y=Transformer.from_crs(4326,'EPSG:31983',always_xy=True).transform(-43.035,-19.76)
    calls=[]
    def fake(q):calls.append(q);assert 'place' in q;return OSM
    out=nearby(tmp_path,'EPSG:31983',[[x-500,y-500],[x+500,y+500]],30,fetch=fake)
    names=[c['name'] for c in out]
    assert names[0]=='Cidade Grande' and 'Cidade Perto' in names and 'Povoado Perto' in names and 'Povoado Longe' not in names and names.count('Cidade Perto')==1
    c=next(c for c in out if c['name']=='Cidade Perto');assert c['dist_km']<1 and c['population']==18000
    again=nearby(tmp_path,'EPSG:31983',[[x-500,y-500],[x+500,y+500]],30,fetch=fake);assert again==out and len(calls)==1
    with pytest.raises(ValueError):nearby(tmp_path,'EPSG:31983',[[float('nan'),0],[1,1]],30,fetch=fake)

def test_cities_endpoint(drawing,monkeypatch):
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
        assert c.get(f'/api/projects/{pid}/cities/auto').status_code==409
        wait(c,c.post(f'/api/projects/{pid}/analyze').json()['id'])
        def offline(*a,**k):raise OSError('sem rede')
        monkeypatch.setattr('urllib.request.urlopen',offline)
        r=c.get(f'/api/projects/{pid}/cities/auto');assert r.status_code==503 and 'à mão' in r.json()['detail']
        assert c.get(f'/api/projects/{pid}/cities/auto?radius_km=0').status_code==422
        monkeypatch.setattr('app.cities._download',lambda q,timeout=30:OSM)
        r=c.get(f'/api/projects/{pid}/cities/auto?radius_km=150');assert r.status_code==200 and isinstance(r.json()['cities'],list)

def test_export_reimport_clean_areas_and_cities(drawing):
    from app.render import Scene
    from app import exporters
    area=[{'x':500150,'y':7799985},{'x':500260,'y':7799985},{'x':500260,'y':7800030}]
    s=S(clean_areas=[area],cities=[{'id':'c1','name':'Nova Era','point':{'x':500100,'y':7800500},'source':'auto','kind':'town','show':False}]);sc=Scene(drawing,s)
    feats=exporters.features(s,sc.stationing,sc.axes,sc.network.raw_info,sc.oae)
    for name,data in [('m.geojson',exporters.geojson(feats,s.crs,True).encode()),('m.kml',exporters.kml(feats,s.crs).encode())]:
        back=exporters.read_any(data,name,s.crs);cfg,count=exporters.apply_import({},back)
        assert count['clean_areas']==1 and count['cities']==1
        c=Settings.model_validate({**s.model_dump(),**cfg})
        assert c.cities[0].name=='Nova Era' and c.cities[0].show is False and abs(c.cities[0].point.y-7800500)<.01
        assert abs(c.clean_areas[0][1].x-500260)<.01

@pytest.mark.parametrize('case',['eixo_curto','eixo_fechado','eixo_repetido','pavimento_degenerado','sem_eixo'])
def test_degenerate_inputs_fail_clearly_or_render(case,tmp_path):
    """Sem ZeroDivisionError/NaN: entradas degeneradas geram mensagem clara ou um quadro válido."""
    import warnings
    from app.render import Scene
    d=ezdxf.new();m=d.modelspace();[d.layers.new(l) for l in ['EIXO','PAVIMENTO']]
    E={'layer':'EIXO'};P={'layer':'PAVIMENTO'}
    if case=='eixo_curto':m.add_lwpolyline([(500000,7800000),(500001,7800000)],dxfattribs=E)
    if case=='eixo_fechado':m.add_lwpolyline([(500000,7800000),(500100,7800000),(500100,7800100),(500000,7800000)],dxfattribs=E)
    if case=='eixo_repetido':m.add_lwpolyline([(500000,7800000),(500000,7800000),(500050,7800000),(500050,7800000),(500100,7800000)],dxfattribs=E)
    if case=='pavimento_degenerado':
        m.add_lwpolyline([(500000,7800000),(500100,7800000)],dxfattribs=E);m.add_lwpolyline([(500000,7800000),(500100,7800000),(500000,7800000)],close=True,dxfattribs=P)
    if case=='sem_eixo':m.add_lwpolyline([(500000,7800000),(500100,7800000),(500100,7800010)],close=True,dxfattribs=P)
    d.saveas(tmp_path/'input.dxf')
    s=S(chainage={'mode':'manual','start':{'x':500050,'y':7800000},'end':{'x':500050,'y':7800000},'calibrate':True},cities=[{'name':'X','point':{'x':500050,'y':7800000}}])
    with warnings.catch_warnings():
        warnings.simplefilter('error',RuntimeWarning)
        try:sc=Scene(tmp_path,s)
        except ValueError as e:
            assert case in ('eixo_curto','sem_eixo') and ('eixo' in str(e).lower());return
        for t in (0,1.5,2.9):im=sc.frame(t)[0];assert im.shape==(720,1280,3)
        sc.frame(0,overview=True)
    assert case not in ('eixo_curto','sem_eixo')

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_clean_area_and_cities_in_browser(drawing):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx,cv2
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
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    from pyproj import Transformer
    lon,lat=Transformer.from_crs('EPSG:31983',4326,always_xy=True).transform(500150,7800300)
    import app.cities as ac
    orig=ac._download;ac._download=lambda q,timeout=30:{'elements':[{'type':'node','lat':lat,'lon':lon,'tags':{'place':'town','name':'Vila OSM'}}]}
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && ready()',timeout=20000)
            ev=page.evaluate;ev('fitView()')
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            def tool(t):page.click(f'#toolbar button[data-tool="{t}"]')
            import math
            tool('cleanarea');pts=[W2C(500150+15*math.cos(t/6),7800000+15*math.sin(t/6)) for t in range(38)]
            page.mouse.move(*pts[0]);page.mouse.down()
            for q in pts[1:]:page.mouse.move(*q)
            page.mouse.up();assert ev('M.clean_areas.length')==1 and ev('M.exclusions.length')==0
            tool('exedit');v=ev('M.clean_areas[0][0]');page.mouse.move(*W2C(v['x'],v['y']));page.mouse.down();page.mouse.move(*W2C(v['x']+4,v['y']+4),steps=3);page.mouse.up()
            assert ev('M.clean_areas[0][0].x')==pytest.approx(v['x']+4,abs=.8)
            ev('undo()');assert ev('M.clean_areas[0][0].x')==pytest.approx(v['x'],abs=.01);ev('redo()')
            tool('city');page.fill('#cityName','Vila Manual');page.mouse.click(*W2C(500100,7800040));assert ev('M.cities[0].name')=='Vila Manual'
            page.click('button[data-act="city-auto"]');page.wait_for_function('M.cities.length===2',timeout=10000)
            assert ev('M.cities[1].name')=='Vila OSM' and ev('M.cities[1].source')=='auto' and abs(ev('M.cities[1].point.y')-7800300)<1
            page.click('button[data-act="city-auto"]');page.wait_for_timeout(500);assert ev('M.cities.length')==2  # sem duplicar
            page.click('#markList button[data-act="del"][data-list="cities"]');assert ev('M.cities.length')==1
            ev("document.getElementById('flow_arrows').closest('details').open=true");page.select_option('#flow_arrows','off');page.uncheck('#direction_badge');ev('scheduleSave()');page.wait_for_timeout(1500)
            cfg=c.get(f'/api/projects/{pid}').json()['config']
            assert len(cfg['clean_areas'])==1 and cfg['cities'][0]['name']=='Vila OSM' and cfg['flow_arrows']=='off' and cfg['direction_badge'] is False and cfg['schema_version']>=9
            b.close()
    finally:
        ac._download=orig;server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
