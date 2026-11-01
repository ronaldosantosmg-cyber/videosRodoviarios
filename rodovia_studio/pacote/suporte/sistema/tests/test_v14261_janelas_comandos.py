import re
"""2.36: para cada comando que abre janela: abre, lista botões, clica em cada um, fecha por Esc/X/Cancelar e exige que não sobre janela aberta."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_janelas_de_comando(junction,tmp_path,monkeypatch):
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
    pid=c.post('/api/projects',json=S(name='Varredura').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];falhas=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':900})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.dismiss())
            page.route('**/tiles/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=90000)
            JS_ABERTAS="""()=>[...document.querySelectorAll('dialog[open],[role=dialog],.winDlg,.modal,.popup')].filter(e=>e.tagName==='DIALOG'?e.open:(e.offsetParent!==null&&getComputedStyle(e).visibility!=='hidden')).map(e=>e.id||e.className||e.tagName)"""
            JS_BOTOES="""()=>{const d=[...document.querySelectorAll('dialog[open]')].pop();if(!d)return[];return [...d.querySelectorAll('button,input[type=button],input[type=submit]')].map((b,i)=>[i,(b.textContent||b.value||b.title||'').trim().slice(0,40),b.disabled,b.offsetParent!==null])}"""
            JS_CLICA="""i=>{const d=[...document.querySelectorAll('dialog[open]')].pop();const b=d&&[...d.querySelectorAll('button,input[type=button],input[type=submit]')][i];if(b)b.click();return !!b}"""
            JS_CMD="""async n=>{try{await Promise.race([Promise.resolve(COMANDOS.get(n)([])),new Promise(r=>setTimeout(r,900))]);return null}catch(e){return String(e&&e.message||e)}}"""
            JS_EST="""()=>[JSON.stringify([cfg,M]).length,(document.getElementById('message')||{}).textContent||'',(document.querySelector('dialog[open] [data-error]')||{}).textContent||'',(document.getElementById('saveState')||{}).textContent||'',document.querySelectorAll('dialog[open]').length+':'+[...document.querySelectorAll('dialog[open]')].map(d=>d.innerText.length).join(',')]"""
            def limpar():
                for _ in range(4):
                    page.keyboard.press('Escape')
                page.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>{try{d.close()}catch(e){}})")
            nomes=page.evaluate('[...COMANDOS.keys()]')
            SKIP=('excluir','apagar','remover','deletar','sair','reiniciar','instalar','limpar','atualizar')
            relatorio=[];problemas=[]
            for n in nomes:
                if any(x in n.lower() for x in SKIP):continue
                limpar();antes=len(errors)
                page.evaluate(JS_CMD,n);page.wait_for_timeout(250)
                ab=page.evaluate(JS_ABERTAS)
                if not ab:continue
                bt=page.evaluate(JS_BOTOES)
                reg={'cmd':n,'janelas':ab,'botoes':[b[1] for b in bt],'resultado':{}}
                # fechar por Esc
                page.keyboard.press('Escape');page.wait_for_timeout(150)
                if page.evaluate("()=>document.querySelectorAll('dialog[open]').length"):reg['esc']='NAO FECHA'
                for bb in bt:
                    i,rot,desab,vis=bb
                    if desab or not vis or any(x in rot.lower() for x in ('excluir','apagar','remover','limpar')):continue
                    limpar();e0=len(errors)
                    page.evaluate(JS_CMD,n);page.wait_for_timeout(200)
                    est0=page.evaluate(JS_EST)
                    try:page.evaluate(JS_CLICA,i)
                    except Exception as ex:problemas.append((n,rot,'clique: '+str(ex)[:80]));continue
                    page.wait_for_timeout(700)
                    restantes=page.evaluate("()=>[...document.querySelectorAll('dialog[open]')].map(d=>d.id||d.className)")
                    reg.setdefault('restam',{})[rot or f'#{i}']=restantes
                    est1=page.evaluate(JS_EST)
                    aberta=bool(restantes)
                    if aberta and re.search(r'^(salvar|aplicar|confirmar|gerar|criar|ok)',rot.strip(),re.I) and est1[2].strip()=='' and est0[:2]==est1[:2] and est0[3]==est1[3] and est0[4]==est1[4]:problemas.append((n,rot,'SEM EFEITO: nada gravado, sem mensagem e sem erro visivel'))
                    reg['resultado'][rot or f'#{i}']='fechou' if not page.evaluate("()=>document.querySelectorAll('dialog[open]').length") else 'continua aberta'
                    if len(errors)>e0:problemas.append((n,rot,'pageerror: '+errors[-1][:160]))
                # toda janela deve ter alguma saida: Esc, ou botao Cancelar/Fechar/X
                limpar();page.evaluate(JS_CMD,n);page.wait_for_timeout(200)
                page.keyboard.press('Escape');page.wait_for_timeout(150)
                if page.evaluate("()=>document.querySelectorAll('dialog[open]').length") and not any(re.search(r'cancel|fechar|✕|×|voltar|ok',bb[1],re.I) for bb in bt):problemas.append((n,'-','janela sem saida (Esc nao fecha e nao ha Cancelar/Fechar)'))
                limpar()
                if page.evaluate(JS_ABERTAS):problemas.append((n,'-','sobrou janela aberta apos fechar'))
                relatorio.append(reg)
            import json
            json.dump({'janelas':relatorio,'problemas':problemas},open('/tmp/janelas.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
            print('comandos com janela',len(relatorio),'problemas',len(problemas))
            b.close()
    finally:
        server.should_exit=True
    assert not problemas,repr(problemas[:30])
