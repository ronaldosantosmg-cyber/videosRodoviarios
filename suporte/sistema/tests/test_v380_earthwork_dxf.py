"""Taludes classificados pelo cadastro/cor DXF e apresentados sem alterar contornos."""
from types import SimpleNamespace as S
import numpy as np
import ezdxf
import pytest
from shapely.geometry import Polygon
from app.models import Settings
from app.geometry import analyze, earthwork_source_rgb, resolve_earthworks
from app.earthworks import earthwork_style


def project(folder):
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');doc.layers.new('TALUDE',dxfattribs={'color':3})
    m=doc.modelspace();m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799993),(500300,7799993),(500300,7800007),(500000,7800007)],is_closed=True)
    for x,color in [(500040,None),(500160,0xb03527)]:
        attrs={'layer':'TALUDE'}
        if color is not None:attrs['true_color']=color
        h=m.add_hatch(color=256,dxfattribs=attrs);h.paths.add_polyline_path([(x,7800010),(x+65,7800010),(x+65,7800038),(x,7800038)],is_closed=True)
        h.paths.add_polyline_path([(x+20,7800020),(x+30,7800020),(x+30,7800030),(x+20,7800030)],is_closed=True,flags=0)
    doc.saveas(folder/'input.dxf')
    return Settings(width=1280,duration_s=3,fps=24,coordinates_confirmed=True,imagery='neutral',hydrography=False,traffic=False,
                    layers={'axis':['EIXO'],'pavement':['PAVIMENTO'],'earthwork':['TALUDE']},route_directions={'layer:EIXO':'forward'},render_profile='rapido')


def test_generic_earthworks_obey_dxf_colors_and_keep_holes(tmp_path):
    settings=project(tmp_path);items,*_=analyze(tmp_path,settings)
    earth=[e for e in items if e['role'] in ('cut','fill')]
    assert {e['role'] for e in earth}=={'cut','fill'}
    assert all(e['earthwork_type_source']=='dxf_color' and len(e['holes'])==1 for e in earth)
    assert all('asset_material' not in e for e in earth)  # Solo genérico não sobrepõe grama do talude.
    assert all(Polygon(e['points'],e['holes']).area==1720 for e in earth)


def test_true_color_and_entity_aci_override_layer_color():
    doc=ezdxf.new();doc.layers.new('TALUDE',dxfattribs={'color':3,'true_color':0x90ba60})
    entity=doc.modelspace().add_line((0,0),(10,0),dxfattribs={'layer':'TALUDE'})
    assert earthwork_source_rgb(entity,doc)==(144,186,96)
    entity.dxf.color=1
    assert earthwork_source_rgb(entity,doc)==(255,0,0)
    entity.dxf.true_color=0x9cbd75
    assert earthwork_source_rgb(entity,doc)==(156,189,117)


def test_color_never_overrides_registered_cut_or_classifies_arbitrary_green_area():
    points=np.array([[0,0],[10,0],[10,10],[0,10]],float)
    cut=dict(role='cut',layer='Escolha manual',points=points,earthwork_source_color='#00ff00')
    median=dict(role='median',layer='CANTEIRO',points=points,earthwork_source_color='#ff0000')
    resolve_earthworks([cut,median],[])
    assert cut['role']=='cut' and median['role']=='median'


def test_ambiguous_neutral_earthwork_is_reported_without_inventing_type():
    entity=dict(role='earth_pending',layer='TALUDE',points=np.array([[0,0],[10,0]]),earthwork_source_color='#0000ff')
    warnings=[];resolve_earthworks([entity],warnings)
    assert entity['role']=='earthwork' and entity['earthwork_type_source']=='unresolved' and warnings


@pytest.mark.parametrize('role,rgb',[('fill',(156,189,117)),('cut',(183,105,84))])
def test_grass_palette_keeps_mask_hole_and_manual_color(role,rgb):
    mask=np.zeros((70,90),np.uint8);mask[5:65,5:85]=255;mask[25:40,30:45]=0
    color,alpha=earthwork_style(mask,np.zeros_like(mask),role,.5,look='textura')
    assert tuple(color[15,20])==rgb and not alpha[25:40,30:45].any() and not alpha[mask==0].any()
    manual,_=earthwork_style(mask,np.zeros_like(mask),role,.5,look='textura',base_color='#7d915a')
    assert tuple(manual[15,20])==(125,145,90)


def test_earthworks_reach_preview_3d_and_decoded_mp4(tmp_path):
    from pathlib import Path
    import os,json
    from PIL import Image
    from app.render import Scene,render
    from app.scene3d import build
    from app.encoding import ffmpeg_exe,validate_mp4
    settings=project(tmp_path);settings.render_workers=1;settings.encoder='cpu'
    (tmp_path/'config.json').write_text(settings.model_dump_json(),encoding='utf-8')
    scene=Scene(tmp_path,settings)
    frame,_=scene.frame(2.8,view=([500140,7800020],310))
    output=Path(os.environ.get('VISUAL_ARTIFACTS',str(tmp_path/'artifacts')));output.mkdir(parents=True,exist_ok=True)
    Image.fromarray(frame).save(output/'taludes_dxf_1280.png')
    data=build(tmp_path,settings)
    meshes={m['role']:m for m in data['meshes'] if m['role'] in ('cut','fill')}
    assert meshes['fill']['color']=='#9cbd75' and meshes['cut']['color']=='#b76954'
    assert all('asset_material' not in mesh for mesh in meshes.values())
    assert validate_mp4(ffmpeg_exe(),render(tmp_path,settings),72,1280,720,24)['ok']
    metadata=json.loads((tmp_path/'video.json').read_text(encoding='utf-8'))
    assert metadata['width']==1280 and metadata['fps']==24
