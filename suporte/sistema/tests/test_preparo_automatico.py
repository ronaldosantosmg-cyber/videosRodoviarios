import io
import ezdxf
from fastapi.testclient import TestClient
from app.server import app
from app import store


def dxf_sujo():
    d = ezdxf.new('R2013'); d.layers.add('AXIS-MAIN'); d.layers.add('SHOULDER')
    m = d.modelspace()
    m.add_line((0, 0), (300, 0), dxfattribs={'layer': 'AXIS-MAIN'}); m.add_line((300.02, 0), (600, 0), dxfattribs={'layer': 'AXIS-MAIN'})
    m.add_line((5, 5), (5, 5), dxfattribs={'layer': 'SHOULDER'})                                   # comprimento zero
    m.add_lwpolyline([(0, 5), (50, 5), (50, 9)], close=True, dxfattribs={'layer': 'SHOULDER'})
    b = io.StringIO(); d.write(b); return b.getvalue().encode()


def _layers(f): return {e.dxf.layer for e in ezdxf.readfile(f).modelspace()}


def test_upload_prepara_sozinho_e_guarda_o_original(monkeypatch):
    monkeypatch.setenv('RODOVIA_PREPARO_AUTO', '1')
    with TestClient(app) as c:
        pid = c.post('/api/projects', json={}).json()['id']
        r = c.post(f'/api/projects/{pid}/files', files={'file': ('a.dxf', dxf_sujo())})
        assert r.status_code == 200, r.text
        p = r.json()['preparo']; d = store.directory(pid)
        assert p['aplicado'] and p['camadas_renomeadas'] >= 2 and p['removidas']['invalidas'] >= 1
        assert {'EIXO_01', 'GE_HZ-ACOSTAMENTO'} <= _layers(d / 'input.dxf')            # camadas no padrão do modelo
        assert 'AXIS-MAIN' in _layers(d / 'input.antes_preparo.dxf')                    # original preservado


def test_desligado_importa_sem_alterar(monkeypatch):
    monkeypatch.setenv('RODOVIA_PREPARO_AUTO', '0')
    with TestClient(app) as c:
        pid = c.post('/api/projects', json={}).json()['id']
        r = c.post(f'/api/projects/{pid}/files', files={'file': ('a.dxf', dxf_sujo())})
        assert r.status_code == 200 and 'preparo' not in r.json()
        assert 'AXIS-MAIN' in _layers(store.directory(pid) / 'input.dxf')


def test_dxf_ilegivel_nao_derruba_o_upload(monkeypatch):
    monkeypatch.setenv('RODOVIA_PREPARO_AUTO', '1')
    lixo = b'0\nSECTION\n2\nHEADER\n' + b'lixo\n' * 50                                      # passa na checagem inicial, falha na leitura
    with TestClient(app) as c:
        pid = c.post('/api/projects', json={}).json()['id']
        r = c.post(f'/api/projects/{pid}/files', files={'file': ('a.dxf', lixo)})
        assert r.status_code in (200, 422)                                               # nunca 500
