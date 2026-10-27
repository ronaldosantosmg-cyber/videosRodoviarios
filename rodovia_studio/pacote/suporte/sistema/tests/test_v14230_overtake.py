from types import SimpleNamespace
import numpy as np
from shapely.geometry import box
from app.models import Settings
from app.shoulder_probe import ShoulderProbe,envelope
from app.vehicle_motion import prepare_points
from app.vehicle_safety import PolygonSafety


def scenario(width=-6.5,obstacles=()):
    p=np.array([[0.,-2.1],[700.,-2.1]]);paved=box(-30,width,730,4)
    sim=SimpleNamespace(s=Settings(heavy_shoulder_overtake=True),paths=[dict(p=p,length=700)],motion_points=[prepare_points(p)],net=SimpleNamespace(allowed=paved,operational_pavement=paved,shoulder_envelope=envelope(paved,obstacles)),blocks=[],time=0)
    sim.polygon_safety=PolygonSafety(sim);sim.shoulder_probe=ShoulderProbe(sim)
    v=dict(id=1,p=0,s=60.,v=8.,v0=8.,t='truck18',L=18.,lc=None)
    w=dict(id=2,p=0,s=105.,v=3.,v0=3.,t='car6',L=6.,lc=None)
    return sim,v,w


def test_heavy_itself_passes_slower_vehicle_on_right_and_returns_with_clearance():
    sim,v,w=scenario();probe=sim.shoulder_probe
    assert probe.try_overtake(v,w,[v,w]);e=probe.events[(1,0)][0]
    assert e['kind']=='ultrapassagem' and e['target']==2
    assert probe.offset(e,e['stations'][0])==probe.offset(e,e['stations'][-1])==0
    for s in np.linspace(*[e['stations'][0],e['stations'][-1]],201):
        ws=w['s']+(s-v['s'])/8*3
        assert probe.area.covers(probe.geometry(v,s,e,False))
        assert not probe.geometry(v,s,e).intersection(probe.geometry(w,ws)).area>1e-7
    v['s']=e['stations'][1];w['s']=v['s']
    assert probe.laterally_separated(v,w)


def test_overtake_refuses_insufficient_width_barrier_equal_speed_and_no_authorization():
    sim,v,w=scenario(width=-3.6);assert not sim.shoulder_probe.try_overtake(v,w,[v,w])
    sim,v,w=scenario(obstacles=[box(80,-8,250,-3.9)]);assert not sim.shoulder_probe.try_overtake(v,w,[v,w])
    sim,v,w=scenario();w['v']=8;assert not sim.shoulder_probe.try_overtake(v,w,[v,w])
    sim,v,w=scenario();sim.s.heavy_shoulder_overtake=False;assert not sim.shoulder_probe.try_overtake(v,w,[v,w])


def test_actual_simulation_overtakes_without_polygon_overlap_and_signals_return(monkeypatch,tmp_path):
    from app import simulation
    from app.traffic import TrafficNetwork
    from app.vehicle_safety import body
    monkeypatch.setattr(simulation,'WARMUP',0)
    original_rng=np.random.default_rng
    class Arrival:
        def __init__(self,*a,**k):self.rng=original_rng(*a,**k)
        def exponential(self,*a,**k):return 30.
        def __getattr__(self,name):return getattr(self.rng,name)
    monkeypatch.setattr(simulation.np.random,'default_rng',Arrival)
    monkeypatch.setitem(simulation.SPEED_FACTOR,'car6',.22)
    monkeypatch.setitem(simulation.SPEED_FACTOR,'truck18',1.)
    s=Settings(heavy_shoulder_overtake=True,traffic_density=8,traffic_speed_kmh=36,duration_s=100,queue_capacity_model=False,hydrography=False,signage_detail='basic',derive_traffic_paths=False,route_directions={'0':'off'},route_alignments=[dict(id='r',name='Ultrapassagem em ensaio',type='unico',lanes=1,lane_width_m=3.6,points=[dict(x=0,y=-2.1),dict(x=700,y=-2.1)])])
    a=np.array([[0.,-2.1],[700.,-2.1]])
    net=TrafficNetwork([box(-30,-6.5,730,4)],[],[],a,np.array([0.,700.]),s)
    sim=simulation.TrafficSim(net,s,lambda kinds,identity:'car6' if identity[1]%3==0 else 'truck18',duration=100)
    assert sim.shoulder_probe.counts['ultrapassagens_aceitas']>0
    crossed=False;codes=set()
    for t in np.arange(0,100,.2):
        polys=[];states={v[0]:v for v in sim.state(float(t))};codes.update(sim.indicators(float(t)).values())
        for c,h,vid,identity,j in sim.vehicles_ex(float(t)):
            vt=sim.info[vid][1];L,B,_,_=__import__('app.vehicle_motion',fromlist=['PROFILES']).PROFILES[vt]
            p=body(c,h,L,B,.15)
            assert all(p.intersection(q).area<.002 for q in polys);polys.append(p)
            v=dict(id=vid,p=states[vid][1],s=states[vid][2],t=vt)
            event=sim.shoulder_probe.event(v)
            if event and event.get('kind')=='ultrapassagem':
                target=states.get(event['target']);crossed|=bool(target and v['s']>target[2]+(L+6)/2)
    assert crossed and {1,2}<=codes
    assert sim.report()['rear_collisions']==sim.report()['side_collisions']==0
    # Quadro do renderizador real com a mesma geometria e chegadas controladas.
    import ezdxf,os,json
    from pathlib import Path
    from PIL import Image
    from app import visual
    from app.render import Scene
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    m.add_lwpolyline([(0,-2.1),(700,-2.1)],dxfattribs={'layer':'EIXO'})
    hatch=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});hatch.paths.add_polyline_path([(-30,-6.5),(730,-6.5),(730,4),(-30,4)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    s.width=1280;s.imagery='neutral';s.imagery_pixels=2048;s.coordinates_confirmed=True;s.camera_mode='trafego';s.view_width_m=100
    (tmp_path/'config.json').write_text(s.model_dump_json())
    monkeypatch.setattr(visual,'vehicle_type',lambda kinds,identity,*args,**kw:'car6' if identity[1]%3==0 else 'truck18')
    scene=Scene(tmp_path,s);actual=scene.traffic();found=False
    for t in np.arange(60,100,.5):
        for vid,i,station,_,_ in actual.state(float(t)):
            v=dict(id=vid,p=i,s=station,t=actual.info[vid][1]);e=actual.shoulder_probe.event(v)
            if e and e.get('kind')=='ultrapassagem' and station>e['stations'][1] and station<e['stations'][2]:
                center=actual.shoulder_probe.pose(v)[0];image,meta=scene.frame(float(t),view=(center,100))
                assert meta['traffic_visibility']['drawn']>=2
                target=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));target.mkdir(parents=True,exist_ok=True)
                Image.fromarray(image).save(target/'14230_pesado_ultrapassa_acostamento.png')
                (target/'ultrapassagem.json').write_text(json.dumps(dict(time_s=float(t),probe=actual.shoulder_probe.report(),visibility=meta['traffic_visibility'],scope='Chegadas e velocidades distintas controladas somente no ensaio; quadro do renderizador real.'),ensure_ascii=False,indent=2))
                found=True;break
        if found:break
    assert found


def test_route_inspection_and_disabled_collision_control_never_permit_overtaking():
    for key in ('traffic_route_only','traffic_prevent_collisions'):
        sim,v,w=scenario();setattr(sim.s,key,key=='traffic_route_only')
        assert not sim.shoulder_probe.try_overtake(v,w,[v,w])
