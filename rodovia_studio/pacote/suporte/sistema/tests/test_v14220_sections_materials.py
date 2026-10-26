import json,os
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import box
from app.models import Settings,RouteAlignment
from app.routes import build_lanes,raw_paths,preview
from app.native_axes import axis_fingerprint
from app.traffic import TrafficNetwork
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot

AXIS=np.array([[0.,0.],[600.,0.]])


@pytest.mark.parametrize('layer,expected',[('ACOSTAMENTO_EXISTENTE','shoulder'),('ACOSTAMENTO_PROJETADO','shoulder'),
 ('OAE_EXISTENTE','oae'),('CORTE_EXISTENTE','cut'),('CANTEIRO_EXISTENTE','median'),('PAVIMENTO_EXISTENTE','existing_pavement'),('PAVIMENTO_PROJETADO','pavement')])
def test_existing_is_condition_not_surface_type(layer,expected):
    import ezdxf
    from app.geometry import hatch_signature
    doc=ezdxf.new();doc.layers.new(layer);h=doc.modelspace().add_hatch(dxfattribs={'layer':layer})
    h.paths.add_polyline_path([(0,0),(100,0),(100,20),(0,20)],is_closed=True)
    assert hatch_signature(h,layer,doc)[1]['suggested_role']==expected


def route(dual=False,third=False,**extra):
    count=2 if dual else 1
    left=[dict(kind='pista',width_m=3.5) for _ in range(count)]+[dict(kind='acostamento',width_m=2.5)]
    right=[dict(kind='pista',width_m=3.5) for _ in range(count+int(third))]+[dict(kind='acostamento',width_m=2.5)]
    return dict(id='r',name='Seção central',points=[dict(x=x,y=y) for x,y in AXIS],sections_only=True,section_surface=True,
                source_axis_fingerprint=axis_fingerprint(AXIS,'EIXO'),
                cross_sections=[dict(id='s',start_m=0,end_m=600,type='dupla' if dual else 'simples',median_m=3 if dual else 0,left=left,right=right)],**extra)


def network(settings,obstacles=()):
    return TrafficNetwork([],obstacles,[dict(points=AXIS,layer='EIXO',role='axis')],AXIS,np.array([0.,600.]),settings)


@pytest.mark.parametrize('dual,third,count',[(False,False,2),(False,True,3),(True,False,4),(True,True,5)])
def test_explicit_typical_section_generates_continuous_lanes_without_dxf_pavement_hatch(dual,third,count):
    s=Settings(route_alignments=[route(dual,third)],hydrography=False,signage_detail='basic')
    n=network(s)
    assert len(n.raw_info)==count and len(n.paths)==count
    assert all(p['length']>=599 for p in n.paths)
    from app.flow_diagnostics import flow_diagnostics
    assert all(row['technical_status']=='ok' for row in flow_diagnostics(n))
    for lane in build_lanes(s.route_alignments[0]):
        p=lane['points'];assert p[-1,0]>p[0,0] if lane['dir']=='f' else p[-1,0]<p[0,0]
        assert np.all(p[:,1]<0) if lane['dir']=='f' else np.all(p[:,1]>0)


def test_lane_selection_preserves_other_lane_positions_and_never_enables_shoulder():
    r=route(True);r['cross_sections'][0]['right'][0]['traffic_enabled']=False
    s=Settings(route_alignments=[r]);lanes=build_lanes(s.route_alignments[0])
    assert len(lanes)==3
    right=[p for p in lanes if p['dir']=='f'];assert len(right)==1 and right[0]['lane']==1
    assert float(right[0]['points'][10,1])==pytest.approx(-6.75)


def test_short_intervals_are_absent_from_motor_and_technical_preview():
    r=route();r['cross_sections'][0].update(start_m=100,end_m=130)
    s=Settings(route_alignments=[r],min_route_segment_m=50)
    assert not raw_paths(s) and not preview(s) and not network(s).paths


def test_section_surface_keeps_real_barriers_and_manual_disable():
    s=Settings(route_alignments=[route()],hydrography=False,signage_detail='basic')
    n=network(s,[box(295,-20,305,20)])
    assert all(not(p['p'][:,0].min()<295 and p['p'][:,0].max()>305) for p in n.paths)
    disabled=Settings(route_alignments=[route(enabled=False)],hydrography=False,signage_detail='basic')
    assert not network(disabled).paths


def test_source_binding_can_be_undone_and_does_not_suppress_another_level():
    assert axis_fingerprint(AXIS,'EIXO',0)!=axis_fingerprint(AXIS,'EIXO',1)
    s=Settings(route_alignments=[route()]);assert network(s).native_axis_report['joined']==0
    assert len(network(s).raw_info)==2
    # Remover a derivação elimina a associação, sem alterar route_directions.
    s.route_alignments=[]
    from app.native_axes import native_paths
    native,_=native_paths([dict(points=AXIS,layer='EIXO',role='axis')],s,box(-20,-20,620,20))
    assert len(native)==1 and s.route_directions=={}


def test_density_box_remains_editable_and_typing_activates_density(gl_page,live):
    p=gl_page;p.evaluate("()=>{fill({...collect(),traffic_demand_vphpl:3500});psOpenHub('video')}")
    p.get_by_text('Tráfego: simulação, engarrafamento e canteiro',exact=True).click()
    assert p.locator('#traffic_density').is_enabled()
    p.locator('#traffic_density').fill('5')
    assert p.locator('#traffic_demand_vphpl').input_value()==''
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=15000)
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert cfg['traffic_density']==5 and cfg['traffic_demand_vphpl'] is None


def test_axis_chooser_builds_section_from_real_dxf_and_shows_lane_controls(gl_page,live):
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending',timeout=60000)
    p.evaluate('RodoviaSections.chooseAxis()')
    p.wait_for_selector('#rsChooseFlowAxis')
    p.locator('#rsChooseFlowAxis [name=axis]').select_option('axis:0')
    p.locator('#rsChooseFlowAxis [data-save]').click();p.wait_for_selector('#rsRoadSections')
    d=p.locator('#rsRoadSections');d.locator('[name=template]').select_option('dupla3')
    d.locator('[data-build-bands]').click()
    assert d.locator('[data-left] .rsSectionBand').count()==3
    assert d.locator('[data-right] .rsSectionBand').count()==4
    assert d.locator('[data-right] .rsSectionBand').last.locator('input[type=checkbox]').is_disabled()
    screenshot(p,'14220_secao_tipica_montagem')
    d.locator('[data-save]').click();p.wait_for_selector('#rsRoadSections',state='detached')
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];r=cfg['route_alignments'][-1]
    assert r['section_surface'] and r['sections_only'] and r['source_axis_fingerprint']
    assert len([b for b in r['cross_sections'][0]['right'] if b['kind']=='pista'])==3
    assert cfg['route_directions'].get('0','auto')=='auto'


def test_artistic_preset_preserves_geometries_and_sets_natural_materials(gl_page):
    p=gl_page;p.evaluate("()=>{window.marksBefore=JSON.stringify(M);psOpenHub('video')}")
    p.locator('#rsArtisticPreset').click()
    values=p.evaluate("()=>({same:JSON.stringify(M)===marksBefore,profile:$('style_profile').value,texture:$('texture_style').value,earth:$('earthwork_look').value})")
    assert values==dict(same=True,profile='padrao',texture='artistico',earth='natural')
    screenshot(p,'14220_maquete_artistica')


def test_all_engineering_materials_render_to_real_mp4_and_3d(tmp_path):
    import ezdxf,cv2
    from test_v1425_scene3d import project
    from app.render import render
    from app.encoding import validate_mp4,ffmpeg_exe
    from app.scene3d import build
    d,s=project(tmp_path)
    doc=ezdxf.readfile(d/'input.dxf');m=doc.modelspace()
    for i,name in enumerate(['PAVIMENTO_EXISTENTE','ACOSTAMENTO_EXISTENTE','ACOSTAMENTO_PROJETADO','CANTEIRO','CORTE','ATERRO','OAE']):
        doc.layers.new(name);y=7800030+i*18;h=m.add_hatch(dxfattribs={'layer':name});h.paths.add_polyline_path([(500040,y),(500460,y),(500460,y+12),(500040,y+12)],is_closed=True)
    doc.saveas(d/'input.dxf')
    s=Settings.model_validate({**s.model_dump(),'render_workers':1,'texture_style':'artistico','earthwork_look':'natural','detail_textures':True,
       'oae_marks':[dict(id='bridge',start=dict(x=500170,y=7800000),end=dict(x=500270,y=7800000))],
       'railways':[dict(id='rail',points=[dict(x=500050,y=7799970),dict(x=500450,y=7799970)],min_wagons=5,max_wagons=5)]})
    r=route(True);p=np.array([[500050.,7800000.],[500450.,7800000.]])
    r['points']=[dict(x=x,y=y) for x,y in p];r['cross_sections'][0]['end_m']=400;r['source_axis_fingerprint']=axis_fingerprint(p,'EIXO')
    s.route_alignments=[RouteAlignment.model_validate(r)]
    (d/'config.json').write_text(s.model_dump_json())
    video=render(d,s);result=validate_mp4(ffmpeg_exe(),video,72,1280,720,24);assert result['ok']
    data=build(d,s);assert any(mesh.get('asset_material')=='concrete' for mesh in data['meshes'])
    assert data['vehicles'] and data['simulation_report']['rear_collisions']==0 and data['simulation_report']['side_collisions']==0
    if os.environ.get('VISUAL_ARTIFACTS'):
        out=Path(os.environ['VISUAL_ARTIFACTS']);out.mkdir(parents=True,exist_ok=True)
        cap=cv2.VideoCapture(str(video));cap.set(cv2.CAP_PROP_POS_FRAMES,70);ok,frame=cap.read();cap.release();assert ok
        cv2.imwrite(str(out/'14220_materiais_video.png'),frame)
        (out/'video_materiais.json').write_text(json.dumps(result,indent=2))


def test_technical_hatch_is_preserved_but_not_overlaid_on_natural_maquette():
    from app.pavement import chosen
    s=Settings(texture_style='artistico',style_profile='padrao',natural_materials_only=True,pavement_styles={'pavement':dict(pattern='diagonal')})
    assert chosen(s,'pavement') is None and s.pavement_styles['pavement'].pattern=='diagonal'
    s.style_profile='tecnico';assert chosen(s,'pavement').pattern=='diagonal'


def test_natural_presentation_invalidates_surface_cache_without_removing_saved_hatch(tmp_path):
    from test_v1425_scene3d import project
    from app.render import Scene
    d,s=project(tmp_path,traffic=False)
    s=Settings.model_validate({**s.model_dump(),'imagery_pixels':2048,'pavement_styles':{'pavement':dict(pattern='diagonal')}})
    first=Scene(d,s);before=first.overlay.copy();del first
    natural=s.model_copy(update=dict(natural_materials_only=True))
    second=Scene(d,natural)
    assert not second.geometry_cache_hit and not np.array_equal(before,second.overlay)
    assert natural.pavement_styles['pavement'].pattern=='diagonal'
    del second
    third=Scene(d,natural);assert third.geometry_cache_hit
