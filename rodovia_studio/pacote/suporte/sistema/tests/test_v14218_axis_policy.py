import numpy as np
from shapely.geometry import box,LineString
from app.models import Settings,DirectionMark
from app.native_axes import native_paths
from app.direction_intervals import split_intervals
from test_v14213_continuity import network,AXIS


def test_pavement_skeleton_is_not_a_source_even_with_legacy_flag_enabled(monkeypatch):
    from app import traffic
    def forbidden(*args,**kwargs):raise AssertionError('Não pode inventar eixos do pavimento.')
    monkeypatch.setattr(traffic,'skeleton_paths',forbidden)
    n=network([dict(layer='EIXO LESTE',role='axis',points=AXIS)],derive_traffic_paths=True)
    assert n.paths and all(r.get('native_axis') for r in n.raw_info)
    assert n.report['source_policy']=='somente_eixos_designados_ou_selecao_explicita'


def test_unassigned_border_and_kmz_reference_do_not_become_axes():
    s=Settings();surface=box(-10,-10,610,10)
    assert not native_paths([dict(layer='BORDO',points=AXIS)],s,surface)[0]
    assert not native_paths([dict(layer='KMZ',role='axis',reference_only=True,points=AXIS)],s,surface)[0]
    assert native_paths([dict(layer='Qualquer',role='axis',points=AXIS)],s,surface)[0]
    assert native_paths([dict(layer='KMZ',role='axis',reference_only=True,points=AXIS)],Settings(route_directions={'0':'forward'}),surface)[0]


def test_start_end_direction_changes_only_the_known_interval_and_keeps_source():
    mark=DirectionMark(id='sentido',start=dict(x=400,y=0),end=dict(x=200,y=0));before=AXIS.copy()
    n=network([dict(layer='EIXO',role='axis',points=AXIS)],direction_marks=[mark])
    interior=[r for r in n.raw_info if r.get('direction_mark_id')=='sentido']
    assert interior and all(not r['forward'] and not r['both'] for r in interior)
    assert all(min(r['points'][:,0])>=199.99 and max(r['points'][:,0])<=400.01 for r in interior)
    middle_edges=[e for e in n.edges if min(e['p'][:,0])>=199.99 and max(e['p'][:,0])<=400.01]
    assert middle_edges and all(e['p'][-1,0]<e['p'][0,0] for e in middle_edges)
    np.testing.assert_array_equal(AXIS,before)
    assert n.direction_report[0]['status']=='applied'


def test_explicit_selected_one_way_route_can_reverse_with_interval_indication():
    s=Settings(route_alignments=[dict(id='r',points=[dict(x=0,y=0),dict(x=600,y=0)],type='unico')],route_directions={'0':'off'},derive_traffic_paths=False)
    from test_v1426_transport import network as net
    s.direction_marks=[DirectionMark(id='rdir',start=dict(x=600,y=0),end=dict(x=0,y=0))]
    n=net(s)
    assert n.paths and all(p['p'][-1,0]<p['p'][0,0] for p in n.paths)


def test_ambiguous_direction_between_parallel_axes_requires_explicit_selection():
    raw=[dict(points=np.array([[0.,y],[600.,y]])) for y in (-2.,2.)]
    marks=[DirectionMark(start=dict(x=100,y=0),end=dict(x=500,y=0))]
    rows,report=split_intervals(raw,marks)
    assert report[0]['status']=='ambiguous' and not any('explicit_direction' in row for row in rows)


def test_selected_line_with_direction_is_usable_without_any_axis_layer(tmp_path):
    import ezdxf
    from app.render import Scene
    from app import store
    doc=ezdxf.new();doc.layers.new('PAVIMENTO');doc.layers.new('LINHA_AUXILIAR');m=doc.modelspace()
    m.add_line((0,0),(600,0),dxfattribs={'layer':'LINHA_AUXILIAR'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(-20,-10),(620,-10),(620,10),(-20,10)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    s=Settings(hydrography=False,imagery='neutral',route_alignments=[dict(id='chosen',points=[dict(x=0,y=0),dict(x=600,y=0)],type='unico')])
    store.write_json(tmp_path/'config.json',s.model_dump());scene=Scene.light(tmp_path,s)
    assert scene.network.paths and all(r.get('route')=='chosen' for r in scene.network.raw_info)


def test_direction_mark_source_line_is_unchanged_and_unmarked_parts_keep_direction():
    source=dict(points=AXIS.copy(),origin_key='source')
    mark=DirectionMark(id='range',start=dict(x=450,y=0),end=dict(x=150,y=0))
    rows,report=split_intervals([source],[mark]);assert len(rows)==3
    assert 'explicit_direction' not in rows[0] and 'explicit_direction' not in rows[2]
    assert rows[1]['explicit_direction'] is False
    np.testing.assert_array_equal(source['points'],AXIS)
