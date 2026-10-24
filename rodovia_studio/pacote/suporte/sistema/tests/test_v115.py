"""1.15: sinalização completa (faixas pela largura, setas por faixa, retenção/PARE, zebrados, faixas de
pedestre, placas, leitura do projeto de sinalização do DXF) e modo básico igual à 1.14."""
import os,json,socket,threading,time
import numpy as np,ezdxf,pytest,cv2
from shapely.geometry import Polygon,Point
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,'lanes_per_direction':0,'lane_arrow_repeat':'all','arrow_min_gap_m':0,**kw})  # 1.18: faixas pela largura e setas como na 1.15
def scene(d,**kw):
    from app.render import Scene
    return Scene(d,S(**kw))

def offsets(net,src):
    ys=sorted({round(float((a[1]+b[1])/2),1) for (a,b,c),s_ in zip(net.markings,net.mark_src) if s_==src and abs(a[1]-b[1])<.05})
    return ys

def test_lane_lines_follow_road_width_and_zones(junction):
    sc=scene(junction);net=sc.network;rep=sc.report['traffic_network']['signage']
    assert rep['full'] and rep['markings']>0
    k=next(k for k,L in net.lane_info.items() if L is not None and net.raw_info[k]['kind']=='main')
    L=net.lane_info[k];assert np.median(L['lanes'][L['lanes']>0])==5  # 17,76 m / 3,5 m
    ys=offsets(net,k);assert len(ys)==4 and np.allclose(np.diff(ys),np.diff(ys)[0],atol=.2)
    # Trecho com número de faixas informado: 2 faixas -> uma divisória.
    zone={'name':'Z','lanes':2,'points':[{'x':499990,'y':7799980},{'x':500100,'y':7799980},{'x':500100,'y':7800020},{'x':499990,'y':7800020}]}
    net2=scene(junction,lane_zones=[zone]).network
    k2=next(k for k,L in net2.lane_info.items() if L is not None and net2.raw_info[k]['kind']=='main' and L['q'][:,0].min()<500050)
    assert set(net2.lane_info[k2]['lanes'][(net2.lane_info[k2]['q'][:,0]>500010)&(net2.lane_info[k2]['q'][:,0]<500090)])=={2}
    # Larguras de faixa diferentes mudam o número de faixas.
    net3=scene(junction,lane_width_m=4.5).network;k3=next(k for k,L in net3.lane_info.items() if L is not None and net3.raw_info[k]['kind']=='main')
    assert np.median(net3.lane_info[k3]['lanes'][net3.lane_info[k3]['lanes']>0])==4

def test_stop_line_pare_and_sign_at_t_junction(junction):
    net=scene(junction).network
    pare=[g for g in net.signs if g['code']=='R-1'];assert len(pare)==1
    # Placa do lado de fora do pavimento, à direita de quem chega pelo ramo em T (desce no sentido -y).
    p=pare[0]['point'];assert not net.paved.contains(Point(*p)) and p[0]<500200
    # Linha de retenção no ramo, junto ao bordo da via principal (y ~ 7800009) e dentro do pavimento.
    bars=[r for r,c in net.fills if len(r)==1 and Polygon(r[0]).area>.5]
    near=[Polygon(r[0]) for r in bars if 7800008<Polygon(r[0]).centroid.y<7800014 and 500190<Polygon(r[0]).centroid.x<500210]
    assert near and all(net.paved.buffer(.01).covers(g) for g in near)
    legend=[r for r,c in net.fills if len(r)>=4];assert legend  # PARE (várias letras/anéis)
    assert all(net.paved.covers(Polygon(x).buffer(-.02)) for r in legend for x in r if Polygon(x).area>.05)
    rep=scene(junction,stop_lines=False).network;assert not [g for g in rep.signs if g['code']=='R-1']

def test_lane_arrows_by_itinerary_and_multilane(junction):
    net=scene(junction).network
    assert len(net.arrow_kinds)==len(net.arrows)==len(net.arrow_anchors)
    assert 'SL' in net.arrow_kinds  # antes do ramo em T à esquerda
    # Na principal, setas lado a lado (uma por faixa) com a mesma âncora na trajetória.
    xs=[round(float(p[0])) for p,_ in net.arrows];common=max(set(xs),key=xs.count);assert xs.count(common)>=4
    basic=scene(junction,signage_detail='basic').network
    assert basic.fills==[] and basic.signs==[] and basic.arrow_kinds==[] and not basic.full
    off=scene(junction,lane_arrows=False).network;assert set(off.arrow_kinds)=={'S'}

def test_crosswalk_hatch_signs_and_clean_areas(junction):
    cw={'name':'FP','a':{'x':500300,'y':7799991},'b':{'x':500300,'y':7800009},'width_m':4}
    ha={'name':'Z','points':[{'x':500330,'y':7799995},{'x':500360,'y':7799995},{'x':500360,'y':7800005},{'x':500330,'y':7800005}],'color':'yellow'}
    sg={'point':{'x':500250,'y':7799988},'code':'R-19','text':'60'}
    net=scene(junction,crosswalks=[cw],hatch_areas=[ha],signs=[sg]).network
    bars=[Polygon(r[0]) for r,c in net.fills if abs(Polygon(r[0]).centroid.x-500300)<2.1 and abs(Polygon(r[0]).area-1.6)<.1]
    assert len(bars)>=15
    yellow=[1 for r,c in net.fills if tuple(c)==(244,200,70)];assert len(yellow)>=5
    assert any(g['code']=='R-19' and g['text']=='60' for g in net.signs)
    # Área sem sinalização remove pintura e placas automáticas, mas não as placas manuais.
    area=[{'x':500150,'y':7799985},{'x':500260,'y':7799985},{'x':500260,'y':7800130},{'x':500150,'y':7800130}]
    net2=scene(junction,crosswalks=[cw],signs=[sg],clean_areas=[area]).network
    g=Polygon([(p['x'],p['y']) for p in area])
    assert not [1 for r,c in net2.fills if g.contains(Point(*np.vstack(r).mean(0)))]
    assert not [x for x in net2.signs if x.get('auto') and g.contains(Point(*x['point']))]
    assert any(x['code']=='R-19' for x in net2.signs)

def test_frame_draws_paint_and_signs(junction):
    from app.render import Scene
    sc=Scene(junction,S(signs=[{'point':{'x':500250,'y':7799988},'code':'R-1'}]));v=((500200,7800000),120)
    im=sc.frame(10,view=v)[0];b=Scene(junction,S(signage_detail='basic')).frame(10,view=v)[0]
    red=lambda a:int(((a[:,:,0]>170)&(a[:,:,1]<70)&(a[:,:,2]<70)).sum())
    assert red(im)>30 and red(b)==0
    white=lambda a:int((a.min(2)>225).sum());assert white(im)>white(b)
    # Noite: pinturas e placas continuam visíveis.
    n=Scene(junction,S(day_night='night',signs=[{'point':{'x':500250,'y':7799988},'code':'R-1'}])).frame(10,view=v)[0]
    assert red(n)>30

def test_dxf_signage_layers_replace_generated(tmp_path,junction):
    d=ezdxf.readfile(junction/'input.dxf');m=d.modelspace()
    d.layers.new('SINALIZACAO_HORIZONTAL');d.layers.new('PLACAS')
    m.add_lwpolyline([(500300,7799999),(500304,7799999),(500304,7800001),(500300,7800001)],close=True,dxfattribs={'layer':'SINALIZACAO_HORIZONTAL'})
    m.add_lwpolyline([(500250,7800000),(500280,7800000)],dxfattribs={'layer':'SINALIZACAO_HORIZONTAL'})
    m.add_text('PARE',dxfattribs={'layer':'SINALIZACAO_HORIZONTAL'}).set_placement((500290,7800000))
    blk=d.blocks.new('PLACA_R-1');blk.add_circle((0,0),.5)
    m.add_blockref('PLACA_R-1',(500260,7799988),dxfattribs={'layer':'PLACAS'})
    blk2=d.blocks.new('VEL');blk2.add_circle((0,0),.5);blk2.add_attdef('V',(0,0))
    r=m.add_blockref('VEL',(500270,7799988),dxfattribs={'layer':'PLACAS'});r.add_attrib('V','80',(0,0))
    m.add_text('Nova Era',dxfattribs={'layer':'PLACAS'}).set_placement((500280,7799988))
    d.saveas(junction/'input.dxf')
    from app.geometry import guess
    assert guess('SINALIZACAO_HORIZONTAL')=='sign_h' and guess('PLACAS')=='sign_v'
    net=scene(junction).network
    codes=sorted((g['code'],g['text']) for g in net.signs if g.get('source')=='DXF')
    assert codes==[('I','Nova Era'),('R-1',''),('R-19','80')]
    assert [r for r,c in net.fills if abs(np.vstack(r)[:,0].mean()-500302)<.5]  # polígono preenchido do DXF
    assert all(s_ in (-4,) for s_ in net.mark_src) and net.arrows==[]  # substitui a gerada
    rep=scene(junction).report;assert any('texto' in w for w in rep['warnings'])
    add=scene(junction,dxf_signage='add').network;assert add.arrows and any(s_==-4 for s_ in add.mark_src)

def test_schema_v14_and_export_roundtrip(junction):
    s=Settings.model_validate({'schema_version':13,'km_start_m':0,'km_end_m':100})
    assert s.schema_version>=14 and s.signage_detail=='full' and s.lane_width_m==3.5 and s.signs==[]
    from app.exporters import features,geojson,_read_geojson,apply_import
    from app.chainage import Stationing
    from app.render import Scene
    cfg=S(crosswalks=[{'name':'FP','a':{'x':500300,'y':7799991},'b':{'x':500300,'y':7800009}}],
          hatch_areas=[{'name':'Z','points':[{'x':500330,'y':7799995},{'x':500360,'y':7799995},{'x':500360,'y':7800005}]}],
          signs=[{'point':{'x':500250,'y':7799988},'code':'OBRAS','text':'OBRAS'}],
          lane_zones=[{'name':'F','lanes':3,'points':[{'x':500000,'y':7799990},{'x':500050,'y':7799990},{'x':500050,'y':7800010}]}])
    sc=Scene.light(junction,cfg)
    feats=features(cfg,sc.stationing)
    back=_read_geojson(geojson(feats,cfg.crs),cfg.crs)
    out,counts=apply_import({},back)
    assert counts.get('crosswalks')==1 and counts.get('hatch_areas')==1 and counts.get('signs')==1 and counts.get('lane_zones')==1
    again=Settings.model_validate({**cfg.model_dump(),**out});assert again.signs[0].code=='OBRAS' and again.lane_zones[0].lanes==3

def test_gore_between_diverging_branches(tmp_path):
    """Bifurcação com pavimento entre os ramos até o nariz: o gore recebe zebrado; sem trajetória num dos ramos, nada."""
    from shapely.geometry import LineString as LS,Polygon as PG
    from shapely.ops import unary_union
    d=ezdxf.new();m=d.modelspace();X,Y=500000,7800000
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(X,Y),(X+200,Y),(X+400,Y-50)],dxfattribs={'layer':'EIXO'})
    g=unary_union([LS([(X,Y),(X+200,Y)]).buffer(4,cap_style=2),LS([(X+190,Y),(X+400,Y+50)]).buffer(4,cap_style=2),LS([(X+190,Y),(X+400,Y-50)]).buffer(4,cap_style=2),
                   PG([(X+195,Y),(X+300,Y+24),(X+300,Y-24)]).difference(PG([(X+262,Y),(X+320,Y+30),(X+320,Y-30)]))]).simplify(.05)
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path(list(g.exterior.coords)[:-1],is_closed=True)
    d.saveas(tmp_path/'input.dxf')
    from app import signage
    assert len(signage.noses(scene(tmp_path).network))==1
    # Um dos ramos sem trajetória de veículos: não há gore (evita zebrar pista sem fluxo modelado).
    assert scene(tmp_path).network.report_signage['paint']==0
    ramo=[{'name':'ramo','points':[{'x':X+150,'y':Y+1.5},{'x':X+205,'y':Y+3},{'x':X+400,'y':Y+50}],'kind':'device','direction':'growing'}]
    net=scene(tmp_path,traffic_paths=ramo).network
    hatched=[PG(r[0]) for r,c in net.fills if len(r)==1]
    assert len(hatched)>=5 and all(net.paved.buffer(.05).covers(x) for x in hatched)
    c=unary_union(hatched).centroid;assert X+200<c.x<X+262 and Y-5<c.y<Y+20
    # Nenhuma pintura de faixa dentro do zebrado.
    zone=unary_union(hatched).convex_hull.buffer(-1)
    assert not [1 for (a,b,col),s_ in zip(net.markings,net.mark_src) if s_>=0 and zone.contains(Point(*(a+b)/2))]
    assert scene(tmp_path,traffic_paths=ramo,gore_hatch=False).network.report_signage['paint']==0

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_signage_tools(junction):
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
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && editor && ready()',timeout=20000)
            ev=page.evaluate
            assert ev('editor.signage_detail')=='full' and ev('editor.paint.length')>0 and ev('editor.signs.some(g=>g.code==="R-1")')
            ev("(()=>{const [ix,iy]=worldToImg({x:500250,y:7800000});view.s=Math.min(60,canvas.width*mpp()/160);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            page.click('#toolbar button[data-tool="sign"]');page.select_option('#signCode','R-19');page.fill('#signText','60');page.mouse.click(*W2C(500250,7799988))
            assert ev('M.signs.length')==1 and ev('M.signs[0].code')=='R-19' and ev('M.signs[0].text')=='60'
            page.click('#toolbar button[data-tool="crosswalk"]');page.mouse.click(*W2C(500230,7799991));page.mouse.click(*W2C(500230,7800009))
            assert ev('M.crosswalks.length')==1
            page.click('#toolbar button[data-tool="hatch"]')
            for x,y in [(500260,7799996),(500280,7799996),(500280,7800004)]:page.mouse.click(*W2C(x,y))
            page.keyboard.press('Enter');assert ev('M.hatch_areas.length')==1
            page.click('#toolbar button[data-tool="lanes"]');page.fill('#laneCount','3')
            for x,y in [(500180,7799986),(500215,7799986),(500215,7800014)]:page.mouse.click(*W2C(x,y))
            page.keyboard.press('Enter');assert ev('M.lane_zones.length')==1 and ev('M.lane_zones[0].lanes')==3
            ev('undo()');assert ev('M.lane_zones.length')==0;ev('redo()');assert ev('M.lane_zones.length')==1
            # Editar na lista: troca o tipo da placa.
            page.select_option('select[data-f="sg.0.code"]','A');page.wait_for_timeout(100);assert ev('M.signs[0].code')=='A'
            ev('save()');page.wait_for_timeout(500)
            conf=c.get(f'/api/projects/{pid}').json()['config']
            assert len(conf['signs'])==1 and len(conf['crosswalks'])==1 and len(conf['hatch_areas'])==1 and conf['lane_zones'][0]['lanes']==3
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
