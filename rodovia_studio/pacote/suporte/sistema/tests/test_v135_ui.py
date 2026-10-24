"""1.35 (tela): nome não some ao trocar a categoria, obras do PER (importar, marcar no desenho, editar), seleção
precisa (prioridade e alternância), menu do botão direito com submenu ao lado e ícones, tela simplificada."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401
from test_v135 import XML

def test_ui_135(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    from app.obras import template_xlsx
    (tmp_path/'modelo.xlsx').write_bytes(template_xlsx());(tmp_path/'per.xml').write_bytes(XML)
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    H=[{'id':'h1','name':'Poste A','point':{'x':500150,'y':7800020}},{'id':'h2','name':'Poste B','point':{'x':500150.5,'y':7800020}}]
    A=[{'id':'a1','name':'Faixa 1','kind':'pavement','material':'auto','points':[{'x':500100,'y':7800010},{'x':500200,'y':7800010},{'x':500200,'y':7800030},{'x':500100,'y':7800030}],'source':'drawn','enabled':True}]
    pid=c.post('/api/projects',json=S(name='Trecho UI 135',highlights=H,pavement_areas=A).model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1700,'height':950},device_scale_factor=1.5)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA&&cfg.name==="Trecho UI 135"',timeout=20000);ev=page.evaluate
            if not ev("document.body.classList.contains('wide')"):ev("$('layoutWide').click()")
            page.wait_for_timeout(300)
            P=lambda x,y:ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{x},y:{y}}});const r=canvas.getBoundingClientRect();return [r.left+(view.ox+ix*view.s)*r.width/canvas.width,r.top+(view.oy+iy*view.s)*r.height/canvas.height]}})()")
            # ---- propriedades: digitar o nome e trocar a categoria não perde o nome; um Ctrl+Z desfaz os dois.
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()")
            page.fill('#propPanel [data-pp="name"]','Casa do João');page.select_option('#propPanel [data-pp="category"]','torre');page.wait_for_timeout(150)
            assert ev("[M.highlights[0].name,M.highlights[0].category]")==['Casa do João','torre']
            ev("undo()");assert ev("[M.highlights[0].name,M.highlights[0].category]")==['Poste A','outro']
            assert ev("document.querySelectorAll('#propPanel [data-pp=category] option').length")>=25
            # ---- seleção: ponto vence a área por baixo; clicar de novo no mesmo lugar alterna entre os pontos sobrepostos.
            ev("(()=>{sel=null;selSet=[];showProps();ev_=0})()");x,y=P(500150,7800020)
            page.mouse.click(x,y);page.wait_for_timeout(100);k1=ev("sel&&sel.key+':'+sel.i");assert k1.startswith('highlights:')
            page.mouse.click(x,y);page.wait_for_timeout(100);k2=ev("sel&&sel.key+':'+sel.i");assert k2!=k1 and 'objetos neste ponto' in ev("$('message').textContent")
            page.mouse.click(*P(500110,7800025));page.wait_for_timeout(100);assert ev("sel&&sel.key")=='pavement_areas'
            assert ev("DPR()")==1.5
            ev("(()=>{sel=null;selSet=[];showProps()})()");page.mouse.move(x,y);page.wait_for_timeout(150);assert ev("!!sobMouse")
            # ---- menu do botão direito: submenu ao lado (sem trocar o menu) e ícones de linha.
            page.mouse.click(*P(500300,7800060),button='right');page.wait_for_selector('#ctxMenu:not([hidden])')
            assert ev("document.querySelectorAll('#ctxMenu .it .ic svg').length")>=8
            page.hover('#ctxMenu .it:has-text("Inserir")');page.wait_for_selector('#ctxMenu .ctxSub');assert ev("!!document.querySelector('#ctxMenu .it[data-i]')") and 'Pórtico' in page.inner_text('#ctxMenu .ctxSub')
            page.click('#ctxMenu .ctxSub .it:has-text("Destaque")');assert ev('tool')=='highlight' and ev("$('ctxMenu').hidden");ev("setTool('pan')")
            # ---- tela simplificada: ferramentas numa linha com grupos suspensos; cabeçalho sem repetições.
            assert ev("document.querySelectorAll('#toolbar .tgBtn').length")>=4 and not ev("$('layoutCompact').checkVisibility()") and not ev("$('new').checkVisibility()")
            g=page.locator('#toolbar .tgroup.dobravel').first;g.locator('.tgBtn').click();assert ev("!!document.querySelector('#toolbar .tgroup.aberto')")
            g.locator('.tbtns button').first.click();page.wait_for_timeout(100);assert ev("!document.querySelector('#toolbar .tgroup.aberto')") and ev("!!document.querySelector('#toolbar .tgroup.temAtiva')");ev("setTool('pan')")
            assert not ev("[...document.querySelectorAll('#atividades [data-pn]')].some(b=>/Manut/.test(b.textContent))")
            # ---- obras do PER: importar o modelo Excel (conferência) e o cronograma XML (só datas).
            ev("abrirImportarObras()");page.set_input_files('#obArq',str(tmp_path/'modelo.xlsx'));page.wait_for_function("!$('obImpOk').disabled")
            assert ev("document.querySelectorAll('#obImpRows tr').length")==4;page.click('#obImpOk');assert ev("M.works.length")==4 and ev("M.works[0].kind")=='duplicacao'
            ev("abrirImportarObras()");page.set_input_files('#obArq',str(tmp_path/'per.xml'));page.wait_for_function("!$('obImpOk').disabled")
            page.fill('[data-obkm="2"]','0+010');page.fill('[data-obkf="2"]','0+040');page.click('#obImpOk')
            assert ev("M.works.length")==7 and ev("M.works.at(-1).description")=='Mobilização do canteiro' and ev("M.works.at(-1).km_end_m")==40
            ev("undo()");assert ev("M.works.length")==4
            # Marcar no desenho: início e fim; a janela pede nome/tipo; a ferramenta continua para a próxima.
            ev("pnAbrir(pnItens.find(i=>i.el.id==='secObras').id)");page.click('#obTela');assert ev('tool')=='obra'
            page.mouse.click(*P(500050,7800000));page.mouse.click(*P(500250,7800000));page.wait_for_selector('#obNovaDlg[open]')
            assert ev("$('obKmA').value")=='0+050' and ev("$('obKmB').value")=='0+250'
            page.fill('#obNome','Via marginal Sul');page.select_option('#obTipo','via_marginal');page.select_option('#obLado','direito');page.keyboard.press('Enter')
            w=ev("M.works.at(-1)");assert (w['description'],w['kind'],w['side'],w['km_start_m'],w['km_end_m'])==('Via marginal Sul','via_marginal','direito',50,250) and ev('tool')=='obra'
            page.focus('#canvas');page.keyboard.press('Escape');page.wait_for_timeout(100)
            if ev("document.getElementById('confirmDlg').open"):page.keyboard.press('Enter')
            # Editar pela lista (duplo clique) e excluir.
            assert ev('pnEstado.aberto') is None   # “Marcar no desenho” tira o painel solto da frente
            ev("pnAbrir(pnItens.find(i=>i.el.id==='secObras').id)")
            page.dblclick('#obRows tr:last-child td:first-child');page.wait_for_selector('#obNovaDlg[open]');page.fill('#obIni','2027-02-01');page.fill('#obFim','2027-09-30');page.click('#obOk')
            assert ev("[M.works.at(-1).start_date,M.works.at(-1).end_date]")==['2027-02-01','2027-09-30']
            n=ev("M.works.length");page.click('#obRows tr:last-child [data-oba="del"]');page.wait_for_selector('#confirmDlg[open]');page.click('#confirmYes');assert ev("M.works.length")==n-1
            ev("scheduleSave()");page.wait_for_timeout(1800);cfg=c.get(f'/api/projects/{pid}').json()['config'];assert len(cfg['works'])==n-1 and cfg['per_display']=='trecho'
            page.select_option('#schedule_mode','linha_do_tempo');ev("scheduleSave()");page.wait_for_timeout(1800);assert c.get(f'/api/projects/{pid}').json()['config']['schedule_mode']=='linha_do_tempo'
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
