"""1.34 (tela): painéis por menu (abrir/fechar, fixar/desafixar), tema claro/escuro/Windows, progresso visível em
tarefas e downloads, comandos contínuos (Enter/Esc) e arrastar com Shift/Esc."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_ui_134(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    H=[{'id':'h1','name':'Poste A','point':{'x':500150,'y':7800020}},{'id':'h2','name':'Poste B','point':{'x':500260,'y':7800020}}]
    pid=c.post('/api/projects',json=S(name='Trecho UI 134',highlights=H).model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);ctx=b.new_context(viewport={'width':1700,'height':950},accept_downloads=True,color_scheme='dark');page=ctx.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA&&cfg.name==="Trecho UI 134"',timeout=20000);ev=page.evaluate
            if not ev("document.body.classList.contains('wide')"):ev("$('layoutWide').click()")
            page.wait_for_timeout(300)
            cw=lambda:ev("canvas.getBoundingClientRect().width")
            # ---- painéis por menu: começam fechados; clicar abre por cima (desenho do mesmo tamanho); clicar de novo fecha.
            assert ev("document.body.classList.contains('paineis')") and ev("document.querySelectorAll('#atividades [data-pn]').length")>=7   # 1.35: +Obras, Manutenção só em Arquivo
            assert not ev("document.querySelector('main>div.pnArea').checkVisibility()");w0=cw()
            page.click('#atividades [data-pn="sec_1"]');page.wait_for_timeout(150)
            assert ev("$('crs').checkVisibility()") and ev("getComputedStyle(document.querySelector('main>div.pnArea')).position")=='fixed' and abs(cw()-w0)<2
            page.click('#atividades [data-pn="sec_1"]');page.wait_for_timeout(150);assert not ev("$('crs').checkVisibility()")
            # Fixar: o painel encaixa e o desenho diminui; × fecha (os campos continuam com o que tinham).
            page.click('#atividades [data-pn="sec_1"]');page.fill('#origin','Belo Horizonte');page.click('#pnFixar');page.wait_for_timeout(200)
            assert ev("getComputedStyle(document.querySelector('main>div.pnArea')).position")!='fixed' and cw()<w0-250
            page.click('#pnFechar');page.wait_for_timeout(200);assert abs(cw()-w0)<2 and ev("$('origin').value")=='Belo Horizonte'
            # Menu (faixa de opções) abre o painel da seção; desafixado, navegar no desenho fecha.
            ev("pnFixar(false);openSection('5. Exportar vídeo')");assert ev("pnEstado.aberto")==ev("$('style_profile').closest('section').id") and ev("$('style_profile').checkVisibility()")
            assert ev("$('texture_style').value")=='artistico'
            cx,cy=ev("(()=>{const r=canvas.getBoundingClientRect();return [r.x+r.width*.7,r.y+r.height*.15]})()");page.mouse.click(cx,cy);page.wait_for_timeout(100);assert ev("pnEstado.aberto") is None
            # Vista e prévia: as linhas de cima do editor ficam num painel (mais altura para o desenho).
            assert ev("$('preview').closest('section').id")=='secVista' and ev("$('baseMode').closest('section').id")=='secVista'
            # ---- tema: segue o Windows (aqui, escuro); claro e escuro escolhidos no menu.
            assert ev("document.documentElement.dataset.tema")=='escuro'
            ev("aplicarTema('claro')");assert ev("document.documentElement.dataset.tema")=='claro' and ev("getComputedStyle(document.body).backgroundColor")=='rgb(243, 243, 243)'
            page.reload();page.wait_for_function('typeof geo!=="undefined"&&geo&&ready()',timeout=20000);assert ev("document.documentElement.dataset.tema")=='claro'
            ev("aplicarTema('sistema')");assert ev("document.documentElement.dataset.tema")=='escuro' and ev("getComputedStyle(document.body).backgroundColor")=='rgb(28, 28, 28)'
            if not ev("document.body.classList.contains('wide')"):ev("$('layoutWide').click()")
            # ---- progresso: quadro visível durante a tarefa e ao baixar arquivos.
            ev("start('analyze')");page.wait_for_selector('#progCard:not([hidden])',timeout=5000);assert ev("$('pcTitulo').textContent")=='Analisando arquivos'
            page.wait_for_function("$('pcInfo').textContent.includes('Concluído')",timeout=60000)
            with page.expect_download() as dl:ev("baixarRegistros()")
            assert dl.value.suggested_filename.endswith('.zip');page.wait_for_function("$('pcInfo').textContent.includes('salvo')",timeout=10000)
            page.wait_for_function('ready()&&!task',timeout=30000)
            # ---- comandos contínuos: MOVER num objeto; depois clicar noutro repete o MOVER; Esc encerra.
            P=lambda x,y:ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{x},y:{y}}});const r=canvas.getBoundingClientRect();return [r.left+(view.ox+ix*view.s)*r.width/canvas.width,r.top+(view.oy+iy*view.s)*r.height/canvas.height]}})()")
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()");cl=page.locator('#cmdLine')
            cl.fill('M');cl.press('Enter');cl.fill('0,0');cl.press('Enter');cl.fill('@2,0');cl.press('Enter');page.wait_for_timeout(100)
            assert abs(ev("M.highlights[0].point.x")-500152)<1e-6 and ev("cmdRep")=='MOVER' and 'próximo objeto' in ev("$('cmdPrompt').textContent")
            page.mouse.click(*P(500260,7800020));page.wait_for_timeout(150)
            assert ev("!!cadCmd") and 'MOVER' in ev("$('cmdPrompt').textContent") and ev("sel&&sel.i")==1
            cl.fill('0,0');cl.press('Enter');cl.fill('@0,3');cl.press('Enter');page.wait_for_timeout(100);assert abs(ev("M.highlights[1].point.y")-7800023)<1e-6 and ev("cmdRep")=='MOVER'
            page.focus('#canvas');page.keyboard.press('Escape');assert ev("cmdRep") is None and not ev("document.getElementById('confirmDlg').open") and ev("$('cmdPrompt').textContent")=='Comando:'
            # Enter vazio também encerra a repetição.
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()");cl.fill('CO');cl.press('Enter');cl.fill('0,0');cl.press('Enter');cl.fill('@0,-5');cl.press('Enter')
            assert ev("M.highlights.length")==3 and ev("cmdRep")=='COPIAR';cl.press('Enter');assert ev("cmdRep") is None
            # Ferramenta de desenho: Enter conclui e a ferramenta continua; Enter sem pontos encerra.
            ev("setTool('pavarea')");n0=ev("M.pavement_areas.length")
            for x,y in [(500100,7799995),(500120,7799995),(500120,7800005)]:page.mouse.click(*P(x,y))
            page.focus('#canvas');page.keyboard.press('Enter');assert ev("M.pavement_areas.length")==n0+1 and ev("tool")=='pavarea'
            page.keyboard.press('Enter');assert ev("tool")=='pan'
            # Arrastar com Shift: só na horizontal; Esc durante o arraste devolve o objeto ao lugar.
            ev("(()=>{sel=null;selSet=[];showProps()})()");x0,y0=ev("[M.highlights[0].point.x,M.highlights[0].point.y]");sx,sy=P(x0,y0)
            page.mouse.move(sx,sy);page.mouse.down();page.keyboard.down('Shift');page.mouse.move(sx+40,sy+25,steps=5);page.keyboard.up('Shift');page.mouse.up()
            x1,y1=ev("[M.highlights[0].point.x,M.highlights[0].point.y]");assert x1>x0+1 and abs(y1-y0)<1e-6
            sx,sy=P(x1,y1);page.mouse.move(sx,sy);page.mouse.down();page.mouse.move(sx+30,sy+30,steps=5);page.keyboard.press('Escape');page.mouse.up()
            x2,y2=ev("[M.highlights[0].point.x,M.highlights[0].point.y]");assert abs(x2-x1)<1e-6 and abs(y2-y1)<1e-6 and not ev("document.getElementById('confirmDlg').open")
            # Nada de TH57 na tela.
            assert 'TH57' not in ev("document.body.innerText")
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
