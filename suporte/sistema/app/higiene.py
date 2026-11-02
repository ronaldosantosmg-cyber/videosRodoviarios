"""2.56: faxina segura da instalação e verificação de pastas/arquivos ausentes, para preparar a publicação.

Princípios
- NADA é apagado na limpeza: o que sai vai para sistema/_quarentena/<data>/ com um índice (quarentena.json) que permite restaurar.
  Só `esvaziar_quarentena` apaga de verdade, e somente o que já está na quarentena há N dias.
- Nunca toca: projetos/, videos/, dados/, ZIPs de atualização ainda NÃO aplicados (atualizacoes/*.zip), o programa em uso
  (sistema/programa), os backups de atualização mais recentes (necessários para "Restaurar versão anterior") nem links simbólicos.
- Só executa com o aplicativo FECHADO (ou com force=True).
- Modo padrão = prévia (executar=False): lista o que sairia, quanto espaço libera e por quê.
A verificação (`verificar`) acusa: pastas/arquivos obrigatórios ausentes, módulos Python importados que não existem, arquivos .py com erro de sintaxe,
scripts/estilos referenciados pela interface que não existem e JSON de versão inválido."""
import ast,json,os,re,shutil,sys,time
from pathlib import Path

DIA=86400
CATEGORIAS={
 'backups_atualizacao':('Cópias de segurança de atualizações antigas','Ficam as mais recentes (restaurar versão anterior continua funcionando).','baixo'),
 'backups_legado':('Cópias de organizações antigas (legado)','Sobras de migrações de versões 1.x; ficam as mais recentes.','baixo'),
 'zips_aplicados':('ZIPs de atualização já aplicados','Ficam os mais recentes; os pendentes (na pasta atualizacoes) nunca são tocados.','baixo'),
 'zips_rejeitados':('ZIPs de atualização rejeitados','Antigos, não aplicados.','baixo'),
 'caches_python':('Caches do Python (__pycache__, .pytest_cache)','Regeneram sozinhos na próxima abertura.','baixo'),
 'resultados_testes':('Resultados de testes visuais','Imagens geradas por testes; refeitas ao testar.','baixo'),
 'logs_grandes':('Registros muito grandes','Registro do servidor acima do limite; um novo é criado.','baixo'),
 'instaladores_cache':('Instaladores guardados (pacotes_webview2)','Só quando o WebView2 já está instalado em webview2/.','medio'),
 'programa_duplicado':('Cópias duplicadas do programa','Outras pastas com o programa (suporte/sistema, sistema.zip) enquanto sistema/programa está completo.','medio'),
 'entrega_extraida':('Sobras da entrega extraída (pacote/, raiz/, apoio/ ...)','Pacote de instalação já extraído na pasta; o programa instalado não depende dele.','medio'),
}
OBRIGATORIOS_PROGRAMA=['app/server.py','app/index.html','app/__init__.py','app/js','assets','run.py','iniciar.ps1','preparar.py','VERSAO.json','requirements.txt','atualizador.py','rodovia.ico','app/georas_logo.png','app/icone.png']
OBRIGATORIOS_RAIZ=['projetos','videos','atualizacoes']
PROTEGIDOS=('projetos','videos','dados')

def _tam(p):
    p=Path(p)
    try:
        if p.is_symlink():return 0
        if p.is_file():return p.stat().st_size
        return sum(f.stat().st_size for f in p.rglob('*') if f.is_file() and not f.is_symlink())
    except OSError:return 0

def _raiz(raiz):
    from atualizador import find_root
    r,_=find_root(raiz);return Path(r).resolve()

def programa_dir(raiz):
    raiz=Path(raiz)
    for c in (raiz/'sistema/programa',raiz/'suporte/sistema',raiz):
        if (c/'app/server.py').exists():return c
    return raiz/'sistema/programa'

def sistema_dir(raiz):
    raiz=Path(raiz);return raiz/'suporte' if (raiz/'suporte/sistema/app/server.py').exists() and not (raiz/'sistema/programa').exists() else raiz/'sistema'

# ------------------------------------------------------------------------------------------------ verificação
def verificar(raiz):
    """pastas e arquivos que faltam ou estão quebrados. {'ok':bool,'problemas':[{'tipo','caminho','detalhe'}]}"""
    raiz=_raiz(raiz);prog=programa_dir(raiz);out=[]
    def add(tipo,caminho,detalhe):out.append({'tipo':tipo,'caminho':str(caminho),'detalhe':detalhe})
    for n in OBRIGATORIOS_PROGRAMA:
        p=prog/n
        if not p.exists():add('ausente',p.relative_to(raiz) if p.is_relative_to(raiz) else p,'item obrigatório do programa não encontrado')
        elif p.is_dir() and not any(p.iterdir()):add('vazio',p.relative_to(raiz),'pasta obrigatória está vazia')
    for n in OBRIGATORIOS_RAIZ:
        if not (raiz/n).is_dir():add('ausente',n,'pasta de dados ausente (será recriada ao abrir; confira se não foi movida)')
    if not ((raiz/'Rodovia Studio.exe').exists() or (raiz/'ABRIR RODOVIA STUDIO.cmd').exists() or (sistema_dir(raiz)/'ABRIR RODOVIA STUDIO.cmd').exists()):add('ausente','Rodovia Studio.exe / ABRIR RODOVIA STUDIO.cmd','nenhum arquivo de abertura encontrado')
    if os.name=='nt' and not any((prog/'runtime'/n).exists() for n in ('python.exe','Scripts/python.exe')):add('ausente',(prog/'runtime/python.exe').relative_to(raiz),'Python portátil ausente (o programa só abre com Python instalado)')
    try:
        from . import texturas_pacote as _T
        st=_T.status(prog/'assets'/'texturas')
        if not st['ok']:add('ausente',(prog/'assets/texturas').relative_to(raiz) if prog.is_relative_to(raiz) else 'assets/texturas','texturas do pacote ausentes/alteradas ('+', '.join((st['faltando']+st['alteradas'])[:4])+'); o motor usa texturas procedurais. Reinstale com ATUALIZAR TEXTURAS E IA.cmd')
    except Exception:pass
    v=prog/'VERSAO.json'
    if v.exists():
        try:
            d=json.loads(v.read_text(encoding='utf-8'))
            if not d.get('version'):add('invalido',v.relative_to(raiz),'VERSAO.json sem o campo version')
        except (ValueError,OSError):add('invalido',v.relative_to(raiz),'VERSAO.json ilegível')
    app=prog/'app'
    if app.is_dir():
        mods={p.stem for p in app.glob('*.py')}|{p.name for p in app.iterdir() if p.is_dir() and (p/'__init__.py').exists()}
        for f in sorted(app.rglob('*.py')):
            if '__pycache__' in f.parts:continue
            try:tree=ast.parse(f.read_text(encoding='utf-8'),filename=str(f))
            except (SyntaxError,UnicodeError,OSError) as e:add('invalido',f.relative_to(raiz),'erro de sintaxe/leitura: '+str(e)[:120]);continue
            base=f.parent
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.level>=1:
                    alvo=base
                    for _ in range(node.level-1):alvo=alvo.parent
                    if node.module:
                        sub=alvo/node.module.replace('.','/')
                        if not (sub.with_suffix('.py').exists() or (sub/'__init__.py').exists()):add('modulo_ausente',f.relative_to(raiz),f'importa .{node.module} mas o módulo não existe')
                    else:
                        for a in node.names:
                            if not ((alvo/(a.name+'.py')).exists() or (alvo/a.name/'__init__.py').exists()) and a.name not in _nomes_modulo(alvo/'__init__.py'):add('modulo_ausente',f.relative_to(raiz),f'importa {a.name} de . mas não existe')
        html=app/'index.html'
        if html.exists():
            txt=html.read_text(encoding='utf-8',errors='replace')
            for ref in sorted(set(re.findall(r'(?:src|href)="(/?(?:js|css|static|assets)/[^"?#]+)',txt))):
                alvo=app/ref.lstrip('/')
                if not alvo.exists() and not (prog/ref.lstrip('/')).exists():add('recurso_ausente','app/index.html',f'referencia {ref} que não existe')
    return {'ok':not out,'problemas':out,'programa':str(prog),'versao':_versao(prog)}

def _nomes_modulo(init):
    try:return {n.id for t in ast.walk(ast.parse(Path(init).read_text(encoding='utf-8'))) if isinstance(t,ast.Assign) for n in t.targets if isinstance(n,ast.Name)}
    except (OSError,SyntaxError,UnicodeError):return set()

def _versao(prog):
    try:return json.loads((Path(prog)/'VERSAO.json').read_text(encoding='utf-8')).get('version')
    except (OSError,ValueError):return None

# ------------------------------------------------------------------------------------------------ inventário
def inventario(raiz,manter_backups=3,manter_legado=1,manter_zips=2,log_max_mb=5,idade_dias=14,agora=None):
    """itens candidatos: [{'categoria','caminho','bytes','motivo'}]. Sem alterar nada."""
    raiz=_raiz(raiz);agora=agora or time.time();prog=programa_dir(raiz);sis=sistema_dir(raiz);itens=[]
    def add(cat,p,motivo):
        p=Path(p)
        if p.is_symlink() or not p.exists():return
        itens.append({'categoria':cat,'caminho':str(p.relative_to(raiz)),'bytes':_tam(p),'motivo':motivo})
    def recentes(pastas,n):return sorted(pastas,key=lambda p:p.stat().st_mtime,reverse=True)
    bk=sis/'backups'
    if bk.is_dir():
        ant=recentes([p for p in bk.glob('antes_*') if p.is_dir()],0)
        for p in ant[manter_backups:]:add('backups_atualizacao',p,f'mais antiga que as {manter_backups} cópias recentes')
        leg=recentes([p for p in list(bk.glob('legado_*'))+list(bk.glob('backup_antes_*')) if p.is_dir()],0)
        for p in leg[manter_legado:]:
            if agora-p.stat().st_mtime>idade_dias*DIA:add('backups_legado',p,'sobra de organização antiga com mais de %d dias'%idade_dias)
    ap=raiz/'atualizacoes'/'aplicadas'
    if ap.is_dir():
        zips=sorted(ap.glob('*.zip'),key=lambda p:p.stat().st_mtime,reverse=True)
        for p in zips[manter_zips:]:add('zips_aplicados',p,'ZIP já aplicado; ficam os %d mais recentes'%manter_zips)
    rj=raiz/'atualizacoes'/'rejeitadas'
    if rj.is_dir():
        for p in rj.glob('*.zip'):
            if agora-p.stat().st_mtime>idade_dias*DIA:add('zips_rejeitados',p,'ZIP rejeitado há mais de %d dias'%idade_dias)
    for base in (prog,):
        for p in list(base.rglob('__pycache__'))+list(base.glob('.pytest_cache')):
            if p.is_dir() and not any(x in ('runtime','webview2','webview2_dados') for x in p.relative_to(base).parts):add('caches_python',p,'cache regenerável')
    rt=prog/'resultados_testes_visuais'
    if rt.is_dir() and any(rt.iterdir()):add('resultados_testes',rt,'imagens de testes anteriores')
    logs=sis/'logs'
    if logs.is_dir():
        for f in logs.glob('*.log'):
            if f.stat().st_size>log_max_mb*1024*1024:add('logs_grandes',f,'registro com %.1f MB (limite %d MB)'%(f.stat().st_size/1048576,log_max_mb))
    wv=prog/'pacotes_webview2'
    if wv.is_dir() and (prog/'webview2').is_dir() and any((prog/'webview2').iterdir()):add('instaladores_cache',wv,'WebView2 já instalado em webview2/')
    if (prog/'app/server.py').exists() and prog.resolve()==(raiz/'sistema/programa').resolve():
        ok=verificar(raiz)['ok']
        if ok:
            add('programa_duplicado',raiz/'suporte','organização antiga (suporte/sistema e documentos); o programa em uso é sistema/programa')
            add('programa_duplicado',sis/'sistema.zip','arquivo compactado de uma versão antiga do programa')
            for n in ('app','assets','runtime','tests'):                      # sobras do formato antigo diretamente em sistema/
                d=sis/n
                if d.is_dir() and d.resolve()!=prog.resolve():add('programa_duplicado',d,'formato antigo; o programa em uso está em sistema/programa')
            if (raiz/'pacote').is_dir():                                      # entrega extraída dentro da pasta
                for n in ('pacote','raiz','apoio'):
                    if (raiz/n).is_dir():add('entrega_extraida',raiz/n,'pacote de entrega extraído; não é usado após a instalação')
                for n in ('manifest.json','instalar.ps1'):
                    if (raiz/n).is_file():add('entrega_extraida',raiz/n,'arquivo da entrega extraída')
    # sem duplicatas (pasta pai já listada)
    caminhos=sorted({i['caminho'] for i in itens});vistos=[];final=[]
    for i in sorted(itens,key=lambda i:len(Path(i['caminho']).parts)):
        if any(Path(i['caminho']).is_relative_to(v) for v in vistos):continue
        vistos.append(Path(i['caminho']));final.append(i)
    return {'raiz':str(raiz),'programa':str(prog),'itens':final,'total_bytes':sum(i['bytes'] for i in final),
            'por_categoria':{c:{'titulo':CATEGORIAS[c][0],'descricao':CATEGORIAS[c][1],'risco':CATEGORIAS[c][2],'bytes':sum(i['bytes'] for i in final if i['categoria']==c),'itens':sum(1 for i in final if i['categoria']==c)} for c in CATEGORIAS}}

# ------------------------------------------------------------------------------------------------ limpeza
def _seguro(raiz,rel):
    """caminho relativo dentro da raiz, fora das áreas protegidas e do programa em uso"""
    p=(Path(raiz)/rel)
    r=Path(raiz).resolve()
    try:rp=p.resolve(strict=False);rp.relative_to(r)
    except ValueError:return None
    if p.is_symlink():return None
    partes=Path(rel).parts
    if not partes or partes[0] in PROTEGIDOS:return None
    if Path(rel).as_posix().startswith('atualizacoes/') and Path(rel).parent.as_posix()=='atualizacoes':return None   # ZIP pendente
    prog=programa_dir(r).resolve()
    if rp==prog or rp==r or rp in prog.parents:return None
    return p

def limpar(raiz,executar=False,categorias=None,force=False,**opcoes):
    """Prévia (padrão) ou execução. Move para sistema/_quarentena/<carimbo>/ e grava quarentena.json."""
    raiz=_raiz(raiz);inv=inventario(raiz,**opcoes);sel=[i for i in inv['itens'] if (categorias is None or i['categoria'] in categorias)]
    res={'executado':bool(executar),'itens':[],'liberado_bytes':0,'erros':[],'quarentena':None}
    if not executar:
        res['itens']=sel;res['liberado_bytes']=sum(i['bytes'] for i in sel);return res
    from atualizador import app_running
    if not force and app_running():raise RuntimeError('O Rodovia Studio está aberto. Feche-o antes de limpar.')
    stamp=time.strftime('%Y%m%d_%H%M%S');q=sistema_dir(raiz)/'_quarentena'/stamp;indice=[]
    for i in sel:
        p=_seguro(raiz,i['caminho'])
        if p is None:res['erros'].append(i['caminho']+': protegido');continue
        dst=q/i['categoria']/p.name
        try:
            dst.parent.mkdir(parents=True,exist_ok=True)
            if i['categoria']=='logs_grandes':
                shutil.copy2(p,dst);p.write_text('',encoding='utf-8')          # registro em uso: esvazia em vez de mover
            else:shutil.move(str(p),str(dst))
            indice.append({'origem':i['caminho'],'destino':dst.relative_to(raiz).as_posix(),'categoria':i['categoria'],'bytes':i['bytes']})
            res['itens'].append(i);res['liberado_bytes']+=i['bytes']
        except OSError as e:res['erros'].append(i['caminho']+': '+str(e)[:160])
    if indice:
        q.mkdir(parents=True,exist_ok=True);(q/'quarentena.json').write_text(json.dumps({'criado':stamp,'itens':indice},ensure_ascii=False,indent=1),encoding='utf-8');res['quarentena']=str(q)
    return res

def restaurar(raiz,stamp):
    """devolve ao lugar de origem tudo o que a limpeza `stamp` moveu (sem sobrescrever o que já existe)."""
    raiz=_raiz(raiz);q=sistema_dir(raiz)/'_quarentena'/stamp;f=q/'quarentena.json'
    if not f.is_file():raise ValueError('Quarentena não encontrada: '+stamp)
    n=0;pulados=[]
    for i in json.loads(f.read_text(encoding='utf-8'))['itens']:
        src=raiz/i['destino'];dst=_seguro(raiz,i['origem'])
        if dst is None or not src.exists():pulados.append(i['origem']);continue
        if i['categoria']=='logs_grandes':
            pulados.append(i['origem']+' (registro esvaziado; cópia fica na quarentena)');continue
        if dst.exists():pulados.append(i['origem']+' (já existe)');continue
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dst));n+=1
    return {'restaurados':n,'pulados':pulados}

def esvaziar_quarentena(raiz,dias=30,executar=False,agora=None):
    """único ponto que apaga de verdade: pastas de quarentena com mais de `dias` dias."""
    raiz=_raiz(raiz);agora=agora or time.time();base=sistema_dir(raiz)/'_quarentena';out=[]
    if not base.is_dir():return {'removidas':[],'bytes':0}
    for d in sorted(base.iterdir()):
        if d.is_dir() and not d.is_symlink() and agora-d.stat().st_mtime>dias*DIA:out.append((d,_tam(d)))
    if executar:
        for d,_ in out:shutil.rmtree(d,ignore_errors=True)
    return {'removidas':[d.name for d,_ in out],'bytes':sum(b for _,b in out),'executado':bool(executar)}

def _fmt(n):
    for u in ('B','KB','MB','GB'):
        if n<1024 or u=='GB':return f'{n:.1f} {u}' if u!='B' else f'{int(n)} B'
        n/=1024

def main(argv=None):
    import argparse
    a=argparse.ArgumentParser(description='Faxina segura e verificação do Rodovia Studio.')
    a.add_argument('--raiz',default='.');a.add_argument('--executar',action='store_true',help='move para a quarentena (padrão: só mostra)')
    a.add_argument('--verificar',action='store_true');a.add_argument('--categoria',action='append');a.add_argument('--force',action='store_true')
    a.add_argument('--restaurar');a.add_argument('--esvaziar-quarentena',type=int,metavar='DIAS');a.add_argument('--manter-backups',type=int,default=3)
    o=a.parse_args(argv)
    try:
        if o.verificar:
            r=verificar(o.raiz);print('Versão',r['versao'],'—','OK, nada ausente.' if r['ok'] else f"{len(r['problemas'])} problema(s):")
            for p in r['problemas']:print(' -',p['tipo'],p['caminho'],'|',p['detalhe'])
            return 0 if r['ok'] else 1
        if o.restaurar:print(restaurar(o.raiz,o.restaurar));return 0
        if o.esvaziar_quarentena is not None:
            r=esvaziar_quarentena(o.raiz,o.esvaziar_quarentena,o.executar);print(('Removidas' if r.get('executado') else 'Removeria'),r['removidas'],_fmt(r['bytes']));return 0
        r=limpar(o.raiz,o.executar,o.categoria,o.force,manter_backups=o.manter_backups)
        print(('Movido para a quarentena: ' if o.executar else 'Prévia — sairia: ')+_fmt(r['liberado_bytes']))
        for i in r['itens']:print(' -',i['categoria'],i['caminho'],_fmt(i['bytes']),'|',i['motivo'])
        for e in r['erros']:print(' ! ',e)
        if not o.executar:print('Nada foi alterado. Use --executar (com o aplicativo fechado).')
        else:print('Quarentena:',r['quarentena'])
        return 0
    except (RuntimeError,ValueError) as e:print('ERRO:',e);return 2

if __name__=='__main__':sys.exit(main())
