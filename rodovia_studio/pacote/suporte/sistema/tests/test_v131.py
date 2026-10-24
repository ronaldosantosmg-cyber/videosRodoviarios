"""1.31: estrutura do código (reorganização sem mudar o comportamento).

- Interface em app/js/NN_assunto.js, servida como um script só, na ordem dos números.
- Sem declarações globais repetidas entre arquivos; extensões só de funções declaradas; ESLint sem erros (quando
  disponível neste ambiente).
- Servidor: rotas em app/rotas/<assunto>.py; nenhuma rota da 1.30 perdida; nenhum nome indefinido.
- Na tela: registros de ferramentas/comandos/faixa coerentes e a página abre sem erros.
"""
import json,os,re,shutil,socket,subprocess,threading,time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1];JS=ROOT/'app'/'js'

def js_files():return sorted(JS.glob('[0-9][0-9]_*.js'))

def test_js_modules_and_concatenation():
    from app.rotas.paginas import interface_js
    F=js_files();nums=[f.name[:2] for f in F]
    assert len(F)>=30 and len(set(nums))==len(nums) and F[0].name=='00_nucleo.js' and F[-1].name=='99_registros.js'
    code=interface_js()
    for f in F:assert f'// ==== arquivo: {f.name} ====' in code
    assert code.index('00_nucleo.js')<code.index('99_registros.js')
    old=ROOT/'app'/'app.js'   # só um aviso de 2 linhas (substitui o app.js antigo nas instalações atualizadas)
    assert not old.exists() or (len(old.read_text(encoding='utf-8').splitlines())<=3 and 'não é mais usado' in old.read_text(encoding='utf-8'))
    c=TestClient(__import__('app.server',fromlist=['app']).app);r=c.get('/app.js')
    assert r.status_code==200 and r.text==code and 'javascript' in r.headers['content-type']
    if shutil.which('node'):
        tmp=ROOT/'tests'/'_tmp_interface.js';tmp.write_text(code,encoding='utf-8')
        try:p=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True)
        finally:tmp.unlink()
        assert p.returncode==0,p.stderr

DECL=re.compile(r'^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)|^(?:const|let|var)\s+([A-Za-z_$][\w$]*)',re.M)
def test_no_duplicate_globals_and_valid_extensions():
    seen={};dups=[];funcs=set()
    for f in js_files():
        for m in DECL.finditer(f.read_text(encoding='utf-8')):
            n=m.group(1) or m.group(2)
            if m.group(1):funcs.add(n)
            if n in seen:dups.append((n,seen[n],f.name))
            seen.setdefault(n,f.name)
    assert not dups,dups
    targets=set()
    nocom=lambda t:'\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('//'))
    for f in js_files():targets|=set(re.findall(r"estender\('([\w$]+)'",nocom(f.read_text(encoding='utf-8'))))
    assert targets and targets<=funcs,targets-funcs
    # Embrulhos antigos sem registro não voltam: {const _x=f;f=function...}
    for f in js_files():
        assert not re.search(r"\{const (_[\w$]+)=([\w$]+);\2=(async\s+)?(function|\()",nocom(f.read_text(encoding='utf-8'))),f.name

ESLINT='/opt/node-tools/node_modules/.bin/eslint'
GLOBALS=['window','document','localStorage','sessionStorage','console','fetch','setTimeout','clearTimeout','setInterval','clearInterval','requestAnimationFrame',
 'cancelAnimationFrame','Image','FormData','Blob','URL','URLSearchParams','navigator','location','crypto','ResizeObserver','MutationObserver','Event','KeyboardEvent',
 'MouseEvent','HTMLElement','Path2D','DOMParser','performance','getComputedStyle','alert','confirm','prompt','globalThis','history','OffscreenCanvas','createImageBitmap',
 'ImageData','TextEncoder','TextDecoder','AbortController','structuredClone','matchMedia','innerWidth','innerHeight','devicePixelRatio','open','screen','Node',
 'DataTransfer','File','FileReader','CSS','PointerEvent','WheelEvent','DOMMatrix','BroadcastChannel','queueMicrotask']
@pytest.mark.skipif(not os.path.exists(ESLINT),reason='ESLint não disponível neste ambiente')
def test_eslint_interface(tmp_path):
    from app.rotas.paginas import interface_js
    (tmp_path/'interface.js').write_text(interface_js(),encoding='utf-8')
    g=','.join(f'{n}:"readonly"' for n in GLOBALS)
    (tmp_path/'eslint.config.mjs').write_text('export default [{files:["**/*.js"],languageOptions:{ecmaVersion:2024,sourceType:"script",globals:{'+g+
        '}},rules:{"no-undef":"error","no-redeclare":"error","no-dupe-keys":"error","no-dupe-else-if":"error","no-self-assign":"error","no-unreachable":"error"}}];',encoding='utf-8')
    p=subprocess.run([ESLINT,'interface.js'],cwd=tmp_path,capture_output=True,text=True)
    assert p.returncode==0,p.stdout[-3000:]+p.stderr[-2000:]

def test_server_split_and_routes():
    import sys
    sys.path.insert(0,str(ROOT/'tests'))
    from nomes_indefinidos import check
    files=sorted((ROOT/'app').glob('*.py'))+sorted((ROOT/'app'/'rotas').glob('*.py'))
    bad=[x for f in files for x in check(f)];assert not bad,bad[:20]
    assert len((ROOT/'app'/'server.py').read_text(encoding='utf-8').splitlines())<120
    from app.server import app
    def flat(rs):
        for r in rs:
            if hasattr(r,'original_router'):yield from flat(r.original_router.routes)
            else:yield r
    now={(tuple(sorted(r.methods or [])),r.path) for r in flat(app.routes) if hasattr(r,'methods')}
    need={(tuple(m),p) for m,p,*_ in json.loads((ROOT/'tests'/'rotas_api_1_30.json').read_text(encoding='utf-8'))}
    assert need<=now,sorted(need-now)
    for m in ('paginas','projetos','modelos','editor','tarefas','arquivos','web','suporte','camadas'):
        assert (ROOT/'app'/'rotas'/f'{m}.py').exists()

def test_css_external_with_variables():
    html=(ROOT/'app'/'index.html').read_text(encoding='utf-8');css=(ROOT/'app'/'estilo.css').read_text(encoding='utf-8')
    assert '<style' not in html and 'href="/estilo.css"' in html
    root=re.search(r':root\{([^}]*)\}',css);assert root and root.group(1).count('--')>=10
    c=TestClient(__import__('app.server',fromlist=['app']).app);r=c.get('/estilo.css');assert r.status_code==200 and 'text/css' in r.headers['content-type'] and r.text==css

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_registries_in_browser():
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1400,'height':900})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base);page.wait_for_function('typeof SCHEMA!=="undefined"',timeout=20000);ev=page.evaluate
            r=ev("""(()=>{const out={};
              out.ferr=Object.keys(FERRAMENTAS).sort();
              out.semFerr=Object.keys(FERRAMENTAS).filter(id=>!TOOLS.some(t=>t[0]===id));
              out.semIcone=Object.keys(FERRAMENTAS).filter(id=>!ICON_PATHS[id]);
              out.cmds=[...COMANDOS.keys()].filter(k=>typeof COMANDOS.get(k)!=='function');
              out.faixa=[];for(const [aba,gr] of RIBBON){if(!gr)continue;for(const [g,itens] of gr)for(const it of itens)if(typeof it[2]!=='function')out.faixa.push(aba+'/'+g+'/'+it[0])}
              out.menu=[];for(const [m,itens] of MENUBAR)for(const it of itens)if(it&&typeof it[it.length-1]!=='function')out.menu.push(m+'/'+it[0]);
              const ids=TOOLS.filter(t=>t!=='|').map(t=>t[0]);out.toolsDup=ids.filter((x,i)=>ids.indexOf(x)!==i);
              const names=CMD_HELP.map(c=>c[0]);out.helpDup=names.filter((x,i)=>names.indexOf(x)!==i);
              out.ext=Object.fromEntries(Object.entries(EXTENSOES).map(([k,v])=>[k,v.length]));
              out.botoes=document.querySelectorAll('#toolbar button[data-tool]').length;return out})()""")
            assert {'route','routesec','brush'}<=set(r['ferr']) and not r['semFerr'] and not r['semIcone']
            assert not r['cmds'] and not r['faixa'] and not r['menu'] and not r['toolsDup'] and not r['helpDup']
            assert r['ext']['draw']>=10 and r['ext']['click']>=6 and r['ext']['runCommand']>=5 and r['botoes']>=40
            # Comandos registrados funcionam pela linha de comando (sem projeto: avisam e não quebram).
            ev("runCommand('RT')");assert ev('tool')=='route';ev("setTool('pan')")
            ev("runCommand('CAMADAS')");assert 'Abra um projeto' in ev("document.getElementById('message').textContent")
            # Ajuda › Sobre mostra a estrutura (extensões por função, ferramentas e comandos registrados).
            ev("openAbout();0");page.wait_for_function("document.getElementById('aboutDlg').open&&document.getElementById('aboutBody').textContent.includes('Estrutura')");t=ev("document.getElementById('aboutDlg').textContent")
            assert 'Estrutura da interface' in t and 'draw' in t
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
