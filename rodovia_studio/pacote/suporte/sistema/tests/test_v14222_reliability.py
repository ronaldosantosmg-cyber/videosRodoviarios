import json,zlib
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box
from app.models import Settings,RouteAlignment
from app.routes import build_lanes
from app.route_lane_cache import RouteLaneCache
from app.flow_diagnostics import flow_diagnostics
from app.road_sections import continuity_report
from test_v14220_sections_materials import route,AXIS
from test_v1425_live_3d import live,gl_page
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_rejected_connection_does_not_block_valid_circulation():
    p=np.array([[0.,0.],[200.,0.]])
    net=SimpleNamespace(min_route=50,paths=[{'edges':[0]}],edges=[dict(base=0,disabled=False),dict(base=0,disabled=False)],
        raw_info=[dict(base=0,points=p)],origin_info={},rejected_edge_ids={1},
        rejected_paths=[dict(edges=[1],audit=dict(critical_center_xy=[150.,0.],reasons=['mudanca_brusca']))],allowed=box(-10,-10,210,10))
    before=list(net.paths);result=flow_diagnostics(net)[0]
    assert result['technical_status']=='adjustment' and result['technical_circulation']['enabled']
    assert result['technical_points'][0]['point']==[150.,0.] and net.paths==before
    assert 'diagnostic_audit' not in net.raw_info[0]


def test_real_unavailable_pavement_remains_red_and_located():
    p=np.array([[0.,0.],[200.,0.]])
    net=SimpleNamespace(min_route=50,paths=[],edges=[dict(base=0,disabled=False)],raw_info=[dict(base=0,points=p)],origin_info={},
        rejected_edge_ids={0},rejected_paths=[],allowed=box(-10,-10,80,10))
    result=flow_diagnostics(net)[0]
    assert result['technical_status']=='problem' and not result['technical_circulation']['enabled']
    assert 'corpo_fora_da_pista' in result['technical_reasons'] and result['technical_points']


def test_route_cache_rebuilds_only_changed_route_and_returns_independent_arrays(tmp_path,monkeypatch):
    import app.routes as routes
    a=RouteAlignment.model_validate(route());b=a.model_copy(deep=True);b.id='b';b.name='Rota B'
    calls=[];original=routes._build_lanes
    def track(r,s):calls.append(r.id);return original(r,s)
    monkeypatch.setattr(routes,'_build_lanes',track)
    cache=RouteLaneCache(tmp_path);settings=Settings()
    original_a=build_lanes(a,settings,cache);build_lanes(b,settings,cache)
    original_a[0]['points'][0,0]=99999
    changed=b.model_copy(deep=True);changed.cross_sections[0].right[0].width_m=4
    next_cache=RouteLaneCache(tmp_path)
    restored=build_lanes(a,settings,next_cache);build_lanes(changed,settings,next_cache)
    assert calls==['r','b','b'] and next_cache.hits==1 and next_cache.misses==1
    assert restored[0]['points'][0,0]!=99999


def test_route_cache_is_independent_of_density_but_respects_pare_siga(tmp_path):
    a=RouteAlignment.model_validate(route());cache=RouteLaneCache(tmp_path)
    build_lanes(a,Settings(traffic_density=1),cache);build_lanes(a,Settings(traffic_density=5),cache)
    settings=Settings(route_alignments=[a],alternating_zones=[dict(id='z',route_id='r',start_m=100,end_m=300)])
    build_lanes(a,settings,cache)
    assert cache.hits==1 and cache.misses==2


def test_corrupt_route_cache_is_rebuilt_and_original_route_preserved(tmp_path):
    a=RouteAlignment.model_validate(route());before=a.model_dump();cache=RouteLaneCache(tmp_path)
    expected=build_lanes(a,Settings(),cache)
    next((tmp_path/'_cache/route_lanes').glob('*.json.z')).write_bytes(zlib.compress(b'{"lanes": []}'))
    result=build_lanes(a,Settings(),cache)
    np.testing.assert_array_equal(expected[0]['points'],result[0]['points'])
    assert cache.invalid==1 and a.model_dump()==before


def test_cached_lanes_do_not_bypass_new_physical_barrier(tmp_path):
    from app.traffic import TrafficNetwork
    s=Settings(route_alignments=[route()],hydrography=False,signage_detail='basic')
    def net(obstacles):return TrafficNetwork([],obstacles,[dict(points=AXIS,layer='EIXO',role='axis')],AXIS,np.array([0.,600.]),s,directory=tmp_path)
    first=net([]);blocked=net([box(295,-20,305,20)])
    assert first.paths and blocked.route_lane_cache.hits>0
    assert all(not(p['p'][:,0].min()<295 and p['p'][:,0].max()>305) for p in blocked.paths)


def test_section_gaps_are_reported_without_filling_them():
    a=RouteAlignment.model_validate(route());a.cross_sections[0].start_m=100;a.cross_sections[0].end_m=300
    before=a.model_dump();report=continuity_report(a)
    assert report['gaps']==[dict(start_m=0.,end_m=100.),dict(start_m=300.,end_m=600.)]
    assert before==a.model_dump()


def test_adjacent_sections_have_no_false_gap():
    a=RouteAlignment.model_validate(route());a.cross_sections[0].end_m=300
    second=a.cross_sections[0].model_copy(deep=True);second.id='second';second.start_m=300;second.end_m=600;a.cross_sections.append(second)
    assert continuity_report(a)['gaps']==[]


def test_picked_material_keeps_original_internal_voids(tmp_path):
    from app.surface_marks import items
    from app.webmap import write_lines,pick_area
    from shapely.geometry import Polygon
    outer=np.array([[0,0],[100,0],[100,100],[0,100]],float);hole=np.array([[30,30],[50,30],[50,50],[30,50]],float)
    entity=dict(role='pavement',layer='PAVIMENTO',closed=True,points=outer,holes=[hole])
    write_lines(tmp_path,[entity]);assert pick_area(tmp_path,40,40) is None
    assert pick_area(tmp_path,10,10)['has_holes']
    s=Settings(pavement_areas=[dict(id='material',source='picked',material='rigido',points=[dict(x=x,y=y) for x,y in outer])])
    result=items(s,[entity],[])
    assert sum(Polygon(e['points'],holes=e.get('holes',[])).area for e in result)==pytest.approx(9600)
    assert not any(Polygon(e['points'],holes=e.get('holes',[])).contains(__import__('shapely').geometry.Point(40,40)) for e in result)


def test_cached_auto_material_follows_project_default_without_changing_manual_material(tmp_path):
    from test_v1425_scene3d import project
    from app.geometry import analyze
    d,s=project(tmp_path,traffic=False)
    def area(identity,x,material):return dict(id=identity,name=identity,points=[dict(x=x,y=7800000),dict(x=x+40,y=7800000),dict(x=x+40,y=7800010),dict(x=x,y=7800010)],material=material)
    s=Settings.model_validate({**s.model_dump(),'pavement_areas':[area('auto',500050,'auto'),area('manual',500150,'flexivel')]})
    analyze(d,s);items,_,_,_,report=analyze(d,s.model_copy(update={'pavement_material':'rigido'}))
    assert report['geometry_cache']['hit']
    marks={e['mark']:e for e in items if e.get('mark')}
    assert marks['auto']['material']=='rigido' and marks['manual']['material']=='flexivel'


def test_route_cache_refuses_symlink_to_other_data(tmp_path):
    outside=tmp_path/'persistent';outside.mkdir();cache_dir=tmp_path/'project/_cache';cache_dir.mkdir(parents=True)
    (cache_dir/'route_lanes').symlink_to(outside,target_is_directory=True)
    build_lanes(RouteAlignment.model_validate(route()),Settings(),RouteLaneCache(tmp_path/'project'))
    assert list(outside.iterdir())==[]


def test_optional_route_cache_failure_cannot_stop_valid_calculation(tmp_path,monkeypatch):
    from pathlib import Path
    replace,unlink=Path.replace,Path.unlink
    def fail_replace(path,*args,**kwargs):
        if path.suffix=='.tmp':raise OSError('Cache indisponível no ensaio.')
        return replace(path,*args,**kwargs)
    def fail_unlink(path,*args,**kwargs):
        if path.suffix=='.tmp':raise OSError('Temporário ocupado no ensaio.')
        return unlink(path,*args,**kwargs)
    monkeypatch.setattr(Path,'replace',fail_replace);monkeypatch.setattr(Path,'unlink',fail_unlink)
    cache=RouteLaneCache(tmp_path);lanes=build_lanes(RouteAlignment.model_validate(route()),Settings(),cache)
    assert lanes and cache.write_errors==2


def test_same_dxf_layer_can_keep_different_3d_materials(tmp_path,monkeypatch):
    from test_v1425_scene3d import project
    from app.render import Scene
    from app.scene3d import build
    d,s=project(tmp_path,traffic=False);original=Scene.light.__func__
    def tagged(cls,*args,**kwargs):
        scene=original(cls,*args,**kwargs);e=next(e for e in scene.items if e['role']=='pavement')
        e['material']='flexivel';other={**e,'points':e['points']+np.array([0,60]),'material':'rigido'};scene.items.append(other);return scene
    monkeypatch.setattr(Scene,'light',classmethod(tagged))
    data=build(d,s);meshes=[m for m in data['meshes'] if m['role']=='pavement']
    assert len(meshes)==2 and {m['asset_material'] for m in meshes}=={'asphalt','concrete'}


def test_repair_center_has_three_primary_actions_and_collapsed_advanced(page):
    seed(page);page.evaluate("()=>{pid='repair';editor.segments[0].technical_status='problem';editor.segments[0].technical_message='Defeito de teste';editor.section_continuity=[{name:'Eixo',gaps:[{start_m:100,end_m:120}]}]}")
    page.get_by_role('tab',name='Tráfego',exact=True).click();page.evaluate('RodoviaFlowRepair.advanced()')
    row=page.locator('[data-flow-repair]').first
    for name in ['Localizar','Tentar correção automática','Editar manualmente']:assert row.get_by_role('button',name=name,exact=True).is_visible()
    assert row.get_by_role('button',name='Recortar início/fim',exact=True).is_hidden()
    assert '100.0 a 120.0' in page.locator('.rsSectionGaps').inner_text()
    row.locator('summary').click();assert row.get_by_role('button',name='Recortar início/fim',exact=True).is_visible()
    screenshot(page,'14222_central_correcao')


def test_contextual_dxf_pavement_uses_material_editor_not_generic_overlay(page):
    seed(page);page.evaluate("()=>{pid='materials';dxfSel={role:'pavement',layer:'PAVIMENTO',points:[[0,0],[100,0],[100,20],[0,20]]};sel=null;selSet=[]}")
    page.get_by_role('tab',name='Cena',exact=True).click();page.get_by_role('button',name='Materiais e texturas',exact=True).click()
    page.get_by_role('button',name='Material da área selecionada',exact=True).click()
    assert page.locator('#texDlg').is_visible()
    assert page.locator('#td_mat').is_visible()
    screenshot(page,'14222_material_contextual')


def test_custom_web_tiles_are_project_scoped_but_public_esri_is_reusable(page):
    result=page.evaluate("()=>{cfg.web_imagery={source:'xyz',url:'https://example.invalid/{z}/{x}/{y}'};pid='a';const a=tileKey(12,1,1);pid='b';const b=tileKey(12,1,1);cfg.web_imagery.source='esri';pid='a';const c=tileKey(12,1,1);pid='b';return {private:a!==b,public:c===tileKey(12,1,1)}}")
    assert result==dict(private=True,public=True)


def test_late_web_tile_cannot_redraw_another_private_project(page):
    result=page.evaluate("()=>{cfg.web_imagery={source:'xyz',url:'https://example.invalid/{z}/{x}/{y}'};pid='before';const tile=getTile(12,1,1);pid='after';const original=tileRedraw;let calls=0;tileRedraw=()=>calls++;try{tile.img.onload();return calls}finally{tileRedraw=original}}")
    assert result==0


def test_online_zoom_out_keeps_available_child_detail(page):
    seed(page)
    result=page.evaluate("""()=>{
      const original=getTile,paint=ctx.drawImage;let count=0;getTile=()=>({ok:false});tiles.clear();
      cfg.web_imagery={source:'esri'};geo={m0x:0,m0y:10,R0:1};view={s:.03,ox:0,oy:0};
      const image=document.createElement('canvas');image.width=image.height=256;
      tiles.set(tileKey(13,4096,4094),{img:image,ok:true});ctx.drawImage=()=>count++;
      try{drawTiles();return count}finally{getTile=original;ctx.drawImage=paint}
    }""")
    assert result>0


def test_custom_profile_can_be_selected_and_saved(gl_page,live):
    p=gl_page;p.evaluate('RodoviaMaterialsHub.open()')
    p.locator('#rsPresentationProfile').select_option('artistic');p.locator('#rsPresentationProfile').select_option('custom')
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened')
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert config['style_profile']=='padrao' and config['natural_materials_only'] is False
    p.evaluate('RodoviaMaterialsHub.open()');assert p.locator('#rsPresentationProfile').input_value()=='custom'


def test_manual_disabled_flow_has_no_automatic_reactivation_action(page):
    seed(page);page.evaluate("()=>{pid='repair';editor.segments[0].disabled=true;editor.segments[0].technical_status='problem'}")
    page.evaluate('RodoviaFlowRepair.advanced()')
    assert page.locator('[data-flow-repair]').first.get_by_role('button',name='Tentar correção automática',exact=True).is_disabled()


def test_keyboard_tabs_and_technical_tool_highlight_remain_consistent(page):
    page.get_by_role('tab',name='Projeto',exact=True).focus();page.keyboard.press('ArrowRight')
    assert page.get_by_role('tab',name='Editar',exact=True).get_attribute('aria-selected')=='true'
    page.evaluate("setTool('move')")
    assert page.locator('[data-rs-tool=move]').get_attribute('aria-pressed')=='true'
    page.locator('#rsQuickNavigation [data-rs-tool=pan]').click()
    assert page.locator('[data-rs-tool=move]').get_attribute('aria-pressed')=='false'
