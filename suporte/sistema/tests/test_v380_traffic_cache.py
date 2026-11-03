import collections
import json
import math
import numpy as np
from app.simulation import TrafficSim
from app.traffic_cache import Codec,cache_key,cache_save,cache_load_into
from tests.test_v14212_traffic_safety import configuration,network


def make(**kw):
    s=configuration(duration_s=8,traffic_density=.2,**kw);n=network(s)
    return s,n,TrafficSim(n,s,lambda *a:'car',duration=8,defer=True)


def same_frames(a,b):
    assert len(a.frames)==len(b.frames)
    for x,y in zip(a.frames,b.frames):
        assert all(np.array_equal(i,j) for i,j in zip(x,y))


def test_ready_roundtrip_real_sim_preserves_owner_and_current_external_bindings(tmp_path):
    s,n,sim=make();sim.run();key=cache_key(n,s,8)
    assert cache_save(sim,tmp_path,key,complete=True)
    _,_,other=make();net,settings,vtype=other.net,other.s,other.vtype
    assert cache_load_into(other,tmp_path,key,complete=True)
    same_frames(sim,other)
    assert other.net is net and other.s is settings and other.vtype is vtype
    assert other.pedestrians.owner is other and other.polygon_safety.sim is other
    assert other.shoulder_probe.sim is other and other.conflict_guard.sim is other
    assert other.paths is net.paths
    assert other._continuation['frames'] is other.frames


def test_checkpoint_continues_deterministically_with_rng(tmp_path):
    s,n,sim=make();blocks=sim.run_blocks(block_seconds=2);next(blocks);blocks.close()
    key=cache_key(n,s,8);assert not sim.simulation_complete
    assert cache_save(sim,tmp_path,key)
    _,_,other=make();assert cache_load_into(other,tmp_path,key)
    sim.run();other.run();same_frames(sim,other)
    assert sim.info==other.info and sim.report()['rear_collisions']==other.report()['rear_collisions']


def test_codec_aliases_zone_and_special_safe_types():
    _,_,sim=make();zone={'phase':'f'};rng=np.random.default_rng(42)
    value={'zone':zone,'gate':{'zone':zone},'rng':rng,'default':collections.defaultdict(lambda:-math.inf),'pairs':{(1,2):np.array([1.,2.])}}
    codec=Codec(sim);root=codec.encode(value);decoded=codec.decode(root,codec.nodes,codec.arrays)
    assert decoded['zone'] is decoded['gate']['zone']
    assert decoded['default']['new']==-math.inf
    assert decoded['rng'].random()==rng.random()
    assert np.array_equal(decoded['pairs'][(1,2)],[1.,2.])


def test_corrupt_or_object_array_cache_is_miss_and_does_not_change_sim(tmp_path):
    s,n,sim=make();sim.run();key=cache_key(n,s,8);assert cache_save(sim,tmp_path,key,complete=True)
    target=next((tmp_path/(key+'.ready')).glob('arrays-*.npz'));target.write_bytes(b'corrupt')
    _,_,other=make();assert not cache_load_into(other,tmp_path,key,complete=True)
    assert not other.simulation_complete and not other.frames
    codec=Codec(sim)
    import pytest
    with pytest.raises(ValueError):codec.encode(np.array([object()],dtype=object))
    with pytest.raises(ValueError):codec.decode({'ref':0},[{'kind':'object','class':'os.system','attrs':None}],{})


def test_partial_never_loads_as_ready_and_unsafe_fleet_never_saved_ready(tmp_path):
    s,n,sim=make();key=cache_key(n,s,8)
    assert cache_save(sim,tmp_path,key)
    assert not cache_save(sim,tmp_path,key,complete=True)
    _,_,other=make();assert not cache_load_into(other,tmp_path,key,complete=True)
    sim.run();sim.fleet_audit['violations'].append({'path':0,'station_m':1})
    assert not cache_save(sim,tmp_path,key,complete=True)


def test_key_invalidates_physics_duration_window_and_code_inputs():
    s,n,_=make();a=cache_key(n,s,8)
    assert cache_key(n,s,9)!=a
    assert cache_key(n,s,8,window=([0,0],50))!=a
    s.traffic_speed_kmh+=1;assert cache_key(n,s,8)!=a
    s.traffic_speed_kmh-=1;n.paths[0]['p'][0,0]+=.1;assert cache_key(n,s,8)!=a


def test_real_alternating_control_alias_survives_restore(tmp_path):
    s,n,sim=make(alternating_zones=[dict(id='z',route_id='r',start_m=180,end_m=340,release_s=10)])
    blocks=sim.run_blocks(block_seconds=2);next(blocks);blocks.close()
    key=cache_key(n,s,8);assert cache_save(sim,tmp_path,key)
    _,_,other=make(alternating_zones=[dict(id='z',route_id='r',start_m=180,end_m=340,release_s=10)])
    assert cache_load_into(other,tmp_path,key)
    gate=next(g for gates in other.alternating.gates for g in gates)
    assert gate['zone'] is other.alternating.zones[0]
    sim.run();other.run();same_frames(sim,other)


def test_geometry_indexes_and_models_roundtrip():
    from scipy.spatial import cKDTree
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    _,_,sim=make();codec=Codec(sim)
    value={'kd':cKDTree([[1.,2.],[3.,4.]]),'tree':STRtree([Point(1,2)]),'model':sim.s.route_alignments[0]}
    root=codec.encode(value);result=codec.decode(root,codec.nodes,codec.arrays)
    assert result['kd'].query([1.,2.])[0]==0
    assert list(result['tree'].query(Point(1,2)))==[0]
    assert result['model'].model_dump()==value['model'].model_dump()


def test_manifest_tamper_is_miss_and_generations_survive_replacement(tmp_path):
    s,n,sim=make();sim.run();key=cache_key(n,s,8)
    assert cache_save(sim,tmp_path,key,complete=True)
    entry=tmp_path/(key+'.ready');first=list(entry.glob('arrays-*.npz'))
    assert cache_save(sim,tmp_path,key,complete=True)
    assert all(p.exists() for p in first) and len(list(entry.glob('arrays-*.npz')))==2
    manifest=entry/'state.json';document=json.loads(manifest.read_bytes());document['complete']=False
    manifest.write_text(json.dumps(document))
    _,_,other=make();assert not cache_load_into(other,tmp_path,key,complete=True)


def test_visual_only_setting_does_not_invalidate_physics_signature():
    s,n,_=make();a=cache_key(n,s,8)
    # model_copy accepts fields even when defaults evolve; key explicitly lists safe visuals.
    visual=s.model_copy(update={'night_start_s':2,'night_darkness':.9,'role_colors':{'road':'red'},'width':1920})
    assert cache_key(n,visual,8)==a


def test_people_state_roundtrip_and_continuation(tmp_path):
    options=dict(pedestrians=True,pedestrian_paths=[dict(id='sidewalk',points=[dict(x=0,y=30),dict(x=100,y=30)])])
    s,n,sim=make(**options);blocks=sim.run_blocks(block_seconds=2);next(blocks);blocks.close()
    assert sim.pedestrians.agents
    key=cache_key(n,s,8);assert cache_save(sim,tmp_path,key)
    _,_,other=make(**options);assert cache_load_into(other,tmp_path,key)
    assert other.pedestrians.agents[0]['route'] is other.pedestrians.routes[0]
    sim.run();other.run();same_frames(sim,other)
    assert sim.pedestrians.times==other.pedestrians.times
    for a,b in zip(sim.pedestrians.agents,other.pedestrians.agents):
        assert a['s']==b['s'] and a['state']==b['state']


def test_external_history_real_roundtrip_clone_shell_and_corruption(tmp_path):
    from app.traffic_history import FrameArchive
    s,n,sim=make();archive=FrameArchive(tmp_path/'histories'/('a'*32))
    sim._history_frames=archive.frames;sim._history_warnings=archive.warnings
    sim.run();archive.flush();key=cache_key(n,s,8)
    assert cache_save(sim,tmp_path,key,complete=True)
    shell=TrafficSim.__new__(TrafficSim);shell.net=n;shell.s=s;shell.vtype=lambda *a:'car';shell.duration=8.
    assert cache_load_into(shell,tmp_path,key,complete=True)
    assert shell.frames is shell._continuation['frames']
    assert shell.warning_frames.archive is shell.frames.archive
    assert shell._history_frames is shell.frames and shell._history_warnings is shell.warning_frames
    same_frames(sim,shell);assert shell.report()==sim.report()
    block=archive.root/archive.segments[0]['name'];block.write_bytes(b'corrupt')
    _,_,other=make();assert not cache_load_into(other,tmp_path,key,complete=True)
    assert not other.frames


def test_external_history_checkpoint_and_lru_two_blocks(tmp_path):
    from app.traffic_history import FrameArchive
    s,n,sim=make();archive=FrameArchive(tmp_path/'histories'/('b'*32))
    sim._history_frames=archive.frames;sim._history_warnings=archive.warnings
    generator=sim.run_blocks(block_seconds=1)
    for _ in range(3):next(generator);archive.flush()
    generator.close();key=cache_key(n,s,8);assert cache_save(sim,tmp_path,key)
    shell=TrafficSim.__new__(TrafficSim);shell.net=n;shell.s=s;shell.vtype=lambda *a:'car';shell.duration=8.
    assert cache_load_into(shell,tmp_path,key)
    restored=shell.frames.archive
    for row in restored.segments:restored.get(row['start'])
    assert len(restored._cache)==2
    sim.run();shell.run();same_frames(sim,shell)


def test_history_prune_preserves_references_and_active_roots(tmp_path):
    from app.traffic_history import FrameArchive
    from app.traffic_cache import prune_history
    s,n,sim=make();archive=FrameArchive(tmp_path/'histories'/('c'*32));sim._history_frames=archive.frames;sim._history_warnings=archive.warnings
    sim.run();key=cache_key(n,s,8);assert cache_save(sim,tmp_path,key,complete=True)
    orphan=tmp_path/'histories'/('d'*32);orphan.mkdir()
    active=tmp_path/'histories'/('e'*32);active.mkdir()
    result=prune_history(tmp_path,active_roots=[active])
    assert result['removed']==1 and not orphan.exists()
    assert archive.root.exists() and active.exists()


def test_prune_reports_budget_when_active_history_cannot_be_deleted(tmp_path,monkeypatch):
    import app.traffic_cache as cache
    active=tmp_path/'histories'/('f'*32);active.mkdir(parents=True);(active/'block').write_bytes(b'x'*200)
    monkeypatch.setattr(cache,'MAX_DISK_BYTES',100)
    result=cache.prune_history(tmp_path,active_roots=[active])
    assert result['over_budget'] is True and result['bytes_remaining']==200
    assert active.exists()
