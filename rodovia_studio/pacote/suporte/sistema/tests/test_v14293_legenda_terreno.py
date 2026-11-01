"""2.61: a legenda do cabeçalho do vídeo não pode quebrar por papel sem rótulo (KeyError 'terrain' abortava o vídeo após ~17 min)."""
import re
from pathlib import Path
SRC=(Path(__file__).resolve().parent.parent/'app'/'render.py').read_text(encoding='utf-8')

def test_todo_papel_da_legenda_tem_rotulo():
    legend=re.search(r"legend=tuple\(role for role in \[([^\]]+)\]",SRC).group(1)
    roles=re.findall(r"'(\w+)'",legend)
    labels=re.search(r"labels=\{(.+?)\}\n",SRC,re.S).group(1)
    assert 'terrain' in roles
    for r in roles:assert f"'{r}':" in labels,r

def test_rotulo_tem_fallback():
    assert "labels.get(role,str(role).replace('_',' ').capitalize())" in SRC
