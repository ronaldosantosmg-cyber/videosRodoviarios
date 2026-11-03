"""Coverage after supersampling must preserve road paint on light concrete."""
import cv2
import numpy as np
from app.signage import marking_pixels


def paint(width, improved):
    scale=width/1920
    im=np.full((round(40*scale),round(100*scale),3),190,np.uint8)
    thickness=marking_pixels(.4/scale,width) if improved else 1
    cv2.line(im,(round(5*scale),round(20*scale)),(round(95*scale),round(20*scale)),(244,242,226),thickness,cv2.LINE_AA)
    return cv2.resize(im,(100,40),interpolation=cv2.INTER_AREA)


def test_supersampled_paint_survives_reduction():
    old=paint(2880,False);new=paint(2880,True)
    assert np.sum(new.astype(float)-190)>np.sum(old.astype(float)-190)*1.5
    assert new[18:23,10:90].max()>225


def test_close_paint_preserves_physical_width_and_optional_emphasis():
    assert marking_pixels(.025,1920)==6
    assert marking_pixels(.4,3840)==2
    assert marking_pixels(.4,3840,False)==1
