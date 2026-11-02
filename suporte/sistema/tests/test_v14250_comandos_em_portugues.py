"""2.22: textos VISÍVEIS em português (Snap/Offset/Layers). Comandos digitados podem seguir com apelidos em inglês."""
from pathlib import Path

APP=Path(__file__).resolve().parents[1]/'app'

def test_textos_visiveis_sem_snap_offset_layers():
    ruins=[]
    for f in sorted((APP/'js').glob('*.js')):
        s=f.read_text(encoding='utf-8')
        for padrao in (">SNAP<","'Snap '","['Snap'","Paralela (offset)","Offset dx","<th>Layer</th>","'Layers'","Analisar layers"):
            if padrao in s:ruins.append((f.name,padrao))
    assert ruins==[],ruins
    assert '> Snap<' not in (APP/'index.html').read_text(encoding='utf-8')

def test_apelidos_em_ingles_continuam_funcionando_como_comando():
    s=(APP/'js'/'14_cad_edicao.js').read_text(encoding='utf-8')
    assert "MOVE:'MOVER'" in s and "SNAP:'SNAP'" in s
