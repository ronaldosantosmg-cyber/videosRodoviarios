import json,os,subprocess
from pathlib import Path
import numpy as np
import pytest
from app.dxf_trim import source_id,visible,annotate,runs,pick
from app.models import Settings,DxfLineTrim

def entity(layer='LINHA'):return {'points':np.array([[0.,0.],[10.,0.],[10.,10.]]),'closed':False,'holes':[],'layer':layer,'role':'domain'}
def cut(e,a=4,b=14):return DxfLineTrim(source_id=source_id(e),layer=e['layer'],start_m=a,end_m=b,length_m=20,start={'x':4,'y':0},end={'x':10,'y':4})

def test_exact_curve_interval_reverse_click_order_and_no_join_over_gap():
    e=entity();parts=visible(e['points'],cuts=[cut(e)]);assert len(parts)==2
    assert np.array_equal(parts[0],[[0,0],[4,0]]) and np.array_equal(parts[1],[[10,4],[10,10]])
    assert not visible(e['points'],cuts=[cut(e,0,20)])

@pytest.mark.parametrize('data',[{'start_m':5,'end_m':5},{'start_m':5,'end_m':4},{'end_m':float('nan')},{'end_m':21},{'length_m':0},{'start':{'x':float('inf'),'y':0}}])
def test_invalid_intervals_refused(data):
    d=cut(entity()).model_dump();d.update(data)
    with pytest.raises(ValueError):DxfLineTrim.model_validate(d)

def test_masks_do_not_change_source_other_layers_or_surface_and_survive_reload():
    e=entity();s=Settings(dxf_line_trims=[cut(e)]);items,missing=annotate([e,entity('OUTRA')],s)
    assert not missing and len(runs(items[0]))==2 and len(runs(items[1]))==1
    assert np.array_equal(items[0]['points'],e['points']) and '_trim_ranges' not in e
    assert Settings.model_validate_json(s.model_dump_json()).dxf_line_trims==s.dxf_line_trims
    changed=entity();changed['points']=changed['points']+1;assert annotate([changed],s)[1]==[source_id(e)]

def test_closed_ring_keeps_surface_and_can_hide_part_of_contour():
    e=entity();e.update(closed=True,role='pavement');s=Settings(dxf_line_trims=[cut(e)]);items,_=annotate([e],s)
    assert items[0]['closed'] and np.array_equal(items[0]['points'],e['points']) and len(runs(items[0]))==2

def test_dependency_scope_does_not_invalidate_geometry_or_traffic(tmp_path):
    from app.dependencies import revisions,geometry_cache_key
    a=Settings();b=Settings(dxf_line_trims=[cut(entity())]);ra=revisions(tmp_path,a);rb=revisions(tmp_path,b)
    assert ra['geometry']==rb['geometry'] and ra['traffic']==rb['traffic'] and ra['editor']!=rb['editor'] and ra['video']!=rb['video']
    assert geometry_cache_key(tmp_path,a)==geometry_cache_key(tmp_path,b)

def test_source_cache_selection_is_exact_rejects_stale_and_skips_hidden_span(tmp_path):
    from app.webmap import write_lines
    e=entity();s=Settings();(tmp_path/'config.json').write_text(s.model_dump_json());write_lines(tmp_path,[e]);r=pick(tmp_path,6,.1,1);assert r['source_id']==source_id(e) and r['length_m']==20
    s.dxf_line_trims=[cut(e)];(tmp_path/'config.json').write_text(s.model_dump_json());assert pick(tmp_path,6,0,.1) is None
    assert pick(tmp_path,2,0,.1)['source_id']==r['source_id']
    (tmp_path/'input.dxf').write_bytes(b'fonte alterada')
    with pytest.raises(ValueError,match='desatualizada'):pick(tmp_path,2,0,.1)

def test_frontend_clipping_has_same_endpoints_and_does_not_close_removed_gap():
    root=Path(__file__).resolve().parents[1];code="const m=require(process.argv[1]);const r=m.records({trim_id:'a',p:[[0,0],[10,0],[10,10]],ds:[0,10,20]},[{source_id:'a',start_m:4,end_m:14,start:{x:4,y:0},end:{x:10,y:4}}]);console.log(JSON.stringify(r.map(x=>x.p)))"
    result=subprocess.run(['node','-e',code,str(root/'app/js/98_trim_visual.js')],text=True,capture_output=True,check=True)
    assert json.loads(result.stdout)==[[[0,0],[4,0]],[[10,4],[10,10]]]

def test_trimmed_dxf_is_absent_in_video_but_traffic_and_original_are_preserved(tmp_path):
    from test_v264_presentation import sample
    from app.render import Scene,render
    from app.encoding import validate_mp4,ffmpeg_exe
    from PIL import Image
    d,s=sample(tmp_path,with_guides=True);s.traffic=True;old=Scene(d,s);e=next(e for e in old.items if e['role']=='domain');sid=source_id(e);original=(d/'input.dxf').read_bytes();oldpaths=[p['p'].copy() for p in old.network.paths]
    s.dxf_line_trims=[DxfLineTrim(source_id=sid,layer=e['layer'],start_m=150,end_m=300,length_m=480,start={'x':500160,'y':7800070},end={'x':500310,'y':7800070})];(d/'config.json').write_text(s.model_dump_json());new=Scene(d,s)
    assert len(oldpaths)==len(new.network.paths) and all(np.array_equal(a,b['p']) for a,b in zip(oldpaths,new.network.paths))
    assert (d/'input.dxf').read_bytes()==original and new.geometry_signature!=old.geometry_signature
    assert len(new.domain)==2 and np.array_equal(new.domain[0][-1],[500160,7800070]) and np.array_equal(new.domain[1][0],[500310,7800070])
    out=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs269-artifacts'));out.mkdir(parents=True,exist_ok=True);a,_=old.frame(2.8,view=([500240,7800050],500));b,_=new.frame(2.8,view=([500240,7800050],500));Image.fromarray(a).save(out/'269_antes_trim.png');Image.fromarray(b).save(out/'269_depois_trim.png');assert np.count_nonzero(np.any(a!=b,axis=2))>50
    assert validate_mp4(ffmpeg_exe(),render(d,s),72,1280,720,24)['ok']


def test_hiding_dxf_edge_does_not_release_physical_guide_or_change_routes(tmp_path):
    import ezdxf
    from test_v1425_scene3d import project
    from app.render import Scene
    d,s=project(tmp_path);doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('BORDO');doc.modelspace().add_lwpolyline([(500050,7799980),(500450,7799980)],dxfattribs={'layer':'BORDO'});doc.saveas(d/'input.dxf');s.layers['edge_line']=['BORDO'];s.imagery_pixels=2048
    a=Scene.light(d,s);e=next(e for e in a.items if e['role']=='edge_line');s.dxf_line_trims=[DxfLineTrim(source_id=source_id(e),start_m=100,end_m=200,length_m=400,start={'x':500150,'y':7799980},end={'x':500250,'y':7799980})]
    b=Scene.light(d,s);assert a.network.allowed.equals(b.network.allowed)
    assert len(a.network.paths)==len(b.network.paths) and all(np.array_equal(p['p'],q['p']) for p,q in zip(a.network.paths,b.network.paths))
    assert len(b.network.dxf_edges)==1 and len(b.network.display_edge_lines)==2
    assert all(not (500150<(m[0][0]+m[1][0])/2<500250) for m,src in zip(b.network.markings,b.network.mark_src) if src==-2)


def test_zero_length_reference_does_not_break_visual_rendering():
    from app.presentation import source_segments
    e={'points':np.array([[0.,0.],[0.,0.]]),'closed':False,'role':'domain','layer':'Vazia','holes':[]}
    assert runs(e)==[] and source_segments(e).shape==(0,2,2)


def test_disabled_surface_and_camera_do_not_invalidate_the_same_cad_selection(tmp_path):
    from app.dxf_trim import context
    from app.webmap import write_lines
    s=Settings();f=tmp_path/'config.json';f.write_text(s.model_dump_json());write_lines(tmp_path,[entity()]);before=context(tmp_path)
    s.pavement_areas=[]
    from app.models import PavementArea
    s.pavement_areas=[PavementArea(name='Pista nova (DESAPROPRIAÇÃO)',enabled=False,points=[{'x':0,'y':0},{'x':2,'y':0},{'x':2,'y':2}])]
    s.preview_time_s=1;s.traffic_density=.4;f.write_text(s.model_dump_json())
    assert context(tmp_path)==before and pick(tmp_path,2,0,.1)
