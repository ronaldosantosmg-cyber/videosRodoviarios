import io,json,zipfile,os
from pathlib import Path
import numpy as np
import pytest
from app.models import Settings
from app.pavement import paint_rigid,JointField
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot


@pytest.mark.parametrize('technical',[False,True])
def test_oae_rigid_concrete_paints_in_both_styles_without_key_error(technical):
    mask=np.zeros((40,60),bool);mask[5:35,5:55]=True
    color=np.array([150,150,150],np.uint8)
    result=paint_rigid(color,mask,'oae',0,40,.2,JointField([np.array([[0.,20.],[100.,20.]])]),5,technical)
    assert result.shape==(40,60,3) and result.dtype==np.uint8
    assert np.any(result[mask]!=150) and np.all(result[~mask]==150)


def test_oae_real_video_renders_and_decodes_after_logged_failure(tmp_path):
    from app.render import render
    from app.encoding import validate_mp4,ffmpeg_exe
    d,s=project(tmp_path)
    s=Settings.model_validate({**s.model_dump(),'render_workers':1,'oae_marks':[dict(id='bridge',start=dict(x=500170,y=7800000),end=dict(x=500270,y=7800000),width_m=14)]})
    (d/'config.json').write_text(s.model_dump_json())
    video=render(d,s)
    validation=validate_mp4(ffmpeg_exe(),video,72,1280,720,24)
    assert validation['ok']
    if os.environ.get('VISUAL_ARTIFACTS'):
        import cv2
        target=Path(os.environ['VISUAL_ARTIFACTS']);target.mkdir(parents=True,exist_ok=True)
        (target/'video_oae_validacao.json').write_text(json.dumps(validation,indent=2))
        cap=cv2.VideoCapture(str(video));ok,frame=cap.read();cap.release();assert ok
        cv2.imwrite(str(target/'video_oae_quadro.png'),frame)


def test_density_changes_real_vehicle_population_and_traffic_revision(tmp_path):
    from app.render import Scene
    from app.dependencies import revisions
    d,s=project(tmp_path);reports=[];keys=[]
    for density in (1,6):
        settings=s.model_copy(update=dict(traffic_density=density,duration_s=20))
        (d/'config.json').write_text(settings.model_dump_json())
        scene=Scene.light(d,settings);sim=scene.traffic();reports.append(sim.report());keys.append(revisions(d)['traffic'])
    assert reports[1]['vehicles']>reports[0]['vehicles'] and keys[0]!=keys[1]
    assert all(r['rear_collisions']==0 and r['side_collisions']==0 for r in reports)
    if os.environ.get('VISUAL_ARTIFACTS'):
        target=Path(os.environ['VISUAL_ARTIFACTS']);target.mkdir(parents=True,exist_ok=True)
        (target/'densidade_comparacao.json').write_text(json.dumps([{k:r[k] for k in ['density','vehicles','rear_collisions','side_collisions']} for r in reports],indent=2))


def test_large_kml_xml_uses_streaming_without_unpacking_images(tmp_path):
    from app.kmz_validation import validate
    from app.geometry import read_kmz
    archive=tmp_path/'large.kmz'
    # 147 MiB de XML válido, com descrições descartáveis e uma linha real.
    block=b'<Placemark><description>'+b'x'*4096+b'</description></Placemark>'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        with z.open('doc.kml','w') as f:
            f.write(b'<kml><Document>')
            for _ in range(147*1024*1024//len(block)):f.write(block)
            f.write(b'<Placemark><LineString><coordinates>-43,-19 -43.001,-19.001</coordinates></LineString></Placemark></Document></kml>')
    result=validate(archive)
    assert result['xml_bytes']>146*1024*1024 and result['method']=='xml_incremental'
    assert result['kml_limit_mb']==256 and not result['attachments_extracted']
    lines,_=read_kmz(archive,'EPSG:31983');assert len(lines)==1
    assert [p.name for p in tmp_path.iterdir()]==['large.kmz']


def test_streaming_rejects_dtd_even_across_reader_chunks(tmp_path):
    from app.kmz_validation import validate
    archive=tmp_path/'bad.kmz'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('doc.kml',b' '*16380+b'<!DOCTYPE kml [<!ENTITY x "text">]><kml>&x;</kml>')
    with pytest.raises(ValueError,match='DTD'):validate(archive)


def test_ui_can_switch_from_manual_demand_to_density_and_save(gl_page,live):
    p=gl_page
    p.evaluate("()=>{$('traffic_demand_vphpl').value='3500';fill({...collect(),traffic_demand_vphpl:3500});psOpenHub('video')}")
    p.get_by_text('Tráfego: simulação, engarrafamento e canteiro',exact=True).click()
    assert p.locator('#traffic_density').is_enabled()
    p.locator('#rsUseDensity').click();assert p.locator('#traffic_density').is_enabled()
    p.locator('#traffic_density').fill('6');p.locator('#traffic_density').dispatch_event('change')
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=15000)
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert config['traffic_density']==6 and config['traffic_demand_vphpl'] is None
    p.evaluate("psOpenHub('video')")
    assert p.locator('#rsPanelPopup').is_visible(),p.evaluate("({opened:RodoviaPanels.opened,section:pnEstado.aberto,message:$('message').textContent,hub:document.querySelector('[data-pshub=video]')?.outerHTML})")
    if not p.locator('#traffic_density').is_visible():p.get_by_text('Tráfego: simulação, engarrafamento e canteiro',exact=True).click()
    screenshot(p,'14219_densidade_ativa')


def test_upload_updates_revision_and_keeps_local_edits(gl_page,live):
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending',timeout=60000)
    response=p.evaluate('''async()=>{
      $('name').value='Edição preservada';scheduleSave();
      const kml='<kml><Placemark><LineString><coordinates>-43,-19 -43.001,-19.001</coordinates></LineString></Placemark></kml>';
      await sendFiles([new File([kml],'referencia.kml')]);
      $('traffic_density').value='4';await save();
      return {name:cfg.name,density:cfg.traffic_density,confirmed:cfg.coordinates_confirmed,revision:projectSession.revision};
    }''')
    remote=p.request.get(live[0]+'/api/projects/'+live[1]).json()
    assert response['name']=='Edição preservada' and response['density']==4
    assert response['confirmed'] is False and response['revision']==remote['config_revision']


def test_nonoverlapping_remote_mutation_is_merged_but_same_field_conflict_is_not_overwritten(gl_page,live):
    p=gl_page;url=live[0]+'/api/projects/'+live[1]
    initial=p.request.get(url).json();remote={**initial['config'],'destination':'Destino alterado em outra janela'}
    assert p.request.put(url+'/config',data=remote,headers={'If-Match':initial['config_revision']}).ok
    result=p.evaluate("async()=>{$('name').value='Nome local';await save();return collect()}")
    assert result['destination']==remote['destination'] and result['name']=='Nome local'
    initial=p.request.get(url).json();remote={**initial['config'],'name':'Nome remoto concorrente'}
    assert p.request.put(url+'/config',data=remote,headers={'If-Match':initial['config_revision']}).ok
    error=p.evaluate("async()=>{$('name').value='Outro nome local';try{await save();return ''}catch(e){return e.message}}")
    assert 'Conflito' in error and p.evaluate("$('name').value")=='Outro nome local'
    assert p.request.get(url).json()['config']['name']=='Nome remoto concorrente'


def test_file_changes_during_job_are_explained_without_sending_mutation(gl_page):
    p=gl_page
    result=p.evaluate("async()=>{task='running';try{await sendFiles([new File(['bad'],'arquivo.kmz')]);return $('message').textContent}finally{task=''}}")
    assert 'conclua ou cancele' in result


def test_resize_is_deferred_and_canvas_camera_remains_finite(gl_page):
    p=gl_page;errors=[];p.on('pageerror',lambda error:errors.append(str(error)))
    for width,height in [(1024,768),(1366,900),(900,700),(1280,800)]:
        p.set_viewport_size(dict(width=width,height=height));p.wait_for_timeout(100)
    assert not [e for e in errors if 'ResizeObserver' in e]
    assert p.evaluate('Number.isFinite(view.s)&&Number.isFinite(view.ox)&&Number.isFinite(view.oy)&&canvas.width>0')
