"""2.63: pavimento, pintura métrica e localização PER sem extrapolação."""
import json,os,subprocess
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box,Polygon
from app.models import Settings,PERWork
from app.chainage import Stationing
from app.per_positioning import locate_works
from app.render import Scene


def test_vehicle_body_must_be_entirely_on_pavement_without_changing_routes():
    scene=Scene.__new__(Scene);scene.s=Settings();scene.allowed=box(-100,-100,100,100)
    scene.network=SimpleNamespace(dxf_pavement=box(-50,-2,50,2),paths=['fluxo preservado'])
    assert scene.fits(0,0,np.array([0.,0.]),np.array([1.,0.]),'car')
    assert not scene.fits(0,0,np.array([49.,0.]),np.array([1.,0.]),'car')
    assert not scene.fits(0,0,np.array([0.,1.7]),np.array([1.,0.]),'car')
    scene.s.vehicles_paved_only=False
    assert scene.fits(0,0,np.array([49.,0.]),np.array([1.,0.]),'car')
    assert scene.network.paths==['fluxo preservado']


def test_empty_pavement_hides_vehicle_including_classic_mode():
    scene=Scene.__new__(Scene);scene.s=Settings(traffic_classic=True);scene.allowed=box(-100,-100,100,100);scene.network=SimpleNamespace(dxf_pavement=Polygon())
    assert not scene.fits(0,0,np.array([0.,0.]),np.array([1.,0.]),'car')


def test_appearance_and_per_do_not_invalidate_geometry_cache(tmp_path):
    from app.dependencies import geometry_cache_key,revisions
    s=Settings();before=geometry_cache_key(tmp_path,s);r=revisions(tmp_path,s)
    other=s.model_copy(update={'vehicles_paved_only':False,'signage_emphasis':False,'works':[PERWork(description='Ponte',km_start_m=100,km_end_m=150)]})
    assert geometry_cache_key(tmp_path,other)==before
    assert revisions(tmp_path,other)['presentation']!=r['presentation']


@pytest.mark.parametrize('reverse',[False,True])
def test_per_position_uses_true_stationing_and_does_not_clip_outside_to_endpoint(reverse):
    s=Settings(km_start_m=2000,km_end_m=5000,chainage={"mode":"auto"})
    axis=np.array([[0.,0.],[1000.,0.]])
    st=Stationing(axis,2000,start=[1000,0] if reverse else None,direction=-1 if reverse else 1)
    works=[PERWork(description='Ponte',km_start_m=2250,km_end_m=2250),PERWork(description='Fora',km_start_m=4000,km_end_m=4100),PERWork(description='Parcial',km_start_m=2900,km_end_m=3100)]
    r=locate_works(s,axis,works,st);a,b,c=r['rows']
    assert a['point']==pytest.approx([750 if reverse else 250,0])
    assert b['status']=='outside' and b['point'] is None
    assert c['status']=='partial' and c['visible_km_end_m']==3000 and c['km_end_m']==3100


def test_per_coordinates_and_off_stationing_are_explicit():
    s=Settings(chainage={'mode':'off'},works=[dict(description='Km sem referência',km_start_m=10,km_end_m=20),dict(description='Manual',km_start_m=10,km_end_m=20,x=25,y=40)])
    r=locate_works(s,[[0,0],[100,0]])
    assert r['rows'][0]['status']=='unconfigured' and r['rows'][0]['point'] is None
    assert r['rows'][1]['point']==[25,40] and 'preservadas' in r['rows'][1]['message']


@pytest.mark.parametrize('value',['NaN','Infinity','-1'])
def test_per_import_refuses_nonfinite_or_negative_km(value):
    from app.obras import read_table
    text=f'Obra;Km inicial;Km final\nInválida;{value};{value}\nVálida;0+100;0+200\n'
    rows,warnings=read_table(text.encode(),'obras.csv')
    assert [r['description'] for r in rows]==['Válida'] and warnings


def test_import_preview_api_uses_current_draft_and_preserves_saved_config(tmp_path,monkeypatch):
    from test_v1425_scene3d import project
    from app import store
    from app.server import app
    from fastapi.testclient import TestClient
    d,s=project(tmp_path);s.chainage.mode='auto';(d/'config.json').write_text(s.model_dump_json());monkeypatch.setattr(store,'directory',lambda pid:d);before=(d/'config.json').read_bytes()
    candidate=s.model_dump();candidate['works']=[dict(description='Ponte',km_start_m=100,km_end_m=120),dict(description='Fora',km_start_m=9000,km_end_m=9100)]
    client=TestClient(app);r=client.post('/api/projects/test/obras/localizar',json={'config':candidate})
    assert r.status_code==200,r.text
    data=r.json();assert data['counts']['located']==1 and data['counts']['outside']==1
    assert (d/'config.json').read_bytes()==before
    assert client.post('/api/projects/test/obras/localizar',json={'comando':'apagar'}).status_code==422
    csv='Obra;Km inicial;Km final\nPonte;0+100;0+120\nFora;9+000;9+100\n'
    r=client.post('/api/projects/test/obras/ler',files={'file':('obras.csv',csv.encode(),'text/csv')})
    assert r.status_code==200 and r.json()['localizacao']['counts']['outside']==1
    assert (d/'config.json').read_bytes()==before
    from app.planilha import write_xlsx
    data=write_xlsx([('Obras',[['Obra','Km inicial','Km final'],['Ponte','0+100','0+120'],['Fora','9+000','9+100']],None)])
    r=client.post('/api/projects/test/obras/ler',files={'file':('obras.xlsx',data,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
    assert r.status_code==200 and r.json()['localizacao']['counts']['located']==1
    assert (d/'config.json').read_bytes()==before


def test_metric_paint_has_correct_width_and_keeps_color_groups():
    module=(Path(__file__).resolve().parents[1]/'app/webgl/paint.mjs').as_uri()
    code=f"import {{markingTriangles}} from {json.dumps(module)};console.log(JSON.stringify(markingTriangles([{{p:[0,0,0,10,0,0],yellow:true}}],.15)));"
    result=json.loads(subprocess.run(['node','--input-type=module','-e',code],capture_output=True,text=True,check=True).stdout)
    p=np.array(result['yellow']).reshape(-1,3);assert p.shape==(6,3) and np.ptp(p[:,2])==pytest.approx(.15) and not result['white']
    triangles=p.reshape(-1,3,3);assert (np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])[:,1]>0).all(), 'A pintura precisa ser visível por cima da pista.'


def road_gap_project(tmp_path):
    import ezdxf
    from app.project_state import save_config
    from app.native_axes import axis_fingerprint
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');ms=doc.modelspace()
    axis=[[500000.,7800000.],[500400.,7800000.]];ms.add_lwpolyline(axis,dxfattribs={'layer':'EIXO'})
    for a,b in [(0,140),(260,400)]:
        h=ms.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000+a,7799990),(500000+b,7799990),(500000+b,7800010),(500000+a,7800010)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    route=dict(id='R',name='Eixo com vazio',points=[dict(x=x,y=y) for x,y in axis],sections_only=True,section_surface=True,cross_sections=[dict(id='S',start_m=0,end_m=400,left=[dict(width_m=3.5)],right=[dict(width_m=3.5)])])
    s=Settings(layers={'axis':['EIXO'],'pavement':['PAVIMENTO']},route_directions={'axis:'+axis_fingerprint(axis,'EIXO'):'off'},route_alignments=[route],derive_traffic_paths=False,traffic_bridge_gaps=False,imagery='neutral',hydrography=False,width=1280,fps=24,duration_s=3,render_workers=1,coordinates_confirmed=True)
    save_config(tmp_path,s.model_dump());return s


def test_paved_only_keeps_flow_geometry_and_removes_3d_gap_interpolation(tmp_path):
    from app.scene3d import build
    from app.vehicle_safety import body
    s=road_gap_project(tmp_path);scene=Scene.light(tmp_path,s);other=Scene.light(tmp_path,s.model_copy(update={'vehicles_paved_only':False}))
    assert scene.network.paths and len(scene.network.paths)==len(other.network.paths)
    assert all(np.array_equal(a['p'],b['p']) for a,b in zip(scene.network.paths,other.network.paths))
    data=build(tmp_path,s);assert data['vehicles'] and data['marking_width_m']==.15
    area=scene.network.dxf_pavement.buffer(.001);origin=data['origin_crs']
    for vehicle in data['vehicles']:
        sides=[]
        for t,x,y,z,hx,hy,hz in vehicle['samples']:
            p=[origin[0]+x,origin[1]-z];assert area.covers(body(p,[hx,-hz],vehicle['length'],vehicle['width']))
            sides.append(p[0]<500200)
        assert all(sides) or not any(sides),'Uma trajetória 3D interpolaria por cima do vazio.'


def test_real_artistic_video_decodes_with_pavement_guard_and_paint(tmp_path):
    from app.render import render
    from app.encoding import ffmpeg_exe,validate_mp4
    from PIL import Image
    s=road_gap_project(tmp_path);s.natural_materials_only=True;scene=Scene(tmp_path,s)
    assert any(list(scene.traffic_iter(t)) for t in (0,1,2))
    evidence=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rodovia263-artifacts'));evidence.mkdir(parents=True,exist_ok=True)
    frames=[]
    for t in (0,1.5,2.9):
        frame,_=scene.frame(t,view=([500200,7800000],450));Image.fromarray(frame).save(evidence/f'263_apresentacao_{t}.png');frames.append(frame)
    assert not np.array_equal(frames[0],frames[-1])
    output=render(tmp_path,s);result=validate_mp4(ffmpeg_exe(),output,72,1280,720,24);assert result['ok']
    (evidence/'263_video.json').write_text(json.dumps(result,indent=2)+'\n')
