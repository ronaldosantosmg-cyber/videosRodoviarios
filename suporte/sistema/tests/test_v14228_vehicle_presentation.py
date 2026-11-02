"""O quadro deve apresentar veículos reais sem alterar as regras de circulação."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box
from app.render import Scene
from app.traffic_presentation import visible,focus_pose,preflight,project_status
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_wide_view_no_longer_hides_simulated_vehicles_and_focus_makes_them_readable(tmp_path):
    d,s=project(tmp_path);s.camera_mode='trafego';s.view_width_m=350
    scene=Scene(d,s);before=s.model_dump();image,meta=scene.frame(1)
    stats=meta['traffic_visibility'];assert stats['active']>0 and stats['drawn']>0 and stats['subpixel']==0
    assert stats['width_m']==350 and not stats['reveal_pending']
    assert preflight(scene)['status']=='visivel'
    draw=scene.draw_vehicles;scene.draw_vehicles=lambda *a:None
    without,_=scene.frame(1);scene.draw_vehicles=draw
    assert np.count_nonzero(image!=without)>50
    _,wide=scene.frame(1,view=(scene.center,4000))
    assert wide['traffic_visibility']['drawn']>0
    assert s.model_dump()==before
    from PIL import Image
    import os
    target=os.environ.get('VISUAL_ARTIFACTS')
    if target:Image.fromarray(image).save(__import__('pathlib').Path(target)/'14228_veiculos_em_evidencia.png')


def test_fit_cache_varies_with_position_and_keeps_actual_body_inside_pavement():
    scene=SimpleNamespace(_fit={},allowed=box(-10,-1,10,1))
    tan=np.array([1.,0.])
    assert Scene.fits(scene,0,0,np.array([0.,0.]),tan,'car')
    assert not Scene.fits(scene,0,0,np.array([0.,2.]),tan,'car')
    assert not Scene.fits(scene,0,0,np.array([np.nan,0.]),tan,'car')
    assert len(scene._fit)==2


def test_focus_rejects_missing_itinerary_without_mutating_restrictions():
    s=SimpleNamespace(traffic=True,view_width_m=350)
    scene=SimpleNamespace(s=s,network=SimpleNamespace(paths=[]))
    with pytest.raises(ValueError,match='itinerário válido'):focus_pose(scene,0)
    assert not scene.network.paths
    s.traffic=False
    with pytest.raises(ValueError,match='ativado'):focus_pose(scene,0)


def test_diagnostic_does_not_invent_simulation_and_ignores_stale_results(tmp_path):
    from app.artifacts import begin,finish
    from app.dependencies import revisions
    d,s=project(tmp_path);keys=revisions(d)
    editor={'engine_revision':keys['editor'],'itineraries':2,'segments':[]}
    (d/'editor.json').write_text(json.dumps(editor));before=(d/'config.json').read_bytes()
    status=project_status(d);assert status['itineraries']==2 and status['preview_active'] is None
    assert (d/'config.json').read_bytes()==before
    s.traffic=False;(d/'config.json').write_text(s.model_dump_json())
    status=project_status(d);assert not status['enabled'] and any('desativado' in x for x in status['notices'])
    s.route_alignments=[];s.min_route_segment_m=200;(d/'config.json').write_text(s.model_dump_json())
    assert not project_status(d)['editor_current']


def test_real_browser_vehicle_diagnostic_can_generate_focused_preview(gl_page,live):
    p=gl_page;p.evaluate('RodoviaTrafficHelp.open()')
    d=p.get_by_role('dialog',name='Diagnosticar veículos',exact=True)
    d.get_by_text('Somente resultados atuais;',exact=False).wait_for()
    # Análise atual antes de habilitar o enquadramento; não pressupor que abrir recalcula.
    if d.get_by_role('button',name='Ativar veículos e gerar prévia de tráfego',exact=True).is_disabled():
        d.get_by_role('button',name='Atualizar diagnóstico das rotas',exact=True).click()
        d.wait_for(state='hidden');d.wait_for(state='visible',timeout=90000)
    d.get_by_role('button',name='Ativar veículos e gerar prévia de tráfego',exact=True).click()
    d.wait_for(state='hidden');d.wait_for(state='visible',timeout=90000)
    p.wait_for_function("document.querySelector('.rsTrafficHelp')?.getAttribute('aria-busy')==='false'",timeout=90000)
    assert p.locator('#camera_mode').input_value()=='trafego'
    result=p.request.get(live[0]+'/api/projects/'+live[1]+'/traffic_status').json()
    assert result['preview_active']>0 and result['preview_drawn']>0
    assert result['preview_width_m']==350
    screenshot(p,'14228_diagnostico_veiculos')
    d.get_by_role('button',name='Fechar',exact=True).click();assert not d.is_visible()


@pytest.mark.parametrize('workers',[1,2])
def test_focused_traffic_mp4_decodes_with_visible_real_vehicles(tmp_path,workers):
    from app.render import render
    from app.encoding import validate_mp4,ffmpeg_exe
    d,s=project(tmp_path);s.camera_mode='trafego';s.view_width_m=350;s.render_workers=workers
    path=render(d,s);check=validate_mp4(ffmpeg_exe(),path,72,1280,720,24)
    assert check['ok']
    meta=json.loads((d/'video.json').read_text())
    assert meta['traffic_presentation']['status']=='visivel'
    assert all(row['drawn']>0 for row in meta['traffic_presentation']['samples'])
    assert meta['motion_audit']['rear_collisions']==0 and meta['motion_audit']['side_collisions']==0
    import os
    target=os.environ.get('VISUAL_ARTIFACTS')
    if target:__import__('pathlib').Path(target,f'video_trafego_{workers}_processos.json').write_text(json.dumps({'decoded':check,'presentation':meta['traffic_presentation'],'motion_audit':{k:meta['motion_audit'][k] for k in ['vehicles','rear_collisions','side_collisions']},'workers':meta['workers']},indent=2))
