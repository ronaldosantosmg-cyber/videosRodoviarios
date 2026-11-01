"""2.36: o sentido desenhado vem SEMPRE do trecho calculado; nenhuma camada de apoio fixa seta 'para frente'."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'app'/'js'
def j(n):return (R/n).read_text(encoding='utf-8')
def test_traffic_paths_seguem_sentido_do_trecho():
    t=j('53_interface_estudos.js')
    assert 'line(route.points,route.enabled===false?{disabled:true}:sg,sf,' in t
    assert "line(route.points,route.enabled===false?{disabled:true}:(editor?.segments||[]).find(s=>s.source===route.name),true,false" not in t
def test_previa_de_faixas_nao_contradiz_trecho_calculado():
    assert 'calculated.length>0' in j('53_interface_estudos.js') and 'if(!calc)arrowsAlong' in j('32_rotas.js')
