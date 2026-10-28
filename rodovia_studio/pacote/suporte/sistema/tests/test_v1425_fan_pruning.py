from types import SimpleNamespace
import numpy as np
from shapely.geometry import box
from app.models import Settings
from app.traffic import TrafficNetwork


def test_converging_and_diverging_mini_routes_are_removed_before_network():
    axis=np.array([[0.,0.],[500.,0.]])
    spokes=[np.array([[250.,0.],[250.+dx,dy]]) for dx,dy in [(10,4),(-12,8),(8,-15),(-10,-10),(0,19)]]
    originals=[p.copy() for p in spokes]
    s=Settings(layers={'axis':['EIXO']},derive_traffic_paths=False,hydrography=False,min_route_segment_m=50)
    n=TrafficNetwork([box(-30,-50,530,50)],[],[dict(points=p,layer='EIXO',role='axis') for p in [axis]+spokes],axis,np.array([0.,500.]),s)
    assert len(n.auto_pruned)>=5
    assert all(np.sum(np.linalg.norm(np.diff(r['points'],axis=0),axis=1))>=50 for r in n.raw_info)
    assert all(e['length']>=50 for e in n.edges)
    assert all(np.array_equal(a,b) for a,b in zip(spokes,originals))
    assert n.paths and all(len(p['edges'])==1 for p in n.paths)


def test_pruning_is_generic_manual_data_kept_and_boundary_is_strict():
    n=TrafficNetwork.__new__(TrafficNetwork);n.min_route=100;n.auto_pruned=[];n.warnings=[];n.pruned_contacts={}
    rows=[{'points':np.array([[0.,0.],[L,0.]]),'source':'qualquer projeto','origin':i} for i,L in enumerate([99.9,100,120])]
    manual={'points':np.array([[0.,0.],[10.,0.]]),'source':'manual','manual':True,'origin':4}
    assert n.prune_automatic(rows+[manual],'original')==rows[1:]+[manual]


def test_cut_segment_does_not_become_artificial_spawn_portal():
    n=TrafficNetwork.__new__(TrafficNetwork);n.original_terminals={0:np.array([[0.,0.],[400.,0.]])};n.pruned_contacts={0:[np.array([10.,0.])]}
    edge={'origin':0,'p':np.array([[10.,0.],[400.,0.]])}
    assert not n.portal_allowed(edge,True) and n.portal_allowed(edge,False)


def test_contact_splits_keep_long_native_axis_without_independent_short_routes():
    axis=np.array([[0.,0.],[600.,0.]])
    # As fontes são longas; o trecho de 25 m só aparece depois dos encontros.
    axes=[{'points':axis},{'points':np.array([[250.,0.],[250.,150.]])},
          {'points':np.array([[275.,0.],[275.,150.]])}]
    s=Settings(layers={'axis':['EIXO']},derive_traffic_paths=False,hydrography=False,min_route_segment_m=50)
    n=TrafficNetwork([box(-30,-180,630,180)],[],[dict(a,layer='EIXO',role='axis') for a in axes],axis,np.array([0.,600.]),s)
    assert any(e['length']<50 and e.get('native_axis') for e in n.edges)
    assert all(n.origin_info[e['origin']][0]>=50 for e in n.edges)
    assert all(p['length']>=50 for p in n.paths)
    for itinerary in n.paths:
        assert n.portal_allowed(n.edges[itinerary['edges'][0]],True)
        assert n.portal_allowed(n.edges[itinerary['edges'][-1]],False)


def test_engine_revision_invalidates_old_editor_cache_when_geometry_engine_changes(tmp_path,monkeypatch):
    import json
    import app.scene3d as module
    from app.scene3d import revision
    from pathlib import Path
    (tmp_path/'config.json').write_text(Settings().model_dump_json())
    previous=revision(tmp_path)
    original=Path.read_bytes
    def changed(path):
        data=original(path)
        return data+b'\n# motor atualizado' if path.name=='traffic.py' else data
    monkeypatch.setattr(Path,'read_bytes',changed)
    assert revision(tmp_path)!=previous
