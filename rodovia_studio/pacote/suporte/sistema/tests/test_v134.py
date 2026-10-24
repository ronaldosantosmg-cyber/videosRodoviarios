"""1.34: texturas “artístico realista” (só no estilo novo; projetos anteriores iguais), esquema 27, tela sem
referências a versões anteriores nem ao TH57, módulos novos da interface e temas claro/escuro."""
import re,html,json
from pathlib import Path
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_v116 import mixed,S,region  # noqa: F401
APP=Path(__file__).resolve().parents[1]/'app'

def test_schema_27_and_texture_default():
    from app.models import Settings
    from app.migration import SCHEMA_VERSION
    assert SCHEMA_VERSION>=27
    old=Settings.model_validate({'schema_version':26,'km_start_m':0,'km_end_m':100});assert old.texture_style=='realistic'   # anterior: igual
    assert Settings.model_validate({'schema_version':26,'km_start_m':0,'km_end_m':100,'texture_style':'anterior'}).texture_style=='anterior'
    assert Settings().texture_style=='artistico'                                                                   # novos projetos

def test_artistic_textures(mixed):
    from app.render import Scene
    from app import visual
    v=((500150,7800005),40)
    real=Scene(mixed,S(texture_style='realistic')).frame(0,view=v)[0];art=Scene(mixed,S(texture_style='artistico')).frame(0,view=v)[0]
    sc=Scene(mixed,S());ex=region(sc,v,(500140,7800007),(500160,7800013));pv=region(sc,v,(500140,7799997),(500160,7800003))
    # Muda as superfícies, sem mudar o tom geral; fora das superfícies nada muda.
    assert not np.array_equal(real[ex],art[ex]) and abs(float(real[ex].mean())-float(art[ex].mean()))<10
    v2=((500298,7800005),40);a2=Scene(mixed,S(texture_style='realistic')).frame(0,view=v2)[0];b2=Scene(mixed,S(texture_style='artistico')).frame(0,view=v2)[0]
    gr=region(sc,v2,(500303,7799999),(500312,7800011));assert np.array_equal(a2[gr],b2[gr])
    # Borda do pavimento mais escura que o meio (sujeira/oclusão suave junto à borda).
    im=np.full((60,80,3),120,np.uint8);surf=np.zeros((60,80),np.uint8);surf[:,10:70]=1
    A=np.array([[.05,0,500000.],[0,-.05,7800000.]]);visual.shade_artistic(im,surf,A,.05,np.ones((60,80),bool))
    assert im[:,11:13].mean()<im[:,35:45].mean()-4 and (im[:,:10]==120).all()
    # Grão fino em vez de manchas grandes: menos variação de baixa frequência no asfalto novo.
    def low(a):g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(np.float32);return float(cv2.GaussianBlur(g,(0,0),12).std())
    assert low(art[pv])<low(real[pv])

def test_texture_preview_artistic():
    from app.server import app
    c=TestClient(app)
    a=c.get('/api/texture_preview.png?surface=concreto&realistic=true').content;b=c.get('/api/texture_preview.png?surface=concreto&realistic=true&estilo=artistico').content
    A=cv2.imdecode(np.frombuffer(a,np.uint8),1);B=cv2.imdecode(np.frombuffer(b,np.uint8),1);assert A.shape==B.shape and not np.array_equal(A,B)

VER=re.compile(r'(?<![\d.,])1\.(?:[2-9]|[1-3]\d)(?![\d,])(?!\s*(?:m\b|km|s\b|×|x\b))')
def visivel(s):
    s=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S)
    attrs=re.findall(r'(?:title|placeholder|aria-label)="([^"]*)"',s)
    t=re.sub(r'<[^>]+>','\n',s);return html.unescape(t)+'\n'+'\n'.join(attrs)

def test_tela_sem_th57_nem_versoes_anteriores():
    for f in ['index.html','ajuda.html']:
        s=(APP/f).read_text(encoding='utf-8')
        # O botão do exemplo e a ficha de referência ficam fora da tela (classe “retirada”).
        s=re.sub(r'<button id="example"[^>]*>.*?</button>','',s);s=re.sub(r'<details class="retirada">.*?</details>','',s,flags=re.S)
        ruins=[l.strip()[:120] for l in visivel(s).splitlines() if 'TH57' in l or VER.search(l)]
        assert not ruins,(f,ruins)
    for f in (APP/'js').glob('*.js'):
        for lit in re.findall(r"'([^'\n]{8,})'",f.read_text(encoding='utf-8')):
            if lit.endswith(('.js','.py')) or re.match(r'^1\.\d+: ',lit):continue   # rótulos internos (sem o prefixo na tela)
            assert 'TH57' not in lit,(f.name,lit[:100])

def test_modulos_1_34():
    js={f.name:f.read_text(encoding='utf-8') for f in (APP/'js').glob('*.js')}
    for nome,fns in {'39_paineis_menu.js':['pnAbrir','pnFixar','pnEntrar','pnSair'],'40_tema.js':['aplicarTema','temaEfetivo'],'41_progresso.js':['baixarArquivo','progMostrar'],'42_comandos_continuos.js':['pedirProximo','encerrarRepeticao']}.items():
        for f in fns:assert f'function {f}(' in js[nome],(nome,f)
    css=(APP/'estilo.css').read_text(encoding='utf-8')
    for k in [':root[data-tema=escuro]',':root[data-tema=claro]','.atividades','.progCard','body.paineis.pnAberto.pnFixado']:assert k in css,k
    for tema in ('escuro','claro'):
        bloco=re.search(r':root\[data-tema=%s\]\{(.*?)\}'%tema,css,re.S).group(1)
        for var in ['--fundo','--panel','--texto','--accent','--accent-texto','--cromo','--menu','--campo','--erro','--aviso']:assert var+':' in bloco,(tema,var)
    h=(APP/'index.html').read_text(encoding='utf-8');assert "localStorage.getItem('rodovia_tema')" in h   # tema aplicado antes de desenhar a página
