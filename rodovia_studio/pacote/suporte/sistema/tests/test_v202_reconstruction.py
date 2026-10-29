"""Reconstrução real e integral, separada da recuperação de partes."""
import json
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import box,LineString
from app.flow_reconstruction import reconstruct,continuity_evidence
from app.flow_recovery import recover_sections
from app.vehicle_motion import analyze_motion
from app.models import Settings
from app.traffic import TrafficNetwork


@pytest.mark.parametrize('reverse',[False,True])
def test_corridor_search_goes_around_physical_obstacle_without_crossing_it(reverse):
    p=np.array([[-50.,0.],[250.,0.]])
    if reverse:p=p[::-1].copy()
    source=p.copy();obstacle=box(80,-10,120,1);allowed=box(-60,-10,260,10).difference(obstacle)
    q,r=reconstruct(p,allowed)
    assert r['continuous'] and r['method']=='busca_no_corredor_validada'
    assert r['search_positions']<=42517 and r['search_links']<=250000
    assert q is not None and analyze_motion(q,allowed=allowed)['ok']
    assert not LineString(q).buffer(.9,cap_style='flat').intersects(obstacle)
    np.testing.assert_array_equal(q[[0,-1]],p[[0,-1]]);np.testing.assert_array_equal(source,p)
    assert r['max_deviation_m']<=8


def test_multiple_outside_defects_are_reconstructed_end_to_end():
    p=np.array([[0,0],[80,0],[84,8],[88,0],[160,0],[164,-8],[168,0],[300,0]],float)
    allowed=box(-10,-6,310,6);assert not allowed.covers(LineString(p))
    q,r=reconstruct(p,allowed)
    assert q is not None and r['continuous'] and r['endpoints_preserved']
    assert analyze_motion(q,allowed=allowed)['ok'];np.testing.assert_array_equal(q[[0,-1]],p[[0,-1]])


def test_full_barrier_never_becomes_partial_success():
    p=[[-50,0],[250,0]];allowed=box(-60,-10,260,10).difference(box(80,-20,120,20))
    pieces,partial=recover_sections(p,allowed)
    assert pieces and partial['status']=='partial'
    whole,report=recover_sections(p,allowed,reconstruct=True)
    assert whole==[] and report['status']=='blocked' and not report['reconstruction']['continuous']
    assert report['reconstruction']['reason']=='extremidades_sem_corredor_fisico_continuo'


@pytest.mark.parametrize('bad',[[[0,0],[float('nan'),2]],[[0,0],[0,0]],[[0,0],[float('inf'),2]]])
def test_invalid_geometry_is_refused(bad):
    assert reconstruct(bad,box(-10,-10,400,10))[0] is None


def test_separate_valid_itineraries_are_not_a_complete_route():
    def network(paths):
        return SimpleNamespace(raw_info=[{'origin_key':'x','reconstruction_requested':True,'recovery_reports':[{'status':'reconstructed'}]}],edges=[{'origin_key':'x','reconstruction_direction':True},{'origin_key':'x','reconstruction_direction':True}],paths=paths)
    assert not continuity_evidence(network([{'edges':[0]},{'edges':[1]}]),'x')['complete']
    assert continuity_evidence(network([{'edges':[0,1]}]),'x')['complete']


def build_network(repair=False,wall=False,disabled=False,cut=False):
    p=[[-50,0],[250,0]];obstacle=box(80,-20 if wall else -10,120,20 if wall else 1)
    values=dict(derive_traffic_paths=False,hydrography=False,signage_detail='basic',vehicle_paths='anterior',route_alignments=[dict(id='r',name='Rota',type='unico',lanes=1,points=[dict(x=x,y=y) for x,y in p])])
    if repair:values['flow_recoveries']=[dict(id='repair',x=0,y=0,reconstruct=True)]
    if disabled:values['flow_overrides']=[dict(x=0,y=0,action='disable')]
    if cut:values['flow_cuts']=[dict(id='cut',start=dict(x=70,y=0),end=dict(x=130,y=0))]
    return TrafficNetwork([box(-60,-10,260,10)],[obstacle],[],np.array(p,float),np.array([0.,300.]),Settings(**values))


def test_network_reconstruction_happens_before_invalid_samples_are_split():
    before=build_network();assert not any(p['length']>290 for p in before.paths)
    n=build_network(True);assert n.paths and max(p['length'] for p in n.paths)>290
    raw=n.raw_info[0];certificate=continuity_evidence(n,raw['origin_key']);assert certificate['complete']
    assert any(r['reconstruction']['method']=='busca_no_corredor_validada' for r in raw['recovery_reports'])


@pytest.mark.parametrize('option',['wall','disabled','cut'])
def test_manual_and_physical_constraints_prevent_false_release(option):
    n=build_network(True,**{option:True})
    assert not any(p['length']>290 for p in n.paths)
    assert all(not continuity_evidence(n,r['origin_key'])['complete'] for r in n.raw_info)


@pytest.fixture
def defective_project(tmp_path):
    import ezdxf
    from app import project_state as P
    from app.native_axes import axis_fingerprint
    from test_v14225_execution import publish
    d=tmp_path/('c'*32);d.mkdir();doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    axis=[(500050,7800000),(500350,7800000)];m.add_lwpolyline(axis,dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799994),(500400,7799994),(500400,7800006),(500000,7800006)],is_closed=True);doc.saveas(d/'input.dxf')
    local=[[50,0],[130,0],[134,8],[138,0],[230,0],[234,-8],[238,0],[350,0]]
    settings=Settings(layers={'axis':['EIXO'],'pavement':['PAVIMENTO']},route_directions={'axis:'+axis_fingerprint(axis,'EIXO'):'off'},route_alignments=[dict(id='R',name='Rota a reconstruir',type='unico',lanes=1,points=[dict(x=500000+x,y=7800000+y) for x,y in local])],derive_traffic_paths=False,vehicle_mix='classico',traffic=True,imagery='neutral',hydrography=False,width=1280,fps=24,duration_s=3,coordinates_confirmed=True,render_workers=1)
    P.save_config(d,settings.model_dump());data=publish(d,settings)
    segment=next(r for r in data['segments'] if r.get('route')=='R')
    assert segment['technical_status']=='problem'
    return d,settings,segment


def test_real_proposal_requires_whole_route_then_applies_revalidates_and_undoes(defective_project):
    from app import assisted_execution as E,project_state as P
    from test_v14225_execution import publish
    d,s,segment=defective_project;before=P.read_config(d);source=(d/'input.dxf').read_bytes()
    plan=E.preview(d,dict(signature=E.signature(d),segment=segment['id'],action='reconstruct'))
    assert plan['can_apply'] and plan['checks']['full_route_continuity']
    assert plan['reconstruction']['complete'] and plan['geometry']
    E.apply(d,plan['id']);result=publish(d,Settings.model_validate(P.read_config(d)))
    selected=[r for r in result['segments'] if r.get('route')=='R']
    assert selected and all(r['technical_reconstruction']['complete'] for r in selected)
    assert E.outcome(d,plan['id'])['resolved']
    E.undo(d,plan['id']);assert P.read_config(d)==before and (d/'input.dxf').read_bytes()==source


def test_reconstructed_route_reaches_actual_3d_and_decoded_video(defective_project):
    import os
    from app import assisted_execution as E,project_state as P
    from app.render import Scene,render
    from app.scene3d import build
    from app.encoding import ffmpeg_exe,validate_mp4
    d,s,segment=defective_project;plan=E.preview(d,dict(signature=E.signature(d),segment=segment['id'],action='reconstruct'));assert plan['can_apply']
    E.apply(d,plan['id']);s=Settings.model_validate(P.read_config(d));scene=Scene(d,s)
    paths=[p for p in scene.network.paths if p.get('route')=='R'];assert paths
    assert any(np.ptp(p['p'][:,0])>285 for p in paths)
    sim=scene.traffic();assert any(list(scene.traffic_iter(t)) for t in [0,.5,1.,1.5])
    data=build(d,s);assert data['vehicles']
    output=render(d,s);check=validate_mp4(ffmpeg_exe(),output,72,1280,720,24);assert check['ok']
    evidence=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rodovia202-evidence'));evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'202_rota_reconstruida_video.json').write_text(json.dumps({'mp4':check,'reconstruction':plan['reconstruction'],'itineraries':len(paths),'scope':'Cenário sintético; não reproduz o projeto salvo do usuário.'},ensure_ascii=False,indent=2)+'\n')


def test_internal_native_contact_is_not_blocked_by_independent_route_limit():
    from test_v14213_continuity import network,AXIS
    axes=[dict(points=AXIS),dict(points=np.array([[250.,0.],[250.,150.]])),dict(points=np.array([[275.,0.],[275.,150.]]))]
    n=network(axes,flow_recoveries=[dict(id='whole-axis',x=100,y=0,reconstruct=True)])
    selected=next(r for r in n.raw_info if r.get('native_id')=='0')
    assert continuity_evidence(n,selected['origin_key'])['complete']
    assert any(e.get('native_id')=='0' and e['length']<50 for e in n.edges)
    assert any(np.ptp(p['p'][:,0])>590 for p in n.paths)


def test_blocked_proposal_explains_localizes_and_cannot_apply_partial_route(defective_project):
    import ezdxf
    from app import assisted_execution as E,project_state as P
    from test_v14225_execution import publish
    d,s,_=defective_project;doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('BARREIRA');doc.modelspace().add_line((500200,7799980),(500200,7800020),dxfattribs={'layer':'BARREIRA'});doc.saveas(d/'input.dxf')
    s.layers['barrier']=['BARREIRA'];P.save_config(d,s.model_dump());data=publish(d,s);segment=next(r for r in data['segments'] if r.get('route')=='R')
    before=P.read_config(d);source=(d/'input.dxf').read_bytes()
    plan=E.preview(d,dict(signature=E.signature(d),segment=segment['id'],action='reconstruct'))
    assert not plan['can_apply'] and not plan['checks']['full_route_continuity']
    failures=[r['reconstruction'] for r in plan['reconstruction']['reports'] if r.get('reconstruction',{}).get('reason')]
    assert failures and all(r.get('message') and r.get('critical_point') for r in failures)
    assert any(abs(r['critical_point'][0]-500200)<3 for r in failures)
    with pytest.raises(ValueError,match='segura'):E.apply(d,plan['id'])
    assert P.read_config(d)==before and (d/'input.dxf').read_bytes()==source


from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_real_ui_refuses_partial_plan_and_locates_impediment(gl_page,live,defective_project):
    import ezdxf
    from app import project_state as P
    from test_v14225_execution import publish
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=180000)
    original,s,_=defective_project;d=live[2]/live[1];doc=ezdxf.readfile(original/'input.dxf');doc.layers.new('BARREIRA');doc.modelspace().add_line((500200,7799980),(500200,7800020),dxfattribs={'layer':'BARREIRA'});doc.saveas(d/'input.dxf');s.layers['barrier']=['BARREIRA']
    P.save_config(d,s.model_dump());publish(d,s);source=(d/'input.dxf').read_bytes()
    p.evaluate('(id)=>load(id)',live[1]);p.wait_for_function('!task&&!taskRequestPending',timeout=90000);before=P.read_config(d);p.evaluate('RodoviaExecution.open()')
    p.get_by_role('button',name='Reconstruir rota completa',exact=True).first.click()
    confirm=p.get_by_role('button',name='Confirmar e aplicar correção',exact=True);confirm.wait_for(timeout=90000)
    assert confirm.is_disabled()
    locate=p.get_by_role('button',name='Localizar impedimento',exact=True);assert locate.is_visible();locate.click()
    p.wait_for_timeout(150);center=p.evaluate('captureProjectView().center')
    assert center['x']==pytest.approx(500200,abs=3)
    assert p.locator('#rsReturnExecution').is_visible()
    assert P.read_config(d)==before and (d/'input.dxf').read_bytes()==source
    screenshot(p,'202_impedimento_localizado')


def test_warning_on_valid_geometry_does_not_offer_an_ineffective_repair(tmp_path):
    from app import assisted_execution as E,project_state as P,store,artifacts
    from test_v1425_scene3d import project
    from test_v14225_execution import publish
    d=tmp_path/('d'*32);d.mkdir();d,s=project(d);P.save_config(d,s.model_dump());data=publish(d,s)
    segment=next(row for row in data['segments'] if row['technical_circulation']['enabled'])
    segment.update(technical_status='adjustment',technical_message='Aviso de frota; geometria já contínua.')
    store.write_json(d/'editor.json',data);ticket=artifacts.begin(d,'test-warning','analyze',s);artifacts.finish(d,ticket)
    before=P.read_config(d);plan=E.preview(d,dict(signature=E.signature(d),segment=segment['id'],action='reconstruct'))
    assert plan['checks']['full_route_continuity'] and not plan['checks']['effective_repair']
    assert not plan['can_apply'] and 'nenhuma reparação efetiva' in plan['notice']
    assert P.read_config(d)==before
    with pytest.raises(ValueError):E.apply(d,plan['id'])
