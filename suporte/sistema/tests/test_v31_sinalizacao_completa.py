"""3.1: no modo 'DXF substitui a gerada' o app completa o que o DXF não traz (gores) sem sobrepor a sinalização do DXF."""
import ezdxf
from shapely.geometry import LineString as LS, Polygon as PG
from shapely.ops import unary_union
from test_v115 import scene


def _fork(tmp_path, com_sinalizacao_dxf):
    d = ezdxf.new(); m = d.modelspace(); X, Y = 500000, 7800000
    for l in ['EIXO', 'PAVIMENTO', 'SINALIZACAO HORIZONTAL']:
        d.layers.new(l)
    m.add_lwpolyline([(X, Y), (X + 200, Y), (X + 400, Y - 50)], dxfattribs={'layer': 'EIXO'})
    g = unary_union([LS([(X, Y), (X + 200, Y)]).buffer(4, cap_style=2), LS([(X + 190, Y), (X + 400, Y + 50)]).buffer(4, cap_style=2),
                     LS([(X + 190, Y), (X + 400, Y - 50)]).buffer(4, cap_style=2),
                     PG([(X + 195, Y), (X + 300, Y + 24), (X + 300, Y - 24)]).difference(PG([(X + 262, Y), (X + 320, Y + 30), (X + 320, Y - 30)]))]).simplify(.05)
    h = m.add_hatch(dxfattribs={'layer': 'PAVIMENTO'}); h.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True)
    if com_sinalizacao_dxf:
        m.add_lwpolyline([(X + 5, Y + 3), (X + 60, Y + 3)], dxfattribs={'layer': 'SINALIZACAO HORIZONTAL'})   # linha do DXF longe do gore
    d.saveas(tmp_path / 'input.dxf')
    principal = {'name': 'principal', 'points': [{'x': X, 'y': Y}, {'x': X + 200, 'y': Y}, {'x': X + 400, 'y': Y - 50}], 'kind': 'main', 'direction': 'growing'}
    ramo = {'name': 'ramo', 'points': [{'x': X + 150, 'y': Y + 1.5}, {'x': X + 205, 'y': Y + 3}, {'x': X + 400, 'y': Y + 50}], 'kind': 'device', 'direction': 'growing'}
    return [principal, ramo]


def test_modo_substitui_completa_gore_e_preserva_linha_do_dxf(tmp_path):
    paths = _fork(tmp_path, True)
    net = scene(tmp_path, traffic_paths=paths, dxf_signage='replace').network
    assert any(s == -4 for s in net.mark_src)                      # linha do DXF mantida
    assert len([1 for r, c in net.fills if len(r) == 1]) >= 5      # zebrado do gore completado
    assert getattr(net, 'signage_completed', 0) >= 1


def test_opcao_desligada_nao_completa(tmp_path):
    paths = _fork(tmp_path, True)
    net = scene(tmp_path, traffic_paths=paths, dxf_signage='replace', dxf_complete=False).network
    assert len([1 for r, c in net.fills if len(r) == 1]) < 5
