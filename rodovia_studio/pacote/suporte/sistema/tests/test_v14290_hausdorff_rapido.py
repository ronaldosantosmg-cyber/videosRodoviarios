import numpy as np
from shapely.geometry import LineString
from app.geom_rapida import hausdorff
def test_igual_ao_geos():
    rng=np.random.default_rng(5)
    for n in (4,9,300,3000):
        t=np.cumsum(rng.normal(1,.3,n));A=np.stack([t,np.sin(t/17)*9],1);B=A[::2]+rng.normal(0,.4,(len(A[::2]),2))
        assert abs(hausdorff(A,B)-LineString(A).hausdorff_distance(LineString(B)))<1e-9
        assert abs(hausdorff(LineString(B),LineString(A))-LineString(B).hausdorff_distance(LineString(A)))<1e-9
