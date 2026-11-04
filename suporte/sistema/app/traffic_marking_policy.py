"""Regras conservadoras para pintura, barreiras e sentido individual por eixo."""
from dataclasses import dataclass

@dataclass(frozen=True)
class LinhaCirculacao:
    identificador: str
    tipo: str
    pintura: str = "desconhecida"
    sentidos: str = "desconhecidos"
    revisada: bool = False

def permissao_cruzamento(linha: LinhaCirculacao, *, manobra="mudanca_faixa"):
    """Nunca deduz permissão somente pelo layer do DXF."""
    if linha.tipo not in {"barreira", "bordo", "divisoria", "desconhecida"}:
        raise ValueError("Tipo de linha inválido.")
    if linha.tipo == "barreira":
        return {"permitido": False, "fisica": True, "revisao": False}
    if linha.tipo == "bordo":
        return {"permitido": False, "fisica": False, "revisao": False}
    if linha.tipo == "desconhecida" or not linha.revisada:
        return {"permitido": False, "fisica": False, "revisao": True}
    if linha.pintura not in {"seccionada", "continua", "dupla_continua"} or linha.sentidos not in {"mesmo", "opostos"}:
        return {"permitido": False, "fisica": False, "revisao": True}
    if linha.pintura != "seccionada":
        return {"permitido": False, "fisica": False, "revisao": False}
    if linha.sentidos == "opostos" or manobra != "mudanca_faixa":
        return {"permitido": False, "fisica": False, "revisao": True}
    return {"permitido": True, "fisica": False, "revisao": False}

def alterar_sentido_individual(config: dict, identificador: str, sentido: str) -> dict:
    """Retorna cópia; não modifica outro eixo, layer, geometria ou km."""
    if not isinstance(identificador, str) or not identificador.startswith("axis:") or len(identificador) <= 5:
        raise ValueError("Selecione um eixo válido antes de alterar o sentido.")
    if sentido not in {"forward", "reverse", "off", "auto"}:
        raise ValueError("Sentido inválido.")
    novo = dict(config or {})
    if sentido == "auto":
        novo.pop(identificador, None)
    else:
        novo[identificador] = sentido
    return novo
