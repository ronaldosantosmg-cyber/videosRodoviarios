import ezdxf, pytest
from app.dxf_leitura import ler

def _dxf(p, extra=''):
    d = ezdxf.new('R2010'); d.modelspace().add_line((0, 0), (10, 0), dxfattribs={'layer': 'EIXO'}); d.saveas(p)
    return p

def test_normal(tmp_path):
    av = []; doc = ler(_dxf(tmp_path / 'a.dxf'), av)
    assert len(doc.modelspace()) == 1 and av == []

def test_vazio_e_inexistente(tmp_path):
    (tmp_path / 'v.dxf').write_bytes(b'')
    with pytest.raises(ValueError, match='vazio'): ler(tmp_path / 'v.dxf')
    with pytest.raises(ValueError, match='não encontrado'): ler(tmp_path / 'x.dxf')

def test_dwg_recusado(tmp_path):
    (tmp_path / 'a.dwg').write_bytes(b'AC1027\x00\x00' + b'0' * 50)
    with pytest.raises(ValueError, match='DWG'): ler(tmp_path / 'a.dwg')

def test_lixo_da_erro_claro(tmp_path):
    (tmp_path / 'l.dxf').write_text('isto nao e dxf\nnada\n')
    with pytest.raises(ValueError): ler(tmp_path / 'l.dxf')

def test_dxf_truncado_e_recuperado_ou_recusado_sem_quebrar(tmp_path):
    p = _dxf(tmp_path / 't.dxf'); b = p.read_bytes(); p.write_bytes(b[:int(len(b) * 0.85)])
    av = []
    try: doc = ler(p, av)
    except ValueError as e: assert 'DXF' in str(e)       # recusa clara é aceitável
    else: assert doc is not None

def test_codificacao_ruim(tmp_path):
    p = _dxf(tmp_path / 'c.dxf'); b = p.read_bytes().replace(b'EIXO', b'EIX\xe7')
    p.write_bytes(b); av = []
    doc = ler(p, av)
    assert len(doc.modelspace()) == 1

def test_insert_quebrado_nao_derruba_leitura(tmp_path):
    from app.geometry import walk, _INSERTS_RUINS
    d = ezdxf.new('R2010'); msp = d.modelspace(); msp.add_line((0, 0), (5, 0))
    msp.add_blockref('NAO_EXISTE', (1, 1))
    _INSERTS_RUINS[0] = 0
    ents = list(walk(msp))
    assert len(ents) == 1

def test_unidades_mapa():
    from app.geometry import UNIDADES_DXF_M
    assert UNIDADES_DXF_M[4] == 0.001 and UNIDADES_DXF_M[5] == 0.01
