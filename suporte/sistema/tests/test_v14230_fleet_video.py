import json,os
from pathlib import Path
from PIL import Image
from app.render import Scene,render
from app.encoding import validate_mp4,ffmpeg_exe
from app.scene3d import build
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def long_vehicle(*args,**kwargs):return 'long30'


def test_long_30m_body_in_real_scene_3d_and_decoded_video(tmp_path,monkeypatch):
    from app import visual
    d,s=project(tmp_path);s.vehicle_mix='engenharia';s.traffic_density=4;s.camera_mode='trafego';s.view_width_m=220;s.render_workers=1
    (d/'config.json').write_text(s.model_dump_json());monkeypatch.setattr(visual,'vehicle_type',long_vehicle)
    scene=Scene(d,s);im,meta=scene.frame(1)
    assert meta['traffic_visibility']['drawn']>0
    sim=scene.traffic();assert sim.info and all(v[1]=='long30' for v in sim.info.values())
    for row in sim.vehicle_body_state(1):
        import numpy as np
        assert np.linalg.norm(np.array(row['front'])-row['rear'])==__import__('pytest').approx(30)
        assert row['width_m']==3
    data=build(d,s);assert data['vehicles'] and all(v['length']==30 and v['width']==3 for v in data['vehicles'])
    out=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));out.mkdir(exist_ok=True,parents=True);Image.fromarray(im).save(out/'14230_longo_30m_envelope.png')
    result=render(d,s);checked=validate_mp4(ffmpeg_exe(),result,72,1280,720,24);assert checked['ok']
    (out/'video_frota_engenharia.json').write_text(json.dumps({'decoded':checked,'dimensions':{'length_m':30,'width_m':3},'simulation':sim.report(),'scope':'Frota forçada no ensaio para conferir o envelope rígido de 30 m; não é articulação homologada.'},ensure_ascii=False,indent=2))


def test_engineering_mix_loads_in_real_webgl(gl_page):
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    p.evaluate("async()=>{fill({...collect(),vehicle_mix:'engenharia'});await save();await Rodovia3D.open(true)}")
    p.wait_for_function('Rodovia3D.stats().ready',timeout=90000)
    assert p.evaluate('Rodovia3D.stats().vehicles')>0
    screenshot(p,'14230_frota_engenharia_webgl')


def test_unchecked_controls_are_identified_in_webgl_and_captured_png(gl_page,tmp_path):
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    p.evaluate("async()=>{cfg.traffic_prevent_collisions=false;cfg.traffic_respect_signals=false;await save();await Rodovia3D.open(true)}")
    p.wait_for_function('Rodovia3D.stats().ready',timeout=90000)
    assert 'ENSAIO' in p.locator('#rs3dState').inner_text()
    p.locator('#rsViewport3D canvas').click(button='right')
    with p.expect_download() as download:p.get_by_role('menuitem',name='Capturar imagem PNG',exact=True).click()
    target=tmp_path/'ensaio.png';download.value.save_as(target);im=Image.open(target).convert('RGB')
    assert im.getpixel((2,im.height-2))==(110,35,20)
