"""1.26: registros (logs) de execução e de erros por projeto, e exportação de um prompt para IA que descreve
como reproduzir a geração do vídeo.

Arquivos (JSON por linha, com rotação simples em 2 MB):
  <projeto>/logs/execucao.jsonl  — início, etapas e fim de cada tarefa (análise, prévia, vídeo...)
  <projeto>/logs/erros.jsonl     — falhas com o rastreamento (traceback) e erros da tela (navegador)
"""
from .tempo import tempo
import json,time,platform,sys,hashlib,os,threading,zipfile,io
from pathlib import Path

MAX_BYTES=2*1024*1024
_lock=threading.Lock()

def _dir(project_dir):
    d=Path(project_dir)/'logs';d.mkdir(exist_ok=True);return d

def _rotate(f):
    if f.exists() and f.stat().st_size>MAX_BYTES:
        old=f.with_suffix('.1.jsonl');old.unlink(missing_ok=True);f.replace(old)

def write(project_dir,kind,event,**data):
    """Acrescenta um registro. kind: 'execucao' ou 'erros'. Nunca levanta exceção (registro é auxiliar)."""
    try:
        f=_dir(project_dir)/f'{kind}.jsonl';rec={'t':time.strftime('%Y-%m-%d %H:%M:%S'),'evento':event,**data}
        line=json.dumps(rec,ensure_ascii=False,default=str)
        with _lock:
            _rotate(f)
            with f.open('a',encoding='utf-8') as fo:fo.write(line+'\n')
    except Exception:pass

def read(project_dir,kind,limit=300):
    out=[];d=Path(project_dir)/'logs'
    for f in (d/f'{kind}.1.jsonl',d/f'{kind}.jsonl'):
        if not f.exists():continue
        for line in f.read_text(encoding='utf-8',errors='replace').splitlines():
            try:out.append(json.loads(line))
            except ValueError:continue
    return out[-limit:]

def clear(project_dir):
    d=Path(project_dir)/'logs';n=0
    if d.exists():
        for f in d.glob('*.jsonl'):f.unlink(missing_ok=True);n+=1
    return n

class JobLog:
    """Envolve o status de uma tarefa: registra cada mensagem nova (sem repetir), a duração e o fim."""
    def __init__(self,project_dir,jid,kind,settings=None):
        self.d=project_dir;self.jid=jid;self.kind=kind;self.t0=time.time();self.last=None
        write(project_dir,'execucao','inicio',tarefa=jid,tipo=kind,versao=app_version(),config_sha=config_hash(settings) if settings is not None else None)
    def status(self,p,msg):
        if msg!=self.last:
            self.last=msg;write(self.d,'execucao','etapa',tarefa=self.jid,tipo=self.kind,progresso=round(float(p),3),mensagem=str(msg)[:300],s=round(time.time()-self.t0,2))
    def done(self,message):
        write(self.d,'execucao','fim',tarefa=self.jid,tipo=self.kind,mensagem=str(message)[:400],duracao_s=round(time.time()-self.t0,2))
    def failed(self,exc,tb):
        write(self.d,'execucao','falha',tarefa=self.jid,tipo=self.kind,erro=type(exc).__name__,mensagem=str(exc)[:400],duracao_s=round(time.time()-self.t0,2))
        write(self.d,'erros','falha_tarefa',tarefa=self.jid,tipo=self.kind,erro=type(exc).__name__,mensagem=str(exc)[:2000],rastreamento=tb[-12000:])

def app_version():
    try:return json.loads((Path(__file__).resolve().parents[1]/'VERSAO.json').read_text(encoding='utf-8')).get('version')
    except Exception:return None

def config_hash(settings):
    try:
        d=settings.model_dump() if hasattr(settings,'model_dump') else settings
        return hashlib.sha256(json.dumps(d,sort_keys=True,default=str).encode()).hexdigest()[:16]
    except Exception:return None

def environment():
    env={'sistema':platform.platform(),'python':sys.version.split()[0],'processador':platform.processor() or platform.machine(),'nucleos':os.cpu_count(),'versao_app':app_version()}
    for mod in ('numpy','cv2','ezdxf','shapely','pyproj','PIL','fastapi','scipy'):
        try:
            m=__import__(mod);env[mod]=getattr(m,'__version__',None) or getattr(m,'VERSION',None)
        except Exception:env[mod]=None
    return env

def _sha(f):
    h=hashlib.sha256()
    with open(f,'rb') as fo:
        while b:=fo.read(1024*1024):h.update(b)
    return h.hexdigest()

def _inputs(d):
    out=[]
    for name in ('input.dxf','input.kmz'):
        f=d/name
        if f.exists():out.append({'arquivo':name,'bytes':f.stat().st_size,'sha256':_sha(f)})
    for sub in ('camadas','imagem_local','imagens'):
        p=d/sub
        if p.exists():
            for f in sorted(p.iterdir()):
                if f.is_file() and not f.name.endswith('.tmp'):out.append({'arquivo':f'{sub}/{f.name}','bytes':f.stat().st_size})
    return out

def _jobs(pid,limit=12):
    try:
        from . import store
        with store.connect() as c:rows=c.execute('SELECT id,kind,state,progress,message,error,created FROM jobs WHERE project=? ORDER BY created DESC LIMIT ?',(pid,limit)).fetchall()
        return [dict(r) for r in rows]
    except Exception:return []

def ai_prompt(project_dir,pid):
    """Texto em Markdown para colar numa IA: o que o programa fez, com quais entradas e parâmetros, e como reproduzir."""
    d=Path(project_dir);cfg=json.loads((d/'config.json').read_text(encoding='utf-8')) if (d/'config.json').exists() else {}
    ana=json.loads((d/'analysis.json').read_text(encoding='utf-8')) if (d/'analysis.json').exists() else None
    vid=json.loads((d/'video.json').read_text(encoding='utf-8')) if (d/'video.json').exists() else None
    env=environment();execs=read(d,'execucao',120);errs=read(d,'erros',8);jobs=_jobs(pid)
    marks={k:len(v) for k,v in cfg.items() if isinstance(v,list) and v}
    L=[]
    L.append(f"# Reproduzir a geração do vídeo — Rodovia Studio {env.get('versao_app') or ''}".rstrip())
    L.append('')
    L.append('Você é um assistente técnico. Abaixo está o registro completo de uma execução do **Rodovia Studio** (aplicativo local, Python/FastAPI, que transforma um DXF/KMZ de projeto rodoviário num vídeo MP4 de apresentação sobre imagem aérea). '
             'Use estas informações para: (1) explicar o que foi feito em cada etapa; (2) reproduzir o mesmo vídeo com a mesma configuração; (3) diagnosticar os erros registrados, se houver. '
             'Não invente dados que não estejam aqui: quando faltar algo (ex.: o próprio DXF), peça o arquivo.')
    L.append('')
    L.append('## Como o vídeo é gerado (pipeline)')
    L.append('1. **Análise** (`analyze`): lê o DXF (ezdxf) e o KMZ; cada camada recebe um tipo (eixo, pista nova, existente, acostamento...) pelo mapeamento `layers` da configuração; hachuras são classificadas por assinatura `camada | padrão | cor` (`hatch_roles`, `hatch_auto`); camadas em `hidden_layers` são ignoradas e as de `frozen_layers` aparecem prontas desde o início.')
    L.append('2. **Eixo e estaqueamento**: maior linha do papel “eixo” (ou `custom_axis`), sentido por `reverse_axis`, km por `km_start_m`/`km_end_m` e `chainage`.')
    L.append('3. **Cena**: mosaico da imagem aérea (`imagery`, `web_imagery`, `local_imagery`), pavimento rasterizado com texturas, sinalização, tráfego simulado (`traffic*`), destaques, pórticos (`gantries`) e chamadas.')
    L.append('4. **Câmera**: percurso ao longo do eixo com paradas nas obras (`camera_mode`, `duration_s`, `view_width_m`); construção progressiva do projeto.')
    L.append('5. **Codificação**: quadros RGB → H.264 (ffmpeg; `encoder`, `fps`, `width`), conferência do MP4 ao final.')
    L.append('')
    L.append('## Ambiente')
    L.append('```json');L.append(json.dumps(env,ensure_ascii=False,indent=1));L.append('```')
    L.append('## Arquivos de entrada (o DXF original não é alterado)')
    L.append('```json');L.append(json.dumps(_inputs(d),ensure_ascii=False,indent=1));L.append('```')
    if ana:
        L.append('## Resultado da análise')
        summ={'comprimento_geometrico_m':ana.get('geometric_length_m'),'limites':ana.get('bounds'),'crs':ana.get('crs'),'camadas':len(ana.get('layers',[])),
              'hachuras':len(ana.get('hatches',[])),'eixos':ana.get('routes'),'conferencia_kmz':{k:v for k,v in (ana.get('georef_check') or {}).items() if k!='samples'},'avisos':ana.get('warnings',[])[:30]}
        L.append('```json');L.append(json.dumps(summ,ensure_ascii=False,indent=1));L.append('```')
    L.append('## Marcações do projeto (quantidade por tipo)')
    L.append('```json');L.append(json.dumps(marks,ensure_ascii=False));L.append('```')
    L.append('## Configuração completa usada (config.json)')
    txt=json.dumps(cfg,ensure_ascii=False,indent=1)
    if len(txt)>120000:txt=json.dumps(cfg,ensure_ascii=False,separators=(',',':'))[:120000]+' …(cortado)'
    L.append('```json');L.append(txt);L.append('```')
    if vid:
        L.append('## Último vídeo gerado (video.json)');L.append('```json');L.append(json.dumps(vid,ensure_ascii=False,indent=1)[:20000]);L.append('```')
    if jobs:
        L.append('## Tarefas recentes');L.append('| criada | tipo | situação | mensagem |');L.append('|---|---|---|---|')
        for j in jobs:L.append(f"| {j.get('created')} | {j.get('kind')} | {j.get('state')} | {str(j.get('message') or '').replace('|','/')[:160]} |")
    if execs:
        L.append('## Registro de execução (últimos eventos)');L.append('```')
        for e in execs:L.append(f"{e.get('t')} {e.get('evento'):<6} {e.get('tipo','')} {e.get('mensagem','')} {('('+tempo(e.get('s') or e.get('duracao_s'))+')') if (e.get('s') or e.get('duracao_s')) else ''}".rstrip())
        L.append('```')
    if errs:
        L.append('## Erros registrados')
        for e in errs:
            L.append(f"### {e.get('t')} — {e.get('evento')} {e.get('tipo','') or ''}: {e.get('erro','')}");L.append(str(e.get('mensagem',''))[:1500])
            if e.get('rastreamento'):L.append('```');L.append(str(e['rastreamento'])[-5000:]);L.append('```')
            if e.get('pilha'):L.append('```');L.append(str(e['pilha'])[-3000:]);L.append('```')
    L.append('## Como reproduzir')
    L.append('1. Instale o Rodovia Studio na mesma versão (ou mais nova; a configuração é migrada automaticamente).')
    L.append('2. Crie um projeto, envie o mesmo DXF/KMZ (confira o SHA-256 acima) e use “Importar configuração” com o JSON acima.')
    L.append('3. Clique “Analisar arquivos”, depois “Gerar / atualizar prévia” e “Gerar novo vídeo”.')
    L.append('4. Pela linha de comando (opcional), na pasta `sistema/programa`: `python -c "from app.render import render; from app.models import Settings; import json,pathlib; d=pathlib.Path(r\'<pasta do projeto>\'); render(d, Settings.model_validate(json.loads((d/\'config.json\').read_text(encoding=\'utf-8\'))), print, lambda: False)"`.')
    L.append('5. Compare a duração, a resolução e as mensagens do registro de execução acima.')
    return '\n'.join(L)+'\n'

def bundle(project_dir,pid):
    """ZIP com os registros, a configuração, a análise e o prompt para IA."""
    d=Path(project_dir);buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted((d/'logs').glob('*.jsonl')) if (d/'logs').exists() else []:z.write(f,'logs/'+f.name)
        for name in ('config.json','analysis.json','video.json','preview.json','error.log','ffmpeg.log'):
            if (d/name).exists():z.write(d/name,name)
        z.writestr('prompt_ia.md',ai_prompt(d,pid));z.writestr('ambiente.json',json.dumps(environment(),ensure_ascii=False,indent=1))
    return buf.getvalue()
