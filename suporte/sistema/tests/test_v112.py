"""1.12: sinalização limpa em todo o modelo, setas em todas as faixas, mão de direção nas ilhas,
tráfego simulado sem colisão (engarrafamento, interdições, desvios) e travessia do canteiro."""
import os,socket,threading,time,math
import numpy as np,ezdxf,pytest,cv2
from shapely.geometry import Polygon,Point,LineString
from test_workflow import settings,wait
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),**kw})

def hatch(m,layer,pts):
    h=m.add_hatch(dxfattribs={'layer':layer});h.paths.add_polyline_path(pts,is_closed=True)

@pytest.fixture
def divided(tmp_path):
    """Rodovia duplicada de 600 m com canteiro central e uma abertura (retorno em nível) em x=500290..500310."""
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO','CANTEIRO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800008),(500600,7800008)],dxfattribs={'layer':'EIXO'})
    m.add_lwpolyline([(500000,7799992),(500600,7799992)],dxfattribs={'layer':'EIXO'})
    hatch(m,'PAVIMENTO',[(500000,7799986),(500600,7799986),(500600,7800014),(500000,7800014)])
    hatch(m,'CANTEIRO',[(500000,7799998),(500290,7799998),(500290,7800002),(500000,7800002)])
    hatch(m,'CANTEIRO',[(500310,7799998),(500600,7799998),(500600,7800002),(500310,7800002)])
    d.saveas(tmp_path/'input.dxf');return tmp_path

@pytest.fixture
def island(tmp_path):
    """Via lateral de mão dupla com ilha divisória no meio (circulação deve deixar a ilha à esquerda)."""
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO','CANTEIRO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
    hatch(m,'PAVIMENTO',[(500000,7799996),(500300,7799996),(500300,7800004),(500000,7800004)])
    hatch(m,'PAVIMENTO',[(500060,7800030),(500240,7800030),(500240,7800048),(500060,7800048)])
    hatch(m,'CANTEIRO',[(500120,7800037),(500180,7800037),(500180,7800041),(500120,7800041)])
    d.saveas(tmp_path/'input.dxf');return tmp_path

def scene(d,**kw):
    from app.render import Scene
    return Scene(d,S(**kw))

def speeds(sim):
    out=[]
    for k in range(1,len(sim.frames)):
        a=dict(zip(sim.frames[k-1][0].tolist(),sim.frames[k-1][1].tolist()));b=dict(zip(sim.frames[k][0].tolist(),sim.frames[k][1].tolist()))
        out+= [(b[i]-a[i])/.2 for i in b if i in a]
    return np.array(out)

def test_clean_signage_follows_pavement_edges_everywhere(junction):
    sc=scene(junction)
    net=sc.network;edges=[(a,b) for (a,b,_),s in zip(net.markings,net.mark_src) if s==-2]
    assert len(edges)>100
    bnd=net.paved.boundary
    d=np.array([bnd.distance(Point(*(a+b)/2)) for a,b in edges]);assert d.max()<.9  # bordo a ~0,35 m do contorno
    old=scene(junction,signage_style='previous')
    centers=[m for m,s in zip(net.markings,net.mark_src) if s>=0]
    # Nenhuma pintura de eixo nas zonas de junção.
    z=net.junction_zones()
    assert not any(z.contains(Point(*(a+b)/2)) for a,b,_ in centers)

def test_every_directional_lane_has_an_arrow(junction):
    sc=scene(junction);net=sc.network
    A=np.array([p for p,_ in net.arrows])
    for e in net.edges:
        if e['disabled'] or e['length']<8:continue
        assert np.min(np.linalg.norm(A[:,None,:]-e['p'][None,::4,:],axis=2))<13,e['kind']

def test_island_keeps_right_hand_rule(island):
    sc=scene(island,traffic=False);net=sc.network
    assert net.splitters
    north=[r for r in net.raw_info if np.mean(r['points'][:,1]>7800041)>.8 and 500125<np.mean(r['points'][:,0])<500175]
    south=[r for r in net.raw_info if np.mean((r['points'][:,1]<7800037)&(r['points'][:,1]>7800030))>.8 and 500125<np.mean(r['points'][:,0])<500175]
    assert north and south
    dx=lambda r:(r['points'][-1][0]-r['points'][0][0])*(1 if r['forward'] else -1)
    assert all(dx(r)<0 for r in north) and all(dx(r)>0 for r in south)  # norte para oeste, sul para leste

@pytest.mark.parametrize('density',[1,5])
def test_simulation_has_no_rear_collisions(junction,divided,density):
    for d in (junction,divided):
        sc=scene(d,traffic_density=density,duration_s=40);sim=sc.traffic()
        r=sim.report();assert r['rear_collisions']==0 and r['vehicles']>0 and (r['min_gap_m'] is None or r['min_gap_m']>=1.0),r

def test_congestion_lowers_speed(divided):
    # 1.37: frota clássica (como quando o teste foi escrito); a variada também reduz, um pouco menos (veículos longos ocupam a via).
    a=speeds(scene(divided,traffic_density=1,duration_s=60,vehicle_mix='classico').traffic());b=speeds(scene(divided,traffic_density=6,duration_s=60,vehicle_mix='classico').traffic())
    assert len(a) and len(b) and b.mean()<a.mean()*.9
    a=speeds(scene(divided,traffic_density=1,duration_s=60,vehicle_mix='variado').traffic());b=speeds(scene(divided,traffic_density=6,duration_s=60,vehicle_mix='variado').traffic())
    assert b.mean()<a.mean()*.97

BLOCK=[{'x':500400,'y':7799986},{'x':500440,'y':7799986},{'x':500440,'y':7799998},{'x':500400,'y':7799998}]

def test_partial_block_slows_and_queues(divided):
    base=scene(divided,traffic_density=3,duration_s=60).traffic()
    sc=scene(divided,traffic_density=3,duration_s=60,lane_blocks=[{'name':'Obra','points':BLOCK,'mode':'partial','speed_kmh':15}]);sim=sc.traffic()
    poly=Polygon([(p['x'],p['y']) for p in BLOCK]);inside=[]
    for k in range(1,len(sim.frames),5):
        for (vid,i,s) in sim.state(k*.2):
            path=sim.paths[i];j=min(len(path['p'])-1,int(np.searchsorted(path['d'],s)))
            if poly.contains(Point(*path['p'][j])):inside.append(vid)
    sp=speeds(sim);assert inside and sim.report()['rear_collisions']==0
    assert sp.mean()<speeds(base).mean()

def test_total_block_stops_traffic_while_active(divided):
    sc=scene(divided,traffic_density=2,duration_s=60,lane_blocks=[{'name':'Fechada','points':BLOCK,'mode':'total','start_s':10,'end_s':40}]);sim=sc.traffic()
    poly=Polygon([(p['x'],p['y']) for p in BLOCK]).buffer(-.5)
    def count(t0,t1):
        n=0
        for t in np.arange(t0,t1,.5):
            for vid,i,s in sim.state(t):
                path=sim.paths[i];j=min(len(path['p'])-1,int(np.searchsorted(path['d'],s)))
                if poly.contains(Point(*path['p'][j])):n+=1
        return n
    assert count(15,40)==0 and count(45,60)>0 and sim.report()['rear_collisions']==0
    # Fila antes da interdição: veículos parados (velocidade ~0) a montante.
    stopped=0
    for vid,i,s in sim.state(35):
        path=sim.paths[i];j=min(len(path['p'])-1,int(np.searchsorted(path['d'],s)));x,y=path['p'][j]
        if 500300<x<500400 and y<7799998:stopped+=1
    assert stopped>=2

def crossing_paths(net):
    """Trechos que trocam de pista (cruzam o canteiro) e continuam liberados para veículos."""
    return sum(1 for e in net.edges if not e['disabled'] and net.side(e['p'][0]) is not None and net.side(e['p'][-1]) is not None and net.side(e['p'][0])!=net.side(e['p'][-1]))

def test_median_crossing_rules(divided):
    free=scene(divided,median_crossing='free',traffic=False).network
    marked=scene(divided,median_crossing='marked',traffic=False).network
    returns=scene(divided,traffic=False).network
    assert len(free.main)==2 and crossing_paths(free)>0 and crossing_paths(returns)>0  # abertura no canteiro = retorno em nível
    assert crossing_paths(marked)==0 and marked.crossings_blocked>0
    allow=scene(divided,median_crossing='marked',traffic=False,crossing_zones=[{'name':'Retorno','mode':'allow','point':{'x':500300,'y':7800000},'radius_m':15}]).network
    assert crossing_paths(allow)>0
    deny=scene(divided,traffic=False,crossing_zones=[{'name':'X','mode':'deny','point':{'x':500300,'y':7800000},'radius_m':15}]).network
    assert crossing_paths(deny)==0

def test_blocks_drawn_only_while_active(divided):
    blk=[{'name':'Obra','points':BLOCK,'mode':'total','start_s':5,'end_s':8}]
    a=scene(divided,traffic=False,duration_s=20,lane_blocks=blk);b=scene(divided,traffic=False,duration_s=20)
    v=((500420,7799992),120)
    fa=a.frame(6,view=v)[0];fb=b.frame(6,view=v)[0];assert np.abs(fa.astype(int)-fb).max()>50
    assert np.array_equal(a.frame(12,view=v)[0],b.frame(12,view=v)[0])

def test_previous_traffic_model_unchanged(junction):
    sc=scene(junction,traffic_model='anterior');assert sc.traffic() is None
    a=list(sc.traffic_iter(3.));b=list(sc.network.vehicles_ex(3.,sc.s.traffic_speed_kmh/3.6));assert len(a)==len(b)

def test_schema_v11_and_export(divided):
    from app import exporters
    s=Settings.model_validate({'schema_version':10,'km_start_m':0,'km_end_m':100})
    assert s.schema_version>=11 and s.traffic_model=='simulado' and s.median_crossing=='returns' and s.traffic_density==1
    with pytest.raises(ValueError):S(lane_blocks=[{'name':'x','points':BLOCK[:2]}])
    s=S(lane_blocks=[{'id':'b','name':'Obra','points':BLOCK,'mode':'total','start_s':3}],crossing_zones=[{'id':'z','name':'Ret','mode':'allow','point':{'x':500300,'y':7800000},'radius_m':12}])
    sc=scene(divided,**{k:v for k,v in s.model_dump().items() if k in ('lane_blocks','crossing_zones')})
    feats=exporters.features(s,sc.stationing,sc.axes,sc.network.raw_info,sc.oae)
    back=exporters.read_any(exporters.geojson(feats,s.crs,True).encode(),'m.geojson',s.crs);cfg,_=exporters.apply_import({},back)
    c=Settings.model_validate({**s.model_dump(),**cfg});assert c.lane_blocks[0].mode=='total' and c.crossing_zones[0].radius_m==12

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_blocks_and_crossings(divided):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(divided/'input.dxf').read_bytes())})
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
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && editor && ready()',timeout=20000)
            ev=page.evaluate;ev('fitView()')
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            def tool(t):page.click(f'#toolbar button[data-tool="{t}"]')
            tool('block');page.select_option('#blkMode','total');page.fill('#blkStart','2');page.fill('#blkEnd','6')
            for v in BLOCK:page.mouse.click(*W2C(v['x'],v['y']))
            page.keyboard.press('Enter')
            bl=ev('M.lane_blocks[0]');assert len(bl['points'])==4 and bl['mode']=='total' and bl['start_s']==2 and bl['end_s']==6
            tool('crossok');page.mouse.click(*W2C(500300,7800000));assert ev('M.crossing_zones[0].mode')=='allow'
            tool('crossno');page.mouse.click(*W2C(500100,7800000));assert ev('M.crossing_zones[1].mode')=='deny'
            tool('exedit');v=bl['points'][1];page.mouse.move(*W2C(v['x'],v['y']));page.mouse.down();page.mouse.move(*W2C(v['x']+3,v['y']),steps=3);page.mouse.up()
            assert ev('M.lane_blocks[0].points[1].x')==pytest.approx(v['x']+3,abs=.8)
            ev('undo()');assert ev('M.lane_blocks[0].points[1].x')==pytest.approx(v['x'],abs=.01);ev('redo()')
            page.fill('input[data-f="blk.0.end_s"]','');page.dispatch_event('input[data-f="blk.0.end_s"]','change');assert ev('M.lane_blocks[0].end_s') is None
            page.click('#markList button[data-act="del"][data-list="crossing_zones"][data-i="1"]');assert ev('M.crossing_zones.length')==1
            ev("document.getElementById('traffic_density').closest('details').open=true");page.fill('#traffic_density','4');page.select_option('#median_crossing','marked');ev('scheduleSave()')
            page.wait_for_timeout(1500)
            cfg=c.get(f'/api/projects/{pid}').json()['config']
            assert cfg['lane_blocks'][0]['mode']=='total' and cfg['lane_blocks'][0]['end_s'] is None and cfg['crossing_zones'][0]['mode']=='allow'
            assert cfg['traffic_density']==4 and cfg['median_crossing']=='marked'
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
