import os
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import pytest
from shapely.geometry import Polygon
from app.models import Settings,HatchArea
from app.zebrados import named_layer,is_source,source_id,collect,resolve

def entity():return {'role':'sign_h','layer':'ZEBRADO AMARELO','closed':True,'points':np.array([[40,-2],[60,-2],[60,2],[40,2],[40,-2]],float),'holes':[]}
def network(opposed=True):return NS(paths=[{'p':np.array([[0,-5],[100,-5]])},{'p':np.array([[100,5],[0,5]]) if opposed else np.array([[0,5],[100,5]])}],edges=[],warnings=[],s=Settings())
@pytest.mark.parametrize('name,expected',[('ZEBRADO-01',True),('Zébrados amarelos',True),('ZEBRA WHITE',True),('SEM_ZEBRADO',False),('NAO ZEBRADO',False),('PAVIMENTO',False),('ZEBRADOLOGIA',False)])
def test_layer_names_are_specific(name,expected):assert named_layer(name)==expected

def test_identity_is_independent_of_start_and_orientation():
    e=entity();id_=source_id(e);q=dict(e);q['points']=np.roll(e['points'][:-1],2,axis=0)[::-1];assert source_id(q)==id_
    q['layer']='Outro zebrado';assert source_id(q)!=id_

def test_lateral_flows_and_explicit_color():
    e=entity();e['layer']='ZEBRADO';a=collect(network(),[e])[0];assert a['status']=='automatic' and a['color']=='yellow' and len(a['guides'])==2
    assert collect(network(False),[e])[0]['color']=='white'
    e['layer']='ZEBRADO BRANCO';assert collect(network(),[e])[0]['color']=='white'
    e['closed']=False;assert not is_source(e) and not collect(network(),[e])

def test_ambiguity_requires_confirmation_without_blocking_routes():
    e=entity();net=network();net.paths.append({'p':np.array([[50,-50],[50,50]])});before=[p['p'].copy() for p in net.paths]
    row=collect(net,[e])[0];assert row['status']=='pending' and row['angle_deg'] is None
    assert not resolve(net,[e]) and net.warnings and all(np.array_equal(a,b['p']) for a,b in zip(before,net.paths))
    net.paths=[];assert collect(net,[e])[0]['status']=='pending'

def test_override_disable_dedup_holes_and_missing_source():
    e=entity();e['holes']=[np.array([[48,-1],[50,-1],[50,1],[48,1]])];net=network();sid=source_id(e)
    h=HatchArea(points=[{'x':x,'y':y} for x,y in e['points']],holes=[[{'x':x,'y':y} for x,y in r] for r in e['holes']],source_id=sid,source_layer=e['layer'],color='white',angle_deg=15,world_aligned=True)
    net.s.hatch_areas=[h];paint=resolve(net,[e,e]);assert len(paint)==1 and paint[0].color=='white' and paint[0].angle_deg==15 and paint[0].holes
    h.enabled=False;assert not resolve(net,[e]) and net.zebra_sources[0]['status']=='disabled'
    assert not resolve(net,[]) and net.zebra_sources[0]['status']=='missing'
    h.source_id='';h.enabled=True;assert resolve(net,[])==[h]

def add_zebra(d):
    import ezdxf
    doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('ZEBRADO AMARELO');model=doc.modelspace();h=model.add_hatch(dxfattribs={'layer':'ZEBRADO AMARELO'});h.paths.add_polyline_path([(500180,7799999.4),(500210,7799999.4),(500210,7800000.6),(500180,7800000.6)],is_closed=True)
    h.paths.add_polyline_path([(500190,7799999.8),(500192,7799999.8),(500192,7800000.2),(500190,7800000.2)],is_closed=True,flags=0)
    doc.layers.new('ZEBRADO ABERTO');model.add_lwpolyline([(500170,7800010),(500180,7800012),(500185,7800010)],dxfattribs={'layer':'ZEBRADO ABERTO'});doc.saveas(d/'input.dxf')

def test_reader_closed_zebra_mapping_and_hidden_layers(tmp_path):
    from test_v1425_scene3d import project
    from app.geometry import analyze
    d,s=project(tmp_path);add_zebra(d);sources=[e for e in analyze(d,s)[0] if is_source(e)];assert len(sources)==1 and len(sources[0]['holes'])==1
    s.hidden_layers=['ZEBRADO AMARELO'];assert not any(is_source(e) for e in analyze(d,s)[0])
    s.hidden_layers=[];s.layers['median']=['ZEBRADO AMARELO'];assert not any(is_source(e) for e in analyze(d,s)[0])

def test_auto_paint_editor_video_3d_and_unchanged_routes(tmp_path):
    from test_v264_presentation import sample
    from app.render import Scene,render
    from app.scene3d import build
    from app.encoding import ffmpeg_exe,validate_mp4
    from PIL import Image
    d,s=sample(tmp_path);s.lanes_per_direction=1;s.traffic=True;oldp=[p['p'].copy() for p in Scene(d,s).network.paths];add_zebra(d);(d/'config.json').write_text(s.model_dump_json());scene=Scene(d,s)
    assert len(oldp)==len(scene.network.paths) and all(np.array_equal(p,q['p']) for p,q in zip(oldp,scene.network.paths))
    rows=scene.editor_data()['zebra_sources'];assert len(rows)==1 and rows[0]['status']=='automatic' and rows[0]['holes']
    area=Polygon(rows[0]['points'],rows[0]['holes']);yellow=[Polygon(r[0],r[1:]) for r,c in scene.network.fills if tuple(c)==(244,200,70) and Polygon(r[0]).intersects(area)]
    assert len(yellow)>3 and all(area.buffer(1e-7).covers(p) for p in yellow) and sum(p.area for p in yellow)<area.area*.7
    out=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs268-artifacts'));out.mkdir(parents=True,exist_ok=True);frame,_=scene.frame(2.8,view=([500195,7800000],60));Image.fromarray(frame).save(out/'268_zebrado_dxf.png')
    assert any(m['role']=='road_paint' and m['color']=='#f4c846' for m in build(d,s)['meshes'])
    assert validate_mp4(ffmpeg_exe(),render(d,s),72,1280,720,24)['ok']


def test_no_flow_index_cost_without_named_sources(monkeypatch):
    import app.zebrados as module
    def forbidden(*a):raise AssertionError('Índice desnecessário')
    monkeypatch.setattr(module,'FlowIndex',forbidden)
    assert module.collect(network(),[])==[]

@pytest.mark.parametrize('extra',[{'source_id':'dxf-zebra-x','angle_deg':None},{'holes':[[{'x':1000,'y':0},{'x':1001,'y':0},{'x':1001,'y':1}]],'world_aligned':True},{'flow_guides':[{'point':{'x':0,'y':0},'heading_deg':float('nan')}]}])
def test_new_configuration_rejects_unsafe_values(extra):
    with pytest.raises(ValueError):HatchArea(points=[{'x':x,'y':y} for x,y in entity()['points']],**extra)


def test_virtual_closure_is_not_an_automatic_zebra():
    e=entity();e['virtual']=[[[40,-2],[40,2]]];assert collect(network(),[e])[0]['status']=='pending'
