"""1.33 (tela): barra lateral em abas (recolhe, reabre ao editar, janela flutuante), área máxima e rodapé da tarefa."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_area_de_trabalho_ui(junction,tmp_path,monkeypatch):
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
    pid=c.post('/api/projects',json=S(name='Trecho UI 133',highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}]).model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1700,'height':950})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=404,body=b''))
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA&&cfg.name==="Trecho UI 133"',timeout=20000);ev=page.evaluate
            if not ev("document.body.classList.contains('wide')"):ev("$('layoutWide').click()")
            page.wait_for_timeout(300)
            # Barra lateral em abas: os mesmos elementos (ids) dentro das abas; uma aba visível por vez.
            assert ev("document.querySelectorAll('.editorSide.dock .dockTab').length")==5
            for id_,aba in [('propPanel','prop'),('markList','marc'),('alignMode','ajuste'),('pathName','fluxos'),('warnings','avisos')]:
                assert ev(f"$('{id_}').closest('.dockItem').dataset.dock")==aba
            ev("abrirAba('ajuste')");assert ev("$('alignMode').offsetParent!==null") and ev("$('markList').offsetParent===null")
            # Recolher: a coluna vira uma faixa de ícones e o desenho ganha a largura.
            w0=ev("canvas.getBoundingClientRect().width");ev("recolherDock(true)");page.wait_for_timeout(300)
            assert ev("document.querySelector('.editorSide').getBoundingClientRect().width")<=40 and ev("canvas.getBoundingClientRect().width")>w0+200
            # Editar reapresenta o painel: selecionar abre Propriedades; desmarcar recolhe de novo.
            ev("(()=>{sel={key:'highlights',i:0};selSet=[];showProps()})()");page.wait_for_timeout(150)
            assert not ev("dockState.recolhida") and ev("dockState.aba")=='prop' and ev("$('propPanel').offsetParent!==null")
            ev("(()=>{sel=null;selSet=[];showProps()})()");page.wait_for_timeout(150);assert ev("dockState.recolhida") and ev("dockState.aba")=='ajuste'
            # Janela flutuante: a aba sai para uma janela, os campos continuam funcionando, e volta ao encaixar.
            ev("recolherDock(false);destacar('marc')");assert ev("!!document.querySelector('.floatWin[data-dock=marc] #markList')")
            assert ev("JSON.parse(localStorage.getItem('rodovia_area_soltas')).marc")
            page.click('.floatWin[data-dock=marc] [data-fw=dock]');assert ev("!document.querySelector('.floatWin') && $('markList').closest('.dockItem').dataset.dock==='marc'")
            # Área máxima (F10): some a coluna da esquerda; abrir uma seção pela faixa traz a coluna até clicar no desenho.
            page.keyboard.press('F10');page.wait_for_timeout(200)
            assert ev("document.body.classList.contains('areaMax')") and ev("!document.querySelector('main>div.pnArea,main>div').checkVisibility()")
            ev("openSection('5. Exportar vídeo')");page.wait_for_timeout(150);assert ev("document.querySelector('main>div.pnArea,main>div').checkVisibility()")
            page.mouse.click(*ev("(()=>{const r=canvas.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()"));page.wait_for_timeout(150)
            assert ev("!document.querySelector('main>div.pnArea,main>div').checkVisibility()");ev("alternarAreaMax(false)");assert not ev("document.body.classList.contains('areaMax')")
            # Rodapé: mensagem, progresso, tempo e Cancelar; as seções antigas não aparecem.
            assert ev("$('message').closest('#taskArea')&&$('progress').closest('#taskArea')&&$('cancel').closest('#taskArea')")
            assert ev("$('logSection').offsetParent===null && $('render').offsetParent===null")
            assert ev("$('progress').offsetParent===null")   # sem tarefa, a barra não aparece
            ev("$('progress').value=.5;marcarTarefa(true)");page.wait_for_timeout(100)
            assert ev("$('progress').offsetParent!==null") and '50%' in ev("$('taskTime').textContent");ev("marcarTarefa(false)")
            ev("msg('Concluído em 125 s')");assert ev("$('message').textContent")=='Concluído em 2 min 05 s'
            ev("abrirMensagem()");page.wait_for_selector('#msgDlg[open]');assert '2 min 05 s' in ev("$('msgFull').textContent");ev("$('msgDlg').close()")
            # Faixa de opções: Gerar vídeo em Início; registros na aba Vídeo.
            page.click('#menuBar .mb:has-text("Início")');assert page.locator('#menuBar .rb:has-text("Gerar vídeo")').count()==1
            page.click('#menuBar .mb:has-text("Vídeo")')
            for t in ['Ver registros','Exportar prompt para IA','Baixar registros (.zip)','Cancelar']:assert page.locator(f'#menuBar .rb:has-text("{t}")').count()>=1,t
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
