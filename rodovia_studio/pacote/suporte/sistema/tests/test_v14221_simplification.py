import hashlib,json,zlib
from pathlib import Path
import numpy as np
import pytest
from app.models import Settings
from app.dependencies import revisions
from app.geometry import analyze
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page,open3d
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


@pytest.mark.parametrize('changes',[dict(traffic_density=6),dict(traffic_speed_kmh=60),dict(traffic_demand_vphpl=5000),dict(traffic_capacity_vphpl=3500)])
def test_simulation_settings_keep_geometry_and_editor_valid(tmp_path,changes):
    d,s=project(tmp_path);before=revisions(d,s);after=revisions(d,s.model_copy(update=changes))
    assert before['geometry']==after['geometry'] and before['editor']==after['editor']
    assert before['traffic']!=after['traffic'] and before['preview']!=after['preview']


def test_density_changes_real_vehicle_simulation_without_collisions():
    from test_v14212_traffic_safety import configuration,network
    from app.simulation import TrafficSim
    totals=[]
    for density in (1,5):
        settings=configuration(traffic_density=density,duration_s=20)
        sim=TrafficSim(network(settings),settings,lambda *args:'car',duration=20)
        report=sim.report();totals.append(report['vehicles'])
        assert report['rear_collisions']==report['side_collisions']==0
    assert totals[1]>totals[0]>0


@pytest.mark.parametrize('changes',[dict(role_colors={'pavement':'#334455'}),dict(natural_materials_only=True),dict(texture_style='artistico')])
def test_presentation_does_not_invalidate_editor(tmp_path,changes):
    d,s=project(tmp_path);a=revisions(d,s);b=revisions(d,s.model_copy(update=changes))
    assert a['editor']==b['editor'] and a['traffic']==b['traffic'] and a['preview']!=b['preview']


def test_geometry_cache_reuses_dxf_for_density_and_material_without_changing_source(tmp_path,monkeypatch):
    import app.geometry as geometry
    d,s=project(tmp_path);before=hashlib.sha256((d/'input.dxf').read_bytes()).hexdigest();calls=[];read=geometry.ezdxf.readfile
    def track(*args,**kwargs):calls.append(1);return read(*args,**kwargs)
    monkeypatch.setattr(geometry.ezdxf,'readfile',track)
    a=analyze(d,s);b=analyze(d,s.model_copy(update=dict(traffic_density=5)))
    c=analyze(d,s.model_copy(update=dict(pavement_material='rigido')))
    assert len(calls)==1 and b[4]['geometry_cache']['hit'] and c[4]['geometry_cache']['hit']
    np.testing.assert_array_equal(a[1],b[1]);assert any(e.get('material')=='rigido' for e in c[0] if e['role']=='pavement')
    assert hashlib.sha256((d/'input.dxf').read_bytes()).hexdigest()==before


def test_corrupt_geometry_cache_falls_back_and_preserves_original(tmp_path):
    d,s=project(tmp_path);a=analyze(d,s)
    cache=next((d/'_cache/geometry').glob('*.json.z'));cache.write_bytes(zlib.compress(b'[{}, {}, {}, {}, {}]'))
    b=analyze(d,s);assert not b[4]['geometry_cache']['hit'];np.testing.assert_array_equal(a[1],b[1])


def test_five_tabs_eight_menus_and_no_duplicate_visible_tool_catalog(page):
    assert page.locator('#rsToolTabs [role=tab]').all_text_contents()==['Projeto','Editar','Tráfego','Cena','Vídeo']
    assert page.locator('#menuBar [data-rs-menu]').all_text_contents()==['Arquivo','Editar','Projeto','Tráfego','Cena','Vídeo','Exibir','Ajuda']
    assert page.get_by_role('tab',name='Todas',exact=True).count()==0
    values=page.locator('#rsToolRibbon [data-activity] [data-rs-tool]:visible').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.rsTool)')
    assert len(values)==len(set(values))
    page.get_by_role('tab',name='Tráfego',exact=True).click()
    assert page.get_by_role('button',name='Configurar faixas',exact=True).is_visible()
    assert page.locator('[data-activity="Tráfego"] .rsAdvancedTools').evaluate_all('(items)=>items.length>0&&items.every(d=>!d.open)')
    screenshot(page,'14221_cinco_abas')


def test_progress_is_unique_in_footer_and_reports_failure_and_indeterminate(page):
    page.evaluate("progMostrar({id:'test',titulo:'Analisando',valor:null,info:'Etapa sem total conhecido'})")
    assert page.locator('#bottomBar #progress').count()==1
    assert page.locator('progress:visible').count()==1
    assert page.locator('#progress').get_attribute('value') is None
    page.evaluate("progFim('test','Falha controlada',true)")
    assert page.locator('#message').inner_text()=='Falha controlada'
    assert page.locator('#progress').get_attribute('value')=='0'
    assert page.locator('#pcCancel').is_hidden()
    screenshot(page,'14221_progresso_unico')


def test_polled_failure_keeps_single_progress_and_disables_old_eta(page):
    result=page.evaluate("""async()=>{
      const before=api;api=async()=>({id:'controlled-failure',state:'failed',progress:null,message:'Falha controlada',kind:'analyze',project:'none'});
      try{await poll('controlled-failure');return {value:$('progress').value,status:$('pcPct').textContent,oldHidden:$('taskTime').hidden,active:RodoviaProgress.snapshot().count}}
      finally{api=before}
    }""")
    assert result==dict(value=0,status='Falhou',oldHidden=True,active=0)


def test_zoom_and_undo_are_accessible_without_changing_tabs(page):
    seed(page);before=page.evaluate('view.s');page.get_by_role('button',name='Aproximar',exact=True).click()
    assert page.evaluate('view.s')>before
    page.evaluate("()=>{checkpoint();M.pois.push({id:'test',title:'Ponto',kind:'obra',x:10,y:10});changed()}")
    page.locator('#rsQuickNavigation [data-quick=undo]').click();assert page.evaluate('M.pois.some(p=>p.id==="test")') is False
    page.locator('#rsQuickNavigation [data-quick=redo]').click();assert page.evaluate('M.pois.some(p=>p.id==="test")') is True


def test_saving_density_and_marks_never_posts_calculation_jobs(gl_page):
    p=gl_page;posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.rsplit('/',1)[-1] in ('analyze','preview','scene3d','render') else None)
    p.evaluate("async()=>{$('traffic_density').value='3';scheduleSave();await save();checkpoint();M.direction_marks.push({id:'d',start:{x:500080,y:7800000},end:{x:500160,y:7800000}});changed();await save()}")
    p.wait_for_timeout(3000)
    assert not posts and p.evaluate('!!editor')
    assert 'pendente' in p.locator('#rsUpdateState').inner_text().lower()


def test_repeated_request_shares_one_real_job(gl_page):
    p=gl_page
    result=p.evaluate("async()=>{const a=start('analyze'),b=start('analyze');const same=a===b;const [x,y]=await Promise.all([a,b]);return {same,first:x.id,second:y.id,state:x.state,queue:RodoviaUpdates.snapshot()}}")
    assert result['same'] and result['first']==result['second'] and result['state']=='done'
    assert result['queue']['requests']==0


def test_explicit_update_refreshes_even_a_current_preview(gl_page):
    p=gl_page;p.evaluate("async()=>{await start('preview')}")
    before=p.evaluate('lastPolled');posts=[]
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/refresh') else None)
    p.evaluate('RodoviaUpdates.update()')
    assert len(posts)==1 and p.evaluate('lastPolled')!=before
    assert p.evaluate('!!baseImage&&!previewStale')


def test_queued_request_is_discarded_if_project_context_changes(page):
    seed(page)
    result=page.evaluate("async()=>{pid='queued-project';task='another';const pending=start('analyze');projectSession.context++;task='';return await pending}")
    assert result is False


def test_waiting_queue_can_be_cancelled_without_submitting_work(page):
    seed(page)
    result=page.evaluate("async()=>{pid='waiting-project';task='occupied';const request=start('analyze');RodoviaUpdates.clearQueue();const value=await request;task='';return {value,queue:RodoviaUpdates.snapshot()}}")
    assert result['value'] is False and result['queue']['requests']==0


def test_late_local_image_response_is_rejected_after_source_changes(page):
    result=page.evaluate("""async()=>{
      const original=window.fetch;let resolve;
      window.fetch=()=>new Promise(r=>resolve=r);
      pid='image-project';localInfo={key:'source-before'};
      const before=localTileKey(12,1,1),tile=getLocalTile(12,1,1);
      localInfo={key:'source-after'};const after=localTileKey(12,1,1);
      resolve(new Response(new Blob(['old image']),{status:200}));
      await new Promise(r=>setTimeout(r,50));window.fetch=original;
      return {different:before!==after,empty:tile.empty,src:tile.img.getAttribute('src')};
    }""")
    assert result['different'] and result['empty'] and result['src'] is None


def test_local_image_keeps_parent_detail_until_child_tile_arrives(page):
    seed(page)
    result=page.evaluate("""()=>{
      const fetchBefore=window.fetch;window.fetch=()=>new Promise(()=>{});
      pid='image-project';localTiles.clear();localInfo={key:'source',max_zoom:12,sources:[{merc:[0,0,10,10]}]};
      geo={m0x:0,m0y:10,R0:1};view={s:.03,ox:0,oy:0};
      const z=12,tx=2048,ty=2047,p=document.createElement('canvas');p.width=p.height=256;
      localTiles.set(localTileKey(z-1,tx>>1,ty>>1),{img:p,ok:true,used:1});
      const drawBefore=ctx.drawImage,calls=[];ctx.drawImage=function(...args){calls.push(args.length)};
      drawLocalTiles();ctx.drawImage=drawBefore;window.fetch=fetchBefore;
      return calls;
    }""")
    assert 9 in result


def test_saving_keeps_aerial_background_cache_and_old_technical_view(page):
    seed(page)
    result=page.evaluate("()=>{draw();const before=RodoviaLayers.stats();const original=editor;window.dispatchEvent(new CustomEvent('rodovia:project-state',{detail:{project:pid,artifacts:{editor:{state:'stale'}}}}));draw();return {same:editor===original,before,after:RodoviaLayers.stats()}}")
    assert result['same'] and result['before']['backgroundBuilds']==result['after']['backgroundBuilds']


def test_materials_window_uses_original_controls_and_saves_to_motor(gl_page,live):
    p=gl_page;p.get_by_role('tab',name='Cena',exact=True).click();p.get_by_role('button',name='Materiais e texturas',exact=True).click()
    p.wait_for_selector('#rsPanelPopup[open] #rsMaterialsSection')
    assert p.locator('#pavement_material').count()==1 and p.locator('#texEditor').is_visible()
    p.locator('#rsPresentationProfile').select_option('artistic');p.locator('#pavement_material').select_option('rigido')
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=15000)
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert cfg['pavement_material']=='rigido' and cfg['natural_materials_only'] is True
    assert cfg['style_profile']=='padrao' and cfg['earthwork_look']=='natural'
    screenshot(p,'14221_materiais_consolidados')


def test_canvas_pan_reuses_cache_and_full_release_matches_direct_drawing(page):
    seed(page)
    result=page.evaluate("()=>{draw();const before=RodoviaLayers.stats();drag={type:'pan'};view.ox+=10;draw();drag=null;draw();const cached=ctx.getImageData(0,0,canvas.width,canvas.height).data;RodoviaLayers.setEnabled(false);const direct=ctx.getImageData(0,0,canvas.width,canvas.height).data;let max=0;for(let i=0;i<cached.length;i++)max=Math.max(max,Math.abs(cached[i]-direct[i]));RodoviaLayers.setEnabled(true);return {before,after:RodoviaLayers.stats(),max}}")
    assert result['after']['panReuses']>result['before']['panReuses'] and result['max']<=3


def test_small_window_has_accessible_tabs_footer_and_controls(page):
    page.set_viewport_size(dict(width=1024,height=720));page.wait_for_timeout(100)
    for name in ['Projeto','Editar','Tráfego','Cena','Vídeo']:page.get_by_role('tab',name=name,exact=True).click()
    box=page.locator('#progCard').bounding_box();assert box['y']+box['height']<=720
    assert page.locator('body').evaluate('b=>b.scrollWidth<=innerWidth')
    screenshot(page,'14221_janela_1024')
