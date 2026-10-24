"""1.33: tempos legíveis (acima de 60 s em minutos), rodapé com a tarefa e estrutura da área de trabalho."""
import json,re,subprocess,shutil
from pathlib import Path
import pytest
from app.tempo import tempo
APP=Path(__file__).resolve().parents[1]/'app'

CASOS=[(0,'0 s'),(45,'45 s'),(59.4,'59 s'),(59.6,'1 min'),(60,'1 min'),(61,'1 min 01 s'),(125,'2 min 05 s'),(600,'10 min'),(3599,'59 min 59 s'),(3600,'1 h'),(3720,'1 h 02 min'),(-3,'0 s')]

def test_tempo_python():
    for s,t in CASOS:assert tempo(s)==t,(s,tempo(s),t)
    assert tempo(float('nan'))=='—' and tempo('x')=='x'

def test_tempo_js_igual_ao_python():
    node=shutil.which('node')
    if not node:pytest.skip('node ausente')
    src=(APP/'js'/'38_area_trabalho.js').read_text(encoding='utf-8')
    fns='\n'.join(l for l in src.splitlines() if l.startswith(('function tempo(',' if(s<3600)',' const h=','function tempoTexto(')))
    code=fns+f"\nconst C={json.dumps(CASOS)};console.log(JSON.stringify([C.map(c=>tempo(c[0])),tempoTexto('Montando quadros · falta ~95 s'),tempoTexto('vídeo de 45 s'),tempoTexto('Concluído em 3600 s'),tempoTexto('30 q/s'),tempoTexto('taxa 12 s/km')]))"
    r=json.loads(subprocess.run([node,'-e',code],capture_output=True,text=True,check=True).stdout)
    assert r[0]==[t for _,t in CASOS]
    assert r[1:]==['Montando quadros · falta ~1 min 35 s','vídeo de 45 s','Concluído em 1 h','30 q/s','taxa 12 s/km']

def test_mensagens_do_servidor_usam_minutos():
    # Render, simulação e registros formatam os tempos com tempo() (nenhum “N s” cru acima de 60 s).
    for f in ['render.py','simulation.py','execlog.py']:
        assert 'tempo(' in (APP/f).read_text(encoding='utf-8'),f
    from app import simulation  # noqa: F401  (importa sem erro)

def test_estrutura_html_css():
    h=(APP/'index.html').read_text(encoding='utf-8');c=(APP/'estilo.css').read_text(encoding='utf-8')
    assert '<div id="bottomBar" class="statusBar"><div id="statusBar" class="sbInfo"></div><div id="taskArea" class="taskArea"></div></div>' in h
    assert 'id="areaMaxBtn"' in h and 'Barra lateral' in h
    for k in ['.editorSide.dock.recolhida','.floatWin','.fwHead','body.wide.areaMax','.taskArea .sbProg','.retirada']:assert k in c,k
    # “Gerar vídeo” e os registros saem da coluna e vão para a faixa de opções (menu superior).
    j=(APP/'js'/'38_area_trabalho.js').read_text(encoding='utf-8');r=(APP/'js'/'30_faixa_opcoes.js').read_text(encoding='utf-8')
    assert "itemFaixa('Início','Vídeo',['Gerar vídeo'" in j and "'Ver registros'" in r and "'Exportar prompt para IA'" in r and 'Baixar registros (.zip)' in j
