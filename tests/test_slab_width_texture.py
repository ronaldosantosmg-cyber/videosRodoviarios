import numpy as np
import pytest
from app.models import PavementStyle
from app.pavement import JointField,paint_style


@pytest.mark.parametrize('centered',[False,True])
def test_slab_joints_use_configured_lane_width_without_changing_holes(centered):
    field=JointField([np.array([[0.,0.],[100.,0.]])]);field.lane_centers=centered
    base=np.full((160,80,3),23,np.uint8);mask=np.ones((160,80),bool);mask[40:60,10:25]=False
    style=PavementStyle(pattern='placas',fill='#cccccc',hatch='#222222',line_m=.12)
    result=paint_style(base,mask,'pavement',0.,8.,.05,style,field,5.,slab_width=4.)
    def at(y):return result[int((8-y)/.05),40].mean()
    assert at(2. if centered else 4.)<100
    assert at(1.75 if centered else 3.5)>180
    np.testing.assert_array_equal(result[~mask],base[~mask])


def test_invalid_slab_dimensions_are_rejected():
    with pytest.raises(ValueError,match='positivas'):
        paint_style(np.zeros((2,2,3),np.uint8),np.ones((2,2),bool),'pavement',0,0,.1,PavementStyle(pattern='placas'),slab_width=0)
