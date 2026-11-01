from pathlib import Path
R=Path(__file__).resolve().parents[1]/'app'
def j(n):return (R/'js'/n).read_text(encoding='utf-8')
def test_item_faixa_nao_derruba_aba_ausente():
    assert 'não existe na faixa de opções' not in j('00_nucleo.js')
def test_snap_tolera_grip_sem_objeto():
    assert 'drag.g?.o?.key' in j('17_transformacoes_snap.js')
def test_barra_de_escala_unica_e_correta():
    assert 'pxPerM()' in j('94_mapa_2d.js') and 'geo.R0/geo.k' not in j('94_mapa_2d.js')
    assert "ctx.fillRect(20,canvas.height-18,len*ppm,4)" not in j('05_desenho.js')
def test_video_em_uso_usa_troca_com_repeticao():
    assert 'store.replace(f,dst)' in (R/'videos.py').read_text(encoding='utf-8')
def test_permissionerror_vira_423():
    t=(R/'server.py').read_text(encoding='utf-8');assert 'exception_handler(PermissionError)' in t and '423' in t
