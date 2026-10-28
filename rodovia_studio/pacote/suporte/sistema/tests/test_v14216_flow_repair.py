import numpy as np
from shapely.geometry import box,LineString
from app.flow_fit import fit_offset,physical_obstacles
from app.traffic import valid_centers
from test_v14213_continuity import network,AXIS
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_reduces_offset_to_fit_narrow_pavement_without_moving_axis():
    q=np.column_stack([np.linspace(5,195,300),np.zeros(300)]);before=q.copy();normal=np.tile([0.,-1.],(len(q),1))
    surface=box(0,-2,200,2)
    assert not valid_centers(surface,q+normal*1.65).all()
    lane,valid,report=fit_offset(q,normal,1.65,surface)
    assert valid.all() and report['applied_m']<1.65
    np.testing.assert_array_equal(q,before)
    assert surface.covers(LineString(lane).buffer(.9))


def test_two_way_fit_never_merges_opposing_lanes_into_axis():
    q=np.column_stack([np.linspace(5,195,300),np.zeros(300)]);normal=np.tile([0.,-1.],(len(q),1))
    lane,valid,report=fit_offset(q,normal,1.65,box(0,-2,200,2),both=True)
    assert not valid.all() and np.min(np.abs(lane[:,1]))>=1.2


def test_perpendicular_reference_is_ignored_but_open_barrier_blocks():
    points=np.array([[300.,-30.],[300.,230.]])
    assert not physical_obstacles([dict(points=points,closed=False,role='edge_line')])
    obstacles=physical_obstacles([dict(points=points,closed=False,role='barrier')])
    n=network([dict(points=AXIS)],obstacles=obstacles)
    assert not any(min(p['p'][:,0])<299 and max(p['p'][:,0])>301 for p in n.paths)


def test_offset_reduction_cannot_cross_a_real_barrier():
    q=np.column_stack([np.linspace(5,195,300),np.zeros(300)]);normal=np.tile([0.,-1.],(len(q),1))
    _,mask,_=fit_offset(q,normal,1.65,box(0,-4,200,4).difference(box(95,-5,105,5)))
    assert not mask.all()


def test_repair_is_visible_and_cut_is_reachable_without_properties_hunt(page):
    seed(page);page.evaluate("()=>{pid='repair';editor.segments[0].mid=[0,0];editor.segments[0].technical_status='problem';editor.segments[0].technical_message='Bloqueio localizado';}")
    page.evaluate('RodoviaFlowRepair.advanced()')
    assert page.get_by_role('dialog',name='Corrigir fluxos').is_visible()
    assert 'sinal vermelho' in page.get_by_role('dialog',name='Corrigir fluxos').inner_text()
    screenshot(page,'14216_central_correcao')
    page.locator('.rsFlowRepairAdvanced').first.locator('summary').click()
    page.locator('[data-repair-action=cut]').click()
    assert page.evaluate('tool')=='flowcut'
    assert page.get_by_role('dialog',name='Corrigir fluxos').count()==0


def test_real_network_fits_one_way_dxf_axis_on_narrow_surface():
    n=network([dict(points=AXIS)],roads=[box(-10,-2,610,2)],route_directions={'axis:'+__import__('app.native_axes',fromlist=['axis_fingerprint']).axis_fingerprint(AXIS,'EIXO'):'forward'})
    assert n.paths and any(r.get('lateral_fits') for r in n.raw_info)
    assert max(p['length'] for p in n.paths)>590
    from app.vehicle_motion import analyze_motion
    assert all(analyze_motion(p['p'],allowed=n.allowed)['ok'] for p in n.paths)


def test_native_axis_not_blocked_by_nearest_axis_heuristic_but_manual_deny_remains():
    from app.traffic import TrafficNetwork
    from app.models import Settings
    from types import SimpleNamespace
    from shapely.geometry import Polygon
    def build(deny):
        n=TrafficNetwork.__new__(TrafficNetwork)
        n.s=Settings();n.main=[0,1];n.islands=[];n.bridges=Polygon();n.warnings=[]
        n.edges=[dict(p=AXIS.copy(),disabled=False,native_axis=True,kind='main')]
        n.connectors={};n.connections={};n.side=lambda p:0 if p[0]<300 else 1
        if deny:n.s.crossing_zones=[SimpleNamespace(kind='point',point=SimpleNamespace(x=300,y=0),radius_m=5,mode='deny')]
        n.crossing_rules();return n
    assert not build(False).edges[0]['disabled']
    assert build(True).edges[0]['disabled']


def test_criteria_review_is_explicit_and_keeps_safety_description(page):
    seed(page);page.evaluate("()=>{pid='repair';editor.segments[0].mid=[0,0]}")
    page.evaluate('RodoviaFlowRepair.advanced()');page.locator('[data-global=criteria]').click()
    assert 'não remove barreiras' in page.get_by_role('dialog').inner_text()
    assert page.locator('[data-mode=free]').is_visible()
    page.locator('[data-cancel]').click()


def test_barrier_holes_are_preserved_and_reference_lines_are_not_obstacles():
    item=dict(role='barrier',closed=True,points=[[0,0],[20,0],[20,20],[0,20]],holes=[[[5,5],[15,5],[15,15],[5,15]]])
    obstacle=physical_obstacles([item])[0]
    from shapely.geometry import Point
    assert not obstacle.covers(Point(10,10)) and obstacle.covers(Point(1,1))


def test_select_command_always_enables_editing_even_when_already_active(page):
    seed(page);page.evaluate("()=>{pid='repair';RodoviaFlowStudy.editing=true;vecOn.flows=false;editor.segments[0].mid=[0,0]}")
    page.evaluate('RodoviaFlowRepair.advanced()');page.locator('[data-global=select]').click()
    assert page.evaluate('RodoviaFlowStudy.editing && vecOn.flows && tool===\'pan\'')


def test_locate_defect_enables_flow_visibility_and_centers_world_point(page):
    seed(page);page.evaluate("()=>{pid='repair';vecOn.flows=false;editor.segments[0].mid=[0,0];editor.segments[0].technical_points=[{point:[30,0]}]}")
    page.evaluate('RodoviaFlowRepair.advanced()');page.locator('[data-repair-action=locate]').click()
    result=page.evaluate('()=>({center:C2W(canvas.width/2,canvas.height/2),visible:vecOn.flows&&RodoviaFlowStudy.editing})')
    assert result['visible'] and abs(result['center']['x']-30)<1e-6
