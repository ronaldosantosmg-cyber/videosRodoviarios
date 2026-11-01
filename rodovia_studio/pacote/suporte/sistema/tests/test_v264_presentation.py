"""Regressões da revisão visual: estabilidade temporal, detalhe e contornos."""
import json,os
from pathlib import Path
import numpy as np
import pytest
from scipy.spatial import cKDTree
from app.models import Settings
from app.presentation import guides,repair_reveal_stations
from app.earthworks import natural_style
from app import relevo


def test_quality_modes_are_explicit_and_invalid_modes_refused():
    assert Settings().realism_profile=='ultra_realista'
    assert Settings(realism_profile='realista').realism_profile=='realista'
    with pytest.raises(ValueError):Settings(realism_profile='qualquer')
    assert not guides(Settings()) and guides(Settings(style_profile='tecnico'))
    assert guides(Settings(presentation_guides=True))


def test_same_world_point_does_not_flash_with_small_zoom_change():
    colors=[]
    for px in (.1999,.2,.2001):
        color=np.full((64,64,3),95,np.uint8)
        colors.append(relevo.acabar(color,'existing_pavement',730000.123-px/2,7824000.456+px/2,px))
    assert np.ptp(np.array([c[0,0] for c in colors]),axis=0).max()<=2
    delta=float(np.abs(colors[0].astype(float)-colors[1]).mean())
    assert delta<1.,delta


def test_lod_transition_is_continuous_not_an_octave_switch():
    X,Y=np.meshgrid(np.linspace(10,30,60),np.linspace(20,40,60))
    a=relevo.fbm(X,Y,4.,4,.9999,11);b=relevo.fbm(X,Y,4.,4,1.0001,11)
    assert np.max(np.abs(a-b))<.002
    for invalid in (0,-1,float('nan'),float('inf')):
        with pytest.raises(ValueError):relevo.stable_noise(X,Y,.1,invalid)


def test_realistic_has_less_micro_detail_and_keeps_manual_material_color():
    c=np.full((128,128,3),(90,110,120),np.uint8)
    ultra=relevo.acabar(c,'existing_pavement',123,456,.04)
    real=relevo.acabar(c,'existing_pavement',123,456,.04,quality='realista')
    assert real.std((0,1)).mean()<ultra.std((0,1)).mean()*.8
    assert np.all(np.abs(real.mean((0,1))-c[0,0])<30)


def test_fill_green_cut_red_and_manual_mapping_preserved():
    m=np.ones((30,30),np.uint8)*255;l=np.zeros_like(m)
    cut,_=natural_style(m,l,'cut',.2);fill,_=natural_style(m,l,'fill',.2)
    assert fill[15,15,1]>fill[15,15,0]+20
    assert cut[15,15,0]>cut[15,15,1]+30
    manual,_=natural_style(m,l,'fill',.2,base_color='#3344aa')
    assert manual[15,15].tolist()==[51,68,170]


def test_detail_reveal_recovers_only_drawn_pixels_missing_in_coarse_map():
    alpha=np.array([[1.,0.,1.],[1.,1.,1.]])
    stations=np.array([[0,65535,65535],[65535,32000,65535]],np.uint16)
    points=np.array([[0.,0.],[1.,0.],[2.,0.],[0.,1.],[1.,1.],[2.,1.]])
    chains=np.array([0.,1.,2.,0.,1.,2.]);tree=cKDTree(points)
    out=repair_reveal_stations(alpha,stations,np.array([[1,0,0],[0,1,0]]),tree,chains,2.)
    assert out[0,0]==0 and out[0,1]==65535 and out[0,2]==65534
    assert out[1,0]==0 and out[1,1]==32000
    assert stations[0,2]==65535  # fonte/cache não é modificado


def test_appearance_changes_do_not_rebuild_traffic_or_geometry(tmp_path):
    from app.dependencies import revisions,geometry_cache_key
    s=Settings();a=revisions(tmp_path,s)
    b=s.model_copy(update={'realism_profile':'realista','presentation_guides':True})
    r=revisions(tmp_path,b)
    assert a['traffic']==r['traffic'] and a['geometry']==r['geometry']
    assert a['presentation']!=r['presentation'] and geometry_cache_key(tmp_path,s)==geometry_cache_key(tmp_path,b)


def sample(tmp_path,profile='ultra_realista',with_guides=False):
    from test_v1425_scene3d import project
    import ezdxf
    d,s=project(tmp_path,traffic=False)
    doc=ezdxf.readfile(d/'input.dxf');model=doc.modelspace()
    for name,y in [('CORTE',7800022),('ATERRO',7799958)]:
        doc.layers.new(name);h=model.add_hatch(dxfattribs={'layer':name});h.paths.add_polyline_path([(500020,y),(500480,y),(500480,y+15),(500020,y+15)],is_closed=True)
    doc.layers.new('DOMINIO');model.add_lwpolyline([(500010,7800070),(500490,7800070)],dxfattribs={'layer':'DOMINIO'});doc.saveas(d/'input.dxf')
    s.layers.update(cut=['CORTE'],fill=['ATERRO'],domain=['DOMINIO'])
    s.realism_profile=profile;s.presentation_guides=with_guides;s.earthwork_look='textura';s.water_animated=False;s.render_workers=1;s.imagery_pixels=2048;s.detail_textures=True;s.progress_indicator=False;s.direction_badge=False
    (d/'config.json').write_text(s.model_dump_json());return d,s


def test_real_scene_hides_only_technical_guides_and_retains_registered_dxf(tmp_path):
    from app.render import Scene
    from PIL import Image
    d,s=sample(tmp_path);scene=Scene(d,s);cam=np.array([500250,7800010]);width=650
    a=scene.draw_base(cam,width,1.);before=[(e['role'],e['points'].copy()) for e in scene.items]
    scene.s.presentation_guides=True;b=scene.draw_base(cam,width,1.)
    assert np.count_nonzero(np.any(a!=b,axis=2))>100
    for old,e in zip(before,scene.items):assert old[0]==e['role'] and np.array_equal(old[1],e['points'])
    # O desenho e suas máscaras continuam presentes, mesmo com referências ocultas.
    assert (scene.surface>0).any() and scene.has_surface
    if os.environ.get('VISUAL_ARTIFACTS'):
        out=Path(os.environ['VISUAL_ARTIFACTS']);out.mkdir(parents=True,exist_ok=True);Image.fromarray(a).save(out/'264_artistico_sem_contornos.png');Image.fromarray(b).save(out/'264_contornos_opcionais.png')


def test_profiles_produce_decodable_video_and_comparable_frames(tmp_path):
    from app.render import Scene,render
    from app.encoding import ffmpeg_exe,validate_mp4
    from PIL import Image
    evidence=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs264-artifacts'));evidence.mkdir(parents=True,exist_ok=True)
    reports={}
    for mode in ('realista','ultra_realista'):
        folder=tmp_path/mode;folder.mkdir();d,s=sample(folder,mode);s.traffic=True;(d/'config.json').write_text(s.model_dump_json())
        scene=Scene(d,s);assert any(list(scene.traffic_iter(t)) for t in (0,1,2));frame,_=scene.frame(2.8,view=([500250,7800010],650));Image.fromarray(frame).save(evidence/f'264_{mode}.png')
        output=render(d,s);result=validate_mp4(ffmpeg_exe(),output,72,1280,720,24);assert result['ok'];reports[mode]=result
    (evidence/'264_videos.json').write_text(json.dumps(reports,indent=2)+'\n')
