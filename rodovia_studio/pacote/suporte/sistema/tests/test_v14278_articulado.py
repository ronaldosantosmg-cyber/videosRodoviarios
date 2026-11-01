"""2.46: off-tracking de carreta — cálculo puro, sem mexer no desenho."""
import numpy as np
from shapely.geometry import LineString
from app.articulado import rastro
from app.vehicle_motion import analyze_motion

def curva(R,ang=90,reta=80.):
    t=np.linspace(0,np.radians(ang),120);arco=np.column_stack([reta+R*np.sin(t),R*(1-np.cos(t))])
    return np.vstack([[[0,0],[reta/2,0]],arco,arco[-1]+np.array([np.cos(np.radians(ang)),np.sin(np.radians(ang))])*np.array([[40.],[80.]])])
def test_reta_nao_tem_offtracking():
    r=rastro(np.array([[0,0],[200,0]],float));assert r['disponivel'] and r['offtracking_max_m']<.01 and r['ok']
def test_offtracking_cresce_quando_o_raio_diminui():
    a=rastro(curva(80))['offtracking_max_m'];b=rastro(curva(30))['offtracking_max_m'];c=rastro(curva(15))['offtracking_max_m']
    assert a<b<c and c>3.0
def test_valor_coerente_com_a_formula_de_regime():
    R,Lt=30.,12.2;r=rastro(curva(R,ang=180))     # regime: raio do eixo traseiro do reboque = sqrt(R²−Lt²)
    esperado=R-np.sqrt(R*R-Lt*Lt);assert abs(r['offtracking_max_m']-esperado)<.35,(r,esperado)
def test_pista_estreita_gera_aviso_e_larga_nao():
    c=curva(15);lin=LineString(c)
    assert not rastro(c,allowed=lin.buffer(3.6))['ok']
    assert rastro(c,allowed=lin.buffer(16.0))['ok']
def test_analyze_motion_informa_articulado_sem_mudar_validade():
    c=curva(60);a=analyze_motion(c,'carreta');assert a['articulado']['disponivel']
    assert analyze_motion(c,'car')['articulado'] is None
def test_relatorio_da_simulacao_traz_rastro_da_carreta():
    import pathlib,tempfile,ezdxf
    from test_v110 import S
    from app.render import Scene
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500900,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799986),(500900,7799986),(500900,7800014),(500000,7800014)],is_closed=True)
    tmp=pathlib.Path(tempfile.mkdtemp());d.saveas(tmp/'input.dxf')
    sim=Scene(tmp,S(vehicle_mix='rodovia_br',route_directions={'layer:EIXO':'forward'},traffic=True,traffic_density=2.0)).traffic();list(sim.vehicles_ex(120.))
    r=sim.report()['articulated_tracking'];assert isinstance(r,list) and (not r or 'offtracking_max_m' in r[0] or 'erro' in r[0]),r
    assert all('erro' not in x for x in r),r
