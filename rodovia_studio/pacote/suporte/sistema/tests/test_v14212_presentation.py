import json,io
from pathlib import Path
import numpy as np
import pytest
import tifffile
from PIL import Image
from app.models import Settings
from app.image_context import run,source_signature,accepted_items
from app.image_context_models import ImageRequest
from app.render import Scene,render
from app.scene3d import build
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot


def local_project(tmp_path):
    (tmp_path/'imagem_local').mkdir();a=np.full((64,64,3),100,np.uint8);a[5:28,5:28]=[200,65,35];a[35:60,5:28]=[25,145,30]
    keys=(1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,31983)
    tifffile.imwrite(tmp_path/'imagem_local/aerea.tif',a,photometric='rgb',extratags=[(33550,'d',3,(2.,2.,0.),False),(33922,'d',6,(0.,0.,0.,500000.,7800128.,0.),False),(34735,'H',len(keys),keys,False)])
    s=Settings(local_imagery=dict(image='aerea.tif',crs='EPSG:31983'),imagery='local');(tmp_path/'config.json').write_text(s.model_dump_json())
    req=ImageRequest(bounds=[500000,7800000,500128,7800128],crs=s.crs,pixels=512).model_dump();return s,req,a


def test_local_analysis_without_dxf_retains_capture_and_rejects_stale_source(tmp_path):
    s,req,_=local_project(tmp_path);run(tmp_path,s,req,lambda *a:None,lambda:False,'job-test')
    result=json.loads((tmp_path/'contexto_imagem/resultado.json').read_text());assert result['features'] and result['job_id']=='job-test'
    assert (tmp_path/'contexto_imagem/fontes'/result['capture']).is_file()
    assert result['signature']==source_signature(tmp_path,s,req)
    s.local_imagery.shift_x=2;assert source_signature(tmp_path,s,req)!=result['signature']


def test_online_analysis_uses_the_same_local_pipeline_without_sending_the_photo(tmp_path,monkeypatch):
    s,req,a=local_project(tmp_path);req['source']='web'
    calls=[]
    def capture(*args,**kwargs):calls.append(args[1].imagery);return np.repeat(np.repeat(a,8,0),8,1),req['bounds'],'Fonte on-line de teste'
    monkeypatch.setattr('app.imagery.mosaic',capture)
    run(tmp_path,s,req,lambda *a:None,lambda:False,'web-job')
    result=json.loads((tmp_path/'contexto_imagem/resultado.json').read_text());assert calls==['esri'] and result['attribution']=='Fonte on-line de teste'
    assert (tmp_path/'contexto_imagem/fontes'/result['capture']).is_file()


def test_cancel_or_changed_georeference_cannot_publish_new_suggestions(tmp_path):
    s,req,_=local_project(tmp_path)
    with pytest.raises(InterruptedError):run(tmp_path,s,req,lambda *a:None,lambda:True)
    assert not (tmp_path/'contexto_imagem/resultado.json').exists()
    changed=False
    def status(p,msg):
        nonlocal changed
        if p>.4 and not changed:
            other=s.model_copy(deep=True);other.local_imagery.shift_x=5;(tmp_path/'config.json').write_text(other.model_dump_json());changed=True
    with pytest.raises(ValueError,match='mudaram'):run(tmp_path,s,req,status,lambda:False)
    assert not (tmp_path/'contexto_imagem/resultado.json').exists()


def features():
    return [dict(id='building',name='Edifício revisado',role='building',points=[dict(x=500100,y=7800040),dict(x=500140,y=7800040),dict(x=500140,y=7800070),dict(x=500100,y=7800070)],material='roof_tile',wall_material='masonry',height_m=8,reviewed=True),dict(id='water',name='Água revisada',role='water',points=[dict(x=500300,y=7800030),dict(x=500350,y=7800030),dict(x=500350,y=7800060),dict(x=500300,y=7800060)],material='water',reviewed=True)]


def test_approved_masks_have_textures_walls_height_and_no_technical_lines_in_video(tmp_path):
    d,s=project(tmp_path,False);s.image_features=__import__('pydantic').TypeAdapter(list[__import__('app.image_context_models',fromlist=['ImageFeature']).ImageFeature]).validate_python(features());(d/'config.json').write_text(s.model_dump_json())
    scene=Scene(d,s);image,_=scene.frame(1,overview=True)
    data=build(d,s);context=[m for m in data['meshes'] if m['id'].startswith('image-')]
    assert {'building','water'}<={m['role'] for m in context}
    assert any(m['asset_material']=='masonry' for m in context) and any(m['asset_material']=='roof_tile' for m in context)
    assert max(np.array(m['positions']).reshape(-1,3)[:,1].max() for m in context if m['role']=='building')==pytest.approx(8)
    assert len({m['id'] for m in data['meshes']})==len(data['meshes'])
    import os
    if os.environ.get('VISUAL_ARTIFACTS'):Image.fromarray(image).save(Path(os.environ['VISUAL_ARTIFACTS'])/'14212_05_mascaras_texturas_2d.png')
    render(d,s)
    from app.encoding import validate_mp4,ffmpeg_exe
    assert validate_mp4(ffmpeg_exe(),d/'video.mp4',72,1280,720,24)['ok']


def test_turn_and_hazard_lamps_are_visible_in_2d_and_real_webgl(gl_page,live):
    from app.traffic_indicators import draw
    from types import SimpleNamespace
    class Sim:
        info={1:(0,'car',(0,1,0))}
        def indicators(self,t):return {1:3}
        def vehicles_ex(self,t):yield np.array([0.,0.]),np.array([1.,0.]),1,(0,1,0),0
    scene=SimpleNamespace(_sim=Sim(),W=400,H=200,screen=lambda points,cam,width:np.asarray(points)*10+[200,100])
    lit=np.zeros((200,400,3),np.uint8);off=lit.copy();draw(scene,lit,0,np.zeros(2),40);draw(scene,off,.4,np.zeros(2),40)
    assert np.any((lit[:,:,0]>200)&(lit[:,:,1]>100)&(lit[:,:,2]<100)) and not off.any()
    p=gl_page;d=live[2]/live[1];s=Settings.model_validate_json((d/'config.json').read_text())
    values=s.model_dump();values.update(duration_s=30,image_features=features(),derive_traffic_paths=False,route_directions={'0':'off'},traffic_density=4,route_alignments=[dict(id='work-route',name='Controle visual',points=[dict(x=500050,y=7800000),dict(x=500450,y=7800000)],type='simples',lanes=1,taper_m=40)],alternating_zones=[dict(id='work',route_id='work-route',start_m=150,end_m=250)])
    response=p.request.put(live[0]+'/api/projects/'+live[1]+'/config',data=values);assert response.ok,response.text()
    p.evaluate('(id)=>load(id)',live[1]);p.wait_for_function('!task && !taskRequestPending && !!editor && !RodoviaFlowStudy.stale',timeout=60000)
    assert p.evaluate('M.alternating_zones.length')==1
    job=p.evaluate("start('scene3d')");assert job and job['state']=='done'
    response=p.request.get(live[0]+'/api/projects/'+live[1]+'/scene3d.json');assert response.ok,response.text();data=response.json()
    times=[row[0] for vehicle in data['vehicles'] for row in vehicle.get('indicators',[]) if row[1]==3 and int(row[0]*2.5)%2==0]
    assert times,{key:data['simulation_report'].get(key) for key in ['vehicles','alternating_traffic','max_waiting_at_entries','narrow_corridor_admission_holds']}
    open3d(p);p.evaluate('(t)=>Rodovia3D.setTime(t)',times[0])
    assert p.evaluate("Rodovia3D.stats().vehicles")>0
    assert p.evaluate("Rodovia3D.stats().activeRoadIndicators")>0
    error=p.evaluate("async data=>{const {validateScene}=await import('/webgl/viewer.mjs');data.vehicles[0].indicators=[[0,Infinity]];try{validateScene(data);return ''}catch(e){return e.message}}",data)
    assert error=='Sinalização do veículo inválida.'
    screenshot(p,'14212_06_edificacoes_3d_pisca_alerta')
