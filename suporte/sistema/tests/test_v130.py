"""1.30: abrir/renomear projeto, modelos (templates), rotas de veículos com trechos de pista simples, dupla por
sentido ou sentido único (faixas geradas e usadas pela rede de tráfego)."""
import json,time
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings,RouteAlignment

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})
Y=7800000
def route(**kw):return {'id':'r1','name':'Rota A','points':[{'x':500020,'y':Y},{'x':500380,'y':Y}],**kw}

def test_route_lane_geometry():
    from app.routes import build_lanes
    def lanes(**kw):
        L=build_lanes(RouteAlignment(**route(**kw)));return {(l['dir'],l['lane']):l for l in L}
    def y_at(l,x):
        P=l['points'];o=np.argsort(P[:,0]);return float(np.interp(x,P[o,0],P[o,1]))-Y
    # Pista simples: sentido do desenho (leste) à direita (sul, y menor), o oposto à esquerda e invertido.
    L=lanes(type='simples');assert set(L)=={('f',0),('r',0)}
    assert abs(y_at(L[('f',0)],500200)+1.75)<1e-6 and abs(y_at(L[('r',0)],500200)-1.75)<1e-6
    assert L[('f',0)]['points'][0,0]<L[('f',0)]['points'][-1,0] and L[('r',0)]['points'][0,0]>L[('r',0)]['points'][-1,0]
    # Sentido único com 2 faixas: as duas no sentido do desenho, centradas.
    U=lanes(type='unico',lanes=2);assert set(U)=={('f',0),('f',1)} and sorted(round(y_at(l,500200),3) for l in U.values())==[-1.75,1.75]
    # Trecho de pista dupla (2 faixas por sentido, canteiro 4 m) no meio de uma pista simples.
    D=lanes(type='simples',sections=[{'start_m':130,'end_m':230,'type':'dupla','lanes':2,'median_m':4}])
    assert set(D)=={('f',0),('f',1),('r',0),('r',1)}
    assert abs(y_at(D[('f',0)],500200)+3.75)<1e-6 and abs(y_at(D[('f',1)],500200)+7.25)<1e-6 and abs(y_at(D[('r',1)],500200)-7.25)<1e-6
    assert abs(y_at(D[('f',0)],500080)+1.75)<1e-6 and abs(y_at(D[('f',0)],500320)+1.75)<1e-6
    # Transição suave (sem degrau): variação lateral por metro limitada.
    P=D[('f',0)]['points'];o=np.argsort(P[:,0]);dy=np.abs(np.diff(P[o,1]))/np.maximum(np.diff(P[o,0]),1e-9);assert dy.max()<.2
    # A 2ª faixa nasce e termina sobre a faixa que continua (as pontas caem nela: a rede liga as duas).
    f1=D[('f',1)]['points'];f0=D[('f',0)]['points']
    from shapely.geometry import LineString,Point
    ln=LineString(f0);assert ln.distance(Point(f1[0]))<.3 and ln.distance(Point(f1[-1]))<.3
    # Trecho de sentido único: o sentido oposto termina no início do trecho e recomeça no fim.
    O=build_lanes(RouteAlignment(**route(type='simples',sections=[{'start_m':150,'end_m':250,'type':'unico','lanes':1}])))
    assert sum(1 for l in O if l['dir']=='r')==2 and sum(1 for l in O if l['dir']=='f')==1

def test_route_traffic_network(junction):
    from app.render import Scene
    base=Scene.light(junction,S(derive_traffic_paths=False));n0=len(base.network.markings)
    sc=Scene.light(junction,S(derive_traffic_paths=False,route_alignments=[route(type='simples',speed_kmh=30,sections=[{'start_m':130,'end_m':230,'type':'dupla','lanes':2,'median_m':4}])]))
    E=[e for e in sc.network.edges if e['source'].startswith('Rota A')]
    assert len(E)>=4 and all(abs(e['speed']-30/3.6)<1e-9 for e in E)
    east=[e for e in E if 'sentido do desenho' in e['source']];west=[e for e in E if 'sentido oposto' in e['source']]
    assert all(e['p'][-1][0]>e['p'][0][0] for e in east) and all(e['p'][-1][0]<e['p'][0][0] for e in west)
    assert all(np.mean(e['p'][:,1])<Y for e in east) and all(np.mean(e['p'][:,1])>Y for e in west)
    # Faixas de rota não recebem pintura (só conduzem veículos).
    assert len(sc.network.markings)==n0
    # A faixa que nasce no trecho duplo é ligada à que continua (há conexões entre arestas da rota).
    idx={i for i,e in enumerate(sc.network.edges) if e['source'].startswith('Rota A')}
    assert any(j in idx for i in idx for j in sc.network.connections.get(i,[]))
    # Rota desativada não gera nada; fora do pavimento só com a opção.
    off=Scene.light(junction,S(derive_traffic_paths=False,route_alignments=[route(enabled=False)]))
    assert not [e for e in off.network.edges if e['source'].startswith('Rota A')]
    far={'id':'r2','name':'Rota B','points':[{'x':500020,'y':Y+60},{'x':500150,'y':Y+60}]}
    assert not [e for e in Scene.light(junction,S(derive_traffic_paths=False,route_alignments=[far])).network.edges if e['source'].startswith('Rota B')]
    assert [e for e in Scene.light(junction,S(derive_traffic_paths=False,route_alignments=[{**far,'outside_pavement':True}])).network.edges if e['source'].startswith('Rota B')]

def test_projects_rename_templates(junction):
    from app.server import app
    from app import store
    c=TestClient(app)
    marks=dict(highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':Y+20}}],route_alignments=[route()])
    pid=c.post('/api/projects',json=S(name='Trecho Modelo',fps=30,signage_style='previous',duration_s=77,**marks).model_dump()).json()['id']
    other=c.post('/api/projects',json=S(name='Outro trecho',km_start_m=1000,km_end_m=1400,**{'highlights':[{'id':'x','name':'Ponte','point':{'x':1,'y':2}}]}).model_dump()).json()['id']
    # Renomear: nome no banco e na configuração; nome sem letra/número recusado.
    r=c.post(f'/api/projects/{pid}/rename',json={'name':'  Trecho   Modelo 2 '});assert r.status_code==200 and r.json()['name']=='Trecho Modelo 2'
    assert c.get(f'/api/projects/{pid}').json()['config']['name']=='Trecho Modelo 2' and any(p['name']=='Trecho Modelo 2' for p in c.get('/api/projects').json())
    assert c.post(f'/api/projects/{pid}/rename',json={'name':'---'}).status_code==422
    # Lista para “Abrir projeto”: datas, arquivos e miniatura da prévia.
    info={p['id']:p for p in c.get('/api/projects_info').json()};assert info[pid]['modified'] and info[pid]['files']=={'dxf':False,'kmz':False} and not info[pid]['preview']
    assert c.get(f'/api/projects/{pid}/miniatura.jpg').status_code==404
    cv2.imwrite(str(store.ROOT/pid/'preview.png'),np.full((900,1600,3),90,np.uint8))
    t=c.get(f'/api/projects/{pid}/miniatura.jpg');assert t.status_code==200;im=cv2.imdecode(np.frombuffer(t.content,np.uint8),1);assert im.shape[1]==320 and im.shape[0]==180
    assert {p['id']:p for p in c.get('/api/projects_info').json()}[pid]['preview']
    # Modelo só com configurações: sem marcações, sem dados do trecho.
    m1=c.post(f'/api/projects/{pid}/modelo',json={'name':'Padrão NOVA 381','description':'vídeo 30 fps'}).json()
    g=c.get(f"/api/modelos/{m1['id']}").json();assert g['config']['fps']==30 and g['config']['highlights']==[] and g['config']['route_alignments']==[] and not g['include_marks']
    assert c.post(f'/api/projects/{pid}/modelo',json={'name':'padrão nova 381'}).status_code==422   # nome repetido
    m2=c.post(f'/api/projects/{pid}/modelo',json={'name':'Com marcações','include_marks':True}).json()
    g2=c.get(f"/api/modelos/{m2['id']}").json();assert len(g2['config']['highlights'])==1 and len(g2['config']['route_alignments'])==1
    L=c.get('/api/modelos').json();assert [x['name'] for x in L]==['Com marcações','Padrão NOVA 381'] and L[0]['marks']==2
    # Novo projeto a partir do modelo.
    n=c.post(f"/api/modelos/{m1['id']}/novo",json={'name':'Trecho novo'});assert n.status_code==201
    nc=c.get(f"/api/projects/{n.json()['id']}").json();assert nc['config']['name']=='Trecho novo' and nc['config']['fps']==30 and nc['config']['signage_style']=='previous' and nc['config']['highlights']==[] and nc['files']=={'dxf':False,'kmz':False}
    # Aplicar a um projeto existente: configurações do modelo, marcações e km do projeto ficam.
    a=c.post(f"/api/projects/{other}/aplicar_modelo/{m1['id']}");assert a.status_code==200
    oc=c.get(f'/api/projects/{other}').json()['config'];assert oc['fps']==30 and oc['duration_s']==77 and oc['name']=='Outro trecho' and oc['km_end_m']==1400 and oc['highlights'][0]['name']=='Ponte'
    assert (store.ROOT/other/a.json()['backup']).exists()
    # Renomear e excluir modelo.
    assert c.post(f"/api/modelos/{m2['id']}/rename",json={'name':'Padrão NOVA 381'}).status_code==422
    assert c.post(f"/api/modelos/{m2['id']}/rename",json={'name':'Trecho completo'}).json()['name']=='Trecho completo'
    d=c.delete(f"/api/modelos/{m2['id']}").json();assert (store.ROOT/'_lixeira'/d['trash']).exists() and len(c.get('/api/modelos').json())==1
    assert c.get('/api/modelos/'+'0'*32).status_code==404 and c.get('/api/modelos/../x').status_code in (404,405)
    # Prévia das faixas para o editor.
    pr=c.post('/api/rotas_previa',json={'route_alignments':[route(type='dupla',lanes=2,median_m=6)]}).json()['lanes'];assert len(pr)==4 and {l['dir'] for l in pr}=={'f','r'}

def test_schema_and_migration():
    old=Settings.model_validate({'schema_version':24,'km_start_m':0,'km_end_m':100});assert old.route_alignments==[] and old.schema_version>=25
    s=S(route_alignments=[route(sections=[{'start_m':200,'end_m':100,'type':'unico'}])]);assert s.route_alignments[0].sections[0].start_m==100
    with pytest.raises(ValueError):S(route_alignments=[route(type='tripla')])
