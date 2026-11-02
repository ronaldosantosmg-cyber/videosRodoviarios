"""2.45: verificação INDEPENDENTE do motor — retângulos orientados de todos os veículos, quadro a quadro; nenhuma sobreposição (impacto lateral, frontal ou traseiro)."""
import pathlib,tempfile
import numpy as np,ezdxf
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from app.visual import TYPES

def _cena(**kw):
    from test_v110 import S
    from app.render import Scene
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(501500,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799986),(501500,7799986),(501500,7800014),(500000,7800014)],is_closed=True)
    tmp=pathlib.Path(tempfile.mkdtemp());d.saveas(tmp/'input.dxf')
    return Scene(tmp,S(route_directions={'layer:EIXO':'forward'},traffic=True,vehicle_mix='rodovia_br',traffic_density=2.0,opposite_overtake=True,**kw)).traffic()
def _ret(pos,tan,vt):
    L,B=TYPES.get(vt,TYPES['car'])['L'],TYPES.get(vt,TYPES['car'])['B'];t=np.asarray(tan,float);n=np.array([-t[1],t[0]]);c=np.asarray(pos,float)
    return Polygon([c+t*L/2+n*B/2,c+t*L/2-n*B/2,c-t*L/2-n*B/2,c-t*L/2+n*B/2])
def test_nenhum_par_de_veiculos_se_sobrepoe():
    sim=_cena();pares=0;quadros=0;sentidos=set()
    for t in np.arange(0,240,1.0):
        rows=[(vid,_ret(p,tn,sim.info[vid][1]),np.asarray(tn,float)) for p,tn,vid,_,_ in sim.vehicles_ex(float(t))]
        if len(rows)<2:continue
        quadros+=1;tree=STRtree([r[1] for r in rows])
        for i,(vid,poly,tn) in enumerate(rows):
            sentidos.add(int(np.sign(tn[0]) or 1))
            for j in tree.query(poly):
                if j>i and poly.intersection(rows[j][1]).area>0.02:pares+=1
    assert quadros>100
    assert pares==0,f'{pares} sobreposições geométricas'
