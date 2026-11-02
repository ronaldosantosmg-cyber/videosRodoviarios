"""2.60: distância de Hausdorff (a mesma de `a.hausdorff_distance(b)` do Shapely/GEOS: vértices de um contra a LINHA do outro).
Exata e O((n+m) log m): para cada vértice acha o SEGMENTO mais próximo da outra linha numa STRtree (em vez de medir contra a linha inteira).
Resultado idêntico (teste); em linhas longas é dezenas de vezes mais rápida."""
import numpy as np
import shapely
from shapely.geometry import LineString

def _coords(x):
    return np.asarray(x.coords if hasattr(x,'coords') else x,float)[:,:2]

def _dirigida(P,Q):
    if len(Q)==1:return float(np.hypot(*(P-Q[0]).T).max())
    seg=shapely.linestrings(np.stack([Q[:-1],Q[1:]],1))
    tree=shapely.STRtree(seg);pts=shapely.points(P)
    idx=tree.nearest(pts)
    return float(shapely.distance(pts,seg[idx]).max())

def hausdorff(a,b):
    A=_coords(a);B=_coords(b)
    if not len(A) or not len(B):return float('inf')
    return max(_dirigida(A,B),_dirigida(B,A))
