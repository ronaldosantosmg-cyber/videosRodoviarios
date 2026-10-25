import json
import pytest
import numpy as np
from app.models import Settings,PedPath
from app.transport_models import Railway
from app import store
from app.scene3d import build
from app.render import Scene
from app.rail_smoke import parameters
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot


def prepare(live):
    d=live[2]/live[1];s=Settings.model_validate_json((d/'config.json').read_text())
    s=s.model_copy(update=dict(duration_s=12,traffic_density=1,pedestrian_paths=[PedPath(id='walk',points=[dict(x=500100,y=7800025),dict(x=500400,y=7800025)],people_per_100m=5)],railways=[Railway(id='rail',points=[dict(x=500050,y=7799900),dict(x=500050,y=7800100)],start_s=0,speed_kmh=40,min_wagons=5,max_wagons=5)]))
    store.write_json(d/'config.json',s.model_dump());return d,s,build(d,s)


def test_shared_people_and_bounded_smoke_are_rendered_by_real_webgl(gl_page,live):
    p=gl_page;d,s,data=prepare(live);p.evaluate('(id)=>load(id)',live[1]);open3d(p)
    p.evaluate('Rodovia3D.setTime(6)');stats=p.evaluate('Rodovia3D.stats()')
    assert stats['pedestrians']>0 and stats['activePedestrians']>0 and 0<stats['smokeParticles']<=240
    assert p.locator('#rsViewport3D canvas').count()==1
    result=p.evaluate("async()=>{const {smokeParameters}=await import('/webgl/agents.mjs');return smokeParameters(42,1.3,4,12)}")
    expected=parameters(42,1.3,4,12)
    for key in expected:assert result[key]==pytest.approx(expected[key],abs=1e-7)
    screenshot(p,'14218_agentes_fumaca_webgl')
    p.locator('[data-rs3d=video3d]').click();p.locator('#rs3dDuration').fill('3');p.locator('#rs3dExportStart').click()
    p.wait_for_function("document.querySelector('#rs3dExportInfo a')!==null",timeout=180000)
    from app.encoding import validate_mp4,ffmpeg_exe
    info=json.loads((d/'video3d.json').read_text());assert info['frames']==72
    assert validate_mp4(ffmpeg_exe(),d/'video3d.mp4',72,1280,720,24)['ok']
    p.locator('#rs3dExport button[value=cancel]').click()

    p.locator('[data-rs3d=view2d]').click();p.wait_for_function('!Rodovia3D.stats().ready')
    assert p.locator('#rsViewport3D canvas').count()==0


def test_actual_2d_frames_show_effect_and_are_reproducible_out_of_order(tmp_path):
    from test_v1425_scene3d import project
    from app.transport_models import Railway
    from app.models import PedPath
    d,s=project(tmp_path,traffic=False)
    s=s.model_copy(update=dict(width=1280,duration_s=12,view_width_m=700,pedestrian_paths=[PedPath(id='walk',points=[dict(x=500100,y=7800025),dict(x=500400,y=7800025)])],railways=[Railway(id='rail',points=[dict(x=500050,y=7799900),dict(x=500050,y=7800100)],start_s=0,speed_kmh=40,min_wagons=5,max_wagons=5)]))
    store.write_json(d/'config.json',s.model_dump());scene=Scene(d,s);a=scene.frame(6)[0];scene.frame(2);b=scene.frame(6)[0]
    np.testing.assert_array_equal(a,b)
    from PIL import Image
    import os
    from pathlib import Path
    target=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));target.mkdir(parents=True,exist_ok=True)
    Image.fromarray(a).save(target/'14218_agentes_2d.png')
    scene.s.rail_smoke=False;without_smoke=scene.frame(6)[0]
    assert np.any(a!=without_smoke)
    scene.s.pedestrians=False;without_people=scene.frame(6)[0]
    assert np.any(without_smoke!=without_people)


def test_interval_arrow_automatically_changes_real_motor_direction(gl_page,live):
    p=gl_page
    p.evaluate("()=>{checkpoint();M.direction_marks=[{id:'range',start:{x:500400,y:7800000},end:{x:500100,y:7800000}}];changed()}")
    p.wait_for_function("!task && !taskRequestPending && (editor?.segments||[]).some(s=>s.points.every(p=>p[0]>=500099.9&&p[0]<=500400.1)&&!s.forward)",timeout=60000)
    data=p.request.get(live[0]+'/api/projects/'+live[1]).json()
    assert data['config']['direction_marks'][0]['id']=='range'
    assert p.evaluate("(editor.segments||[]).some(s=>s.points.every(p=>p[0]>=500099.9&&p[0]<=500400.1)&&!s.forward)")
    screenshot(p,'14218_sentido_intervalo_motor')


def test_2d_mp4_with_agents_decodes_all_frames_and_preserves_collision_audit(tmp_path):
    from test_v1425_scene3d import project
    from app.render import render
    from app.encoding import validate_mp4,ffmpeg_exe
    d,s=project(tmp_path)
    s=Settings.model_validate({**s.model_dump(),'duration_s':3,'render_workers':1,'traffic_density':1,
        'pedestrian_paths':[dict(id='walk',points=[dict(x=500100,y=7800025),dict(x=500400,y=7800025)])],
        'railways':[dict(id='train',points=[dict(x=500050,y=7799900),dict(x=500050,y=7800100)],start_s=0,speed_kmh=40,min_wagons=5,max_wagons=5)]})
    store.write_json(d/'config.json',s.model_dump());output=render(d,s)
    assert validate_mp4(ffmpeg_exe(),output,72,1280,720,24)['ok']
    meta=json.loads((d/'video.json').read_text());assert meta['motion_audit']['rear_collisions']==0
    assert meta['pedestrian_audit']['vehicle_collisions']==0 and meta['pedestrian_audit']['people_collisions']==0
