import json
import os
from pathlib import Path
import cv2
import ezdxf
import numpy as np
from PIL import Image
from app.models import Settings
from app.render import render


def test_export_decodes_all_frames_and_has_front_rear_audit(tmp_path):
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    m.add_lwpolyline([(500050,7800000),(500450,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799980),(500500,7799980),(500500,7800020),(500000,7800020)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    s=Settings(layers={'axis':['EIXO'],'pavement':['PAVIMENTO']},width=1280,fps=24,duration_s=3,imagery='neutral',coordinates_confirmed=True,hydrography=False,render_workers=1)
    output=render(tmp_path,s);cap=cv2.VideoCapture(str(output));assert cap.isOpened()
    assert int(cap.get(cv2.CAP_PROP_FPS))==24 and int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))==1280
    frames=[]
    while True:
        ok,frame=cap.read()
        if not ok:break
        frames.append(frame)
    cap.release();assert len(frames)==72 and not np.array_equal(frames[0],frames[-1])
    meta=json.loads((tmp_path/'video.json').read_text())
    assert meta['validation']['ok'] and meta['motion_audit']['vehicles']>0
    assert meta['motion_audit']['rear_collisions']==0
    for vehicle in meta['motion_audit']['body_samples']:
        assert np.isfinite(vehicle['front']).all() and np.isfinite(vehicle['rear']).all()
        assert np.linalg.norm(np.array(vehicle['front'])-vehicle['rear'])>2
    out=os.environ.get('VISUAL_ARTIFACTS')
    if out:
        target=Path(out);target.mkdir(parents=True,exist_ok=True)
        for i in [0,36,71]:Image.fromarray(cv2.cvtColor(frames[i],cv2.COLOR_BGR2RGB)).save(target/f'1423_video_quadro_{i}.png')
        (target/'1423_video_metadados.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
