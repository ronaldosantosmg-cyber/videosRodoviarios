import math
import ezdxf
import pytest
from app import dxf_preparo as P


def _dxf(tmp_path, build):
    doc = ezdxf.new('R2013'); build(doc, doc.modelspace()); f = tmp_path / 'in.dxf'; doc.saveas(f); return f


def _layers(path):
    return {e.dxf.layer for e in ezdxf.readfile(path).modelspace()}


def test_renomeia_camadas_por_papel_e_une_eixo_em_fragmentos(tmp_path):
    def b(doc, m):
        for n in ('AXIS-MAIN', 'ROAD_NEW_HATCH', 'EXISTING ROAD', 'SHOULDER', 'GUARDRAIL', 'XYZ'):
            doc.layers.add(n)
        m.add_line((0, 0), (300, 0), dxfattribs={'layer': 'AXIS-MAIN'})
        m.add_line((300.02, 0), (600, 0), dxfattribs={'layer': 'AXIS-MAIN'})   # folga 0,02 m: deve unir
        for n in ('ROAD_NEW_HATCH', 'EXISTING ROAD', 'SHOULDER', 'GUARDRAIL', 'XYZ'):
            m.add_lwpolyline([(0, 5), (100, 5), (100, 9), (0, 9)], close=True, dxfattribs={'layer': n})
    src = _dxf(tmp_path, b); out = tmp_path / 'out.dxf'
    rel = P.preparar(src, out)
    assert rel['aplicado'] and out.exists()
    L = _layers(out)
    assert {'EIXO_01', 'HATCH_PAV_NOVO', 'HATCH_PAV_EXISTENTE', 'GE_HZ-ACOSTAMENTO', 'BARREIRA', 'XYZ'} <= L
    assert 'AXIS-MAIN' not in L and rel['eixos'] == ['EIXO_01'] and rel['eixos_unidos'] == 1
    assert 'XYZ' in rel['sem_papel']
    assert _layers(src) >= {'AXIS-MAIN'}     # original intacto


def test_eixo_inferido_pela_geometria_quando_o_nome_nao_ajuda(tmp_path):
    def b(doc, m):
        doc.layers.add('LINHA_A')
        m.add_lwpolyline([(0, 0), (400, 0), (800, 100)], dxfattribs={'layer': 'LINHA_A'})
    rel = P.preparar(_dxf(tmp_path, b), tmp_path / 'o.dxf')
    assert rel['eixos_inferidos'] == ['LINHA_A'] and rel['avisos'] and rel['eixos'] == ['EIXO_01']


def test_protecoes_vazio_nao_finito_zero_e_duplicata(tmp_path):
    with pytest.raises(ValueError):
        P.preparar(_dxf(tmp_path, lambda d, m: None), tmp_path / 'o.dxf')
    def b(doc, m):
        doc.layers.add('EIXO')
        m.add_line((0, 0), (500, 0), dxfattribs={'layer': 'EIXO'})
        m.add_line((0, 0), (500, 0), dxfattribs={'layer': 'EIXO'})            # duplicata exata
        m.add_line((5, 5), (5, 5), dxfattribs={'layer': 'EIXO'})              # comprimento zero
        m.add_lwpolyline([(0, 0), (math.nan, 1)], dxfattribs={'layer': 'EIXO'})   # não finito
    r = P.preparar(_dxf(tmp_path, b), tmp_path / 'o.dxf')
    assert r['removidas']['invalidas'] >= 2 and r['eixos'] == ['EIXO_01']


def test_camada_bloqueada_e_preservada(tmp_path):
    def b(doc, m):
        l = doc.layers.add('SHOULDER'); l.lock()
        doc.layers.add('EIXO'); m.add_line((0, 0), (500, 0), dxfattribs={'layer': 'EIXO'})
        m.add_lwpolyline([(0, 5), (50, 5), (50, 9)], close=True, dxfattribs={'layer': 'SHOULDER'})
    src = _dxf(tmp_path, b); P.preparar(src, tmp_path / 'o.dxf')
    assert 'SHOULDER' in _layers(tmp_path / 'o.dxf')


def test_idempotente(tmp_path):
    def b(doc, m):
        doc.layers.add('EIXO LESTE'); m.add_line((0, 0), (500, 0), dxfattribs={'layer': 'EIXO LESTE'})
    a = tmp_path / 'a.dxf'; c = tmp_path / 'c.dxf'
    P.preparar(_dxf(tmp_path, b), a); r2 = P.preparar(a, c)
    assert r2['eixos'] == ['EIXO_LESTE'] and _layers(a) == _layers(c)


def test_api_relatorio_aplicar_e_usar_preservam_o_original(tmp_path, monkeypatch):
    from app import store
    from app.server import app
    from fastapi.testclient import TestClient
    d = tmp_path / ('a' * 32); d.mkdir()
    doc = ezdxf.new('R2013'); doc.layers.add('AXIS-MAIN'); doc.layers.add('SHOULDER')
    m = doc.modelspace(); m.add_line((0, 0), (500, 0), dxfattribs={'layer': 'AXIS-MAIN'})
    m.add_lwpolyline([(0, 5), (50, 5), (50, 9)], close=True, dxfattribs={'layer': 'SHOULDER'})
    doc.saveas(d / 'input.dxf'); original = (d / 'input.dxf').read_bytes()
    monkeypatch.setattr(store, 'directory', lambda pid: d)
    c = TestClient(app, base_url='http://127.0.0.1')
    r = c.post('/api/projects/x/dxf/preparar', json={'aplicar': False}); assert r.status_code == 200, r.text
    assert r.json()['eixos'] == ['EIXO_01'] and not r.json()['aplicado'] and not (d / 'input_preparado.dxf').exists()
    r = c.post('/api/projects/x/dxf/preparar', json={'aplicar': True}); assert r.status_code == 200, r.text
    assert (d / 'input_preparado.dxf').exists() and (d / 'input.dxf').read_bytes() == original
    assert c.get('/api/projects/x/dxf/preparado').status_code == 200
    r = c.post('/api/projects/x/dxf/preparar', json={'usar': True}); assert r.status_code == 200, r.text
    assert r.json()['backup'] == 'input.antes_preparo.dxf' and (d / 'input.antes_preparo.dxf').read_bytes() == original
    assert (d / 'input.dxf').read_bytes() != original
    assert c.post('/api/projects/x/dxf/preparar', json='lixo').status_code in (200, 422)
