import hashlib,json,math
import cv2
import ezdxf
import numpy as np
import pytest
from shapely.geometry import box,LineString
from app.flow_reconstruction import reconstruct
from app.flow_recovery import recover_sections
from app.vehicle_motion import analyze_motion
from app.cad_curves import from_entity,evaluate,length,closest
from test_v142_visual import page


@pytest.mark.parametrize('reverse',[False,True])
def test_continuous_reconstruction_preserves_endpoints_direction_and_source(reverse):
    p=np.array([[0.,0.],[150.,0.],[150.,150.]])
    if reverse:p=p[::-1].copy()
    original=p.copy();surface=box(-15,-15,165,165)
    assert not analyze_motion(p,allowed=surface)['ok']
    q,report=reconstruct(p,surface)
    assert report['status']=='reconstructed' and report['max_deviation_m']<=8
    np.testing.assert_array_equal(q[[0,-1]],p[[0,-1]])
    np.testing.assert_array_equal(original,p)
    assert analyze_motion(q,allowed=surface)['ok'] and LineString(q).is_simple
    from shapely import line_locate_point,points
    assert np.all(np.diff(line_locate_point(LineString(p),points(q)))>=-.01)


def test_reconstruction_cannot_cross_barrier_or_disconnected_pavement():
    p=[[0,0],[150,0],[150,150]]
    surface=box(-20,-20,170,170).difference(box(70,-30,75,180))
    assert reconstruct(p,surface)[0] is None
    # Mesmo uma barreira na região que a curva suavizada cortaria impede a aceitação.
    surface=box(-20,-20,170,170).difference(box(130,1,150,20))
    q,r=reconstruct(p,surface)
    assert q is None or analyze_motion(q,allowed=surface)['ok']


@pytest.mark.parametrize('p',[[[0,0],[None,0]],[[0,0],[float('inf'),0]],[[0,0],[0,0]]])
def test_reconstruction_rejects_invalid_inputs(p):
    assert reconstruct(p,box(-10,-10,200,200))[0] is None


def test_recovery_keeps_legacy_exclusion_but_opt_in_can_reconstruct():
    p=[[0,0],[150,0],[150,150]];surface=box(-15,-15,165,165)
    assert recover_sections(p,surface)[1]['status']=='partial'
    pieces,report=recover_sections(p,surface,reconstruct=True)
    assert report['status']=='reconstructed' and len(pieces)==1 and report['excluded']==[]


def test_network_reconstructs_only_requested_axis_and_respects_manual_disable():
    from app.models import Settings
    from app.traffic import TrafficNetwork
    axis=np.array([[0.,0.],[150.,0.],[150.,150.]])
    def build(disabled=False):
        s=Settings(layers={'axis':['EIXO']},derive_traffic_paths=False,hydrography=False,signage_detail='basic',vehicle_paths='anterior',
                   min_route_segment_m=50,flow_recoveries=[dict(id='repair',x=100,y=0,reconstruct=True)],
                   flow_overrides=[dict(x=100,y=0,action='disable')] if disabled else [])
        return TrafficNetwork([box(-15,-15,165,165)],[],[dict(points=axis,layer='EIXO',role='axis')],axis,np.array([0,150,300]),s)
    n=build()
    assert n.paths and max(p['length'] for p in n.paths)>290
    assert any(r.get('status')=='reconstructed' for raw in n.raw_info for r in raw['recovery_reports'])
    assert not build(True).paths


def test_arc_exact_length_projection_and_utm_coordinates():
    e=ezdxf.new().modelspace().add_arc((730000,7800000),100,350,80)
    curve=from_entity(e)
    assert length(curve)==pytest.approx(50*math.pi,abs=1e-10)
    q=evaluate(curve,.4);radial=(q-np.array(curve['center']))/100
    result=closest(curve,q+radial*3)
    np.testing.assert_allclose(result['point'],q,atol=1e-8)
    assert result['distance_m']==pytest.approx(3,abs=1e-8)
    assert result['parameter']==pytest.approx(.4,abs=1e-9)


def test_rational_spline_quarter_circle_preserves_exact_form():
    c=dict(kind='nurbs',degree=2,control_points=[[1,0],[1,1],[0,1]],weights=[1,math.sqrt(.5),1],knots=[0,0,0,1,1,1])
    assert length(c)==pytest.approx(math.pi/2,abs=1e-9)
    np.testing.assert_allclose(evaluate(c,.5),[math.sqrt(.5)]*2,atol=1e-12)
    result=closest(c,[2,2])
    np.testing.assert_allclose(result['point'],[math.sqrt(.5)]*2,atol=1e-7)


def test_bulge_polyline_keeps_analytic_semicircle():
    e=ezdxf.new().modelspace().add_lwpolyline([(0,0,1),(20,0,0)],format='xyb')
    curve=from_entity(e)
    assert curve['kind']=='composite' and length(curve)==pytest.approx(10*math.pi)
    assert closest(curve,[10,-12])['distance_m']==pytest.approx(2,abs=1e-9)


def test_negative_bulge_keeps_vertex_order_and_continuity():
    e=ezdxf.new().modelspace().add_lwpolyline([(0,0,-1),(20,0,0),(30,0,0)],format='xyb')
    curve=from_entity(e)
    np.testing.assert_allclose(evaluate(curve,0),[0,0],atol=1e-10)
    np.testing.assert_allclose(evaluate(curve,1),[30,0],atol=1e-10)
    np.testing.assert_allclose(evaluate(curve['parts'][0],.5),[10,10],atol=1e-10)
    assert closest(curve,[10,12])['distance_m']==pytest.approx(2)


def test_import_and_editor_pick_use_native_arc_not_chord(tmp_path):
    from app.geometry import convert
    from app.webmap import write_lines,pick_line
    e=ezdxf.new().modelspace().add_arc((730000,7800000),100,0,90)
    items=[];warnings=[];convert(e,'EIXO','axis',1,items,warnings)
    assert not warnings and items[0]['cad_curve']['kind']=='arc'
    write_lines(tmp_path,items)
    curve=items[0]['cad_curve'];q=evaluate(curve,.333)
    selected=pick_line(tmp_path,*q,tol=.01)
    assert selected['distance_m']<1e-8
    assert selected['length_m']==pytest.approx(50*math.pi,abs=1e-10)
    np.testing.assert_allclose(selected['curve_projection']['point'],q,atol=1e-8)


def model_files(tmp_path):
    weights=tmp_path/'modelo.onnx';weights.write_bytes(b'fixture-only')
    sha=hashlib.sha256(weights.read_bytes()).hexdigest()
    config=dict(sha256=sha,classes=['building','vegetation'],input_size=256,output='logits',mean=[0,0,0],std=[1,1,1],confidence_threshold=.75,
                evaluation=dict(model_sha256=sha,dataset='fixture-sintetica-nao-validacao-de-modelo',independent_holdout=True,classes={role:dict(annotated_objects=20,iou=.8) for role in ['building','vegetation']}))
    (tmp_path/'modelo.json').write_text(json.dumps(config));return config


def test_semantic_uninstalled_is_explicit_and_never_claims_available(tmp_path):
    from app.image_semantic import status,predict
    assert status(tmp_path)['available'] is False
    with pytest.raises(ValueError,match='não instalado'):predict(np.zeros((16,16,3),np.uint8),tmp_path)


@pytest.mark.parametrize('failure',['integrity','holdout','class_metric','normalization'])
def test_semantic_requires_integrity_and_per_class_evaluation(tmp_path,failure):
    from app.image_semantic import status
    cfg=model_files(tmp_path)
    if failure=='integrity':cfg['sha256']='0'*64
    if failure=='holdout':cfg['evaluation']['independent_holdout']=False
    if failure=='class_metric':cfg['evaluation']['classes']['building']['iou']=.1
    if failure=='normalization':cfg['std']=[1,0,1]
    (tmp_path/'modelo.json').write_text(json.dumps(cfg))
    assert status(tmp_path)['available'] is False


def test_semantic_adapter_masks_low_confidence_and_preserves_provenance(tmp_path,monkeypatch):
    from app.image_semantic import predict
    from app.image_context import segment
    cfg=model_files(tmp_path)
    class Net:
        def setPreferableBackend(self,*a):pass
        def setPreferableTarget(self,*a):pass
        def setInput(self,value):assert value.shape==(1,3,256,256)
        def forward(self):
            out=np.zeros((1,2,32,32),np.float32);out[0,0,:,:15]=10;out[0,1,:,17:]=10;return out
    monkeypatch.setattr(cv2.dnn,'readNetFromONNX',lambda *args:Net())
    image=np.full((128,128,3),180,np.uint8)
    prediction=predict(image,tmp_path)
    assert (prediction['labels'][:,60:68]==-1).all()
    result=segment(image,[0,0,128,128],semantic=prediction)
    assert result['method']=='modelo_semantico_local' and result['model_sha256']==cfg['sha256']
    assert {f['role'] for f in result['features']}=={'building','vegetation'}
    assert all(not f['reviewed'] for f in result['features'])
    assert result['evaluation']['dataset'].startswith('fixture-sintetica')


def test_reconstruct_action_is_available_in_visual_repair_dialog(page):
    from test_v1422_layout import seed
    from visual_harness import screenshot
    seed(page);page.evaluate("()=>{pid='repair';editor.segments[0].technical_status='problem';}")
    page.get_by_role('tab',name='Tráfego',exact=True).click()
    page.evaluate('RodoviaFlowRepair.advanced()')
    page.locator('.rsFlowRepairAdvanced').first.locator('summary').click()
    assert page.get_by_role('button',name='Reconstruir rota completa…').first.is_visible()
    assert '8 m' in page.get_by_role('dialog',name='Corrigir fluxos').inner_text()
    screenshot(page,'14219_reconstrucao_continua')
