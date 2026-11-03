import numpy as np
from app import visual


def test_cut_and_fill_share_grass_sample_without_leaking_into_other_surfaces(monkeypatch):
    calls=[]
    class Grass:
        def sample(self, matrix, shape, mpp):
            calls.append(shape)
            return np.full(shape,.5,np.float32)
    class Soil:
        def sample(self, matrix, shape, mpp):return np.zeros(shape,np.float32)
    monkeypatch.setattr(visual,'grass',lambda:Grass())
    monkeypatch.setattr(visual,'soil',lambda:Soil())
    im=np.full((3,3,3),100,np.uint8)
    surface=np.array([[6,7,0],[6,7,0],[0,0,0]],np.uint8)
    lut={key:np.zeros(256,np.float32) for key in ('spk','patch','crack','shift')}
    visual.shade_realistic(im,surface,np.array([[1,0,0],[0,-1,0]],float),.5,np.ones((3,3),bool),lut=lut,earth_grass=True)
    assert len(calls)==1
    np.testing.assert_array_equal(im[0,0],[90,122,94])
    np.testing.assert_array_equal(im[0,1],[107,114,107])
    np.testing.assert_array_equal(im[:,2],np.full((3,3),100))
    np.testing.assert_array_equal(im[2],np.full((3,3),100))
