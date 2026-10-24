"""1.27: fluxos (velocidade por trecho, redução nas curvas, proibir/forçar ligações), áreas do desenho para trocar
textura/nome, textura própria por área, janela Sobre e iniciador com janela própria (WebView2)."""
import json,math,re,time
from pathlib import Path
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

ROOT=Path(__file__).resolve().parents[1]
def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})

def test_models_and_migration():
    s=S();assert s.curve_speed is True and s.connection_rules==[] and s.schema_version>=24
    old=Settings.model_validate({'schema_version':23,'km_start_m':0,'km_end_m':100});assert old.curve_speed is False
    with pytest.raises(ValueError,match='km/h'):S(flow_overrides=[{'x':0,'y':0,'action':'speed'}])
    S(flow_overrides=[{'x':0,'y':0,'action':'speed','speed_kmh':40}])
    a=S(pavement_areas=[{'points':[{'x':0,'y':0},{'x':5,'y':0},{'x':5,'y':5}],'texture':{'grao':2}}]);assert a.pavement_areas[0].texture.grao==2

def test_curve_envelope():
    from app.simulation import curve_envelope,LAT_ACC
    d=np.arange(0,300,1.);straight=np.column_stack([d,0*d]);assert curve_envelope(straight,d).min()>=59
    R=30;th=d/R;arc=np.column_stack([R*np.sin(th),R-R*np.cos(th)]);v=curve_envelope(arc,d)
    assert abs(float(np.median(v[50:250]))-math.sqrt(LAT_ACC*R))<1.
    # Antes da curva o limite cai aos poucos (frenagem antecipada), não de repente.
    P=np.vstack([np.column_stack([np.arange(-200,0,1.),np.zeros(200)]),arc[:150]]);dd=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    e=curve_envelope(P,dd);assert e[0]>e[150]+5 and np.all(np.diff(e[:190])<=1e-3+0)  # não cresce enquanto se aproxima

def test_connection_rules_and_speed(junction):
    from app.render import Scene,connection_data
    sc=Scene.light(junction,S());cd=connection_data(sc.network);assert cd['connections']
    c=cd['connections'][0];n0=sum(map(len,sc.network.connections.values()))
    rule={'id':'r1','name':'Proibido virar','a':{'x':c['a'][0],'y':c['a'][1]},'b':{'x':c['b'][0],'y':c['b'][1]},'action':'deny'}
    s2=Scene.light(junction,S(connection_rules=[rule]));d2=connection_data(s2.network)
    assert sum(map(len,s2.network.connections.values()))==n0-1 and len(d2['denied'])==1 and d2['connection_rules'][0]['applied']
    # Forçar depois de proibir: a ligação volta (as regras valem na ordem da lista).
    s4=Scene.light(junction,S(connection_rules=[rule,{**rule,'id':'r2','action':'force'}]));r4=connection_data(s4.network)
    assert sum(map(len,s4.network.connections.values()))==n0 and any(x['forced'] for x in r4['connections']) and all(x['applied'] for x in r4['connection_rules'])
    bad=Scene.light(junction,S(connection_rules=[{**rule,'a':{'x':0,'y':0}}]));assert any('não encontrado' in w for w in bad.network.warnings)
    # Velocidade por trecho: as arestas do trecho recebem o limite, e a simulação o respeita.
    seg=sc.editor_data()['segments'][0];mid=seg['mid']
    s5=Scene.light(junction,S(flow_overrides=[{'id':'v','x':mid[0],'y':mid[1],'action':'speed','speed_kmh':20}]))
    sp=[e for e in s5.network.edges if e.get('speed')];assert sp and all(abs(e['speed']-20/3.6)<1e-9 for e in sp)
    assert s5.editor_data()['segments'][0]['speed_kmh']==20 or any(x['speed_kmh']==20 for x in s5.editor_data()['segments'])

def test_simulation_speed_limits(junction):
    from app.render import Scene
    from app.simulation import TrafficSim
    from app.visual import vehicle_type
    base=Scene.light(junction,S(traffic_density=2))
    main=[x for x in base.editor_data()['segments'] if x['kind']=='main'][0];mid=main['mid']
    from app.simulation import DT
    def vmax(**kw):
        sc=Scene.light(junction,S(traffic_density=2,duration_s=40,**kw));sim=TrafficSim(sc.network,sc.s,vehicle_type,40)
        sp=[]
        for k in range(1,len(sim.frames)):
            a=dict(zip(sim.frames[k-1][0].tolist(),sim.frames[k-1][1].tolist()))
            for i,s_ in zip(sim.frames[k][0].tolist(),sim.frames[k][1].tolist()):
                if i in a:sp.append((s_-a[i])/DT)
        return max(sp) if sp else 0
    v1=vmax();v2=vmax(flow_overrides=[{'id':'v','x':mid[0],'y':mid[1],'action':'speed','speed_kmh':25}])
    assert v1>15 and v2<v1

def test_textured_area_in_frame(junction):
    from app.render import Scene
    from app.visual import texture_lut
    area={'id':'a1','name':'Trecho fresado','kind':'existing_pavement','points':[{'x':500050,'y':7799991},{'x':500150,'y':7799991},{'x':500150,'y':7800009},{'x':500050,'y':7800009}]}
    a=Scene(junction,S(traffic=False,pavement_areas=[area]));b=Scene(junction,S(traffic=False,pavement_areas=[{**area,'texture':{'grao':3,'fissuras':3,'brilho':-.25}}]))
    codes=np.unique(b.surface);assert 32 in codes and 32 not in np.unique(a.surface)
    L=texture_lut(None,[(32,2,{'grao':3,'tom':1,'remendos':1,'fissuras':3,'brilho':-.25})]);assert L['crack'][32]==pytest.approx(3*L['crack'][2]) and L['bright'][32]==pytest.approx(-.25)
    view=((500100,7800000),60);fa=a.frame(5,view=view)[0];fb=b.frame(5,view=view)[0]
    assert fb.mean()<fa.mean()-3                                  # área mais escura (brilho -0,25)
    # Textura neutra: nenhum código novo (resultado igual ao da área sem textura).
    c=Scene(junction,S(traffic=False,pavement_areas=[{**area,'texture':{}}]));assert 32 not in np.unique(c.surface)

def test_api_area_and_about(junction):
    from app.server import app
    from app import worker
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=S().model_dump()).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
        j=c.post(f'/api/projects/{pid}/analyze').json();worker.run(j['id'])
        r=c.get(f'/api/projects/{pid}/area',params={'x':500300,'y':7800000}).json()
        assert r['layer']=='PAVIMENTO' and r['role']=='pavement' and r['area_m2']==pytest.approx(400*18,rel=.01) and len(r['points'])==4
        r2=c.get(f'/api/projects/{pid}/area',params={'x':500200,'y':7800060}).json();assert r2['area_m2']==pytest.approx(20*111,rel=.01)
        assert c.get(f'/api/projects/{pid}/area',params={'x':0,'y':0}).status_code==404
        ed=c.get(f'/api/projects/{pid}/editor.json').json();assert ed['connections'] and {'from','to','p','a','b','forced'}<=set(ed['connections'][0])
        ab=c.get('/api/sobre').json();assert ab['app'] and ab['schema']>=24

def test_launcher_webview2_source():
    src=(ROOT/'iniciador'/'RodoviaStudio.cs').read_text(encoding='utf-8-sig')
    code=re.sub(r'//[^\n]*','',re.sub(r'"(?:\\.|[^"\\])*"','""',src))
    assert '$""' not in code and '?.' not in code and 'nameof(' not in code and not re.search(r'\)\s*=>',code) and 'out var' not in code
    assert code.count('{')==code.count('}') and code.count('(')==code.count(')')
    assert '#if WEBVIEW2' in src and '#endif' in src and 'SetLoaderDllFolderPath' in src and 'AssemblyResolve' in src and 'CreateAsync' in src and '--app=' in src
    assert re.search(r'Version = "1\.[1-9]\d*"',src) and 'iniciador_versao.txt' in src
    # Fora do bloco WEBVIEW2 não há referência aos tipos do WebView2 (compila sem as DLLs).
    outside=re.sub(r'#if WEBVIEW2.*?#endif','',src,flags=re.S);assert 'CoreWebView2' not in outside and 'WebView2 ' not in outside
    cmd=(ROOT/'raiz_extra'/'COMPILAR INICIADOR.cmd').read_bytes();t=cmd.decode('ascii')
    assert b'\r\n' in cmd and '/define:WEBVIEW2' in t and 'Microsoft.Web.WebView2.WinForms.dll' in t and 'pacotes_webview2' in t and 'WebView2Loader.dll' in t

def test_advance_speed_and_zones(junction):
    from app.render import Scene,duration_for_speed,tour_seconds
    T=duration_for_speed(4000,100,True);assert abs(tour_seconds(T,True)-4000/(100/3.6))<.2
    assert duration_for_speed(10,500,False)==45 and duration_for_speed(10**6,5,True)==1800
    sc=Scene.light(junction,S(duration_s=100));assert sc.advance_map(.3)==.3                      # sem trechos: igual
    z={'id':'z','name':'Obra','start':{'x':500100,'y':7800000},'end':{'x':500200,'y':7800000},'speed_pct':25}
    sz=Scene.light(junction,S(duration_s=100,advance_zones=[z]))
    # No trecho lento (25%) a câmera gasta 4× o tempo: a fração de tempo para atravessá-lo cresce.
    u=np.linspace(0,1,2001);f=np.array([sz.advance_map(x) for x in u]);ch=f*sz.length
    inside=(ch>=100)&(ch<=200);share=inside.mean();assert .5<share<.65                           # 400/(300+400)≈0,57
    assert np.all(np.diff(f)>=0) and f[0]==0 and abs(f[-1]-1)<1e-9
    v=Scene(junction,S(advance_mode='velocidade',advance_speed_kmh=36,traffic=False));assert abs(tour_seconds(v.s.duration_s,bool(v.pois))-40)<.3 or v.s.duration_s==45

def free_port():
    import socket
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_127_ui(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import os,threading,uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    cfg=S(highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}]).model_dump()
    pid=c.post('/api/projects',json=cfg).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && editor && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500240,y:7800005});view.s=Math.min(240,canvas.width*mpp()/110);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            page.locator('#canvas').scroll_into_view_if_needed()
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            def C(q):
                R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Clique sobre a pista (área do desenho): seleciona com os vértices destacados.
            page.keyboard.down('Alt');page.mouse.click(*W2C(500280,7799993));page.keyboard.up('Alt');page.wait_for_function('dxfSel&&dxfSel.layer==="PAVIMENTO"')
            assert 'Área do desenho' in page.inner_text('#propPanel') and not ev("document.getElementById('selBar').hidden")
            # Botão direito: só os comandos da área; menu com largura fixa.
            page.mouse.click(*W2C(500280,7799993),button='right');page.wait_for_selector('#ctxMenu:not([hidden])')
            t=page.inner_text('#ctxMenu');assert 'Trocar textura' in t and 'Trocar nome' in t and 'Enquadrar tudo' not in t and 'Inserir' not in t
            assert ev("document.getElementById('ctxMenu').getBoundingClientRect().width")==300
            page.click('#ctxMenu .it:has-text("Trocar textura")');page.wait_for_selector('#texDlg[open]')
            ev("(()=>{const i=document.getElementById('td_grao');i.value='2.5';i.dispatchEvent(new Event('input',{bubbles:true}))})()")
            assert 'grao' in ev("decodeURIComponent(document.getElementById('td_img').src)") and '2.5' in ev("decodeURIComponent(document.getElementById('td_img').src)")
            page.click('#td_ok');page.wait_for_function('M.pavement_areas.length===1')
            a=ev('M.pavement_areas[0]');assert a['texture']['grao']==2.5 and a['source']=='picked' and len(a['points'])==4 and ev('selObjs().length')==0   # 1.28: comando concluído limpa a seleção
            # Trocar nome pelo menu (caixa de diálogo, Enter confirma).
            page.mouse.click(*W2C(500280,7799993));page.wait_for_function("sel&&sel.key==='pavement_areas'")
            page.mouse.click(*W2C(500280,7799993),button='right');page.wait_for_selector('#ctxMenu:not([hidden])');page.click('#ctxMenu .it:has-text("Trocar nome")')
            page.wait_for_selector('#inputDlg[open]');page.fill('#inputValue','Faixa fresada');page.keyboard.press('Enter');assert ev('M.pavement_areas[0].name')=='Faixa fresada'
            # Arrastar o destaque move direto (sem clicar antes); setas deslocam 0,10 m.
            ev("(()=>{sel=null;selSet=[];showProps();draw()})()")
            x,y=W2C(500250,7800020);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+40,y,steps=5);page.mouse.up()
            px=ev('M.highlights[0].point.x');assert px>500252 and ev('sel.key')=='highlights'
            y0=ev('M.highlights[0].point.y');page.focus('#canvas');page.keyboard.press('ArrowUp');assert abs(ev('M.highlights[0].point.y')-y0-.1)<1e-6
            # Caixa de chamada: arrastar o losango muda a linha; o comprimento também é editável.
            lp=ev('W2C(labelPos(objOf(sel)))');x,y=C(lp);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+60,y-30,steps=5);page.mouse.up()
            assert ev('M.highlights[0].label')!=None;d0=ev('leaderInfo(objOf(sel)).d')
            page.fill('#propPanel [data-leader="d"]','25');page.press('#propPanel [data-leader="d"]','Enter');assert abs(ev('leaderInfo(objOf(sel)).d')-25)<1e-6
            # Alça de giro: gira a área selecionada em torno do centro.
            ev("(()=>{sel={key:'pavement_areas',i:0};selSet=[];showProps();draw()})()");P0=ev('M.pavement_areas[0].points.map(p=>[p.x,p.y])')
            h=ev('rotHandle()');x,y=C([h['x'],h['y']]);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+120,y+80,steps=6);page.mouse.up()
            P1=ev('M.pavement_areas[0].points.map(p=>[p.x,p.y])');assert P1!=P0 and abs(np.mean(P1,0)-np.mean(P0,0)).max()<1e-6
            ev('undo()');assert ev('M.pavement_areas[0].points.map(p=>[p.x,p.y])')==P0
            # Fluxos: selecionar trajetória, ver e proibir uma ligação.
            ev("(()=>{sel=null;selSet=[];dxfSel=null;showProps();draw()})()")
            seg=ev("(()=>{const c=editor.connections[0];const s=editor.segments.find(x=>x.id===c.from);selSeg={id:s.id};showSegProps();const q=P(c.p[Math.floor(c.p.length/2)]);const [ix,iy]=worldToImg(q);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw();return {c,q:[q.x,q.y]}})()")
            assert 'Velocidade (km/h)' in page.inner_text('#propPanel') and 'saída' in page.inner_text('#propPanel')
            page.mouse.click(*W2C(*seg['q']));page.wait_for_function('selLink!==null')
            page.click('#propPanel [data-lk="deny"]');assert ev('M.connection_rules.length')==1 and ev('M.connection_rules[0].action')=='deny'
            # Velocidade de avanço: modo por velocidade calcula a duração.
            ev("(()=>{const s=document.getElementById('profileBox');s.open=true;s.closest('section').classList.remove('collapsed')})()")
            page.select_option('#advance_mode','velocidade');page.fill('#advance_speed_kmh','36');page.dispatch_event('#advance_speed_kmh','change')
            page.wait_for_function("document.getElementById('advInfo').textContent.includes('km/h')");assert ev("document.getElementById('duration_s').disabled")
            # Ferramenta de trecho com velocidade própria.
            ev("(()=>{const [ix,iy]=worldToImg({x:500200,y:7800000});view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            page.click('#toolbar button[data-tool="advzone"]');page.fill('#advPct','40');page.mouse.click(*W2C(500170,7800000));page.mouse.click(*W2C(500230,7800000))
            assert ev('M.advance_zones.length')==1 and ev('M.advance_zones[0].speed_pct')==40
            page.keyboard.press('Escape');page.wait_for_timeout(100)
            if ev("document.getElementById('confirmDlg').open"):page.keyboard.press('Enter')
            # Barra de menus: Ajuda > Sobre.
            page.click('#menuBar .mb:has-text("Ajuda")');page.click('#menuBar .rb:has-text("Sobre")');page.wait_for_selector('#aboutDlg[open]')
            assert 'Formato do projeto' in page.inner_text('#aboutBody');page.keyboard.press('Escape')
            sbt=page.inner_text('#statusBar');assert 'SNAP' in sbt and 'ORTO' in sbt and 'X 5002' in sbt
            page.wait_for_timeout(1300);conf=c.get(f'/api/projects/{pid}').json()['config']
            assert conf['advance_mode']=='velocidade' and conf['advance_speed_kmh']==36 and conf['connection_rules'] and conf['advance_zones'] and conf['pavement_areas'][0]['texture']['grao']==2.5
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors

def test_editor_1271_commands_finish_clean_and_apply(junction):
    """1.28: comandos terminam limpando a seleção/mini-barra; menu fecha ao clicar na tela; edição feita durante
    uma tarefa é salva e não some ao recarregar; desfazer continua; com a prévia à vista ela é refeita sozinha."""
    pw=pytest.importorskip('playwright.sync_api')
    import os,threading,uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800020}}],signs=[{'id':'s1','code':'R-1','point':{'x':500230,'y':7800012}}]).model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && editor && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500240,y:7800010});view.s=Math.min(240,canvas.width*mpp()/110);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            def W2C(x,y):
                ev("canvas.scrollIntoView({block:'center'})");q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            def conf():page.wait_for_timeout(1300);return c.get(f'/api/projects/{pid}').json()['config']
            # Girar pelo menu: o pedido aparece na mensagem; ao concluir, seleção, grips e mini-barra somem.
            page.mouse.click(*W2C(500250,7800020),button='right');page.wait_for_selector('#ctxMenu:not([hidden])')
            page.click('#ctxMenu .it:has(span:text-is("Girar"))');assert 'GIRAR' in ev("document.getElementById('message').textContent") and ev("document.getElementById('selBar').hidden")
            cl=page.locator('#cmdLine');cl.fill('500240,7800010');cl.press('Enter');cl.fill('90');cl.press('Enter')
            page.wait_for_function('selObjs().length===0');assert ev("document.getElementById('selBar').hidden") and ev('!cadCmd')
            hp=ev('M.highlights[0].point');assert abs(hp['x']-500230)<.1 and abs(hp['y']-7800020)<.1
            assert abs(conf()['highlights'][0]['point']['x']-hp['x'])<1e-9
            # Menu aberto + clique sobre um objeto: o menu fecha.
            page.mouse.click(*W2C(500230,7800020),button='right');page.wait_for_selector('#ctxMenu:not([hidden])')
            page.mouse.click(*W2C(500198,7800012));assert ev("document.getElementById('ctxMenu').hidden") and not ev("document.getElementById('inputDlg').open")
            # Edição durante uma tarefa: é salva e não some quando a tarefa termina (nem o desfazer).
            ev("(()=>{sel=null;selSet=[];showProps();draw()})()");ev("start('analyze');0");page.wait_for_function('!!task')
            x,y=W2C(500230,7800012);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+40,y,steps=4);page.mouse.up()
            moved=ev('M.signs[0].point.x');assert moved>500231;n_undo=ev('undoStack.length')
            page.wait_for_function('!task',timeout=60000);page.wait_for_timeout(1500)
            assert abs(ev('M.signs[0].point.x')-moved)<1e-9 and abs(conf()['signs'][0]['point']['x']-moved)<1e-9 and ev('undoStack.length')>=n_undo
            # Com a prévia renderizada à vista, uma alteração refaz a prévia sozinha.
            ev("start('preview');0");page.wait_for_function('!!task');page.wait_for_function('!task&&meta&&baseImage',timeout=90000);page.wait_for_timeout(500)
            page.select_option('#baseMode','preview');page.wait_for_function("baseMode==='preview'&&previewVisible()")
            x,y=W2C(500230,7800020);page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+20,y,steps=3);page.mouse.up()
            assert ev('previewStale');page.wait_for_function('!!task',timeout=10000);page.wait_for_function('!task&&!previewStale',timeout=120000);page.wait_for_timeout(800);assert ev("baseMode==='preview'") and ev('previewVisible()')
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
