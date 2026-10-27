import json,os
from pathlib import Path
import ezdxf
import numpy as np
from PIL import Image
from app.models import Settings
from app.render import Scene,render
from app.scene3d import build
from app.encoding import validate_mp4,ffmpeg_exe


def test_typed_nodes_use_existing_2d_3d_and_decoded_mp4(tmp_path):
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    m.add_lwpolyline([(0,0),(400,0)],dxfattribs={'layer':'EIXO'})
    hatch=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});hatch.paths.add_polyline_path([(-30,-12),(430,-12),(430,12),(-30,12)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    s=Settings(width=1280,fps=24,duration_s=3,imagery='neutral',imagery_pixels=2048,coordinates_confirmed=True,hydrography=False,signage_detail='basic',camera_mode='trafego',view_width_m=180,render_workers=1,route_directions={'0':'off'},route_alignments=[dict(id='P',name='Principal orientada pelos nós',type='simples',flow_role='principal',flow_start='saida',flow_end='entrada',points=[dict(x=0,y=0),dict(x=400,y=0)])])
    (tmp_path/'config.json').write_text(s.model_dump_json());original=(tmp_path/'input.dxf').read_bytes()
    scene=Scene(tmp_path,s);sim=scene.traffic();assert sim.spawned>0
    assert all(scene.network.edges[k].get('route_dir')=='r' for p in scene.network.paths for k in p['edges'])
    image,meta=scene.frame(1);assert meta['traffic_visibility']['drawn']>0
    target=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));target.mkdir(parents=True,exist_ok=True)
    Image.fromarray(image).save(target/'14231_fluxo_decrescente_nos.png')
    path=render(tmp_path,s);video=validate_mp4(ffmpeg_exe(),path,72,1280,720,24);assert video['ok']
    data=build(tmp_path,s);assert data['vehicles'] and data['simulation_report']['flow_balance']['conserved']
    assert (tmp_path/'input.dxf').read_bytes()==original
    (target/'video_nos.json').write_text(json.dumps(dict(decoded=video,balance=data['simulation_report']['flow_balance'],scope='Percurso decrescente por nós, mesmos motores 2D, 3D e MP4; fonte CAD preservada.'),ensure_ascii=False,indent=2))
