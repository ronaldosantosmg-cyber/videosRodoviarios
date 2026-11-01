"""1.40: segurança contra nomes e caminhos longos (limite de 260 caracteres do Windows, agravado pelas pastas do OneDrive).

Todo arquivo que entra no programa (envios, pacotes .gras, vídeos, exportações) passa por aqui:
- limpar(): tira caracteres inválidos e nomes reservados do Windows (CON, NUL, COM1…), pontos e espaços finais;
- encurtar(): corta o nome (mantendo a extensão) para que pasta + nome caibam no limite, com um sufixo curto de
  controle (~ + 6 letras do hash) para dois nomes longos parecidos não se confundirem;
- longo(): caminho no formato \\\\?\\ (só no Windows) para ler, gravar e apagar mesmo acima de 260;
- apagar(): remove arquivo ou pasta tentando o formato longo;
- situacao(): quanto da folga a instalação deixa para os nomes (avisa na tela quando é pouca).
O limite padrão é 240 (260 menos uma margem para .tmp, .json e visões reduzidas); RODOVIA_LIMITE_CAMINHO o altera."""
from .falhas import registrar as _falha
import os,re,shutil,hashlib,unicodedata
from pathlib import Path

RESERVADOS={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
INVALIDOS=re.compile(r'[\\/:*?"<>|\x00-\x1f]+')

def limite():
    try:return max(60,int(os.environ.get('RODOVIA_LIMITE_CAMINHO') or 240))
    except ValueError:return 240

def comprimento(p):return len(os.path.abspath(str(p)))

def limpar(nome,padrao='arquivo',substituto='_'):
    """Nome de arquivo seguro para o Windows (sem pastas, sem caracteres inválidos, sem nome reservado)."""
    t=unicodedata.normalize('NFC',str(nome or ''));t=t.replace('\\','/').rsplit('/',1)[-1]
    t=INVALIDOS.sub(substituto,t);t=re.sub(r'\s+',' ',t).strip(' .')
    stem,dot,ext=t.rpartition('.') if '.' in t.strip('.') else (t,'','')
    if stem.split('.')[0].upper() in RESERVADOS:t='_'+t
    return t or padrao

def recortar(texto,room):
    """Corta o texto para caber em room caracteres, acrescentando -xxxxxx (hash do texto original, para dois
    nomes longos parecidos não se confundirem). Texto que já cabe não muda. None se room for pequeno demais."""
    texto=str(texto)
    if len(texto)<=room:return texto
    if room<8:return None
    h=hashlib.sha1(texto.encode('utf-8')).hexdigest()[:6]
    return texto[:room-7].rstrip(' .')+'-'+h

def _longo_demais(pasta):
    return ValueError(f'A pasta do programa é longa demais para guardar este arquivo ({comprimento(pasta)} caracteres de {limite()}). '
                      'Mova a pasta do Rodovia Studio para um caminho curto (por exemplo C:\\RodoviaStudio) ou ative “caminhos longos” no Windows.')

def encurtar(pasta,nome,extra=0,maximo=None):
    """Nome de arquivo (com extensão) que cabe em pasta + limite. Nomes que já cabem não mudam.
    O hash vem só do nome sem a extensão e a reserva da extensão é fixa (5): imagem, arquivo de mundo e .prj
    com o mesmo nome base continuam com o mesmo nome base depois de cortados."""
    nome=limpar(nome);room=limite()-comprimento(Path(pasta))-1-int(extra)
    if maximo:room=min(room,int(maximo))
    if len(nome)<=room:return nome
    ext=Path(nome).suffix if len(Path(nome).suffix)<=12 else '';stem=nome[:len(nome)-len(ext)]
    cut=recortar(stem,room-max(len(ext),5))
    if cut is None:raise _longo_demais(pasta)
    return cut+ext

def encurtar_pasta(raiz,nome,filho_max=0,limite_nome=60,sufixo=0):
    """Nome de subpasta que deixa espaço para um arquivo de até filho_max caracteres dentro dela."""
    nome=limpar(nome,'Projeto');room=min(limite()-comprimento(Path(raiz))-2-int(filho_max)-int(sufixo),limite_nome)
    cut=recortar(nome,room)
    if cut is None:raise _longo_demais(raiz)
    return cut

def longo(p):
    """Caminho no formato \\\\?\\ (Windows) — fora do Windows devolve o caminho absoluto."""
    p=os.path.abspath(str(p))
    if os.name=='nt' and not p.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\'+p[2:] if p.startswith('\\\\') else '\\\\?\\'+p
    return p

def apagar(p):
    """Remove arquivo ou pasta (também acima de 260 no Windows). Não falha se não existir."""
    q=longo(p)
    try:
        if os.path.isdir(q) and not os.path.islink(q):shutil.rmtree(q)
        elif os.path.lexists(q):os.remove(q)
    except FileNotFoundError as _e:_falha(__name__,_e)

def rmtree(p):
    """shutil.rmtree que aceita caminho longo no Windows (mesma regra de erro do rmtree comum)."""
    shutil.rmtree(longo(p))

def unlink(p):
    """Path.unlink que aceita caminho longo no Windows."""
    os.remove(longo(p))

def gravar(p,dados):
    """Grava bytes criando as pastas (aceita caminho longo no Windows)."""
    q=longo(p);os.makedirs(os.path.dirname(q),exist_ok=True)
    with open(q,'wb') as f:f.write(dados)

def traduzir(exc):
    """Mensagem em português para erros de nome/caminho longo (None se o erro é de outro tipo)."""
    import errno
    if isinstance(exc,OSError) and (exc.errno==errno.ENAMETOOLONG or getattr(exc,'winerror',None) in (206,)):
        return ('O nome ou o caminho do arquivo é longo demais para o Windows (limite de 260 caracteres). '
                'Use um nome mais curto ou mova a pasta do Rodovia Studio para um caminho curto (por exemplo C:\\RodoviaStudio).')
    return None

def situacao(raiz,caminho_mais_longo=0):
    """Folga que a instalação deixa para os nomes: caracteres livres depois da pasta de projetos e de vídeos."""
    lim=limite();r=comprimento(raiz)
    pior=lim-r-1-(32+1+len('imagem_local')+1)   # <projetos>\<id de 32>\imagem_local\<nome>
    return {'limite':lim,'pasta':str(raiz),'comprimento_pasta':r,'folga_nome':pior,'curto':pior<60,
            'mensagem':'' if pior>=60 else (f'A pasta de projetos tem {r} caracteres e sobram só {max(pior,0)} para o nome dos arquivos '
                       f'(limite do Windows: {lim}). Nomes longos serão encurtados. Para evitar, mova a pasta do Rodovia Studio para um caminho curto (por exemplo C:\\RodoviaStudio).')}
