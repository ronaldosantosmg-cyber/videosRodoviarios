"""2.36: botões de janela (Salvar e fechar / Aplicar / Salvar e atualizar) executam a ação: gravam e fecham, ou mostram o erro VISÍVEL. Caso real: Fim arredondado para cima travava o salvamento sem aviso."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_salvar_e_fechar_executa_a_acao(junction,tmp_path,monkeypatch):
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
            page.evaluate("""()=>{const p=editor.segments[0].points[0];const x=Array.isArray(p)?p[0]:p.x,y=Array.isArray(p)?p[1]:p.y;
              M.route_alignments=[{id:'rt1',name:'EIXO_TESTE',points:[{x,y},{x:x+123.4567,y}],enabled:true,type:'dupla',lanes:1,lane_width_m:3.6,median_m:0,cross_sections:[],sections:[]}];changed()}""");page.evaluate("async()=>{await save()}")
            page.wait_for_timeout(500)
            VIS="""()=>{const p=document.querySelector('dialog[open] [data-error]');if(!p||!p.textContent.trim())return null;const r=p.getBoundingClientRect(),s=p.closest('section'),sr=s?s.getBoundingClientRect():r;return {txt:p.textContent.trim().slice(0,160),visivel:r.top>=sr.top-1&&r.bottom<=sr.bottom+1&&r.height>0}}"""
            falhas=[]
            def abrir():
                for _ in range(3):page.keyboard.press('Escape')
                page.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>{try{d.close();d.remove()}catch(e){}})")
                page.evaluate("COMANDOS.get('SECOESTIPO')([])");page.wait_for_timeout(700)
                if page.evaluate("!!document.querySelector('#rsChooseFlowAxis[open]')"):
                    page.evaluate("()=>{const d=document.querySelector('#rsChooseFlowAxis');const s=d.querySelector('select');if(s){const o=[...s.options].find(o=>/route:/.test(o.value))||s.options[0];s.value=o.value;s.dispatchEvent(new Event('change',{bubbles:true}))}[...d.querySelectorAll('button')].find(b=>/Configurar/.test(b.textContent)).click()}");page.wait_for_timeout(900)
            # 1) Salvar e fechar com os valores padrão (Fim = comprimento do eixo) deve gravar e fechar
            abrir()
            assert page.evaluate("!!document.querySelector('#rsRoadSections[open]')"),'janela de seções não abriu'
            page.evaluate("()=>document.querySelector('#rsRoadSections [data-save]').click()");page.wait_for_timeout(2500)
            fechou=not page.evaluate("!!document.querySelector('#rsRoadSections[open]')")
            n=page.evaluate("(M.route_alignments[0].cross_sections||[]).length")
            err=page.evaluate(VIS)
            if not fechou:falhas.append(('Salvar e fechar não fechou',err))
            if fechou and n<1:falhas.append(('fechou mas NÃO gravou a seção',n))
            # 2) Fim acima do comprimento: não pode ser silencioso — erro visível e campo marcado
            page.evaluate("async()=>{M.route_alignments[0].cross_sections=[];changed();await save()}")
            abrir()
            page.evaluate("()=>{const d=document.querySelector('#rsRoadSections');d.querySelector('[name=reference]').value='meters';d.querySelector('[name=start]').value='0';d.querySelector('[name=end]').value='999'}")
            page.evaluate("()=>document.querySelector('#rsRoadSections [data-save]').click()");page.wait_for_timeout(1500)
            err=page.evaluate(VIS)
            if not err or not err['visivel']:falhas.append(('erro de Fim inválido não está visível',err))
            if not page.evaluate("document.querySelector('#rsRoadSections [name=end]').getAttribute('aria-invalid')==='true'"):falhas.append(('campo inválido não foi marcado',None))
            b.close()
    finally:
        server.should_exit=True
    assert not falhas,repr(falhas)
