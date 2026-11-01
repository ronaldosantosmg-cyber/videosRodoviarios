"""2.19: contorno de hachura sem linha real no DXF não é traçado (a hachura continua preenchendo)."""
import numpy as np
from app.webmap import backing_lines,unbacked_skips,vectors

def ent(role,pts,hatch=False,closed=False):
    return {'layer':'L','role':role,'closed':closed,'points':np.array(pts,float),'holes':[],**({'hatch':True} if hatch else {})}

def test_segmento_sem_linha_real_e_omitido_e_o_sustentado_fica():
    ring=[(0,0),(100,0),(100,30),(0,30),(0,0)]
    items=[ent('edge_line',[(0,0),(100,0)]),ent('edge_line',[(0,30),(100,30)]),ent('pavement',ring,hatch=True,closed=True)]
    U=backing_lines(items)
    sk=unbacked_skips(ring,True,U)
    assert sorted(sk)==[1,3]            # as duas pontas transversais (sem linha no DXF); bordos reais ficam

def test_sem_nenhuma_linha_real_contorno_inteiro_fica():
    ring=[(0,0),(100,0),(100,30),(0,30),(0,0)]
    assert unbacked_skips(ring,True,backing_lines([ent('pavement',ring,hatch=True,closed=True)]))==[]

def test_vectors_marca_k_apenas_em_hachura():
    ring=[(0,0),(100,0),(100,30),(0,30),(0,0)]
    items=[ent('edge_line',[(0,0),(100,0)]),ent('edge_line',[(0,30),(100,30)]),ent('pavement',ring,hatch=True,closed=True)]
    v=vectors(items,np.array([[0,15],[100,15]]))
    assert v['layers']['pavement'][0].get('k')
    assert not any(r.get('k') for r in v['layers']['edge_line'])
