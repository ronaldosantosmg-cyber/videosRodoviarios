"""2.59: a análise com prévias usa o cache de geometria e devolve exatamente o mesmo resultado."""
import numpy as np
from test_v110 import junction  # noqa: F401
from test_workflow import settings  # noqa: F401
import shutil,pytest

def _eq(a,b):
    if isinstance(a,np.ndarray):return np.array_equal(a,b)
    if isinstance(a,dict):return a.keys()==b.keys() and all(_eq(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return len(a)==len(b) and all(_eq(x,y) for x,y in zip(a,b))
    return a==b

def test_analyze_com_previas_acerta_o_cache(junction,tmp_path):
    from app import geometry as G
    from app.models import Settings
    d=tmp_path/'p';d.mkdir();shutil.copy(junction/'input.dxf',d/'input.dxf')
    s=Settings(name='x');(d/'config.json').write_text(s.model_dump_json())
    p1=[];h1={};r1=G.analyze(d,s,preview=p1,hatch_preview=h1);assert r1[4]['geometry_cache']['hit'] is False
    p2=[];h2={};r2=G.analyze(d,s,preview=p2,hatch_preview=h2);assert r2[4]['geometry_cache']['hit'] is True
    assert _eq(p1,p2) and _eq(h1,h2) and _eq(r1[0],r2[0]) and _eq(r1[1],r2[1])
    assert len(list((d/'_cache'/'geometry').glob('*.json.z')))==1      # o cache principal não é apagado pelo das prévias
    p3=[];G.analyze(d,s,preview=p3,hatch_preview=None);assert _eq(p1,p3)

def test_assinatura_da_geometria_ignora_codigo_de_tela_texturas_e_ia():
    from app import dependencies as D
    mods=set(D._cierre('geometry'))
    assert {'geometry','models','pavement','kmz_validation'}<=mods
    assert not ({'relevo','render','higiene','ia_correcoes','componentes','small_ai','texturas_pacote','scene3d','videos','visual'}&mods)
