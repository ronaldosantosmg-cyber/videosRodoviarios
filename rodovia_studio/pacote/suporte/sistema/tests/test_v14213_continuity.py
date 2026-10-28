import hashlib
import numpy as np
from shapely.geometry import box,LineString
from app.models import Settings
from app.native_axes import native_paths
from app.traffic import TrafficNetwork,sample
from app.flow_diagnostics import flow_diagnostics

AXIS=np.array([[0.,0.],[600.,0.]])

def network(axes,**kw):
    roads=kw.pop('roads',[box(-20,-20,620,220)]);obstacles=kw.pop('obstacles',[]);borders=kw.pop('borders',[])
    axes=[dict(a,layer=a.get('layer','EIXO'),role='axis') for a in axes]
    kw.setdefault('layers',{'axis':list(dict.fromkeys(a['layer'] for a in axes))})
    s=Settings(**dict(dict(derive_traffic_paths=False,hydrography=False),**kw))
    return TrafficNetwork(roads,obstacles,axes,AXIS,np.array([0.,600.]),s,edge_lines=borders)


def test_minor_dxf_axis_is_used_instead_of_only_the_main_skeleton():
    minor=np.array([[100.,30.],[300.,30.]])
    n=network([dict(points=AXIS),dict(points=minor)],derive_traffic_paths=True)
    assert any(r.get('native_id')=='1' and np.allclose(r['points'][:,1],30) for r in n.raw_info)
    assert any(p['length']>=190-1e-6 and np.ptp(p['p'][:,1])<.01 and np.mean(p['p'][:,1])>25 for p in n.paths)


def test_short_contact_piece_does_not_break_a_long_native_axis():
    axes=[dict(points=AXIS),dict(points=np.array([[250.,0.],[250.,150.]])),dict(points=np.array([[275.,0.],[275.,150.]]))]
    n=network(axes)
    assert any(e['native_id']=='0' and e['length']<50 for e in n.edges)
    assert any(np.ptp(p['p'][:,0])>590 and np.ptp(p['p'][:,1])<.01 for p in n.paths)
    rows=flow_diagnostics(n)
    assert any(r['technical_status']=='ok' and 'Subtrecho integrado' in r['technical_message'] for r in rows)
    assert all(p['length']>=50 for p in n.paths)


def test_short_fragments_join_only_in_derived_geometry_and_preserve_source():
    axes=[dict(layer='EIXO',points=np.array([[100.+i*30,30.],[130.+i*30,30.]])) for i in range(3)]
    before=[a['points'].copy() for a in axes];n=network([dict(points=AXIS)]+axes)
    assert n.native_axis_report['joined']==2
    assert any(p['length']>=80-1e-6 and np.ptp(p['p'][:,0])<100 for p in n.paths)
    for a,b in zip(axes,before):np.testing.assert_array_equal(a['points'],b)


def test_border_paint_does_not_interrupt_but_real_obstacles_do():
    border=np.array([[300.,-15.],[300.,15.]])
    a=network([dict(points=AXIS)]);b=network([dict(points=AXIS)],borders=[border])
    assert len(a.paths)==len(b.paths)>0
    for p,q in zip(a.paths,b.paths):np.testing.assert_array_equal(p['p'],q['p'])
    obstacle=box(295,-20,305,220);blocked=network([dict(points=AXIS)],obstacles=[obstacle])
    assert not any(np.min(p['p'][:,0])<295 and np.max(p['p'][:,0])>305 for p in blocked.paths)
    diagnostics=flow_diagnostics(blocked)
    assert any('corpo_fora_da_pista' in d['technical_reasons'] and d['technical_points'] for d in diagnostics)
    assert any('Linhas de bordo não são barreiras' in d['technical_manual'] for d in diagnostics)


def test_join_rejects_real_gap_ambiguity_incompatible_layer_and_disabled_axis():
    s=Settings(layers={'axis':['EIXO A','EIXO B']});surface=box(-10,-10,200,10)
    def row(a,b,layer='EIXO A'):return dict(points=np.array([[a,0.],[b,0.]]),layer=layer)
    rows,report=native_paths([row(0,60),row(60.1,120)],s,surface)
    assert len(rows)==1 and report['joined']==1 and abs(report['max_gap_m']-.1)<1e-6
    for axes in [[row(0,60),row(61,120)],[row(0,60),row(60,120,'EIXO B')],
                 [row(0,60),row(60,120),row(60,130)]]:
        assert native_paths(axes,s,surface)[1]['joined']==0
    s.route_directions={'axis:'+__import__('app.native_axes',fromlist=['axis_fingerprint']).axis_fingerprint([[60,0],[120,0]],'EIXO A'):'off'}
    assert len(native_paths([row(0,60),row(60,120)],s,surface)[0])==1
    assert native_paths([row(0,60),row(60.1,120)],Settings(layers={'axis':['EIXO A']}),surface.difference(box(60,-10,60.1,10)))[1]['joined']==0


def test_old_main_axis_disable_keeps_its_identity():
    p,_=sample(AXIS,3);coordinates=np.round(p,3).astype('<f8')
    key=hashlib.sha256(b'eixo principal DXF|0'+min(coordinates.tobytes(),coordinates[::-1].tobytes())).hexdigest()
    n=network([dict(points=AXIS)],flow_overrides=[dict(id='old',x=300,y=0,target_key=key,action='disable')])
    assert n.raw_info and all(r['disabled'] for r in n.raw_info)
    assert not n.paths


def test_external_axis_excess_is_trimmed_without_creating_portals_at_internal_gaps():
    n=network([dict(points=AXIS)],roads=[box(40,-10,560,10)])
    assert n.paths and abs(max(p['length'] for p in n.paths)-510)<1e-6
    assert all(np.min(p['p'][:,0])>40 and np.max(p['p'][:,0])<560 for p in n.paths)
    blocked=network([dict(points=AXIS)],roads=[box(40,-10,560,10)],obstacles=[box(290,-10,310,10)])
    assert not blocked.paths


def test_nearly_coincident_contacts_do_not_delete_one_meter_of_axis():
    axes=[dict(points=AXIS)]+[dict(points=np.array([[x,0.],[x,150.]])) for x in (250.,251.)]
    n=network(axes)
    assert any(np.ptp(p['p'][:,0])>590 and np.ptp(p['p'][:,1])<.01 for p in n.paths)


def test_sparse_dxf_vertices_do_not_leave_a_duplicate_skeleton_flow():
    n=network([dict(points=AXIS)],derive_traffic_paths=True,roads=[box(-10,-6,610,6)])
    assert n.paths and all(raw.get('native_axis') for raw in n.raw_info)


def test_partial_overlap_connector_requires_explicit_selection(monkeypatch):
    import app.traffic as module
    p,_=sample(np.array([[0.,0.],[460.,0.],[480.,20.]]))
    monkeypatch.setattr(module,'skeleton_paths',lambda *a,**k:[dict(points=p,halfwidth=3.5,source='Ligação complementar',level=0)])
    n=network([dict(points=AXIS)],derive_traffic_paths=True)
    assert not any(r['source']=='Ligação complementar' for r in n.raw_info)
    explicit=network([dict(points=AXIS)],traffic_paths=[dict(id='chosen',name='Ligação selecionada',points=[dict(x=float(x),y=float(y)) for x,y in p])])
    assert any(r['source']=='Ligação selecionada' and r['manual'] for r in explicit.raw_info)
