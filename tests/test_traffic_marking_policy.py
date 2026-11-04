"""Testes de regressão das novas regras conservadoras."""
import pytest
from app.traffic_marking_policy import LinhaCirculacao, permissao_cruzamento, alterar_sentido_individual

def test_divisoria_seccionada_validada_pode_ser_cruzada():
    r = permissao_cruzamento(LinhaCirculacao("1", "divisoria", "seccionada", "mesmo", True))
    assert r == {"permitido": True, "fisica": False, "revisao": False}

@pytest.mark.parametrize("tipo,pintura", [
    ("barreira", "seccionada"), ("bordo", "seccionada"),
    ("divisoria", "continua"), ("divisoria", "dupla_continua"),
])
def test_limites_e_continuas_bloqueiam_mas_so_barreira_e_fisica(tipo, pintura):
    r = permissao_cruzamento(LinhaCirculacao("2", tipo, pintura, "mesmo", True))
    assert not r["permitido"]
    assert r["fisica"] == (tipo == "barreira")

def test_ambiguidade_exige_revisao():
    assert permissao_cruzamento(LinhaCirculacao("3", "divisoria", "seccionada", "mesmo"))["revisao"]
    assert permissao_cruzamento(LinhaCirculacao("4", "divisoria", "seccionada", "opostos", True))["revisao"]

def test_altera_so_eixo_selecionado_sem_mutar_original():
    original = {"axis:principal": "forward", "axis:marginal": "reverse", "layer:EIXO": "reverse"}
    novo = alterar_sentido_individual(original, "axis:marginal", "forward")
    assert novo["axis:marginal"] == "forward"
    assert novo["axis:principal"] == original["axis:principal"]
    assert novo["layer:EIXO"] == original["layer:EIXO"]
    assert original["axis:marginal"] == "reverse"
    assert "axis:marginal" not in alterar_sentido_individual(novo, "axis:marginal", "auto")

def test_sem_selecao_nao_altera_configuracoes():
    cfg = {"axis:principal": "forward"}
    with pytest.raises(ValueError):
        alterar_sentido_individual(cfg, "", "reverse")
    assert cfg == {"axis:principal": "forward"}
