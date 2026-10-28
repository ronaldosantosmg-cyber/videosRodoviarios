import json
from pathlib import Path
import numpy as np
from app.full_update import complete_update,required
from app.models import Settings,RouteAlignment
from app.geometry import analyze
from app.routes import build_lanes
from app.route_lane_cache import RouteLaneCache
from test_v1425_scene3d import project
from test_v14220_sections_materials import route
from test_v1425_live_3d import live,gl_page,open3d
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_complete_context_rebuilds_geometry_once_and_does_not_leak(tmp_path,monkeypatch):
    import app.geometry as geometry
    d,s=project(tmp_path);calls=[];read=geometry.ezdxf.readfile
    def count(*a,**k):calls.append(1);return read(*a,**k)
    monkeypatch.setattr(geometry.ezdxf,'readfile',count)
    first=analyze(d,s);cached=analyze(d,s);assert cached[4]['geometry_cache']['hit']
    with complete_update():
        fresh=analyze(d,s);again=analyze(d,s)
        assert not fresh[4]['geometry_cache']['hit'] and again[4]['geometry_cache']['hit']
    assert not required('geometry','anything') and len(calls)==2
    np.testing.assert_array_equal(first[1],fresh[1])


def test_complete_context_rebuilds_each_route_only_once(tmp_path):
    r=RouteAlignment.model_validate(route());s=Settings();cache=RouteLaneCache(tmp_path)
    build_lanes(r,s,cache);build_lanes(r,s,cache)
    with complete_update():build_lanes(r,s,cache);build_lanes(r,s,cache)
    assert cache.misses==2 and cache.hits==2


def test_full_scene_rebuilds_cached_surface_without_changing_pixels(tmp_path):
    from app.render import Scene
    d,s=project(tmp_path,traffic=False);before=Scene(d,s);cached=Scene(d,s)
    assert cached.geometry_cache_hit
    with complete_update():fresh=Scene(d,s)
    assert not fresh.geometry_cache_hit
    np.testing.assert_array_equal(before.overlay,fresh.overlay)
    np.testing.assert_array_equal(before.surface,fresh.surface)


def test_refresh_endpoint_reuses_valid_geometry_and_finishes_with_current_outputs(gl_page,live):
    p=gl_page;before=p.evaluate('lastPolled')
    result=p.evaluate("async()=>await start('refresh')")
    assert result['state']=='done' and result['kind']=='refresh' and result['id']!=before
    assert p.evaluate("['analysis','editor','vectors','preview'].every(k=>projectSession.artifacts[k].state==='ready')")
    report=p.request.get(live[0]+'/api/projects/'+live[1]).json()['analysis']
    assert report['geometry_cache']['hit']


def test_manual_form_confirmation_saves_but_keeps_update_pending(gl_page,live):
    p=gl_page;posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate("RodoviaUpdatePolicy.setMode('manual');RodoviaMaterialsHub.open()")
    p.locator('#pavement_material').select_option('rigido');p.locator('#rsPanelSave').click()
    p.wait_for_function('!RodoviaPanels.opened');p.wait_for_timeout(1100)
    assert not posts and 'pendente' in p.locator('#rsUpdateState').inner_text().lower()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['pavement_material']=='rigido'
    screenshot(p,'14223_manual_pendente')


def test_automatic_form_confirmation_runs_one_refresh_with_confirmed_values(gl_page,live):
    p=gl_page;before=p.evaluate('lastPolled');posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate("RodoviaUpdatePolicy.setMode('automatic');RodoviaMaterialsHub.open()")
    p.locator('#pavement_material').select_option('flexivel');p.locator('#rsPanelSave').click()
    p.wait_for_function('(old)=>lastPolled!==old',arg=before,timeout=30000)
    p.wait_for_function('!task&&!taskRequestPending',timeout=60000)
    assert len(posts)==1 and not p.evaluate('RodoviaPanels.opened')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['pavement_material']=='flexivel'
    assert p.evaluate("projectSession.artifacts.preview.state==='ready'")
    screenshot(p,'14223_automatico_concluido')


def test_explicit_project_save_refreshes_once_in_manual_mode(gl_page):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')");posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate('RodoviaUpdatePolicy.saveProject()')
    assert len(posts)==1 and p.evaluate("projectSession.artifacts.preview.state==='ready'")


def test_reopening_project_refreshes_without_result_reload_loop(gl_page,live):
    p=gl_page;posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate('(id)=>load(id)',live[1]);p.wait_for_timeout(600)
    assert len(posts)==1 and p.evaluate('!task&&!taskRequestPending')


def test_save_as_refreshes_copy_and_preserves_source(gl_page,live):
    p=gl_page;before=live[1]
    p.evaluate("void RodoviaUpdatePolicy.saveAs()")
    p.locator('#inputValue').fill('Cópia com cálculo completo');p.locator('#inputOk').click()
    p.wait_for_function('(old)=>pid!==old',arg=before,timeout=15000)
    p.wait_for_function("!task&&!taskRequestPending&&projectSession.artifacts.preview?.state==='ready'",timeout=60000)
    new=p.evaluate('pid');assert new!=before
    assert (live[2]/before/'input.dxf').read_bytes()==(live[2]/new/'input.dxf').read_bytes()


def test_manual_cancels_pending_automatic_confirmation_without_submitting(page):
    seed(page)
    result=page.evaluate("async()=>{pid='policy';RodoviaUpdatePolicy.setMode('automatic');RodoviaUpdatePolicy.committed();RodoviaUpdatePolicy.setMode('manual');await new Promise(r=>setTimeout(r,500));return RodoviaUpdatePolicy.snapshot()}")
    assert result==dict(mode='manual',waiting=False)


def test_empty_identified_project_opens_without_invalid_calculation(gl_page,live):
    p=gl_page;r=p.request.post(live[0]+'/api/projects',data={'name':'Sem arquivos ainda'});assert r.ok
    identity=r.json()['id'];posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate('(id)=>load(id)',identity)
    assert p.evaluate('pid')==identity and not posts and 'Importe' in p.locator('#message').inner_text()


def test_mode_survives_browser_reload_and_reuses_current_results(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('automatic')")
    p.reload(wait_until='domcontentloaded')
    p.wait_for_function("!!window.RodoviaUpdatePolicy&&!!pid&&projectSession.artifacts.editor?.state==='ready'&&!task&&!taskRequestPending",timeout=60000)
    assert p.locator('#rsUpdateMode').input_value()=='automatic'
    assert p.evaluate('pid')==live[1]


def test_model_dialog_automatic_save_runs_once_with_saved_density(gl_page,live):
    p=gl_page;before=p.evaluate('lastPolled');posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate("""()=>{RodoviaUpdatePolicy.setMode('automatic');RodoviaModelDialog.open({id:'testPolicyModel',title:'Confirmação de densidade',html:'<label>Densidade<input name="density" value="4"></label>',save:async d=>{$('traffic_density').value=d.querySelector('input').value;scheduleSave();await save()}})}""")
    p.locator('#testPolicyModel [data-save]').click()
    p.wait_for_function('(old)=>lastPolled!==old&&!task&&!taskRequestPending',arg=before,timeout=60000)
    assert len(posts)==1 and p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['traffic_density']==4


def test_invalid_confirmation_does_not_start_automatic_calculation(gl_page):
    p=gl_page;posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate("RodoviaUpdatePolicy.setMode('automatic');openSection('Configuração')")
    p.locator('#name').fill('');p.locator('#rsPanelSave').click();p.wait_for_timeout(600)
    assert p.evaluate('!!RodoviaPanels.opened') and not posts
    assert 'Não foi salvo' in p.locator('#rsPanelStatus').inner_text()


def test_internal_file_reload_defers_calculation_until_upload_is_released(gl_page,live):
    p=gl_page;before=p.evaluate('lastPolled')
    p.evaluate('(id)=>{fileMutationPending=true;return load(id)}',live[1])
    assert p.evaluate('lastPolled')==before and p.evaluate('RodoviaUpdatePolicy.snapshot().waiting')
    p.evaluate('fileMutationPending=false')
    p.wait_for_function('(old)=>lastPolled!==old&&!task&&!taskRequestPending',arg=before,timeout=60000)


def test_video_refreshes_model_and_publishes_current_editor_and_vectors(gl_page,live):
    from app.encoding import validate_mp4,ffmpeg_exe
    p=gl_page;p.evaluate("async()=>{$('render_workers').value='1';await save()}")
    result=p.evaluate("async()=>await start('render')")
    assert result['state']=='done'
    d=live[2]/live[1];info=json.loads((d/'video.json').read_text())
    assert info['geometry_cache_hit'] and validate_mp4(ffmpeg_exe(),d/'video.mp4',72,1280,720,24)['ok']
    assert p.evaluate("['analysis','editor','vectors','video'].every(k=>projectSession.artifacts[k].state==='ready')")


def test_render_confirmation_consumes_automatic_refresh_without_a_second_job(gl_page):
    p=gl_page;p.evaluate("async()=>{$('render_workers').value='1';await save();RodoviaUpdatePolicy.setMode('automatic');RodoviaMaterialsHub.open()}")
    p.locator('#pavement_material').select_option('rigido' if p.locator('#pavement_material').input_value()!='rigido' else 'flexivel')
    posts=[];p.on('request',lambda r:posts.append(r.url.rsplit('/',1)[-1]) if r.method=='POST' and r.url.rsplit('/',1)[-1] in ('refresh','render') else None)
    p.evaluate("window.renderFinished=null;window.renderError=null;void start('render').then(r=>window.renderFinished=r).catch(e=>window.renderError=e.message)")
    p.locator('#rsPanelDecision [data-choice=save]').click()
    p.wait_for_function('renderFinished||renderError',timeout=180000)
    assert p.evaluate('renderError') is None
    p.wait_for_timeout(900)
    assert posts==['render'] and p.evaluate('!RodoviaUpdatePolicy.snapshot().waiting')


def test_3d_rebuild_preserves_camera_light_time_and_technical_visibility(gl_page):
    p=gl_page;open3d(p)
    p.locator('[data-rs3d=top3d]').click();p.locator('[data-rs3d=light3d]').click();p.locator('[data-rs3d=flows3d]').click();p.evaluate('Rodovia3D.setTime(1)')
    before=p.evaluate('Rodovia3D.stats()');assert p.evaluate('Rodovia3D.open(true)')
    after=p.evaluate('Rodovia3D.stats()')
    assert after['light']==before['light'] and after['time']==before['time'] and after['diagnostics']==before['diagnostics']


def test_cancelled_refresh_keeps_previous_preview_and_sources(tmp_path,monkeypatch):
    from app import store,worker
    root=tmp_path/'data';root.mkdir();monkeypatch.setattr(store,'ROOT',root);monkeypatch.setattr(store,'DB',root/'studio.sqlite3');store.init()
    identity='a'*32;d=root/identity;d.mkdir();d,s=project(d)
    original=(d/'input.dxf').read_bytes();(d/'preview.png').write_bytes(b'previous-preview')
    with store.connect() as c:
        c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(identity,s.name))
        c.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',('c'*32,identity,'refresh','cancel_requested','Cancelar'))
    assert worker.run('c'*32)==0 and store.job('c'*32)['state']=='cancelled'
    assert (d/'input.dxf').read_bytes()==original and (d/'preview.png').read_bytes()==b'previous-preview'


def test_failed_3d_refresh_keeps_existing_view(gl_page):
    p=gl_page;open3d(p)
    p.route('**/api/projects/*/scene3d',lambda r:r.fulfill(status=503,json={'detail':'Falha de cálculo controlada'}))
    assert p.evaluate('Rodovia3D.open(true)') is False
    assert p.evaluate('Rodovia3D.stats().ready&&Rodovia3D.stats().stale')
    assert p.locator('#rsViewport3D canvas').count()==1 and p.locator('#rsViewport3D').is_visible()


def test_finishing_task_does_not_commit_or_close_a_form_opened_during_calculation(page):
    seed(page);page.evaluate("pid='editing';openSection('Configuração')")
    page.locator('#name').fill('Ainda editando')
    result=page.evaluate("""async()=>{
      const before={api,load,save};let writes=0;savePending=true;
      api=async()=>({id:'complete',kind:'refresh',project:pid,state:'done',progress:1,message:'Concluído'});
      load=async()=>true;save=async()=>{writes++;throw Error('Não salvar uma edição não confirmada.')};
      try{await poll('complete');return {writes,opened:!!RodoviaPanels.opened,pending:savePending,value:$('name').value}}
      finally{api=before.api;load=before.load;save=before.save}
    }""")
    assert result==dict(writes=0,opened=True,pending=True,value='Ainda editando')
