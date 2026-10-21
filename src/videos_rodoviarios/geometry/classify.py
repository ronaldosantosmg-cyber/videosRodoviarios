from __future__ import annotations
import re,unicodedata
def _norm(value:str)->str:
 value=unicodedata.normalize("NFKD",value);value="".join(c for c in value if not unicodedata.combining(c));return re.sub(r"[^A-Z0-9]+","_",value.upper()).strip("_")
def pavement_profile(layer:str)->str|None:
 """Classifica material/estado do pavimento exclusivamente por referências no nome da layer."""
 k=_norm(layer);pav=any(t in k for t in ("PAV","PAVIMENTO","PISTA","PLATAFORMA"))
 if not pav:return None
 rigid=any(t in k for t in ("RIGID","RIGIDO","CONCRETO","CONC","PCC"));flex=any(t in k for t in ("FLEX","FLEXIVEL","ASFALTO","ASFALT","CBUQ"));existing=any(t in k for t in ("EXIST","EXISTENTE","ATUAL"));new=any(t in k for t in ("EXEC","EXECUTADO","PROJ","PROJETADO","NOVO","IMPLANT"))
 material="rigid" if rigid else "flexible" if flex else "pavement";state="existing" if existing else "new" if new else "unspecified";return f"pavement_{state}_{material}"
RULES=[
 ("cut",("TALUDE_CORTE","CORTE","CUT","OFFSET_CORTE","OFF_CORTE","HCORTE")),
 ("fill",("TALUDE_ATERRO","ATERRO","FILL","OFFSET_ATERRO","OFF_ATERRO","HATERRO")),
 ("median_grass",("CANTEIRO_CENTRAL","CANTEIRO_GRAMA","CANTEIRO_GRAMADO","MEDIANA_GRAMA")),
 ("domain",("FAIXA_DOMINIO","DOMINIO","RIGHT_OF_WAY","ROW")),
 ("marking",("SINALIZACAO_HORIZONTAL","SINAL_HORIZONTAL","MARKING","PINTURA","FAIXA_CONTINUA","FAIXA_TRACEJADA","LINHA_BORDO","FAIXA_BORDO","LINHA_EIXO","FAIXA_EIXO","SETA_PAVIMENTO","SETA_DIRECIONAL")),
 ("barrier",("NEWJERSEY","NEW_JERSEY","BARREIRA","DEFENSA","SEPARADOR_FISICO")),
 ("grass",("CANTEIRO","GRAMA","GRAMADO","PAISAGISMO","AREA_VERDE","GREEN","MEDIANA")),
 ("crossing",("RETORNO","RETORNO_X","U_TURN","UTURN","INTERSECAO","ACESSO","ROTATORIA")),
 ("oae",("OAE","PONTE","VIADUTO","VIAD","TUNEL","DESNIVEL")),
 ("footbridge",("PASSARELA",)),
 ("center",("EIXO","CENTERLINE","CENTER","ALIGNMENT","ALINHAMENTO","HZ_EIXO")),
 ("water",("HIDRO","RIO","CORREGO","RIBEIRAO","DRENAGEM_NATURAL","WATER")),
 ("rail",("FERROVIA","FERROV","RAIL","TRILHO","EFVM")),]
def classify_layer(layer:str)->str:
 p=pavement_profile(layer)
 if p:return p
 key=_norm(layer)
 for category,tokens in RULES:
  if any(t in key for t in tokens):return category
 if "FAIXA" in key and "DOMINIO" not in key:return "marking"
 if any(t in key for t in ("BORDO","EDGE","ACOSTAMENTO")):return "edge"
 return "other"
