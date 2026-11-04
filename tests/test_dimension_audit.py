import math
import pytest
from app.models import Gantry,Settings
from app.dimension_audit import resize_crossing,gantry_dimensions,audit


def gantry():
    return Gantry(name='G',a={'x':734000.,'y':7830000.},b={'x':734030.,'y':7830040.},height_m=7)


def test_travessia_does_not_include_posts_or_height():
    original=gantry()
    assert gantry_dimensions(original)['support_axis_distance_m']==50
    assert gantry_dimensions(original)['crossing_m'] is None
    for width in (12.,18.):
        changed=resize_crossing(original,width)
        measured=gantry_dimensions(changed)
        assert measured['crossing_m']==pytest.approx(width,abs=1e-8)
        assert measured['support_axis_distance_m']==pytest.approx(width+.9,abs=1e-8)
        assert changed.height_m==7
        assert (changed.a.x+changed.b.x)/2==(original.a.x+original.b.x)/2
        assert (changed.a.y+changed.b.y)/2==(original.a.y+original.b.y)/2
        assert gantry_dimensions(changed.model_copy(update={'height_m':15}))['crossing_m']==measured['crossing_m']
        assert Settings.model_validate_json(Settings(gantries=[changed]).model_dump_json()).gantries[0].crossing_a==changed.crossing_a


def test_unpaired_measurement_rejected():
    with pytest.raises(ValueError,match='dois limites'):
        Gantry.model_validate({**gantry().model_dump(),'crossing_a':{'x':0,'y':0}})


def test_other_dimensions_are_separate_quantities():
    report=audit(Settings(route_alignments=[{'name':'Condução','type':'unico','points':[{'x':0,'y':0},{'x':3,'y':4}]}]))
    assert report['elements'][0]['length_m']==5
    assert 'area_m2' not in report['elements'][0]
