"""Prioridade de fases e revelação comum no vídeo, sem alterar a engenharia."""
import json,os
from pathlib import Path
import numpy as np
import pytest
from app.models import Settings
from app.presentation import is_existing,reveal_mask,clip_reveal


def project(tmp_path):
    import ezdxf
    doc=ezdxf.new();m=doc.modelspace()
    def layer(n):
        if n not in doc.layers:doc.layers.new(n)
    def area(n,pts):
        layer(n);h=m.add_hatch(dxfattribs={'layer':n});h.paths.add_polyline_path(pts,is_closed=True)
    layer('EIXO');m.add_lwpolyline([(500000,7800000),(501000,7800000)],dxfattribs={'layer':'EIXO'})
    area('Pista existente',[(500000,7799985),(501000,7799985),(501000,7800015),(500000,7800015)])
    area('Pista projetada',[(500100,7799990),(500900,7799990),(500900,7800010),(500100,7800010)])
    area('OAE existente',[(500380,7799980),(500420,7799980),(500420,7800020),(500380,7800020)])
    area('Edificação projetada',[(500800,7800040),(500840,7800040),(500840,7800080),(500800,7800080)])
    area('Edificação existente',[(500900,7800040),(500940,7800040),(500940,7800080),(500900,7800080)])
    layer('Domínio projetado');m.add_lwpolyline([(500010,7800120),(500990,7800120)],dxfattribs={'layer':'Domínio projetado'})
    doc.saveas(tmp_path/'input.dxf')
    s=Settings(layers={'axis':['EIXO'],'existing_pavement':['Pista existente'],'pavement':['Pista projetada'],'oae':['OAE existente'],'building':['Edificação projetada','Edificação existente'],'domain':['Domínio projetado']},width=1280,fps=24,duration_s=3,imagery='neutral',hydrography=False,traffic=False,coordinates_confirmed=True,imagery_pixels=2048,detail_textures=False,render_profile='rapido',dxf_lead_m=0,direction_badge=False,presentation_guides=True,frozen_layers=['Pista projetada'])
    (tmp_path/'config.json').write_text(s.model_dump_json());return tmp_path,s


def pixel(scene,p,cam,width):return tuple(np.rint(scene.screen(np.asarray([p]),np.asarray(cam),width)[0])[::-1].astype(int))


def test_existing_semantics_and_invalid_options_are_explicit():
    assert Settings().existing_visibility=='initial'
    assert is_existing({'role':'existing_pavement'}) and is_existing({'role':'shoulder','layer':'Acostamento EXISTENTE'})
    assert is_existing({'role':'oae','oae_kind':'existente'})
    assert not is_existing({'role':'shoulder','layer':'ACOSTAMENTO PROJETADO'})
    assert not is_existing({'layer':'Existente','presentation_state':'projected'})
    assert not is_existing({'layer':'Pista nova sobre existente'})
    with pytest.raises(ValueError):Settings(existing_visibility='qualquer')


def test_presentation_option_does_not_rebuild_geometry_or_traffic(tmp_path):
    from app.dependencies import revisions,geometry_cache_key
    a=Settings();b=a.model_copy(update={'existing_visibility':'progressive'})
    x,y=revisions(tmp_path,a),revisions(tmp_path,b)
    assert x['geometry']==y['geometry'] and x['traffic']==y['traffic'] and x['presentation']!=y['presentation']
    assert geometry_cache_key(tmp_path,a)==geometry_cache_key(tmp_path,b)


def test_reveal_is_finite_monotonic_and_keeps_endpoint(tmp_path):
    from app.render import Scene
    d,s=project(tmp_path);sc=Scene(d,s);cam=np.array([500500,7800000]);w=1200
    a=reveal_mask(sc,cam,w,.2);b=reveal_mask(sc,cam,w,.6)
    assert np.all(b>=a) and np.isfinite(b).all()
    assert not a[pixel(sc,[500850,7800000],cam,w)] and b[pixel(sc,[500350,7800000],cam,w)]==1
    assert reveal_mask(sc,cam,w,1).min()==1
    with pytest.raises(ValueError):reveal_mask(sc,cam,float('nan'),.5)
    blank=np.zeros((sc.H,sc.W,3),np.uint8);colored=np.full_like(blank,255)
    assert (clip_reveal(sc,colored,blank,cam,w,.2)[a==0]==0).all()


def test_project_over_existing_in_mosaic_detail_cache_and_worker_snapshot(tmp_path):
    from app.render import Scene
    from app.detail import Detail
    from app import visual
    d,s=project(tmp_path);sc=Scene(d,s)
    pt=np.array([[500400,7800000.]]) # projected asphalt must cover an existing OAE
    x,y=np.rint(sc.worldpx(pt)[0]).astype(int)
    assert sc.surface[y,x]==visual.SURF['pavement'] and sc.existing_surface[y,x]!=visual.SURF['pavement']
    detail=Detail(sc,.5);i=int((pt[0,0]-detail.x0)//(1024*detail.R));j=int((detail.y1-pt[0,1])//(1024*detail.R));ov,surf=detail.overlay_tile(i,j);x,y=np.rint(detail.worldpx(i,j)(pt)[0]).astype(int)
    assert surf[y,x]==visual.SURF['pavement']
    cached=Scene(d,s);assert cached.geometry_cache_hit and np.array_equal(sc.existing_overlay,cached.existing_overlay)
    folder=tmp_path/'worker';key=sc.snapshot(folder);worker=Scene.load_snapshot(folder,key=key)
    assert np.array_equal(worker.existing_surface,sc.existing_surface)
    assert (d/'input.dxf').read_bytes()==(cached.directory/'input.dxf').read_bytes()


def test_all_project_features_reveal_existing_can_be_initial_or_progressive(tmp_path):
    from app.render import Scene
    from PIL import Image
    d,s=project(tmp_path);sc=Scene(d,s);cam=np.array([500500,7800040]);width=1200
    sc.pose=lambda t:(cam,width,float(t),None,'tour')
    early,_=sc.frame(.1);middle,_=sc.frame(.5);final,_=sc.frame(1.)
    road=pixel(sc,[500850,7800000],cam,width);building=pixel(sc,[500820,7800060],cam,width);oldbuilding=pixel(sc,[500920,7800060],cam,width)
    assert np.linalg.norm(early[road].astype(float)-final[road])>15
    assert np.linalg.norm(early[building].astype(float)-final[building])>20
    assert np.linalg.norm(early[oldbuilding].astype(float)-final[oldbuilding])<5
    sc.s.existing_visibility='progressive';hidden,_=sc.frame(.1)
    assert np.linalg.norm(hidden[oldbuilding].astype(float)-early[oldbuilding])>20
    assert np.linalg.norm(hidden[road].astype(float)-early[road])>20
    # No projected domain, even when technical guides are requested.
    domain=pixel(sc,[500850,7800120],cam,width)
    assert np.linalg.norm(hidden[domain].astype(float)-final[domain])>20
    out=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs270-artifacts'));out.mkdir(parents=True,exist_ok=True)
    for name,image in [('270_inicio_existente',early),('270_meio',middle),('270_final',final),('270_existente_progressivo',hidden)]:Image.fromarray(image).save(out/(name+'.png'))


def test_short_video_and_classic_mode_do_not_bypass_reveal(tmp_path):
    from app.render import Scene
    d,s=project(tmp_path);s.traffic_classic=True;sc=Scene(d,s)
    sc.frame(.3);assert sc._reveal_view_chains.max()>0
    before=sc._reveal_view_chains.copy();sc.frame(2.8)
    assert np.isfinite(before).all() and sc.reveal_opacity==1


def test_video_export_is_decodable_and_reveal_changes_frames(tmp_path):
    from app.render import render
    from app.encoding import validate_mp4,ffmpeg_exe
    from PIL import Image
    import subprocess
    d,s=project(tmp_path);s.render_workers=1;(d/'config.json').write_text(s.model_dump_json());video=render(d,s)
    info=validate_mp4(ffmpeg_exe(),video,72,1280,720,24);assert info['ok']
    frames=[]
    for second in (.1,2.9):
        r=subprocess.run([ffmpeg_exe(),'-v','error','-ss',str(second),'-i',str(video),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
        frames.append(np.frombuffer(r.stdout,np.uint8).reshape(720,1280,3))
    assert np.abs(frames[0].astype(float)-frames[1]).mean()>1
    out=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs270-artifacts'));out.mkdir(parents=True,exist_ok=True)
    (out/'270_video.json').write_text(json.dumps(info,default=str))
    Image.fromarray(frames[0]).save(out/'270_video_inicio.png');Image.fromarray(frames[1]).save(out/'270_video_final.png')


def test_dynamic_features_share_the_front_and_night_preserves_ambient(tmp_path,monkeypatch):
    from app.render import Scene
    from app import engineering_assets,transport_render,traffic_indicators
    import cv2
    d,s=project(tmp_path);sc=Scene(d,s);cam=np.array([500500,7800040]);width=1200;sc.pose=lambda t:(cam,width,float(t),None,'tour')
    calls=[]
    def marker(scene,image,*args):
        if scene is not sc:return
        calls.append(True);q=scene.screen(np.array([[500850,7800100.]]),cam,width)[0].astype(int);cv2.circle(image,tuple(q),5,(255,0,128),-1)
    monkeypatch.setattr(engineering_assets,'draw_map',marker);monkeypatch.setattr(transport_render,'draw_static',marker);monkeypatch.setattr(transport_render,'draw_dynamic',marker);monkeypatch.setattr(traffic_indicators,'draw',marker)
    early,_=sc.frame(.1);late,_=sc.frame(1.);p=pixel(sc,[500850,7800100],cam,width)
    assert len(calls)>=8 and tuple(late[p])==(255,0,128) and tuple(early[p])!=(255,0,128)
    sc.s.day_night='night';night,_=sc.frame(.1)
    assert night[p].mean()<early[p].mean()*.7


def test_3d_presentation_lift_and_colors_keep_projected_above_existing(tmp_path):
    from app.scene3d import build
    d,s=project(tmp_path);data=build(d,s)
    new=next(m for m in data['meshes'] if m['role']=='pavement');old=next(m for m in data['meshes'] if m['role']=='existing_pavement');oae=next(m for m in data['meshes'] if m['role']=='oae')
    assert new['presentation_state']=='projected' and old['presentation_state']=='existing'
    assert min(new['positions'][1::3])>max(oae['positions'][1::3])
    assert new['color']!=old['color']
