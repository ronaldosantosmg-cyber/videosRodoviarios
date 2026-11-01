"""2.41: fluxo COMPLETO na tela, no navegador: escolher eixo → aplicar seção (janela Seções tipo) → inverter o eixo (caixa “Inverter início e fim”)
→ trocar o sentido do eixo na layer → salvar → recarregar a página. Em cada etapa o sentido das faixas da prévia tem de ser o do KM, e o que volta
do disco tem de ser igual ao que estava na tela."""
import os,threading,time,json
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

LANES="()=>{const d=[...new Set((routeLanes||[]).map(l=>l.dir))].sort().join('');return {dirs:d,n:(routeLanes||[]).length,sign:Object.values(routeKmSigns())[0],rev:!!cfg.reverse_axis}}"
def test_aplicar_secao_inverter_salvar_e_reabrir(junction,tmp_path,monkeypatch):
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
    pid=c.post('/api/projects',json=S(name='FluxoCompleto').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];log=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':900})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.dismiss())
            page.route('**/tiles/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=90000)
            # 1) escolher o eixo e aplicar a seção pelas janelas reais
            page.evaluate("()=>{RodoviaSections.chooseAxis()}")
            page.wait_for_selector('dialog[open] [name=axis]',timeout=15000)
            log.append(('eixos',page.evaluate("()=>[...document.querySelectorAll('dialog[open] [name=axis] option')].map(o=>o.textContent)")))
            page.click('dialog[open] [data-save]')
            page.wait_for_selector('dialog[open] [data-add-section]',timeout=15000)
            page.click('dialog[open] [data-add-section]');page.wait_for_timeout(300)
            log.append(('erro',page.evaluate("()=>(document.querySelector('dialog[open] [data-error]')||{}).textContent")))
            page.click('dialog[open] [data-save]');page.wait_for_timeout(800)
            log.append(('rotas',page.evaluate("()=>(M.route_alignments||[]).map(r=>({n:r.name,s:(r.cross_sections||[]).length,fp:(r.source_axis_fingerprint||'').slice(0,8)}))")))
            def lanes(esperado,motivo):
                """espera a prévia (assíncrona) assentar no sentido esperado; registra falha com o estado real se não assentar"""
                page.evaluate("()=>refreshRouteLanes(true)")
                try:page.wait_for_function("(e)=>{const d=[...new Set((routeLanes||[]).map(l=>l.dir))].sort().join('');return (routeLanes||[]).length>0&&d===e}",arg=esperado,timeout=8000)
                except Exception:falhas.append((motivo,'esperado',esperado,'tela',page.evaluate(LANES)))
            def esperado_do_km(escolha):
                s=page.evaluate("()=>Object.values(routeKmSigns())[0]")
                return 'f' if (s>=0)==(escolha=='forward') else 'r'
            falhas=[]
            fp=page.evaluate("()=>M.route_alignments[0].source_axis_fingerprint")
            # 2) sentido Crescente no eixo; inverter o eixo; trocar para Decrescente
            page.evaluate("(fp)=>{FLUXO.definir('axis:'+fp,'forward');changed()}",fp)
            lanes(esperado_do_km('forward'),'Crescente, eixo normal')
            s0=page.evaluate("()=>Object.values(routeKmSigns())[0]")
            page.click('#reverse_axis') if page.is_visible('#reverse_axis') else page.evaluate("()=>{const c=document.getElementById('reverse_axis');c.checked=!c.checked;c.dispatchEvent(new Event('change',{bubbles:true}))}")
            page.wait_for_timeout(400)
            s1=page.evaluate("()=>Object.values(routeKmSigns())[0]")
            if s1==s0:falhas.append(('inverter eixo não mudou o sinal do km da seção',s0,s1,page.evaluate(LANES)))
            lanes(esperado_do_km('forward'),'Crescente, eixo invertido')
            page.evaluate("(fp)=>{FLUXO.definir('axis:'+fp,'reverse');changed()}",fp)
            lanes(esperado_do_km('reverse'),'Decrescente, eixo invertido')
            # 3) salvar e reabrir
            antes=page.evaluate("()=>({rd:cfg.route_directions,rev:reverseAxisPendente(),rotas:JSON.stringify(M.route_alignments)})")
            page.evaluate("()=>save()");page.wait_for_function("()=>!savePending",timeout=15000)
            disco=c.get(f'/api/projects/{pid}').json()
            cfgd=disco.get('config',disco)
            if bool(cfgd.get('reverse_axis'))!=antes['rev']:falhas.append(('reverse_axis não gravado',cfgd.get('reverse_axis'),antes['rev']))
            if cfgd.get('route_directions',{}).get('axis:'+fp)!='reverse':falhas.append(('sentido do eixo não gravado',cfgd.get('route_directions')))
            if len(cfgd.get('route_alignments',[]))!=1:falhas.append(('seção não gravada',len(cfgd.get('route_alignments',[]))))
            page.reload()
            try:page.wait_for_function('typeof geo!=="undefined"&&geo&&typeof cfg!=="undefined"&&cfg&&cfg.route_alignments&&cfg.route_alignments.length>0&&typeof M!=="undefined"&&M.route_alignments&&M.route_alignments.length>0',timeout=60000)  
            except Exception:falhas.append(('a página reaberta não trouxe a seção do disco',page.evaluate("()=>({pid:typeof pid!=='undefined'?pid:null,cfgR:cfg&&(cfg.route_alignments||[]).length,M:(M.route_alignments||[]).length,ls:localStorage.getItem('rodovia_project'),msg:(document.getElementById('msg')||{}).textContent})")))

            depois=page.evaluate("()=>({rd:cfg.route_directions,rev:reverseAxisPendente(),rotas:JSON.stringify(M.route_alignments)})")
            if depois['rd']!=antes['rd'] or depois['rev']!=antes['rev']:falhas.append(('reabrir mudou sentido/inverter',antes['rd'],depois['rd'],antes['rev'],depois['rev']))
            if json.loads(depois['rotas'])[0]['cross_sections']!=json.loads(antes['rotas'])[0]['cross_sections']:falhas.append(('reabrir mudou a seção',))
            lanes(esperado_do_km('reverse'),'Decrescente, depois de reabrir')
            # 4) a interface de “Sentido do eixo” mostra o mesmo valor
            ui=page.evaluate("(fp)=>FLUXO.obter('axis:'+fp)",fp)
            if ui!='reverse':falhas.append(('sentido lido da tela diferente',ui))
            b.close()
    finally:
        server.should_exit=True
    assert not errors,errors
    assert not falhas,repr(falhas)
