import numpy as np
from app.earthworks import earthwork_style

def test_visible_fill_and_cut_without_expanding_areas():
    mask=np.zeros((80,100),np.uint8);mask[10:70,15:85]=255
    lines=np.zeros_like(mask)
    for role in ('cut','fill'):
        color,alpha=earthwork_style(mask,lines,role,.5)
        assert alpha[mask>0].min()>=98
        assert alpha[mask==0].max()==0
        assert alpha.max()==235
        if role=='fill':assert color[40,40,1]>color[40,40,0]
        else:assert color[40,40,0]>color[40,40,1]

def test_native_open_offsets_are_visible_without_inventing_a_polygon():
    mask=np.zeros((80,100),np.uint8);lines=mask.copy();lines[40,10:90]=255
    color,alpha=earthwork_style(mask,lines,'cut',.5)
    assert alpha[40,50]>200
    assert not alpha[10:20].any()
