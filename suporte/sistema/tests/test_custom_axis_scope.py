"""Um alinhamento local não altera a referência global nem a orientação das faixas."""
import numpy as np
import pytest
from test_workflow import settings
from test_v110 import junction
from app.models import Settings
from app.geometry import analyze
from app import routes


@pytest.mark.parametrize('reverse',[False,True])
def test_local_axis_and_its_orientation_do_not_replace_main_axis(junction,reverse):
    base=Settings.model_validate({**settings().model_dump(),'reverse_axis':reverse})
    _,main,stations,_,_=analyze(junction,base)
    points=[{'x':500300,'y':7800003},{'x':500200,'y':7800003}]
    for points in (points,points[::-1]):
        cfg=Settings.model_validate({**base.model_dump(),'custom_axis':{'points':points,'enabled':True}})
        # Legacy saved alignments, without the new flag, are local as well.
        assert cfg.custom_axis.use_as_reference is False
        _,axis,ds,_,_=analyze(junction,cfg)
        np.testing.assert_array_equal(axis,main)
        np.testing.assert_array_equal(ds,stations)
        chain=routes.make_chain(axis,ds)
        assert chain([500100,7800000])==routes.make_chain(main,stations)([500100,7800000])
        assert cfg.custom_axis.points[0].x==points[0]['x']


def test_explicit_promotion_is_saved_and_restored(junction):
    base=settings().model_dump()
    cfg=Settings.model_validate({**base,'custom_axis':{'points':[{'x':500100,'y':7800003},{'x':500200,'y':7800003}],'smooth':False,'use_as_reference':True}})
    cfg=Settings.model_validate_json(cfg.model_dump_json())
    _,axis,_,_,_=analyze(junction,cfg)
    np.testing.assert_array_equal(axis,[[500100,7800003],[500200,7800003]])


def test_all_secondary_alignments_leave_main_reference_and_other_flows_unchanged(junction):
    from app.models import RouteAlignment
    from app.native_axes import axis_fingerprint,native_paths
    from shapely.geometry import box
    base=Settings.model_validate(settings().model_dump())
    _,main,ds,axes,_=analyze(junction,base)
    directives={'axis:'+axis_fingerprint(a['points'],a['layer'],a.get('level',0)):'forward' for a in axes}
    base=base.model_copy(update={'route_directions':directives})
    baseline,_=native_paths(axes,base,box(499000,7799000,502000,7802000))
    a=RouteAlignment(id='sec-a',name='Secundário A',type='unico',flow_direction='crescente',
        points=[{'x':500000,'y':7800010},{'x':500800,'y':7800010}])
    b=RouteAlignment(id='sec-b',name='Secundário B',type='unico',flow_direction='decrescente',
        points=[{'x':500000,'y':7800020},{'x':500800,'y':7800020}])
    cfg=base.model_copy(update={'route_alignments':[a,b]})
    for changed in (a,a.model_copy(update={'flow_direction':'decrescente'}),a.model_copy(update={'enabled':False})):
        current=cfg.model_copy(update={'route_alignments':[changed,b]})
        _,axis,stations,ax,_=analyze(junction,current)
        np.testing.assert_array_equal(axis,main)
        np.testing.assert_array_equal(stations,ds)
        native,_=native_paths(ax,current,box(499000,7799000,502000,7802000))
        assert [r['native_direction'] for r in native]==[r['native_direction'] for r in baseline]
        lanes=routes.raw_paths(current)
        assert {r['route_dir'] for r in lanes if r['route']=='sec-b'}=={'r'}
