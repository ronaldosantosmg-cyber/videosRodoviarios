"""Fase A: editor, estaqueamento, offset, sentidos, fluxos, OAE, cruzamentos e chamadas."""
import json,math
import numpy as np
import pytest
from shapely.geometry import LineString,box
from test_workflow import drawing,settings,wait
from app.models import Settings,TrafficPath,Point,FlowOverride,DirectionMark,NoConnectionZone,OAEMark,POI
from app.migration import migrate,repair_text,SCHEMA_VERSION
from app.chainage import Stationing,fmt
from app.alignment import fit,apply,inverse
from app.traffic import TrafficNetwork,valid_centers
from app.markup import validate_path,oae_items,zones_geometry

OLD_V1={'name':'TH57','km_start_m':325850.0,'km_end_m':335000.0,'pois':[
    {'id':'fauna','title':'OAE â€¢ Passagem de fauna','subtitle':'Segunda OAE â€¢ sentido crescente','kind':'fauna','x':1.,'y':2.,'km_m':None},
    {'id':'d','title':'InterseÃ§Ã£o em desnÃ­vel â€” Diamante','kind':'intersecao','x':3.,'y':4.,'km_m':326900.}],
    'exclusions':[[{'x':0,'y':0},{'x':1,'y':0},{'x':1,'y':1}]]}

def test_migration_from_v1_repairs_text_and_keeps_manual_km():
    s=Settings.model_validate(OLD_V1)
    assert s.schema_version==SCHEMA_VERSION
    assert s.pois[0].title=='OAE • Passagem de fauna' and s.pois[0].subtitle=='Segunda OAE • sentido crescente'
    assert s.pois[1].title=='Interseção em desnível — Diamante'
    assert s.pois[0].km_mode=='auto' and s.pois[1].km_mode=='manual' and s.pois[1].km_m==326900.
    assert repair_text('Correção')=='Correção'  # texto correto não muda
    with pytest.raises(ValueError):Settings.model_validate({'schema_version':SCHEMA_VERSION+1})

def test_markings_persist_in_crs_through_api(drawing):
    from fastapi.testclient import TestClient
    from app.server import app
    marks=dict(chainage={'start':{'x':500050.,'y':7800000.}},
        direction_marks=[{'id':'d1','start':{'x':500100,'y':7799995},'end':{'x':500140,'y':7799995}}],
        flow_overrides=[{'id':'f1','x':500150,'y':7800005,'action':'reverse'}],
        oae_marks=[{'id':'o1','name':'Ponte','start':{'x':500100,'y':7800000},'end':{'x':500160,'y':7800000},'level_m':7}],
        no_connection_zones=[{'id':'z1','kind':'point','point':{'x':500200,'y':7800010},'radius_m':12}],
        dxf_alignment={'mode':'translation','pairs':[{'id':'p','dxf':{'x':0,'y':0},'image':{'x':1.5,'y':-2}}],'applied':False},
        pois=[{'id':'a','title':'Obra','x':500150,'y':7800000,'anchor':{'x':500155,'y':7800020}}])
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings(**marks).model_dump()).json()['id']
        got=c.get(f'/api/projects/{pid}').json()['config']
        for k in marks:
            assert got[k]==Settings(**{**settings().model_dump(),**marks}).model_dump()[k],k
        assert got['pois'][0]['anchor']=={'x':500155.,'y':7800020.}
        # Exclusão da âncora: volta ao automático.
        got['pois'][0]['anchor']=None;assert c.put(f'/api/projects/{pid}/config',json=got).status_code==200
        assert c.get(f'/api/projects/{pid}').json()['config']['pois'][0]['anchor'] is None
        assert c.get('/app.js').status_code==200

def test_km_by_distance_along_curved_axis():
    # Quarto de círculo r=100 seguido de reta de 50 m.
    a=np.linspace(0,math.pi/2,400);arc=np.column_stack([100*np.cos(a),100*np.sin(a)]);axis=np.vstack([arc,[[-50.,100.]]])
    L=LineString(axis).length
    st=Stationing(axis,1000.,Point(x=100,y=0))
    assert st.km([100,0])==pytest.approx(1000)
    q=[100*math.cos(math.pi/4),100*math.sin(math.pi/4)]
    assert st.km(q)==pytest.approx(1000+L*0+LineString(arc).length/2,abs=.05)  # metade do arco, não a corda
    assert st.km([-50,100])==pytest.approx(1000+L,abs=.01)
    # Início no meio do arco: pontos anteriores recebem km menor.
    st2=Stationing(axis,1000.,Point(x=q[0],y=q[1]))
    assert st2.km([100,0])==pytest.approx(1000-LineString(arc).length/2,abs=.05)
    assert np.allclose(st2.point(1000),q,atol=1e-6)
    assert fmt(326900.4)=='326+900' and fmt(-12)=='-0+012'

def test_km_with_inverted_axis(tmp_path):
    import ezdxf
    from app.geometry import analyze
    d=ezdxf.new();d.layers.new('EIXO');m=d.modelspace();m.add_lwpolyline([(0,0),(300,0),(300,200)],dxfattribs={'layer':'EIXO'});d.saveas(tmp_path/'input.dxf')
    _,axis,_,_,_=analyze(tmp_path,settings(reverse_axis=True))
    assert np.allclose(axis[0],[300,200])
    st=Stationing(axis,5000.,Point(x=300,y=150))
    assert st.km([300,200])==pytest.approx(4950)
    assert st.km([100,0])==pytest.approx(5000+350)
    assert st.km([300,100])>st.km([300,150])

def two_carriageways(**kw):
    axis=np.array([[0.,0.],[200.,0.]]);ds=np.array([0.,200.])
    bottom=np.array([[0.,-5.],[200.,-5.]]);top=np.array([[200.,5.],[0.,5.]])
    roads=[box(0,-9,200,-1),box(0,1,200,9)];s=Settings(derive_traffic_paths=False,hydrography=False,**kw)
    return TrafficNetwork(roads,[box(0,-1,200,1)],[{'points':bottom},{'points':top}],axis,ds,s)

def lane_dirs(n):
    return {('bottom' if e['p'][:,1].mean()<0 else 'top'):int(np.sign(e['p'][-1,0]-e['p'][0,0])) for e in n.edges}

def test_flow_reverse_and_disable_are_reversible():
    base=lane_dirs(two_carriageways());assert base=={'bottom':1,'top':-1}
    rev=two_carriageways(flow_overrides=[FlowOverride(x=100,y=-5,action='reverse')])
    assert lane_dirs(rev)=={'bottom':-1,'top':-1}  # só a pista clicada muda
    off=two_carriageways(flow_overrides=[FlowOverride(x=100,y=5,action='disable')])
    top=[e for e in off.edges if e['p'][:,1].mean()>0]
    assert top and all(e['disabled'] for e in top)  # geometria preservada
    assert all(not any(off.edges[i]['disabled'] for i in p['edges']) for p in off.paths)
    assert any('desativados' in w for w in off.warnings)
    again=two_carriageways(flow_overrides=[FlowOverride(x=100,y=5,action='disable',enabled=False)])
    assert not any(e['disabled'] for e in again.edges)

def test_direction_arrow_overrides_automatic_direction():
    n=two_carriageways(direction_marks=[DirectionMark(start=Point(x=120,y=-5),end=Point(x=80,y=-5))])
    assert lane_dirs(n)['bottom']==-1 and lane_dirs(n)['top']==-1

def test_include_flow_validation_and_rejection_reasons():
    roads=box(0,-9,200,9);obstacles=box(0,-1,200,1);ex=box(150,1,170,9)
    allowed=roads.difference(obstacles.buffer(.15)).buffer(-.12).difference(ex)
    ok=validate_path([Point(x=10,y=5),Point(x=120,y=5)],roads,obstacles,ex,allowed);assert ok['ok'],ok
    out=validate_path([Point(x=10,y=5),Point(x=10,y=30)],roads,obstacles,ex,allowed)
    assert not out['ok'] and 'Fora do pavimento' in out['reason'] and out['at'][1]>9
    med=validate_path([Point(x=10,y=5),Point(x=10,y=-5)],roads,obstacles,ex,allowed)
    assert not med['ok'] and 'canteiro' in med['reason']
    exc=validate_path([Point(x=140,y=5),Point(x=180,y=5)],roads,obstacles,ex,allowed)
    assert not exc['ok'] and 'exclusão' in exc['reason']
    edge=validate_path([Point(x=10,y=8.6),Point(x=100,y=8.6)],roads,obstacles,ex,allowed)
    assert not edge['ok'] and 'não cabe' in edge['reason']
    # Fluxo incluído e desativado: entra ou sai do grafo sem apagar dados.
    path=TrafficPath(name='Novo',kind='device',direction='growing',points=[Point(x=5,y=5),Point(x=150,y=5)])
    def net(p):
        s=Settings(derive_traffic_paths=False,hydrography=False,traffic_paths=[p]);a=np.array([[0.,0.],[200.,0.]])
        return TrafficNetwork([roads],[obstacles],[],a,np.array([0.,200.]),s)
    assert any(e['source']=='Novo' for e in net(path).edges)
    assert not any(e['source']=='Novo' for e in net(path.model_copy(update={'enabled':False})).edges)

def test_no_connection_zone_blocks_turns_keeps_straight():
    axis=np.array([[-60.,0.],[60.,0.]])
    def build(zones):
        s=Settings(derive_traffic_paths=False,hydrography=False,no_connection_zones=zones,traffic_paths=[
            TrafficPath(name='EW',kind='main',direction='growing',points=[Point(x=-55,y=0),Point(x=55,y=0)]),
            TrafficPath(name='NS',kind='device',direction='growing',points=[Point(x=0,y=-55),Point(x=0,y=55)]),
            TrafficPath(name='Ramo',kind='device',direction='growing',points=[Point(x=0,y=0),Point(x=40,y=40)])])
        return TrafficNetwork([box(-58,-6,58,6),box(-6,-58,6,58),LineString([(0,0),(42,42)]).buffer(6)],[],[],axis,np.array([0.,120.]),s)
    free=build([]);blocked=build([NoConnectionZone(kind='point',point=Point(x=0,y=0),radius_m=15)])
    def turns(n):return [(n.edges[a]['source'],n.edges[b]['source']) for a,bs in n.connections.items() for b in bs if n.edges[a]['source']!=n.edges[b]['source']]
    assert turns(free),'sem zona deveria haver troca de via no cruzamento em nível'
    assert not turns(blocked)
    # Na zona, a via segue: nenhum veículo troca de pista nem de mão.
    for p in blocked.paths:
        assert len({blocked.edges[e]['source'] for e in p['edges']})==1
    assert zones_geometry([NoConnectionZone(kind='area',points=[Point(x=0,y=0),Point(x=1,y=0),Point(x=1,y=1)])]).area==pytest.approx(.5)

def test_oae_by_two_points_on_axis():
    axis=np.array([[0.,0.],[1000.,0.]])
    s=Settings(km_start_m=10000,km_end_m=11000,chainage={'start':{'x':100,'y':0}},
        oae_marks=[OAEMark(name='Viaduto',start=Point(x=400,y=3),end=Point(x=300,y=-2),level_m=8,width_m=12)])
    st=Stationing(axis,s.km_start_m,s.chainage.start);o=oae_items(s,st)[0]
    assert o['km_start_m']==pytest.approx(10200) and o['km_end_m']==pytest.approx(10300)
    assert o['deck'].area==pytest.approx(100*12,rel=1e-6) and o['level_m']==8
    s2=s.model_copy(update={'oae_marks':[s.oae_marks[0].model_copy(update={'km_start_override_m':10195.})]})
    assert oae_items(s2,st)[0]['km_start_m']==10195 and oae_items(s2,st)[0]['km_auto'][0]==pytest.approx(10200)

def test_oae_mark_blocks_xy_turns_and_is_drawn(drawing):
    from app.render import Scene
    cfg=settings(oae_marks=[OAEMark(name='OAE teste',start=Point(x=500100,y=7800000),end=Point(x=500160,y=7800000),level_m=6,width_m=14)])
    sc=Scene(drawing,cfg);assert sc.oae and sc.network.bridges.covers(LineString([(500110,7800000),(500150,7800000)]))
    a,_=sc.frame(0,view=((500130,7800000),120));b,_=Scene(drawing,settings()).frame(0,view=((500130,7800000),120))
    assert np.abs(a.astype(int)-b.astype(int)).sum()>0
    assert any(p.get('source')=='oae_mark' and 'km' in p['subtitle'] for p in sc.pois)

def test_callout_anchor_saved_drawn_and_removed(drawing):
    from app.render import Scene
    poi={'id':'c1','title':'Obra A','kind':'outro','x':500150,'y':7800000}
    def long(**kw):return Settings(**{**settings().model_dump(),'duration_s':60,**kw})
    with_anchor=long(pois=[{**poi,'anchor':{'x':500170,'y':7800020}}])
    assert with_anchor.pois[0].anchor==Point(x=500170,y=7800020)
    def shot(cfg):
        sc=Scene(drawing,cfg);t=next(t for t in np.arange(0,60,.5) if sc.pose(t)[4].startswith('detalhe'))
        for k in np.arange(0,t+.01,.5):im,_=sc.frame(k)
        return im
    a=shot(with_anchor);b=shot(long(pois=[poi]));c=shot(long(pois=[{**poi,'anchor':None}]))
    assert np.abs(a.astype(int)-b.astype(int)).sum()>0
    assert np.array_equal(b,c)

def test_offset_transform_known_residuals():
    pairs=[{'dxf':{'x':0,'y':0},'image':{'x':2,'y':-1}},{'dxf':{'x':100,'y':0},'image':{'x':102,'y':-1}},{'dxf':{'x':0,'y':100},'image':{'x':2,'y':99.4}}]
    r=fit(pairs,'translation')
    # Média de (2,-1),(2,-1),(2,-0.6): dy=-0.8667; resíduos conhecidos.
    assert r['tx']==pytest.approx(2) and r['ty']==pytest.approx(-0.8666667)
    assert r['residuals_m']==pytest.approx([0.1333333,0.1333333,0.2666667],abs=1e-6)
    # Similaridade exata: rotação 30°, escala 1.002, translação (500,-300).
    th=math.radians(30);k=1.002;src=np.array([[0,0],[1000,0],[0,800],[640,330]],float)
    dst=apply(src,{'a':k*math.cos(th),'b':k*math.sin(th),'tx':500,'ty':-300})
    sim=fit([{'dxf':{'x':a[0],'y':a[1]},'image':{'x':b[0],'y':b[1]}} for a,b in zip(src,dst)],'similarity')
    assert sim['rotation_deg']==pytest.approx(30) and sim['scale']==pytest.approx(1.002) and max(sim['residuals_m'])<1e-6
    assert np.allclose(apply(apply(src,sim),inverse(sim)),src)
    # Par desativado não entra no ajuste, mas recebe resíduo para conferência.
    off=fit(pairs[:2]+[{**pairs[2],'enabled':False}],'translation');assert off['ty']==pytest.approx(-1) and off['residuals_m'][2]==pytest.approx(.4)
    with pytest.raises(ValueError):fit(pairs[:1],'similarity')

def test_alignment_applied_in_memory_only(drawing):
    from app.geometry import analyze
    raw=(drawing/'input.dxf').read_bytes()
    cfg=settings(dxf_alignment={'mode':'translation','pairs':[{'dxf':{'x':0,'y':0},'image':{'x':3,'y':-4}}],'applied':True})
    _,axis0,*_=analyze(drawing,settings());_,axis1,_,_,rep=analyze(drawing,cfg)
    assert np.allclose(axis1-axis0,[3,-4]) and rep['alignment']['tx']==3
    assert (drawing/'input.dxf').read_bytes()==raw

def test_editor_endpoints_after_preview(drawing):
    from fastapi.testclient import TestClient
    from app.server import app
    with TestClient(app) as c:
        cfg=settings(chainage={'start':{'x':500100,'y':7800000}}).model_dump();pid=c.post('/api/projects',json=cfg).json()['id']
        assert c.post(f'/api/projects/{pid}/validate_path',json={'points':[]}).status_code==409
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
        j=wait(c,c.post(f'/api/projects/{pid}/preview').json()['id']);assert j['state']=='done',j
        ed=c.get(f'/api/projects/{pid}/editor.json').json()
        assert ed['stationing']['defined'] and ed['stationing']['s0_m']==pytest.approx(100,abs=.01) and ed['segments']
        bad=c.post(f'/api/projects/{pid}/validate_path',json={'points':[{'x':500050,'y':7800005},{'x':500050,'y':7800040}]}).json()
        assert not bad['ok'] and 'pavimento' in bad['reason']
        good=c.post(f'/api/projects/{pid}/validate_path',json={'points':[{'x':500020,'y':7800005},{'x':500200,'y':7800005}]}).json()
        assert good['ok'],good
        cfg2=c.get(f'/api/projects/{pid}').json()['config'];cfg2.update(preview_mode='custom',preview_center={'x':500150,'y':7800000},preview_width_m=90)
        c.put(f'/api/projects/{pid}/config',json=cfg2);j=wait(c,c.post(f'/api/projects/{pid}/preview').json()['id']);assert j['state']=='done',j
        assert c.get(f'/api/projects/{pid}').json()['preview']['width_m']==90
        fitted=c.post('/api/alignment/fit',json={'mode':'translation','pairs':[{'dxf':{'x':0,'y':0},'image':{'x':1,'y':1}}]}).json();assert fitted['tx']==1

def test_reference_export_is_binary_copy(tmp_path,monkeypatch):
    """Exportar referência continua cópia binária (SHA-256 igual), agora com troca atômica tolerante a bloqueio."""
    import hashlib,json
    from fastapi.testclient import TestClient
    import app.worker as w
    from app.server import app
    assets=tmp_path/'assets';(assets/'th57').mkdir(parents=True)
    blob=bytes(range(256))*4099;(assets/'th57/referencia.mp4').write_bytes(blob)
    monkeypatch.setattr(w,'ASSETS',assets)
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        # O despachante roda o worker em outro processo: executa direto para usar o ASSETS de teste.
        from app import store
        jid='f'*32
        with store.connect() as con:con.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'reference','running',''))
        assert w.run(jid)==0
        got=(store.ROOT/pid/'video.mp4').read_bytes()
        assert hashlib.sha256(got).hexdigest()==hashlib.sha256(blob).hexdigest()
        assert json.loads((store.ROOT/pid/'video.json').read_text(encoding='utf-8'))['mode']=='reference'
