"""2.35: varredura real — abre o app, dispara TODOS os comandos registrados (COMANDOS) e abas, e exige zero erro de página."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_varredura_comandos(junction,tmp_path,monkeypatch):
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
            nomes=page.evaluate('[...COMANDOS.keys()]')
            SKIP=('excluir','apagar','remover projeto','deletar','sair','fechar','reiniciar','atualizar sistema','instalar')
            for n in nomes:
                if any(s in n.lower() for s in SKIP):continue
                antes=len(errors)
                r=page.evaluate('async n=>{try{await Promise.race([Promise.resolve(COMANDOS.get(n)([])),new Promise(r=>setTimeout(r,1500))]);return null}catch(e){return String(e&&e.message||e)}}',n)
                page.keyboard.press('Escape')
                if r and not r.startswith('Carregue'):falhas.append((n,r))
                if len(errors)>antes:falhas.append((n,'pageerror: '+errors[-1]))
            # fase 2: executa a ação de TODO item da faixa de opções (RIBBON) e exige zero erro
            itens=page.evaluate('RIBBON.flatMap(([t,gs])=>(gs||[]).flatMap(([g,its])=>its.filter(i=>typeof i[2]==="function").map(i=>[t,g,String(i[0])])))')
            for t,g,l in itens:
                if any(x in (t+g+l).lower() for x in ('exclu','apag','remov','sair','reinic','instal','fechar','limpar')):continue
                antes=len(errors)
                r=page.evaluate('''async([t,g,l])=>{const it=RIBBON.find(x=>x[0]===t)[1].find(x=>x[0]===g)[1].find(i=>String(i[0])===l);
                  try{await Promise.race([Promise.resolve(it[2]()),new Promise(r=>setTimeout(r,1200))]);return null}catch(e){return String(e&&e.message||e)}}''',[t,g,l])
                page.keyboard.press('Escape')
                if r and not r.startswith('Carregue'):falhas.append((f'{t}/{g}/{l}',r[:150]))
                if len(errors)>antes:falhas.append((f'{t}/{g}/{l}','pageerror: '+errors[-1][:200]))
            print('itens da faixa',len(itens))
            b.close()
    finally:
        server.should_exit=True
    assert not falhas,f'{len(falhas)} de {len(nomes)}: '+repr(falhas[:25])
