"""1.26: pórticos (dois apoios + imagem na chamada), caixas de chamada sem sobreposição e com janela de tempo,
ocultar/congelar camada, leitura de hachuras ampliada (MPOLYGON, padrões, cor), seleção de linha/encadeada para o
alinhamento, sessões de trabalho, imagens enviadas e registros (execução, erros, prompt para IA)."""
import io,json,time,zipfile
import numpy as np,cv2,ezdxf,pytest
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})
def png(color=(0,120,40),w=300,h=100):
    im=np.full((h,w,3),color,np.uint8);cv2.putText(im,'SAIDA 12',(10,h//2+10),cv2.FONT_HERSHEY_SIMPLEX,1.2,(255,255,255),3);return cv2.imencode('.png',im)[1].tobytes()

def test_gantry_model_validation_and_migration():
    g={'name':'P1','a':{'x':0,'y':0},'b':{'x':20,'y':0}}
    s=S(gantries=[g]);assert s.gantries[0].kind=='portico' and s.gantries[0].height_m==7 and s.callout_layout=='auto'
    with pytest.raises(ValueError,match='mínimo 2 m'):S(gantries=[{**g,'b':{'x':1,'y':0}}])
    with pytest.raises(ValueError):S(gantries=[{**g,'image':'../x.png'}])
    with pytest.raises(ValueError,match='depois do início'):S(highlights=[{'name':'H','point':{'x':0,'y':0},'start_s':5,'end_s':2}])
    old=Settings.model_validate({'schema_version':22,'km_start_m':0,'km_end_m':100});assert old.callout_layout=='anterior' and old.schema_version>=23
    assert Settings.model_validate({'schema_version':22,'km_start_m':0,'km_end_m':100,'callout_layout':'auto'}).callout_layout=='auto'

def test_place_card_avoids_overlap_and_window_fade():
    from app.visual import place_card,_overlap
    from app.render import window_fade
    placed=[];boxes=[]
    for k in range(4):
        x,y=place_card((640+k*15,500),(300,120),1280,100,620,placed,.5);r=(x,y,x+300,y+120);assert all(_overlap(r,p)==0 for p in placed);placed.append(r)
    assert place_card((640,400),(300,120),1280,100,620,[],.5,label=(200,300))==(50.0,240.0)
    assert window_fade({'start_s':None,'end_s':None},3)==1 and window_fade({'start_s':5,'end_s':None},4)==0 and window_fade({'start_s':5,'end_s':9},9.5)==0
    assert 0<window_fade({'start_s':5,'end_s':9},5.3)<1

def test_gantry_and_callouts_in_frame(junction):
    from app.render import Scene
    (junction/'imagens').mkdir();name='a'*24+'.png';(junction/'imagens'/name).write_bytes(png())
    g={'id':'g1','name':'Pórtico km 0+200','a':{'x':500200,'y':7799990},'b':{'x':500200,'y':7800010},'image':name,'description':'Saída 12'}
    hl=[{'id':'h1','name':'Poste A','point':{'x':500215,'y':7800004},'category':'poste'},{'id':'h2','name':'Poste B','point':{'x':500218,'y':7800002},'category':'poste','style':'compacto'}]
    view=((500205,7800000),120)
    base=Scene(junction,S(traffic=False)).frame(5,view=view)[0]
    sc=Scene(junction,S(traffic=False,gantries=[g],highlights=hl))
    assert sc.gantries[0]['pic'].shape==(100,300,3) and sc.gantries[0]['panel_rgb'] is not None
    im=sc.frame(5,view=view)[0];d=np.abs(im.astype(int)-base.astype(int)).sum(2)>30
    q=sc.screen(np.array([[500200,7800000.]]),np.array(view[0],float),view[1])[0].astype(int)
    assert d[q[1]-5:q[1]+5,q[0]-5:q[0]+5].mean()>.5            # viga desenhada no meio do vão
    assert d.sum()>20000                                         # cartões com a imagem da placa
    # Janela de tempo: antes do início o pórtico continua, mas a chamada não aparece.
    sc2=Scene(junction,S(traffic=False,gantries=[{**g,'start_s':8}]));sc3=Scene(junction,S(traffic=False,gantries=[{**g,'callout':False}]))
    assert np.array_equal(sc2.frame(5,view=view)[0],sc3.frame(5,view=view)[0])
    # Layout anterior com destaque: idêntico ao desenho da 1.25 (sem janela de tempo).
    a=Scene(junction,S(traffic=False,highlights=hl[:1],callout_layout='anterior')).frame(5,view=view)[0]
    from app import visual
    calls=[];orig=visual.draw_highlight
    try:
        visual.draw_highlight=lambda *a,**k:(calls.append(1),orig(*a,**k))
        b=Scene(junction,S(traffic=False,highlights=hl[:1],callout_layout='anterior')).frame(5,view=view)[0]
    finally:visual.draw_highlight=orig
    assert calls and np.array_equal(a,b)

def test_hidden_and_frozen_layers(junction):
    from app.geometry import analyze
    from app.render import Scene
    items,_,_,_,rep=analyze(junction,S(hidden_layers=['PAVIMENTO']))
    assert not [e for e in items if e['layer']=='PAVIMENTO'] and any('oculta' in w for w in rep['warnings'])
    with pytest.raises(ValueError):analyze(junction,S(hidden_layers=['EIXO']))   # sem eixo não há vídeo: o erro é claro
    items=analyze(junction,S(frozen_layers=['PAVIMENTO']))[0];assert all(e.get('frozen') for e in items if e['layer']=='PAVIMENTO')
    sc=Scene(junction,S(frozen_layers=['PAVIMENTO']));nf=Scene(junction,S())
    paved=nf.stations!=65535;assert (sc.stations[paved]==0).mean()>.95 and (nf.stations[paved]>0).mean()>.5
    assert sc.geometry_signature!=nf.geometry_signature
    # Construção progressiva: no início, a camada congelada já aparece.
    cam=np.array([500300.,7800000.]);a=sc.draw_base(cam,300,0.02);b=nf.draw_base(cam,300,0.02)
    assert np.abs(a.astype(int)-b.astype(int)).sum()>0

def hatch_dxf(tmp_path):
    d=ezdxf.new();m=d.modelspace()
    m.add_lwpolyline([(0,0),(400,0)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(color=3,dxfattribs={'layer':'X_GRAMA_PATTERN'});h.set_pattern_fill('GRASS',scale=1);h.paths.add_polyline_path([(0,10),(100,10),(100,20),(0,20)],is_closed=True)
    h=m.add_hatch(dxfattribs={'layer':'H1'});h.dxf.true_color=0x2e7d32;h.paths.add_polyline_path([(0,30),(50,30),(50,40),(0,40)],is_closed=True)
    mp=m.add_mpolygon(dxfattribs={'layer':'PISTA_MP'});mp.paths.add_polyline_path([(0,-9),(400,-9),(400,9),(0,9)],is_closed=True);mp.paths.add_polyline_path([(100,-2),(110,-2),(110,2),(100,2)],is_closed=True)
    h=m.add_hatch(dxfattribs={'layer':'H2'});h.set_pattern_fill('AR-CONC',scale=1);h.paths.add_polyline_path([(200,30),(260,30),(260,40),(200,40)],is_closed=True)
    d.saveas(tmp_path/'input.dxf');return tmp_path

def test_hatch_reading_improvements(tmp_path):
    from app.geometry import analyze
    d=hatch_dxf(tmp_path);hp={}
    items,_,_,_,rep=analyze(d,S(layers={'axis':['EIXO'],'pavement':['PISTA_MP']},hatch_auto=True),hatch_preview=hp)
    H={h['layer']:h for h in rep['hatches']}
    mp=[e for e in items if e['layer']=='PISTA_MP'];assert len(mp)==1 and len(mp[0]['holes'])==1 and H['PISTA_MP']['islands']==1 and H['PISTA_MP']['entity']=='MPOLYGON'
    assert H['PISTA_MP']['area_m2']==pytest.approx(400*18-40,rel=.01)
    assert H['X_GRAMA_PATTERN']['suggested_role']=='median' and H['X_GRAMA_PATTERN']['confidence']=='alta'
    assert H['H2']['suggested_role']=='pavement' and H['H2']['suggested_material']=='rigido' and H['H2']['confidence']=='média' and 'AR-CONC' in H['H2']['reason']
    assert H['H1']['suggested_role'] is None and H['H1']['color_hint']=='median'          # cor é só indicação
    assert not [e for e in items if e['layer']=='H1'] and [e for e in items if e['layer']=='H2' and e['material']=='rigido']
    assert set(hp)==set(h['sig'] for h in rep['hatches']) and all(v['p'] for v in hp.values())

def test_pick_line_and_chain(tmp_path):
    from app.webmap import write_lines,pick_line,chain_lines
    P=lambda *a:np.array(a,float)
    items=[{'layer':'E1','role':'axis','closed':False,'points':P((0,0),(100,0))},{'layer':'E2','role':'axis','closed':False,'points':P((200,0),(100,0))},
           {'layer':'E3','role':'axis','closed':False,'points':P((200,0),(300,50))},{'layer':'R','role':'edge_line','closed':False,'points':P((100,0),(100,-80))},
           {'layer':'F','role':'pavement','closed':True,'points':P((0,10),(10,10),(10,20)),'frozen':True}]
    write_lines(tmp_path,items)
    r=pick_line(tmp_path,50,1.2,5);assert r['layer']=='E1' and r['points']==[[0,0],[100,0]] and r['distance_m']==pytest.approx(1.2)
    assert pick_line(tmp_path,5,15,3) is None                      # congelada não é selecionável
    c=chain_lines(tmp_path,250,25,5);assert c['parts']==2 and c['points'][0]==[100,0] and c['points'][-1]==[300,50]   # para na bifurcação (x=100); mantém o sentido da linha clicada
    items[3]['points']=P((100,0.5),(100,-80));write_lines(tmp_path,items)
    import app.webmap as wm;wm._lines_cache.clear()
    c=chain_lines(tmp_path,250,25,5);assert c['parts']==3 and c['points'][0]==[0,0] and c['length_m']==pytest.approx(200+np.hypot(100,50),abs=.01)

def test_api_images_lines_sessions_and_logs(junction):
    from app.server import app
    from app import worker
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=S().model_dump()).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
        j=c.post(f'/api/projects/{pid}/analyze').json();worker.run(j['id'])
        # Imagem: normalizada em PNG, nome pelo conteúdo; arquivo inválido recusado.
        r=c.post(f'/api/projects/{pid}/imagens',files={'file':('placa.png',png())});assert r.status_code==201 and r.json()['size']==[300,100]
        name=r.json()['image'];assert c.get(f'/api/projects/{pid}/imagens/{name}').content[:4]==b'\x89PNG'
        assert c.post(f'/api/projects/{pid}/imagens',files={'file':('x.png',b'nada')}).status_code==415
        assert c.get(f'/api/projects/{pid}/imagens/..%2Fconfig.json').status_code==404
        g={'id':'g1','name':'P1','a':{'x':500200,'y':7799990},'b':{'x':500200,'y':7800010},'image':name}
        conf=c.get(f'/api/projects/{pid}').json()['config'];conf['gantries']=[g];assert c.put(f'/api/projects/{pid}/config',json=conf).status_code==200
        # Linhas do desenho.
        r=c.get(f'/api/projects/{pid}/linha',params={'x':500150,'y':7800000.5}).json();assert r['layer']=='EIXO' and len(r['points'])==2
        assert c.get(f'/api/projects/{pid}/linha',params={'x':0,'y':0}).status_code==404
        assert c.get(f'/api/projects/{pid}/hachuras_previa').json()
        # Sessões.
        st={'view':{'cx':500200,'cy':7800000,'w':300},'tool':'pan','collapsed':['sec_1']}
        assert c.put(f'/api/projects/{pid}/sessoes/Revisão 1',json={'state':st}).status_code==200
        assert c.put(f'/api/projects/{pid}/sessoes/a%2Fb',json={'state':st}).status_code in (404,422)
        L=c.get(f'/api/projects/{pid}/sessoes').json()['sessions'];assert L[0]['name']=='Revisão 1' and L[0]['state']['view']['w']==300
        assert c.delete(f'/api/projects/{pid}/sessoes/Revisão 1').status_code==200 and not c.get(f'/api/projects/{pid}/sessoes').json()['sessions']
        # Registros: a análise deixou início, etapas e fim; uma falha deixa o rastreamento.
        ev=c.get(f'/api/projects/{pid}/registros').json()['eventos'];kinds=[e['evento'] for e in ev]
        assert kinds[0]=='inicio' and 'etapa' in kinds and kinds[-1]=='fim' and ev[0]['tipo']=='analyze'
        (junction/'x').mkdir(exist_ok=True)
        from app import store
        d=store.directory(pid);cfgf=d/'config.json';good=cfgf.read_text(encoding='utf-8')
        jid=c.post(f'/api/projects/{pid}/preview').json()['id'];(d/'input.dxf').write_bytes(b'0\nSECTION\nquebrado');worker.run(jid)
        err=c.get(f'/api/projects/{pid}/registros',params={'tipo':'erros'}).json()['eventos'];assert err and err[-1]['evento']=='falha_tarefa' and 'Traceback' in err[-1]['rastreamento']
        assert c.post(f'/api/projects/{pid}/registros/erro_tela',json={'mensagem':'TypeError: x is null','pilha':'at draw (app.js:1)'}).status_code==200
        for _ in range(7):c.post(f'/api/projects/{pid}/registros/erro_tela',json={'mensagem':'repetido'})
        err=c.get(f'/api/projects/{pid}/registros',params={'tipo':'erros'}).json()['eventos'];assert sum(e.get('mensagem')=='repetido' for e in err)==5
        md=c.get(f'/api/projects/{pid}/prompt_ia.md').text
        assert '# Reproduzir a geração do vídeo' in md and '"gantries"' in md and 'input.dxf' in md and 'falha_tarefa' in md and 'Como reproduzir' in md
        z=zipfile.ZipFile(io.BytesIO(c.get(f'/api/projects/{pid}/registros.zip').content));assert {'logs/execucao.jsonl','logs/erros.jsonl','config.json','prompt_ia.md'}<=set(z.namelist())
        assert c.delete(f'/api/projects/{pid}/registros').json()['removed']>=2 and not c.get(f'/api/projects/{pid}/registros').json()['eventos']

def free_port():
    import socket
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_126_ui(junction,tmp_path):
    pw=pytest.importorskip('playwright.sync_api')
    import os,threading,uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60);pid=c.post('/api/projects',json=S(highlights=[{'id':'h1','name':'Poste','point':{'x':500250,'y':7800004}}]).model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    (tmp_path/'placa.png').write_bytes(png())
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
            # Tela ampla com divisor; o divisor muda a largura do painel.
            assert ev("document.body.classList.contains('wide') && !!document.getElementById('splitter')")
            sp=page.locator('#splitter').bounding_box();page.mouse.move(sp['x']+4,sp['y']+200);page.mouse.down();page.mouse.move(sp['x']+84,sp['y']+200,steps=4);page.mouse.up()
            assert 470<=ev("parseInt(getComputedStyle(document.documentElement).getPropertyValue('--side'))")<=520
            ev("(()=>{const [ix,iy]=worldToImg({x:500220,y:7800000});view.s=Math.min(240,canvas.width*mpp()/140);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            page.locator('#canvas').scroll_into_view_if_needed()
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Pórtico: dois cliques, imagem pelo painel, rótulos em português.
            page.click('#toolbar button[data-tool="gantry"]');page.fill('#gtName','Pórtico Saída 12')
            page.mouse.click(*W2C(500220,7799990));page.mouse.click(*W2C(500220,7800010))
            assert ev('M.gantries.length')==1 and ev('M.gantries[0].name')=='Pórtico Saída 12' and ev('sel.key')=='gantries'
            assert 'Altura (m)' in page.inner_text('#propPanel') and 'Mostrar a partir de (s)' in page.inner_text('#propPanel')
            page.set_input_files('#propPanel input[data-ppimg]',str(tmp_path/'placa.png'));page.wait_for_function('M.gantries[0].image.length>10')
            page.fill('#propPanel [data-pp="start_s"]','4');page.press('#propPanel [data-pp="start_s"]','Enter');assert ev('M.gantries[0].start_s')==4
            page.wait_for_timeout(1300);conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['gantries'][0]['image'].endswith('.png') and conf['gantries'][0]['start_s']==4
            # Atributos em lote: copia o pórtico e altera a altura dos dois de uma vez.
            cl=page.locator('#cmdLine');cl.fill('CO');cl.press('Enter');cl.fill('0,0');cl.press('Enter');cl.fill('@30,0');cl.press('Enter')
            ev("(()=>{selSet=[{key:'gantries',i:0},{key:'gantries',i:1}];sel=selSet[1];showProps()})()")
            assert 'Atributos em comum' in page.inner_text('#propPanel')
            page.fill('#propPanel [data-mpp="height_m"]','9');page.press('#propPanel [data-mpp="height_m"]','Enter');assert ev('M.gantries.map(g=>g.height_m)')==[9,9]
            # Menu de contexto (botão direito) com ajuda; Esc fecha sem pedir confirmação.
            x,y=W2C(500220,7800000);page.mouse.click(x,y,button='right');page.wait_for_selector('#ctxMenu:not([hidden])')
            assert 'Atributos em comum' in page.inner_text('#ctxMenu') and 'Enquadrar tudo' not in page.inner_text('#ctxMenu')   # 1.27: com seleção, só os comandos da seleção
            page.hover('#ctxMenu .it:has-text("Girar")');assert 'graus' in page.inner_text('#ctxMenu .ctxHelp')
            page.keyboard.press('Escape');assert ev("document.getElementById('ctxMenu').hidden") and not ev("document.getElementById('confirmDlg').open")
            ev("(()=>{sel=null;selSet=[];showProps()})()")
            page.mouse.click(x,y,button='right');page.wait_for_selector('#ctxMenu:not([hidden])');page.click('#ctxMenu .it:has-text("Inserir")');assert 'Pórtico' in page.inner_text('#ctxMenu')
            page.click('#ctxMenu .it:has-text("Destaque")');assert ev('tool')=='highlight'
            page.keyboard.press('Escape');page.wait_for_selector('#confirmDlg[open]');page.keyboard.press('Enter');assert ev('tool')=='pan'
            # Camadas: ocultar e congelar (editor imediato).
            ev("(()=>{const d=document.getElementById('layers').closest('details');d.open=true;d.closest('section').classList.remove('collapsed')})()")
            n0=ev('vecPaths.pavement?vecPaths.pavement.n:0');assert n0>0
            page.click('[data-lyh="PAVIMENTO"]');assert ev("cfg.hidden_layers")==['PAVIMENTO'] and not ev('vecPaths.pavement')
            page.click('[data-lyh="PAVIMENTO"]');page.click('[data-lyf="PAVIMENTO"]');assert ev("cfg.frozen_layers")==['PAVIMENTO'] and ev('vecPaths.frozen.n')==n0 and not ev('vecPaths.pavement')
            page.click('[data-lyf="PAVIMENTO"]');assert ev('vecPaths.pavement.n')==n0
            # Alinhamento selecionando a linha do desenho; Enter confirma.
            page.click('#toolbar button[data-tool="align"]');page.select_option('#alMode','linha')
            page.mouse.click(*W2C(500150,7800000.3));page.wait_for_function("draft&&draft.type==='align'&&draft.pts.length===2")
            page.keyboard.press('Enter');page.wait_for_function("M.custom_axis&&M.custom_axis.source==='linha'")
            assert ev('M.custom_axis.smooth') is False and ev('M.custom_axis.points.map(p=>[p.x,p.y])')==[[500000,7800000],[500400,7800000]]
            ev("setTool('pan')")
            # Linha de comando: lista de comandos e histórico.
            cl.fill('?');cl.press('Enter');page.wait_for_selector('#cmdHelpDlg[open]');assert 'PINTAR' in page.inner_text('#cmdHelpDlg');page.keyboard.press('Escape')
            cl.focus();page.keyboard.press('ArrowUp');assert cl.input_value()=='?'
            # Sessões: salvar, mudar a vista, restaurar.
            page.click('#sessSave');page.wait_for_selector('#inputDlg[open]');page.fill('#inputValue','Revisão do pórtico');page.keyboard.press('Enter');page.wait_for_function("[...document.querySelectorAll('#sessList option')].some(o=>o.value==='Revisão do pórtico')")
            c0=ev('C2W(canvas.width/2,canvas.height/2)');ev("(()=>{view.ox+=400;draw()})()")
            page.select_option('#sessList','Revisão do pórtico');page.click('#sessLoad');page.wait_for_timeout(300)
            c1=ev('C2W(canvas.width/2,canvas.height/2)');assert abs(c1['x']-c0['x'])<.5 and abs(c1['y']-c0['y'])<.5
            # Fluidez: durante a roda do mouse os quadros são agrupados; ao parar, desenho completo.
            page.locator('#canvas').scroll_into_view_if_needed();bx=page.locator('#canvas').bounding_box();page.mouse.move(bx['x']+bx['width']/2,bx['y']+bx['height']/2);[page.mouse.wheel(0,-60) for _ in range(5)];assert ev('drawStats().gesture') is True
            page.wait_for_timeout(400);assert ev('drawStats().gesture') is False
            # Registros: diálogo com a análise e erro da tela registrado.
            ev("msg('Teste de erro de tela',true)");ev("runCommand('LOG')");page.wait_for_selector('#logDlg[open]');assert 'analyze' in page.inner_text('#logView')
            page.click('#logDlg [data-lg="erros"]');page.wait_for_function("document.getElementById('logView').textContent.includes('Teste de erro de tela')");page.click('#logClose')
            md=c.get(f'/api/projects/{pid}/prompt_ia.md').text;assert 'Pórtico Saída 12' in md
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
