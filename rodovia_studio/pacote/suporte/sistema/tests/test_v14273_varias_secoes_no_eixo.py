"""2.43: várias seções DISTINTAS no mesmo eixo, pelas janelas reais: pista simples, pista duplicada, um só sentido do eixo e um só sentido OPOSTO,
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
    threading.Thread(target=server.run,daemon=True).start();base=f'http://127.0.0.1:{port}'
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
                page.evaluate("([n,v])=>{const e=document.querySelector('dialog[open] [name='+n+']');if(e.type==='checkbox')e.checked=!!v;else e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}",[nome,valor])
            def erro():return (page.evaluate("()=>(document.querySelector('dialog[open] [data-error]')||{}).textContent")or'').strip()
            def adicionar(rotulo):
                page.click('dialog[open] [data-add-section]');page.wait_for_timeout(250)
                e=erro()
                if e:falhas.append((rotulo,'erro',e))
            L=page.evaluate("()=>{const r=document.querySelector('dialog[open] [name=end]');return Number(r.value)}")
            # A: pista simples, dois sentidos, por metros 0–150
            campo('axisMode','dois');campo('template','simples');campo('reference','meters');campo('start','0');campo('end','150');adicionar('A simples por metros')
            # B: pista duplicada, dois sentidos, por KM 150–300
            campo('template','dupla');campo('reference','km')
            origem=page.evaluate("()=>document.querySelector('dialog[open] [name=origin]').value")
            page.evaluate("()=>{const f=(typeof formatKm==='function')?formatKm:null;window.__km=(m)=>f?f(parseKm(document.querySelector('dialog[open] [name=origin]').value)+m):String(m)}")
            campo('start',page.evaluate("()=>__km(150)"));campo('end',page.evaluate("()=>__km(300)"));adicionar('B duplicada por km')
            # C: um só sentido OPOSTO ao eixo (eixo no bordo esquerdo), por coordenadas 300–400 (limite por clique é a mesma tela de coordenadas)
            campo('template','simples');campo('axisMode','bordo_dir');campo('flowDir','oposto');campo('reference','meters');campo('start','300');campo('end',str(int(L)));adicionar('C um sentido oposto')
            # D: nova seção SOBRE as anteriores (resolve a sobreposição, sem erro): um sentido do eixo 100–200
            campo('flowDir','mesmo');campo('start','100');campo('end','200');adicionar('D sobreposta')
            tipos=page.evaluate("()=>[...document.querySelectorAll('dialog[open] [data-sections] li')].map(l=>l.textContent.replace(/\\s+/g,' ').trim())")
            page.click('dialog[open] [data-save]');page.wait_for_timeout(1500)
            e=erro()
            if e:falhas.append(('salvar','erro',e))
            rotas=page.evaluate("()=>JSON.parse(JSON.stringify(M.route_alignments||[]))")
            secs=sorted(rotas[0]['cross_sections'],key=lambda s:s['start_m']) if rotas else []
            faixas=[(round(s['start_m']),round(s['end_m']),s['type'],s['left_dir'],s['right_dir'],s.get('authorize_surface')) for s in secs]
            esperado_intervalos=[(0,100),(100,200),(200,300),(300,round(L))]
            if [(a,b) for a,b,*_ in faixas]!=esperado_intervalos:falhas.append(('intervalos',faixas,esperado_intervalos))
            if len(rotas)!=1 or rotas[0].get('section_surface'):falhas.append(('a rota nova não deve se autorizar como pavimento',rotas and rotas[0].get('section_surface')))
            # prévia das faixas calculada pelo servidor com as 4 seções: sentidos por trecho
            prev=c.post('/api/rotas_previa',json={'route_alignments':rotas,'route_directions':{},'km_signs':{rotas[0]['id']:1}}).json()
            dirs=lambda a,b:sorted({l['dir'] for l in prev['lanes'] if l['start_m']<=a+1 and l['end_m']>=b-1 or (l['start_m']<b and l['end_m']>a)})
            lista=[(a,b,sorted({l['dir'] for l in prev['lanes'] if l['start_m']<(a+b)/2<l['end_m']})) for a,b in esperado_intervalos]
            esp=['f','r'],['f'],['f','r'],['r']
            ok=[(l[2]==list(x)) for l,x in zip(lista,esp)]
            if not all(ok):falhas.append(('sentidos por trecho',lista,esp))
            b.close()
    finally:
        server.should_exit=True
    assert not errors,errors
    assert not falhas,repr(falhas)
