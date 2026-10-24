"""1.24: Enter/Esc com confirmação, menus, seleção múltipla e comandos CAD (copiar, girar, escalar, espelhar,
offset), snap exato, informação na tela, fluxos pela seleção, texturas editáveis, leitura automática das
hachuras do DXF e motor de montagem otimizado."""
import os,json,socket,threading,time
import numpy as np,ezdxf,pytest,cv2
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})

def test_texture_lut_default_and_effect():
    from app import visual
    assert visual.texture_lut({})is None and visual.texture_lut({'pista_nova':{'grao':1,'tom':1,'remendos':1,'fissuras':1,'brilho':0}}) is None
    L=visual.texture_lut({'pista_nova':{'grao':2,'tom':0,'remendos':1,'fissuras':1,'brilho':.1}})
    assert L['grain'][1]==pytest.approx(2*visual._LUT_GRAIN[1]) and L['tone'][1]==0 and L['bright'][1]==pytest.approx(.1)
    assert visual._LUT_GRAIN[1]==pytest.approx(.075)       # o padrão não foi alterado
    im=np.full((120,160,3),90,np.uint8);surf=np.ones((120,160),np.uint8);A=np.array([[.02,0,700000.],[0,-.02,7800000.]]);v=np.ones((120,160),bool)
    a=im.copy();visual.shade_surface(a,surf,A,.02,v,True);b=im.copy();visual.shade_surface(b,surf,A,.02,v,True,lut=L)
    assert b.mean()>a.mean()+5 and b.std()>a.std()

def test_texture_preview_endpoint_and_frame(junction):
    from app.server import app
    c=TestClient(app)
    r=c.get('/api/texture_preview.png',params={'surface':'pista_existente','p':json.dumps({'fissuras':3})});assert r.status_code==200 and r.content[:4]==b'\x89PNG'
    assert c.get('/api/texture_preview.png',params={'surface':'xx'}).status_code==422
    assert c.get('/api/texture_preview.png',params={'surface':'pista_nova','p':json.dumps({'grao':9})}).status_code==422
    from app.render import Scene
    base=dict(imagery='neutral',width=1280)
    a=Scene(junction,S(**base)).frame(0,view=((500200,7799996),30))[0].astype(int)
    b=Scene(junction,S(**base,texture_params={'pista_nova':{'brilho':.25}})).frame(0,view=((500200,7799996),30))[0].astype(int)
    assert b[300:400,500:700].mean()>a[300:400,500:700].mean()+8

def hatch_dxf(tmp_path):
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','HACH_CONCRETO','X1']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(color=8,dxfattribs={'layer':'HACH_CONCRETO'});h.set_pattern_fill('AR-CONC',scale=1);h.paths.add_polyline_path([(500000,7799991),(500150,7799991),(500150,7800009),(500000,7800009)],is_closed=True)
    h=m.add_hatch(color=3,dxfattribs={'layer':'X1'});h.paths.add_polyline_path([(500150,7799991),(500300,7799991),(500300,7800009),(500150,7800009)],is_closed=True)
    d.saveas(tmp_path/'input.dxf');return tmp_path

def test_hatch_signatures_suggestions_and_roles(tmp_path):
    from app.geometry import analyze
    d=hatch_dxf(tmp_path);lay={'axis':['EIXO']}
    items,_,_,_,rep=analyze(d,S(layers=lay,hatch_auto=False))
    H={h['layer']:h for h in rep['hatches']};assert set(H)=={'HACH_CONCRETO','X1'}
    c=H['HACH_CONCRETO'];assert c['pattern']=='AR-CONC' and c['suggested_role']=='pavement' and c['suggested_material']=='rigido' and c['area_m2']==pytest.approx(2700,rel=.01) and c['count']==1
    assert H['X1']['suggested_role'] is None and not [e for e in items if e['role']=='pavement']
    # Automático: só as hachuras com sugestão entram, com material.
    items,_,_,_,rep=analyze(d,S(layers=lay,hatch_auto=True))
    pv=[e for e in items if e['role']=='pavement'];assert len(pv)==1 and pv[0]['material']=='rigido' and {h['layer']:h for h in rep['hatches']}['HACH_CONCRETO']['auto_applied']
    # Escolha do usuário pela assinatura (vale mesmo com a camada sem tipo) e “ignorar”.
    sig=H['X1']['sig'];items=analyze(d,S(layers=lay,hatch_auto=True,hatch_roles={sig:{'role':'existing_pavement','material':'flexivel'}}))[0]
    ex=[e for e in items if e['role']=='existing_pavement'];assert len(ex)==1 and ex[0]['material']=='flexivel'
    items=analyze(d,S(layers=lay,hatch_auto=True,hatch_roles={H['HACH_CONCRETO']['sig']:{'role':'ignore'}}))[0];assert not [e for e in items if e['role']=='pavement']
    old=Settings.model_validate({'schema_version':21,'km_start_m':0,'km_end_m':100});assert old.hatch_auto is False and old.schema_version>=22

def test_exact_snap_points(junction):
    from app.server import app
    import app.store as store
    with TestClient(app) as c:
        pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
        j=c.post(f'/api/projects/{pid}/analyze').json()
        from app import worker;worker.run(j['id'])
        r=c.get(f'/api/projects/{pid}/snap',params={'x0':500180,'y0':7800000,'x1':500220,'y1':7800130}).json()
        assert r['available'] and [500190.0,7800009.0] in r['v'] and [500200.0,7800120.0] in r['m']
        assert c.get(f'/api/projects/{pid}/snap',params={'x0':0,'y0':0,'x1':10000,'y1':10000}).status_code==422

def test_render_engine_skips_base_when_detail_covers(junction):
    """Otimizado: mesmos quadros quando o detalhe cobre a tela; 'anterior' reproduz o caminho antigo."""
    from app.render import Scene
    sc=Scene(junction,S(imagery='neutral',width=1280));sc2=Scene(junction,S(imagery='neutral',width=1280,render_engine='anterior'))
    for v in (((500200,7800000),300),((500200,7800000),2500)):
        a=sc.frame(0,view=v)[0];b=sc2.frame(0,view=v)[0]
        assert np.abs(a.astype(int)-b.astype(int)).mean()<2.5

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_enter_esc_selection_commands_flows_textures(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    cfg={**settings().model_dump(),'duration_s':10,'signs':[{'id':'s1','code':'R-1','point':{'x':500200,'y':7800005}},{'id':'s2','code':'I','point':{'x':500210,'y':7800005}}],
         'hatch_areas':[{'id':'h1','name':'Z1','points':[{'x':500250,'y':7799992},{'x':500270,'y':7799992},{'x':500270,'y':7799998},{'x':500250,'y':7799998}]}]}
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
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1200})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && editor && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            # Menus: barra de seções e recolher/expandir.
            assert ev("document.querySelectorAll('#secNav button').length")>=8
            ev("document.querySelector('#sec_0 > h2, main section:first-of-type > h2').click()");assert ev("document.querySelector('main section').classList.contains('collapsed')")
            ev("document.querySelector('main section > h2').click()")
            ev("(()=>{const [ix,iy]=worldToImg({x:500230,y:7800000});view.s=Math.min(240,canvas.width*mpp()/120);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            page.locator('#canvas').scroll_into_view_if_needed()
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Esc pede confirmação: “Continuar” mantém o comando; “Cancelar” sai.
            page.click('#toolbar button[data-tool="pavarea"]');page.mouse.click(*W2C(500170,7799995));page.keyboard.press('Escape')
            page.wait_for_selector('#confirmDlg[open]');assert 'ponto' in ev("document.getElementById('confirmText').textContent")
            page.click('#confirmNo');assert ev('tool')=='pavarea' and ev('draft.pts.length')==1
            page.keyboard.press('Escape');page.wait_for_selector('#confirmDlg[open]');page.keyboard.press('Enter');assert ev('tool')=='pan' and ev('draft')is None
            # Enter num campo das opções da ferramenta aceita o valor e volta para a tela.
            page.click('#toolbar button[data-tool="shoulder"]');page.fill('#shWidth','3.2');page.press('#shWidth','Enter');assert ev('document.activeElement.id')=='canvas' and ev('tool')=='shoulder'
            page.keyboard.press('Escape');page.wait_for_selector('#confirmDlg[open]');page.keyboard.press('Enter')
            # Seleção por janela (Ctrl+arrastar da esquerda para a direita) pega as duas placas.
            page.keyboard.down('Control');page.mouse.move(*W2C(500195,7800010));page.mouse.down();page.mouse.move(*W2C(500215,7800001),steps=5);page.mouse.up();page.keyboard.up('Control')
            assert ev('allSelected().length')==2 and 'Seleção · 2 objetos' in ev("document.getElementById('propPanel').textContent")
            cl=page.locator('#cmdLine')
            cl.fill('CO');cl.press('Enter');cl.fill('0,0');cl.press('Enter');cl.fill('@0,-20');cl.press('Enter')
            assert ev('M.signs.length')==4 and abs(ev('M.signs[2].point.y')-7799985)<1e-9 and ev('M.signs[2].id')!='s1'
            assert ev('selObjs().length')==0;ev("(()=>{selSet=[{key:'signs',i:2},{key:'signs',i:3}];sel=selSet[1];showProps()})()");cl.fill('RO');cl.press('Enter');cl.fill('500200,7799985');cl.press('Enter');cl.fill('90');cl.press('Enter')
            P=sorted((round(q['x'],6),round(q['y'],6)) for q in ev('M.signs.slice(2).map(s=>s.point)'));assert P==[(500200,7799985),(500200,7799995)],P
            ev("(()=>{selSet=[{key:'signs',i:2},{key:'signs',i:3}];sel=selSet[1];showProps()})()");cl.fill('SC');cl.press('Enter');cl.fill('500200,7799985');cl.press('Enter');cl.fill('2');cl.press('Enter')
            P=sorted((round(q['x'],6),round(q['y'],6)) for q in ev('M.signs.slice(2).map(s=>s.point)'));assert P==[(500200,7799985),(500200,7800005)],P
            ev("(()=>{selSet=[{key:'signs',i:2},{key:'signs',i:3}];sel=selSet[1];showProps()})()");cl.fill('MI');cl.press('Enter');cl.fill('500000,7800000');cl.press('Enter');cl.fill('500400,7800000');cl.press('Enter')
            assert ev('M.signs.length')==6;P=sorted(round(q['y'],6) for q in ev('M.signs.slice(4).map(s=>s.point)'));assert P==[7799995,7800015],P
            ev('(()=>{sel={key:"signs",i:5};selSet=[{key:"signs",i:4},{key:"signs",i:5}];showProps()})()');page.focus('#canvas');page.keyboard.press('Delete');assert ev('M.signs.length')==4
            # OFFSET do zebrado (área): paralela 1 m para fora.
            ev('(()=>{sel={key:"hatch_areas",i:0};selSet=[];showProps()})()');assert 'área 120' in ev("document.getElementById('propPanel').textContent")
            cl.fill('OF');cl.press('Enter');cl.fill('1');cl.press('Enter');cl.fill('500260,7800020');cl.press('Enter')
            P=ev('M.hatch_areas[1].points');xs=[q['x'] for q in P];ys=[q['y'] for q in P];assert abs(min(xs)-500249)<1e-6 and abs(max(ys)-7799999)<1e-6
            # Fluxos: clicar numa trajetória seleciona e permite inverter.
            ev('(()=>{sel=null;selSet=[];showProps()})()');seg=ev('(()=>{const s=editor.segments.find(s=>s.kind==="main")||editor.segments[0];const q=P(s.points[Math.floor(s.points.length/2)]);const [ix,iy]=worldToImg(q);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw();return {id:s.id,mid:[q.x,q.y]}})()')
            page.mouse.click(*W2C(seg['mid'][0],seg['mid'][1]))
            assert ev('selSeg&&selSeg.id')==seg['id'];n0=ev('M.flow_overrides.length');page.click('#propPanel [data-seg="reverse"]');assert ev('M.flow_overrides.length')==n0+1
            # Texturas: alterar um controle grava os parâmetros e atualiza a amostra.
            ev("(()=>{const i=document.querySelector('[data-tex=pista_nova] input[data-f=grao]');i.value='2';i.dispatchEvent(new Event('input',{bubbles:true}));i.dispatchEvent(new Event('change',{bubbles:true}))})()")
            page.wait_for_timeout(1500);conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['texture_params']['pista_nova']['grao']==2
            assert 'grao' in ev("decodeURIComponent(document.querySelector('[data-tex=pista_nova] img').src)")
            assert len(conf['signs'])==4 and len(conf['hatch_areas'])==2
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
