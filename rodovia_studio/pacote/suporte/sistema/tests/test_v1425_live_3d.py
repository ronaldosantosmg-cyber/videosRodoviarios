import json,socket,threading,time,urllib.request
from pathlib import Path
import pytest
import uvicorn
from playwright.sync_api import sync_playwright
from test_v1425_scene3d import project
from app.scene3d import build
from visual_harness import screenshot

@pytest.fixture(scope='module')
def live(tmp_path_factory):
    from app import store
    from app.server import app
    root=tmp_path_factory.mktemp('webgl_real');patch=pytest.MonkeyPatch();patch.setenv('RODOVIA_DATA',str(root));patch.setattr(store,'ROOT',root);patch.setattr(store,'DB',root/'studio.sqlite3');store.init()
    pid='f'*32;d=root/pid;d.mkdir();d,s=project(d);build(d,s)
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,s.name))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    for _ in range(150):
        if server.started:break
        time.sleep(.05)
    assert server.started
    yield f'http://127.0.0.1:{port}',pid,root
    server.should_exit=True;thread.join(timeout=15);assert not thread.is_alive();patch.undo()

@pytest.fixture
def gl_page(live):
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        page=b.new_page(viewport={'width':1440,'height':900},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(live[0]+'/') else route.abort())
        page.goto(live[0],wait_until='networkidle');page.wait_for_function('!!window.Rodovia3D && !!window.RodoviaNewProject')
        page.evaluate('(pid)=>load(pid)',live[1]);page.wait_for_timeout(300);page.wait_for_function('!task',timeout=60000)
        yield page
        assert not errors,errors;b.close()


def open3d(page):
    page.locator('[data-rs3d=view3d]').click()
    try:page.wait_for_function('Rodovia3D.stats().ready',timeout=45000)
    except Exception as exc:raise AssertionError(page.locator('#rs3dState').inner_text()+' | '+page.locator('#message').inner_text()) from exc


def test_real_webgl_has_geometry_traffic_controls_and_no_duplicate_bar(gl_page):
    page=gl_page;open3d(page);stats=page.evaluate('Rodovia3D.stats()')
    assert stats['triangles']>100 and stats['vehicles']>0 and not stats['lost']
    assert page.locator('#canvas').is_hidden() and page.locator('#rsViewport3D canvas').is_visible()
    assert page.locator('#rsQuickTools').count()==0 and page.locator('#rsToolNames').count()==0
    page.locator('[data-rs3d=play3d]').click();page.wait_for_timeout(400);assert page.evaluate('Rodovia3D.stats().time')>0
    page.locator('[data-rs3d=pause3d]').click();page.locator('#rs3dTime').fill('1.2');page.locator('#rs3dTime').dispatch_event('input')
    assert page.evaluate('Rodovia3D.stats().time')==pytest.approx(1.2)
    page.locator('[data-rs3d=scene3d]').click();assert page.evaluate('Rodovia3D.stats().followId') is not None
    page.locator('[data-rs3d=flows3d]').click();assert page.evaluate('Rodovia3D.stats().diagnostics')
    page.locator('[data-rs3d=light3d]').click();assert page.evaluate('Rodovia3D.stats().light')=='entardecer'
    screenshot(page,'1425_01_webgl_trafego_real')
    page.locator('[data-rs3d=view2d]').click();assert page.locator('#canvas').is_visible()


def test_snapshot_is_real_png_and_diagnostic_overlay_is_preserved(gl_page,tmp_path):
    from PIL import Image
    page=gl_page;open3d(page);page.locator('[data-rs3d=flows3d]').click()
    with page.expect_download() as download:page.locator('[data-rs3d=png3d]').click()
    path=tmp_path/'vista.png';download.value.save_as(path);im=Image.open(path).convert('RGB')
    assert im.width>500 and im.height>200 and len(im.getcolors(maxcolors=im.width*im.height))>100
    assert page.evaluate('Rodovia3D.stats().diagnostics')
    screenshot(page,'1425_02_captura_e_diagnostico')


def test_camera_navigation_context_recovery_and_disposal(gl_page):
    page=gl_page;open3d(page)
    point=page.locator('#rsViewport3D canvas').bounding_box();page.mouse.move(point['x']+point['width']/2,point['y']+point['height']/2);page.mouse.wheel(0,-300)
    page.locator('[data-rs3d=top3d]').click();page.locator('[data-rs3d=fit3d]').click()
    page.evaluate("window._gl=document.querySelector('#rsViewport3D canvas').getContext('webgl2');window._lost=_gl.getExtension('WEBGL_lose_context');_lost.loseContext();void 0")
    page.wait_for_function('Rodovia3D.stats().lost');assert not page.evaluate('Rodovia3D.stats().playing')
    page.wait_for_timeout(250);page.evaluate('_lost.restoreContext()');page.wait_for_function('!Rodovia3D.stats().lost')
    for _ in range(3):
        page.locator('[data-rs3d=view2d]').click();assert page.locator('#rsViewport3D canvas').count()==0
        open3d(page);assert page.locator('#rsViewport3D canvas').count()==1
    screenshot(page,'1425_03_contexto_recuperado')


def test_new_project_requires_identity_and_saves_all_initial_settings(gl_page,live):
    page=gl_page;page.evaluate('RodoviaNewProject.open()');assert page.locator('#rsNewProject').is_visible()
    page.locator('#rsNewName').fill('Trecho novo identificado');page.locator('#rsNewOrigin').fill('Cidade A');page.locator('#rsNewDestination').fill('Cidade B');page.locator('#rsNewStart').fill('284+000');page.locator('#rsNewEnd').fill('288+500')
    screenshot(page,'1425_04_novo_projeto_identificado')
    page.locator('#rsNewCreate').click();page.wait_for_selector('#rsNewProject',state='hidden')
    assert page.evaluate('cfg.name')=='Trecho novo identificado' and page.evaluate('cfg.km_start_m')==284000 and page.evaluate('cfg.km_end_m')==288500
    assert 'Cidade A' in page.locator('#rsProjectIdentity').inner_text()
    new_id=page.evaluate('pid');assert new_id!=live[1]
    data=json.loads((live[2]/new_id/'config.json').read_text());assert data['origin']=='Cidade A' and data['destination']=='Cidade B'
    assert data['min_route_segment_m']==50 and data['width']==1920


def test_invalid_km_and_cancel_do_not_create_blank_projects(gl_page,live):
    page=gl_page;before=len([p for p in live[2].iterdir() if p.is_dir() and len(p.name)==32]);old=page.evaluate('pid')
    page.evaluate('RodoviaNewProject.open()');page.locator('#rsNewName').fill('Inválido');page.locator('#rsNewOrigin').fill('A');page.locator('#rsNewDestination').fill('B');page.locator('#rsNewStart').fill('288+000');page.locator('#rsNewEnd').fill('284+000');page.locator('#rsNewCreate').click()
    assert 'maior' in page.locator('#rsNewError').inner_text();page.locator('#rsNewCancel').click();assert page.evaluate('pid')==old
    assert len([p for p in live[2].iterdir() if p.is_dir() and len(p.name)==32])==before


def test_real_webgl_mp4_export_is_complete_and_archived(gl_page,live):
    import subprocess
    from app.encoding import ffmpeg_exe,validate_mp4
    page=gl_page;open3d(page)
    page.locator('[data-rs3d=flows3d]').click()
    page.locator('[data-rs3d=video3d]').click();page.locator('#rs3dDuration').fill('3');page.locator('#rs3dExportStart').click()
    page.wait_for_function("document.querySelector('#rs3dExportInfo a')!==null",timeout=180000)
    d=live[2]/live[1];info=json.loads((d/'video3d.json').read_text())
    assert info['frames']==72 and info['width']==1280 and info['fps']==24
    assert validate_mp4(ffmpeg_exe(),d/'video3d.mp4',72,1280,720,24)['ok']
    assert info['motor']=='WebGL 3D' and info['camera3d']['light']=='dia'
    link=page.locator('#rs3dExportInfo a');assert page.request.get(live[0]+link.get_attribute('href')).status==200
    assert not (d/'video3d.partial.mp4').exists()
    page.locator('#rs3dExport button[value=cancel]').click()
    assert page.evaluate('Rodovia3D.stats().diagnostics')
    screenshot(page,'1425_05_video_3d_conferido')
