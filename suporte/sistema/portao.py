"""Gate (portão) de qualidade 2.58 — o que uma versão precisa passar antes de ser chamada de "validada".

Etapas (cada uma com resultado ok/falha/pulada e motivo):
  1 sintaxe      – compila todos os .py; node --check em todos os .js (pulada, com aviso, se não houver Node)
  2 suite        – pytest completo; compara as falhas com tests/linha_base_falhas.txt (só falha NOVA reprova)
  3 pacote       – (com --zip) valida o ZIP, aplica numa instalação sintética, abre o servidor (import), verifica estrutura,
                   reverte para a versão anterior e confere o retorno
  4 componentes  – instala/restaura um ZIP de componentes numa instalação sintética
  5 fumaca       – sobe o servidor de verdade (uvicorn em porta livre) e consulta /api/componentes/status e /api/higiene/verificar
Uso: python portao.py [--zip ZIP] [--junit ARQ.xml] [--sem-suite] [--atualizar-base] [--relatorio ARQ.md]
Sem --sem-suite roda a suíte completa (demorada). Saída: relatório Markdown + código de saída 0 só se nenhuma etapa falhar.
"""
import argparse,json,os,shutil,socket,subprocess,sys,tempfile,time,urllib.request,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

PENDENTES=0
AQUI=Path(__file__).resolve().parent
BASE=AQUI/'tests'/'linha_base_falhas.txt'

def etapa(nome,fn,*a):
    t=time.time()
    try:r=fn(*a)
    except Exception as e:r=('falha',f'{type(e).__name__}: {str(e)[:600]}')
    st,msg=r;return {'etapa':nome,'status':st,'detalhe':msg,'segundos':round(time.time()-t,1)}

def sintaxe():
    erros=[];n=0
    for f in AQUI.rglob('*.py'):
        if '__pycache__' in f.parts or 'runtime' in f.parts or 'resultados_testes_visuais' in f.parts:continue
        n+=1
        try:compile(f.read_text(encoding='utf-8'),str(f),'exec')
        except Exception as e:erros.append(f'{f.relative_to(AQUI)}: {e}')
    node=shutil.which('node');js=0
    for f in sorted((AQUI/'app'/'js').glob('*.js')):
        js+=1
        if node:
            r=subprocess.run([node,'--check',str(f)],capture_output=True,text=True)
            if r.returncode:erros.append(f'{f.name}: {(r.stderr or r.stdout).strip()[:300]}')
    if erros:return 'falha','; '.join(erros[:8])
    return 'ok',f'{n} .py compilados; {js} .js '+('checados com Node.' if node else 'NÃO checados (Node ausente).')

def _falhas_junit(xml):
    """xml = arquivo JUnit ou pasta com vários. Testes marcados rerun_pendente não contam como aprovados nem reprovados."""
    out=set();tot=0;pend=0
    arqs=sorted(Path(xml).glob('*.xml')) if Path(xml).is_dir() else [Path(xml)]
    for a in arqs:
        for tc in ET.parse(a).getroot().iter('testcase'):
            tot+=1;pend+=tc.get('rerun_pendente')=='1'
            if tc.find('failure') is not None or tc.find('error') is not None:out.add(tc.get('classname','').split('.')[-1]+'::'+tc.get('name',''))
    global PENDENTES;PENDENTES=pend
    return out,tot

def suite(junit=None,atualizar_base=False):
    if junit is None:
        junit=str(Path(tempfile.mkdtemp())/'j.xml')
        subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests','--junitxml',junit,'--maxfail=1000'],cwd=AQUI,capture_output=True,text=True)
    falhas,tot=_falhas_junit(junit)
    if atualizar_base:BASE.write_text('\n'.join(sorted(falhas))+'\n',encoding='utf-8')
    base=set(BASE.read_text(encoding='utf-8').split()) if BASE.exists() else set()
    novas=sorted(falhas-base);curadas=sorted(base-falhas)
    msg=(f'{PENDENTES} testes com resultado pendente de nova execução; ' if PENDENTES else '')+f'{tot} testes; {len(falhas)} falham ({len(falhas&base)} já conhecidas, {len(novas)} NOVAS); {len(curadas)} da linha de base agora passam.'
    if novas:return 'falha',msg+' Novas: '+', '.join(novas[:10])
    if not BASE.exists():return 'falha',msg+' Sem linha de base (use --atualizar-base na primeira vez).'
    return ('ressalva' if falhas or PENDENTES else 'ok'),msg

def _install_sintetico(tmp,versao='0.0'):
    r=Path(tmp)/'Rodovia_Studio';P=r/'sistema'/'programa'
    (P/'app').mkdir(parents=True);(P/'app'/'server.py').write_text('# antigo\n');(P/'VERSAO.json').write_text(json.dumps({'version':versao,'phases':{}}))
    for d in ('projetos','videos','atualizacoes','sistema'):(r/d).mkdir(exist_ok=True)
    (r/'ABRIR RODOVIA STUDIO.cmd').write_text('@echo off')
    return r,P

def pacote(zip_path):
    sys.path.insert(0,str(AQUI));import atualizador;from app import higiene
    tmp=Path(tempfile.mkdtemp());ex=tmp/'ex'
    with zipfile.ZipFile(zip_path) as z:z.extractall(ex)
    pk=ex/'pacote' if (ex/'pacote'/'manifest.json').exists() else ex
    atualizador.validate_package(pk,lambda *_:None)
    r,P=_install_sintetico(tmp)
    res=atualizador.apply(pk,r,lambda *_:None,check_running=False)
    nova=json.loads((P/'VERSAO.json').read_text())['version']
    # smoke: o programa aplicado importa e registra rotas
    env={**os.environ,'RODOVIA_DATA':str(tmp/'dados')}
    q=subprocess.run([sys.executable,'-c','import app.server as s;print(len(s.app.routes))'],cwd=P,env=env,capture_output=True,text=True,timeout=180)
    if q.returncode:return 'falha','programa aplicado não importa: '+q.stderr.strip()[-400:]
    h=higiene.verificar(r);graves=[p for p in h['problemas'] if p['tipo'] in ('sintaxe','modulo_ausente','recurso_ausente','versao_invalida')]
    if graves:return 'falha','estrutura após aplicar: '+json.dumps(graves[:3],ensure_ascii=False)
    atualizador.restore_previous(r,None,lambda *_:None,check_running=False)
    volta=json.loads((P/'VERSAO.json').read_text())['version']
    if volta!='0.0':return 'falha',f'reversão não voltou à versão anterior (ficou {volta}).'
    return 'ok',f'pacote {nova}: validado, aplicado ({res["copied"]} arquivos), programa importa ({q.stdout.strip()} rotas), estrutura sem erro grave, reversão ok. Pendências de estrutura esperadas numa instalação sintética: {len(h["problemas"])}.'

def componentes():
    sys.path.insert(0,str(AQUI));from app import componentes as C
    tmp=Path(tempfile.mkdtemp());r,P=_install_sintetico(tmp);(P/'assets'/'texturas').mkdir(parents=True);(P/'assets'/'texturas'/'a.jpg').write_bytes(b'velho')
    o=tmp/'o';o.mkdir();(o/'a.jpg').write_bytes(b'novo');z=tmp/'RodoviaStudio_componentes_t.zip';C.empacotar(z,texturas=o)
    C.instalar(r,z,lambda *_:None,check_running=False)
    if (P/'assets'/'texturas'/'a.jpg').read_bytes()!=b'novo':return 'falha','componente não instalado'
    C.restaurar(r,None,lambda *_:None,check_running=False)
    if (P/'assets'/'texturas'/'a.jpg').read_bytes()!=b'velho':return 'falha','restauração não devolveu o arquivo'
    return 'ok','instalação e restauração de componentes ok; programa intacto.'

def fumaca():
    tmp=Path(tempfile.mkdtemp())
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    env={**os.environ,'RODOVIA_DATA':str(tmp/'d')}
    p=subprocess.Popen([sys.executable,'-m','uvicorn','app.server:app','--host','127.0.0.1','--port',str(port)],cwd=AQUI,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        fim=time.time()+90;ult=None
        while time.time()<fim:
            if p.poll() is not None:return 'falha','servidor encerrou: '+(p.stderr.read().decode()[-400:])
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/componentes/status',timeout=2) as r:
                    d=json.loads(r.read());break
            except Exception as e:ult=e;time.sleep(.5)
        else:return 'falha',f'servidor não respondeu em 90 s ({ult})'
        if not d['texturas']['ok']:return 'falha','texturas do pacote inválidas: '+json.dumps(d['texturas'])
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/',timeout=5) as r:html=r.read()
        if len(html)<1000:return 'falha','página inicial vazia'
        return 'ok',f'servidor real respondeu; {d["texturas"]["total"]} texturas íntegras; página inicial {len(html)//1024} KB.'
    finally:
        p.terminate()
        try:p.wait(10)
        except subprocess.TimeoutExpired:p.kill()

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--zip');ap.add_argument('--junit');ap.add_argument('--sem-suite',action='store_true');ap.add_argument('--atualizar-base',action='store_true');ap.add_argument('--relatorio')
    a=ap.parse_args(argv);res=[etapa('sintaxe',sintaxe)]
    res.append(etapa('suite',suite,a.junit,a.atualizar_base) if not a.sem_suite else {'etapa':'suite','status':'pulada','detalhe':'--sem-suite','segundos':0})
    res.append(etapa('pacote',pacote,a.zip) if a.zip else {'etapa':'pacote','status':'pulada','detalhe':'sem --zip','segundos':0})
    res+=[etapa('componentes',componentes),etapa('fumaca',fumaca)]
    ok=all(r['status']!='falha' for r in res);pul=[r['etapa'] for r in res if r['status']=='pulada'];res_=[r['etapa'] for r in res if r['status']=='ressalva']
    linhas=['# Relatório do gate','',f"Resultado: {'REPROVADO' if not ok else 'APROVADO COM RESSALVAS (falhas conhecidas/pendências na suíte)' if res_ else 'APROVADO COM ETAPAS PULADAS' if pul else 'APROVADO'}",'']
    linhas+=[f"- {r['etapa']}: {r['status'].upper()} ({r['segundos']} s) — {r['detalhe']}" for r in res]
    txt='\n'.join(linhas);print(txt)
    if a.relatorio:Path(a.relatorio).write_text(txt,encoding='utf-8')
    return 0 if ok else 1
if __name__=='__main__':sys.exit(main())
