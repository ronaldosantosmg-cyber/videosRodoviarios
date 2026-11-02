import json,os
from pathlib import Path
import numpy as np
from PIL import Image
from app.render import Scene,render
from app.encoding import validate_mp4,ffmpeg_exe
from test_v14229_shoulder_probe import actual_network
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_probe_checkbox_is_saved_and_can_be_disabled(gl_page,live):
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    p.evaluate("psOpenHub('video')");p.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    c=p.locator('#heavy_shoulder_probe');assert c.is_checked();c.uncheck()
    screenshot(p,'14229_sonda_pesados_configuracao')
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=30000)
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert config['heavy_shoulder_probe'] is False


def heavy(*args,**kwargs):return 'truck'


def test_actual_heavy_probe_survives_render_and_mp4_with_indicators(tmp_path,monkeypatch):
    import ezdxf
    from app import visual
    _,s=actual_network();s.width=1280;s.imagery='neutral';s.imagery_pixels=2048;s.coordinates_confirmed=True;s.duration_s=12;s.fps=24;s.camera_mode='trafego';s.view_width_m=160;s.render_workers=1
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    m.add_lwpolyline([(0,0),(600,0)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(-30,-3.2),(630,-3.2),(630,3.2),(-30,3.2)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf');(tmp_path/'config.json').write_text(s.model_dump_json())
    monkeypatch.setattr(visual,'vehicle_type',heavy)
    scene=Scene(tmp_path,s);sim=scene.traffic();assert sim.shoulder_probe.events
    found=None
    for t in np.arange(0,12,.1):
        states=sim.state(float(t))
        for vid,i,station,to,a in states:
            v=dict(id=vid,p=i,s=station,t='truck');event=sim.shoulder_probe.event(v)
            if event and abs(sim.shoulder_probe.offset(event,station))>.15:
                pose=sim.shoulder_probe.pose(v);frame,meta=scene.frame(float(t),view=(pose[0],100));found=(t,frame,meta);break
        if found:break
    assert found is not None
    assert found[2]['traffic_visibility']['drawn']>0
    target=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));target.mkdir(parents=True,exist_ok=True)
    Image.fromarray(found[1]).save(target/'14229_pesado_sonda_acostamento.png')
    result=render(tmp_path,s);check=validate_mp4(ffmpeg_exe(),result,288,1280,720,24);assert check['ok']
    meta=json.loads((tmp_path/'video.json').read_text());probe=meta['motion_audit']['shoulder_probe']
    assert probe['maneuvers']>0 and probe['maximum_beyond_pavement_m']==1
    assert meta['motion_audit']['rear_collisions']==meta['motion_audit']['side_collisions']==0
    (target/'video_sonda.json').write_text(json.dumps({'decoded':check,'shoulder_probe':probe,'presentation':meta['traffic_presentation'],'scope':'Frota pesada forçada somente no ensaio, sem alterar o mix do produto.'},ensure_ascii=False,indent=2))
