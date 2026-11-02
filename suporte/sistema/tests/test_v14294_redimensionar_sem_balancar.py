"""2.62: abrir/fechar painel redimensiona o canvas sem mudar zoom nem posição do mapa (node, sem navegador)."""
import re,shutil,subprocess,json
from pathlib import Path
import pytest
JS=Path(__file__).resolve().parent.parent/'app'/'js'/'02_vista_imagem_web.js'

@pytest.mark.skipif(not shutil.which('node'),reason='node ausente')
def test_resize_preserva_vista():
    src=JS.read_text(encoding='utf-8');i=src.index('function resizeCanvas()');j=src.index('// O espaço de imagem',i)
    code=src[i:j]
    script="""
const window={devicePixelRatio:1};let rect={width:1000,height:600};const canvas={width:300,height:150,getBoundingClientRect:()=>rect};
const view={s:2,ox:100,oy:50};let canvasResizeFrame=0;function draw(){}const performance={now:()=>0};
"""+code+"""
resizeCanvas();const a={...view,w:canvas.width};
rect={width:800,height:600};resizeCanvas();const b={...view,w:canvas.width};
rect={width:1000,height:600};resizeCanvas();const c={...view,w:canvas.width};
console.log(JSON.stringify([a,b,c]))"""
    out=json.loads(subprocess.run(['node','-e',script],capture_output=True,text=True,check=True).stdout)
    a,b,c=out
    assert b['w']==800 and c['w']==1000
    assert (b['s'],b['ox'],b['oy'])==(a['s'],a['ox'],a['oy'])==(c['s'],c['ox'],c['oy'])
