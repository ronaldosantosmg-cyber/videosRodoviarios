"""2.55: diálogo de seções — pista simples/dupla, acostamento, fluxo, origem, transição. (base 2.43: várias seções DISTINTAS no mesmo eixo, pelas janelas reais: pista simples, pista duplicada, um só sentido do eixo e um só sentido OPOSTO,
por distância (m), por km e por coordenadas; uma seção nova sobre outras recorta as anteriores sem erro; salvar não gera erro."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_varias_secoes_no_mesmo_eixo_sem_erro(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    server_thread=threading.Thread(target=server.run,daemon=True);server_thread.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='VariasSecoes').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];falhas=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.dismiss())
            page.route('**/tiles/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=90000)
            page.evaluate("()=>{RodoviaSections.chooseAxis()}");page.wait_for_selector('dialog[open] [name=axis]',timeout=15000)
            page.click('dialog[open] [data-save]');page.wait_for_selector('dialog[open] [data-add-section]',timeout=15000)
            def campo(nome,valor):
                page.evaluate("([n,v])=>{const e=document.querySelector('dialog[open] [name='+n+']');if(e.type==='checkbox')e.checked=!!v;else e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}",[nome,valor]);page.wait_for_timeout(120)
            val=lambda n:page.evaluate("(n)=>{const e=document.querySelector('dialog[open] [name='+n+']');return e.type==='checkbox'?e.checked:e.value}",n)
            dis=lambda n:page.evaluate("(n)=>document.querySelector('dialog[open] [name='+n+']').disabled",n)
            def erro():return (page.evaluate("()=>(document.querySelector('dialog[open] [data-error]')||{}).textContent")or'').strip()
            def faixas(lado):return page.evaluate("(l)=>[...document.querySelectorAll('dialog[open] [data-'+l+'] .rsSectionBand')].map(r=>[r.querySelector('select').value,Number(r.querySelector('input[type=number]').value)])",lado)
            def checa(rot,cond,det=''):
                if not cond:falhas.append((rot,det))
            # 1) PISTA SIMPLES: dois sentidos, sem canteiro, 1 faixa por lado + acostamento 2,5
            campo('template','simples')
            checa('simples→modo dois sentidos',val('axisMode')=='dois',val('axisMode'));checa('simples sem canteiro',float(val('median'))==0)
            checa('simples com acostamento',faixas('left')==[['pista',3.5],['acostamento',2.5]] and faixas('right')==[['pista',3.5],['acostamento',2.5]],(faixas('left'),faixas('right')))
            campo('shoulderMode','sem');checa('sem acostamento',faixas('left')==[['pista',3.5]] and faixas('right')==[['pista',3.5]],(faixas('left'),faixas('right')))
            campo('shoulderMode','com');checa('com acostamento de novo',len(faixas('left'))==2)
            campo('quickShoulderLeft','1.5');checa('personalizado detectado',val('shoulderMode')=='custom')
            campo('shoulderMode','com')
            # 2) modo dois sentidos não vira dupla sozinho; fluxo travado nesse modo
            campo('axisMode','dois');checa('dois sentidos mantém simples',val('template')=='simples',val('template'));checa('fluxo travado em dois sentidos',dis('flowDir'))
            # 3) um só sentido: mudar o sentido do fluxo muda as setas e legenda
            campo('axisMode','bordo_dir');checa('fluxo liberado em um só sentido',not dis('flowDir'))
            s0=page.evaluate("()=>document.querySelector('dialog[open] [data-section-preview]').textContent")
            campo('flowDir','oposto');s1=page.evaluate("()=>document.querySelector('dialog[open] [data-section-preview]').textContent")
            leg=page.evaluate("()=>document.querySelector('dialog[open] [data-leg-right]').textContent")
            checa('setas invertem com o fluxo',s0!=s1 and '←' in s1,(s0,s1));checa('legenda acompanha o fluxo','contr' in leg,leg)
            campo('flowDir','mesmo');campo('axisMode','dois');campo('template','simples')
            # 4) origem: em km, mudar o km inicial desloca início/fim e a lista
            L=int(float(val('end')));campo('reference','km');o0=val('origin');i0=val('start')
            campo('origin','280+000');i1=val('start');checa('origem muda início em km',i0!=i1 and i1.startswith('280'),(o0,i0,i1))
            campo('reference','meters');campo('start','0');campo('end','200');page.click('dialog[open] [data-add-section]');page.wait_for_timeout(250)
            lista=page.evaluate("()=>[...document.querySelectorAll('dialog[open] [data-sections] li')].map(l=>l.textContent.replace(/\\s+/g,' ').trim())")
            checa('lista mostra km da origem nova',any('km 280' in x for x in lista),lista)
            # 5) pista dupla encostada → aparece a transição obrigatória
            campo('template','dupla');campo('start','200');campo('end',str(L));page.click('dialog[open] [data-add-section]');page.wait_for_timeout(1200)
            tr=page.evaluate("()=>({hidden:document.querySelector('dialog[open] [data-transitions-box]').hidden,t:[...document.querySelectorAll('dialog[open] [data-transitions] li')].map(l=>l.textContent)})")
            checa('transição simples→dupla listada',(not tr['hidden']) and any('simples' in x for x in tr['t']),tr)
            checa('sem erro ao montar',not erro(),erro())
            b.close()
    finally:
        server.should_exit=True;server_thread.join(timeout=15);assert not server_thread.is_alive()
    assert not errors,errors
    assert not falhas,repr(falhas)
