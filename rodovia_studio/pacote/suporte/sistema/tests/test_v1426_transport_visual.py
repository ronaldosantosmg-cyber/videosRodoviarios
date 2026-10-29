from ui_release_helpers import ribbon_control
import json,os
import pytest
from pathlib import Path
import numpy as np
from PIL import Image
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot
from test_v1425_scene3d import project
from app.models import Settings
from app.render import Scene,render
from app.scene3d import build
from app.encoding import ffmpeg_exe,validate_mp4


def controls(s,duration=40):
    return Settings.model_validate(dict(s.model_dump(),duration_s=duration,railways=[{'id':'ferrovia','points':[{'x':500350,'y':7799850},{'x':500350,'y':7800150}],'start_s':0,'direction':'both','tracks':2}],traffic_signals=[{'id':'s1','name':'Cruzamento A','point':{'x':500150,'y':7800000},'phases':3,'lanes_a':2,'lanes_b':2}]))


def click_world(page,x,y,button='left'):
    # A expansão do ribbon agenda resize no frame seguinte; calcular o clique depois.
    page.evaluate('async()=>{await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}')
    point=page.evaluate("p=>{const [x,y]=W2C(p),r=canvas.getBoundingClientRect();return {x:r.left+x*r.width/canvas.width,y:r.top+y*r.height/canvas.height}}",{'x':x,'y':y})
    page.mouse.click(point['x'],point['y'],button=button)


def test_controls_are_saved_from_dialog_with_undo_and_context(gl_page):
    p=gl_page
    ribbon_control(p,'railway').hover();assert 'Ferrovia' in p.locator('#rsToolHelp').inner_text()
    ribbon_control(p,'railway').click();assert p.evaluate('tool')=='railway'
    click_world(p,500250,7799920);click_world(p,500250,7800080);p.keyboard.press('Enter');p.wait_for_selector('#rsTransportDialog')
    p.locator('[data-transport-field=tracks]').select_option('2');p.locator('[data-transport-field=direction]').select_option('both')
    p.locator('#rsTransportDialog button[type=submit]').click();p.wait_for_selector('#rsTransportDialog',state='detached')
    assert p.evaluate('M.railways.length')==1 and p.evaluate('M.railways[0].tracks')==2
    p.evaluate('undo()');assert p.evaluate('M.railways.length')==0
    p.evaluate('redo()');assert p.evaluate('M.railways.length')==1
    ribbon_control(p,'traffic_signal').click();click_world(p,500150,7800000);p.wait_for_selector('#rsTransportDialog')
    p.locator('[data-transport-field=phases]').select_option('3');p.locator('[data-transport-field=phases]').dispatch_event('input')
    assert '19 s' in p.locator('#rsTransportTiming').inner_text()
    screenshot(p,'1426_01_semaforo_tres_tempos')
    p.locator('#rsTransportDialog button[type=submit]').click();p.wait_for_selector('#rsTransportDialog',state='detached')
    p.evaluate('save()');assert p.evaluate('cfg.traffic_signals[0].phases')==3
    click_world(p,500250,7800000,button='right');p.get_by_role('menuitem',name='Propriedades de Ferrovia 1',exact=True).click();assert p.locator('[data-transport-field=direction]').input_value()=='both'
    screenshot(p,'1426_02_ferrovia_propriedades');p.locator('#rsTransportDialog [data-cancel]').click()
    ribbon_control(p,'railway').click();p.locator('#rsRailMode').select_option('linha');click_world(p,500200,7800000);p.wait_for_selector('#rsTransportDialog')
    before=p.evaluate('M.railways.length');p.locator('#rsTransportDialog button[type=submit]').click();p.wait_for_selector('#rsTransportDialog',state='detached')
    assert p.evaluate('M.railways.length')==before+1 and p.evaluate('M.railways.at(-1).points[0].x')==pytest.approx(500050,abs=.01)
    p.evaluate('async()=>{undo();await save()}')


def test_invalid_dialog_keeps_geometry_and_existing_project(gl_page):
    p=gl_page;before=p.evaluate('M.railways.length')
    p.evaluate("RodoviaTransport.newRail([{x:1,y:1},{x:2,y:1}])")
    p.locator('#rsTransportDialog button[type=submit]').click();p.wait_for_function("document.querySelector('#rsTransportError').textContent.length>0")
    assert p.evaluate('M.railways.length')==before and p.locator('#rsTransportDialog').is_visible()
    p.locator('#rsTransportDialog [data-cancel]').click()


def test_real_3d_controls_tracks_and_lamps(gl_page,live):
    p=gl_page;d=live[2]/live[1];s=controls(Settings.model_validate_json((d/'config.json').read_text()))
    # Os testes de diálogo anteriores podem ter controles salvos: este cenário usa uma configuração explícita.
    (d/'config.json').write_text(s.model_dump_json());build(d,s);p.evaluate('(id)=>load(id)',live[1]);p.wait_for_timeout(300);p.wait_for_function('!task',timeout=60000)
    open3d(p);p.evaluate('Rodovia3D.setTime(20)');p.locator('[data-rs3d=top3d]').click()
    assert p.evaluate('Rodovia3D.stats().vehicles')>=6
    assert p.evaluate('Rodovia3D.stats().trafficLights')==4
    assert p.evaluate('Rodovia3D.stats().railLights')>0 and p.evaluate('Rodovia3D.stats().trainHeadlights')>=2
    screenshot(p,'1426_03_ferrovia_semaforos_webgl')
    p.locator('[data-rs3d=view2d]').click()


def test_video_has_train_textures_signal_lights_and_complete_mp4(tmp_path):
    d,s=project(tmp_path,traffic=False);data=s.model_dump();data.update(duration_s=3,fps=24,traffic=False,traffic_signals=[{'id':'S','point':{'x':500150,'y':7800000},'phases':3,'offset_s':69}],railways=[{'id':'R','points':[{'x':500250,'y':7799985},{'x':500250,'y':7800015}],'start_s':0}])
    s=Settings.model_validate(data);(d/'config.json').write_text(s.model_dump_json());scene=Scene(d,s)
    evidence=Path(os.environ.get('VISUAL_ARTIFACTS','/workspace/rodovia-1426-evidencias'));evidence.mkdir(parents=True,exist_ok=True)
    frames=[]
    for t in [0,1.5,2.9]:
        im,_=scene.frame(t,view=([500200,7800000],180));frames.append(im);Image.fromarray(im).save(evidence/f'1426_video_{t}.png')
    assert not np.array_equal(frames[0],frames[-1])
    path=render(d,s);check=validate_mp4(ffmpeg_exe(),path,72,1280,720,24);assert check['ok'],check
    (evidence/'1426_video_metadados.json').write_text(json.dumps(check,indent=2)+'\n')


def test_cabin_camera_obeys_controls_and_renders_train_and_signals(tmp_path):
    from app.cabin import CabinView
    d,s=project(tmp_path);s=controls(s,60);s.cabin.enabled=True
    s=Settings.model_validate(dict(s.model_dump(),cabin=dict(s.cabin.model_dump(),start={'x':500070,'y':7800000},duration_s=60)))
    (d/'config.json').write_text(s.model_dump_json());scene=Scene(d,s);cabin=CabinView(scene)
    assert hasattr(cabin,'control_clock') and np.isfinite(cabin.control_clock).all()
    changes=np.diff(cabin.control_clock);assert np.min(changes)==0 and np.max(changes)>0
    image,meta=cabin.frame(15);assert image.shape==(720,1280,3) and np.isfinite(image).all()
    evidence=Path(os.environ.get('VISUAL_ARTIFACTS','/workspace/rodovia-1426-evidencias'));evidence.mkdir(exist_ok=True,parents=True);Image.fromarray(image).save(evidence/'1426_04_cabine_controle.png')


def test_cabin_keeps_front_rear_clearance_behind_long_trucks(tmp_path):
    from app.cabin import CabinView
    from app.simulation import TrafficSim
    from app.vehicle_motion import PROFILES
    d,s=project(tmp_path);s=controls(s,60);data=s.model_dump();data['cabin'].update(enabled=True,start={'x':500070,'y':7800000},duration_s=60);s=Settings.model_validate(data)
    (d/'config.json').write_text(s.model_dump_json());scene=Scene(d,s);sim=TrafficSim(scene.network,s,lambda *a:'carreta',duration=60);scene._sim=sim;cabin=CabinView(scene);checked=0
    for k,distance in enumerate(cabin.control_clock[:300]):
        if distance<cabin.d0+10:continue
        for vid,path,station,_,_ in sim.state(k*.2):
            if path==cabin.i and station>distance+1:
                length=PROFILES[sim.info[vid][1]][0]
                assert station-length/2-(distance+2.25)>=.5
                checked+=1
    assert checked>10


def test_link_tool_connects_signals_and_context_edits_link(gl_page):
    p=gl_page
    p.evaluate("async()=>{M.traffic_signals=[{id:'A',name:'A',point:{x:500100,y:7800010},heading_deg:0,phases:2,lanes_a:2,lanes_b:2,lane_width_m:3.5,offset_s:0,enabled:true,level:0},{id:'B',name:'B',point:{x:500400,y:7800010},heading_deg:0,phases:2,lanes_a:2,lanes_b:2,lane_width_m:3.5,offset_s:0,enabled:true,level:0}];M.signal_links=[];draw();await save()}")
    ribbon_control(p,'signal_link').click();click_world(p,500100,7800010);click_world(p,500400,7800010)
    p.wait_for_selector('#rsTransportDialog');p.locator('[data-transport-field=speed_kmh]').fill('36');p.locator('#rsTransportDialog button[type=submit]').click();p.wait_for_selector('#rsTransportDialog',state='detached')
    assert p.evaluate('M.signal_links[0].source')=='A' and p.evaluate('M.signal_links[0].target')=='B'
    p.evaluate("setTool('pan')");click_world(p,500280,7800010,button='right');p.get_by_role('menuitem',name='Propriedades do link de onda verde',exact=True).click()
    assert p.locator('[data-transport-field=speed_kmh]').input_value()=='36'
    screenshot(p,'1426_07_link_onda_verde');p.locator('#rsTransportDialog [data-cancel]').click()
    ribbon_control(p,'signal_link').click();click_world(p,500100,7800010)
    ribbon_control(p,'pan').click();ribbon_control(p,'signal_link').click();click_world(p,500400,7800010)
    assert p.locator('#rsTransportDialog').count()==0
    p.keyboard.press('Escape')
