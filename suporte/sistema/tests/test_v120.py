"""1.20: veículos em linha reta, sentido pelo eixo, áreas de pista (nova/existente/acostamento) desenhadas ou
selecionadas, acostamento por início/fim/largura e perfil "Apresentação técnica" (hachuras, voo contínuo,
indicador de progresso, conferência DXF×KMZ, blocos vazios na imagem e conferência do MP4)."""
import os,json,socket,threading,time,subprocess
import numpy as np,ezdxf,pytest,cv2
from shapely.geometry import Polygon,Point,box,LineString
from shapely.ops import unary_union
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})

# ---------------- veículos ----------------
def test_steady_path_removes_backtracks_and_steps():
    from app.traffic import steady_path,drop_backtracks
    allowed=box(-5,-6,400,6)
    # Duas arestas emendadas com sobreposição de 1,5 m (o veículo "voltava") e degraus de esqueleto.
    a=np.column_stack([np.arange(0,200.1,.45),np.round(np.sin(np.arange(0,200.1,.45))*.0+((np.arange(0,200.1,.45)//.9)%2)*.45,2)])
    b=np.column_stack([np.arange(198.5,390,.45),np.zeros(len(np.arange(198.5,390,.45)))])
    P=np.vstack([a,b]);v=np.diff(P,axis=0);assert (np.sum(v[1:]*v[:-1],axis=1)<0).any()
    q=drop_backtracks(P);w=np.diff(q,axis=0);assert not (np.sum(w[1:]*w[:-1],axis=1)<0).any()
    p,d=steady_path(P,allowed);t=np.diff(p,axis=0)
    assert not (np.sum(t[1:]*t[:-1],axis=1)<0).any()
    head=np.degrees(np.arctan2(t[:,1],t[:,0]));assert np.abs(head[20:-20]).max()<6      # sem zigue-zague
    assert abs(d[-1]-390)<3 and np.allclose(p[0],P[0]) and np.allclose(p[-1],P[-1],atol=.5)
    # Curva fechada que sairia da pista ao suavizar: mantém o traçado dentro do permitido.
    ring=Point(0,0).buffer(14).difference(Point(0,0).buffer(8))
    th=np.linspace(0,np.pi*1.5,300);C=np.column_stack([11*np.cos(th),11*np.sin(th)])
    from app.traffic import valid_centers
    pc,_=steady_path(C,ring);assert valid_centers(ring,pc).all()

def test_network_paths_have_no_backtracks(junction):
    from app.render import Scene
    for mode,expect in (('smooth',0),('anterior',None)):
        net=Scene.light(junction,S(vehicle_paths=mode)).network;assert net.paths
        bt=sum(int((np.sum(np.diff(p['p'],axis=0)[1:]*np.diff(p['p'],axis=0)[:-1],axis=1)<0).sum()) for p in net.paths)
        if expect is not None:assert bt==expect

def test_direction_from_axis(tmp_path):
    """Pista dupla sem setas: à direita do eixo (que cresce para leste) os veículos vão para leste."""
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500400,7800000)],dxfattribs={'layer':'EIXO'})
    for y0,y1 in ((7799988,7799997),(7800003,7800012)):
        h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,y0),(500400,y0),(500400,y1),(500000,y1)],is_closed=True)
    d.saveas(tmp_path/'input.dxf')
    from app.render import Scene
    net=Scene.light(tmp_path,S()).network;checked=0
    for e in net.edges:
        if e['disabled'] or e['length']<50:continue
        y=float(np.median(e['p'][:,1]));dx=e['p'][-1,0]-e['p'][0,0]
        if y<7800000-1:assert dx>0;checked+=1      # lado direito (sul): km crescente
        elif y>7800000+1:assert dx<0;checked+=1    # lado esquerdo (norte): km decrescente
    assert checked>=2

# ---------------- áreas de pista e acostamento ----------------
def pav(**kw):return {'name':'Área','kind':'existing_pavement','points':[{'x':500050,'y':7799992},{'x':500150,'y':7799992},{'x':500150,'y':7800008},{'x':500050,'y':7800008}],**kw}

def test_pavement_area_overrides_dxf(junction):
    from app.geometry import analyze
    items=analyze(junction,S(pavement_areas=[pav()]))[0]
    ex=unary_union([Polygon(e['points'],e.get('holes',[])) for e in items if e['role']=='existing_pavement'])
    new=unary_union([Polygon(e['points'],e.get('holes',[])) for e in items if e['role']=='pavement'])
    assert ex.area==pytest.approx(1600,rel=.02) and not new.buffer(-.05).intersects(box(500060,7799993,500140,7800007))
    base=unary_union([Polygon(e['points'],e.get('holes',[])) for e in analyze(junction,S())[0] if e['role']=='pavement'])
    assert unary_union([ex,new]).area==pytest.approx(base.area,rel=.01)          # a soma das superfícies não muda
    # Desligada: nada muda.
    off=analyze(junction,S(pavement_areas=[pav(enabled=False)]))[0];assert not [e for e in off if e['role']=='existing_pavement']

def test_shoulder_by_start_end_width(junction):
    from app.geometry import analyze
    sh={'name':'Acost.','start':{'x':500250,'y':7799991.2},'end':{'x':500350,'y':7799991.2},'width_m':2.5}
    items,_,_,_,rep=analyze(junction,S(shoulder_marks=[sh]))
    g=unary_union([Polygon(e['points'],e.get('holes',[])) for e in items if e['role']=='shoulder'])
    assert g.area==pytest.approx(250,rel=.05) and g.bounds[1]==pytest.approx(7799991,abs=.05) and g.bounds[3]==pytest.approx(7799993.5,abs=.1)
    bad=analyze(junction,S(shoulder_marks=[{**sh,'start':{'x':500250,'y':7799900}}]))[4]
    assert any('mesmo bordo' in w for w in bad['warnings'])

def test_export_roundtrip_areas(junction):
    from app.exporters import features,geojson,_read_geojson,apply_import
    from app.render import Scene
    sh={'name':'Acost.','start':{'x':500250,'y':7799991.2},'end':{'x':500350,'y':7799991.2},'width_m':2.5}
    cfg=S(pavement_areas=[pav()],shoulder_marks=[sh]);sc=Scene.light(junction,cfg)
    out,counts=apply_import({},_read_geojson(geojson(features(cfg,sc.stationing),cfg.crs),cfg.crs))
    s=Settings.model_validate({**cfg.model_dump(),**out})
    assert counts.get('pavement_areas')==1 and counts.get('shoulder_marks')==1 and s.pavement_areas[0].kind=='existing_pavement' and s.shoulder_marks[0].width_m==2.5

# ---------------- perfil técnico ----------------
def test_hatch_anchored_to_project_coordinates():
    from app.visual import surface_hatch
    a,_=surface_hatch((200,200),700000.,7800000.,.2,'pavement')
    b,_=surface_hatch((200,200),700000.+10*.2,7800000.-6*.2,.2,'pavement')   # raster deslocado 10 e 6 pixels
    assert np.allclose(a[6:,10:],b[:-6,:-10],atol=1e-3) and .05<a.mean()<.3
    e,_=surface_hatch((200,200),700000.,7800000.,.2,'existing_pavement');assert not np.allclose(a,e)

def test_tech_profile_frames(junction):
    from app.render import Scene
    base=dict(imagery='neutral',width=1280,duration_s=60,fps=24)
    std=Scene(junction,S(**base));tech=Scene(junction,S(**base,style_profile='tecnico',progress_indicator=True,camera_mode='continuo',flow_arrows='off',traffic=False,
        pois=[{'id':'p1','title':'Obra','x':500300,'y':7800000}]))
    # Hachura dourada só no perfil técnico.
    v=((500200,7800000),40)
    a=std.frame(0,view=v)[0];b=tech.frame(0,view=v)[0]
    gold=lambda im:float(np.mean((im[:,:,0]>150)&(im[:,:,1]>120)&(im[:,:,2]<120)&(im[:,:,0]-im[:,:,2]>50)))
    assert gold(b)>gold(a)+.01
    # Voo contínuo: sem paradas nas obras, revelação cresce sem voltar e chega a 100% no fim.
    ps=[tech.pose(t)[2] for t in np.linspace(0,60,121)];assert all(y>=x-1e-9 for x,y in zip(ps,ps[1:])) and ps[-1]==1
    assert all(tech.pose(t)[3] is None for t in np.linspace(0,60,61)) and np.allclose(tech.pose(59.9)[0],tech.smooth[-1])
    # Indicador de progresso no rodapé.
    f1=tech.frame(30)[0];tech.s.progress_indicator=False;f0=tech.frame(30)[0]
    H=f1.shape[0];assert np.abs(f1[H-60:].astype(int)-f0[H-60:].astype(int)).sum()>0 and (f1[:H-60]==f0[:H-60]).all()

def test_georef_check_dxf_vs_kmz():
    from app.geometry import georef_check
    ax=np.column_stack([np.linspace(0,1000,50),np.zeros(50)]);ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(ax,axis=0),axis=1))]
    r=georef_check(ax,ds,[np.array([[0,3.],[1000,3.]])]);assert r['points']==25 and r['median_m']==pytest.approx(3,abs=.01) and r['max_m']==pytest.approx(3,abs=.01)
    r=georef_check(ax,ds,[np.array([[0,3.],[500,3.]])]);assert r['points']>=24 and r['max_m']>400   # KMZ cobre só metade

def test_blank_tiles_detected():
    from app.imagery import is_blank
    rng=np.random.default_rng(1)
    assert is_blank(np.full((256,256,3),250,np.uint8)) and is_blank(np.zeros((256,256,3),np.uint8))
    ph=np.full((256,256,3),205,np.uint8);cv2.putText(ph,'Map data not yet available',(10,128),cv2.FONT_HERSHEY_SIMPLEX,.5,(120,120,120),1);assert is_blank(ph)
    real=np.clip(rng.normal(90,25,(256,256,3)),0,255).astype(np.uint8);real[:,:,1]+=20;assert not is_blank(real)
    assert not is_blank(np.full((256,256,3),(40,70,90),np.uint8))                 # água uniforme não é "vazio"

def test_validate_mp4(tmp_path):
    from app.encoding import validate_mp4
    from app.render import ffmpeg_exe
    ff=ffmpeg_exe();out=tmp_path/'v.mp4'
    subprocess.run([ff,'-y','-v','error','-f','lavfi','-i','testsrc=size=320x180:rate=24','-frames:v','48','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
    r=validate_mp4(ff,out,48,320,180,24);assert r['ok'],r;assert r['frames_decoded']==48 and r['codec']=='h264' and r['faststart']
    assert not validate_mp4(ff,out,50,320,180,24)['ok']
    out.write_bytes(out.read_bytes()[:len(out.read_bytes())//2]);assert not validate_mp4(ff,out,48,320,180,24)['ok']

def test_schema_v19():
    s=Settings.model_validate({'schema_version':18,'km_start_m':0,'km_end_m':100})
    assert s.schema_version>=19 and s.vehicle_paths=='smooth' and s.direction_reference=='axis' and s.style_profile=='padrao' and s.camera_mode=='obras' and not s.progress_indicator and s.pavement_areas==[]

# ---------------- editor ----------------
def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_pavement_tools_and_preset(junction):
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
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500200,y:7800000});view.s=Math.min(60,canvas.width*mpp()/420);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Desenhar área de pista existente.
            page.click('#toolbar button[data-tool="pavarea"]');page.select_option('#pavKind','existing_pavement')
            for x,y in [(500050,7799993),(500150,7799993),(500150,7800007),(500050,7800007)]:page.mouse.click(*W2C(x,y))
            page.keyboard.press('Enter');assert ev('M.pavement_areas.length')==1 and ev('M.pavement_areas[0].kind')=='existing_pavement'
            page.keyboard.press('Enter');assert ev('tool')=='pan'   # 1.34: Enter conclui e a ferramenta continua; Enter sem pontos encerra
            # Selecionar a área fechada do ramo (pavimento do DXF) como pista nova.
            page.click('#toolbar button[data-tool="pavpick"]');page.select_option('#pavKind','pavement');page.mouse.click(*W2C(500200,7800060))
            assert ev('M.pavement_areas.length')==2 and ev('M.pavement_areas[1].source')=='picked' and ev('M.pavement_areas[1].points.length')>=4
            # Acostamento por início e fim.
            page.click('#toolbar button[data-tool="shoulder"]');page.fill('#shWidth','3');page.mouse.click(*W2C(500250,7799991.5));page.mouse.click(*W2C(500350,7799991.5))
            assert ev('M.shoulder_marks.length')==1 and ev('M.shoulder_marks[0].width_m')==3
            ev('undo()');assert ev('M.shoulder_marks.length')==0;ev('redo()');assert ev('M.shoulder_marks.length')==1
            # Perfil "Apresentação técnica".
            ev("document.getElementById('presetTech').click()");page.wait_for_timeout(800)
            conf=c.get(f'/api/projects/{pid}').json()['config']
            assert conf['fps']==24 and conf['duration_s']==96 and conf['style_profile']=='tecnico' and conf['camera_mode']=='continuo' and conf['flow_arrows']=='off' and conf['traffic'] is False and conf['progress_indicator']
            assert len(conf['pavement_areas'])==2 and len(conf['shoulder_marks'])==1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
