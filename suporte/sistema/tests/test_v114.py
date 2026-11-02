"""1.14: camadas sem regras fixas (perfis reutilizáveis), novos tipos (bordo, hidrografia, talude),
cores por tipo, prévia por camada e setas giráveis que reorientam o fluxo."""
import json,os,socket,threading,time
import numpy as np,ezdxf,pytest,cv2
from fastapi.testclient import TestClient
from test_workflow import settings,wait
from test_v110 import junction
from app.models import Settings
from app import layer_profiles as LP

def S(**kw):return Settings(**{**settings().model_dump(),**kw})

TH57=['GE_HZ-EIXORODPROJ','F1-HZ-EIXO','GE_HZ-HPAVPROJ','GE_HZ-HPAVEXIST','GE_HZ-HACOSTAMENTOPROJ','GE_SC-HCANTEIRO','GE_SC-HNEWJERSEY',
      'GE_HZ-HOAEPROJET','F1-HZ-OFFSET-CORTE','F1-HZ-OFFSET-ATERRO','faixa_dominio_nova381']

def test_builtin_profile_and_wildcards():
    m=LP.apply(TH57,LP.BUILTIN)
    assert set(m['axis'])=={'GE_HZ-EIXORODPROJ','F1-HZ-EIXO'} and m['pavement']==['GE_HZ-HPAVPROJ'] and m['existing_pavement']==['GE_HZ-HPAVEXIST']
    assert m['shoulder']==['GE_HZ-HACOSTAMENTOPROJ'] and m['median']==['GE_SC-HCANTEIRO'] and m['barrier']==['GE_SC-HNEWJERSEY'] and m['oae']==['GE_HZ-HOAEPROJET']
    assert m['cut']==['F1-HZ-OFFSET-CORTE'] and m['fill']==['F1-HZ-OFFSET-ATERRO'] and m['domain']==['faixa_dominio_nova381']
    assert LP.role_for('Hidrografia_Rios',LP.BUILTIN['rules'])=='water' and LP.role_for('LBO_BORDO',LP.BUILTIN['rules'])=='edge_line'
    assert LP.role_for('TERRITORIO',LP.BUILTIN['rules']) is None  # 'RIO' só como palavra
    assert LP.matches('pista-?xist*','PISTA-EXISTENTE_01') and not LP.matches('PISTA','PISTA2') and LP.matches('*ção*','LOCACAO_X')

def test_user_profiles_save_list_delete(tmp_path):
    with pytest.raises(ValueError):LP.save(tmp_path,{'name':'','rules':[{'pattern':'A','role':'axis'}]})
    with pytest.raises(ValueError):LP.save(tmp_path,{'name':'X','rules':[{'pattern':'A','role':'nada'}]})
    LP.save(tmp_path,{'name':'Empresa','rules':[{'pattern':'C-EIXO*','role':'axis'},{'pattern':'C-PAV-*','role':'pavement'}]})
    names=[p['name'] for p in LP.load(tmp_path)];assert names[0]==LP.BUILTIN['name'] and 'Empresa' in names
    assert LP.apply(['C-EIXO-01','C-PAV-NOVO','OUTRA'],LP.load(tmp_path)[1])=={'axis':['C-EIXO-01'],'pavement':['C-PAV-NOVO']}
    assert LP.delete(tmp_path,'Empresa') and not LP.delete(tmp_path,LP.BUILTIN['name'])

def test_migration_makes_existing_pavement_explicit():
    s=Settings.model_validate({'schema_version':12,'km_start_m':0,'km_end_m':100,'layers':{'pavement':['GE_HZ-HPAVPROJ','GE_HZ-HPAVEXIST']}})
    assert s.layers['pavement']==['GE_HZ-HPAVPROJ'] and s.layers['existing_pavement']==['GE_HZ-HPAVEXIST'] and s.schema_version>=13
    # Mapeamento explícito agora é respeitado: 'pavement' numa camada com EXIST continua pista projetada.
    s2=Settings.model_validate({**s.model_dump(),'layers':{'pavement':['X_EXIST']}});assert s2.layers['pavement']==['X_EXIST']

@pytest.fixture
def odd(tmp_path):
    """Modelo de outra empresa: nomes de camada sem nenhuma palavra conhecida."""
    d=ezdxf.new();m=d.modelspace()
    for l in ['L01','L02','L03','L04','L05','L06']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'L01'})
    h=m.add_hatch(dxfattribs={'layer':'L02'});h.paths.add_polyline_path([(500000,7799991),(500300,7799991),(500300,7800009),(500000,7800009)],is_closed=True)
    h=m.add_hatch(dxfattribs={'layer':'L05'});h.paths.add_polyline_path([(500100,7800030),(500200,7800030),(500200,7800060),(500100,7800060)],is_closed=True)
    for y in (-8.6,8.6):m.add_lwpolyline([(500000,7800000+y),(500300,7800000+y)],dxfattribs={'layer':'L06'})
    for y in (-30,30):m.add_lwpolyline([(499990,7800000+y),(500310,7800000+y)],dxfattribs={'layer':'L03'})
    m.add_text('nota',dxfattribs={'layer':'L04'})
    d.saveas(tmp_path/'input.dxf');return tmp_path

def test_other_model_works_only_through_mapping(odd):
    from app.render import Scene
    with pytest.raises(ValueError):Scene(odd,S())  # nada reconhecido: sem eixo
    layers={'axis':['L01'],'pavement':['L02'],'domain':['L03'],'water':['L05'],'edge_line':['L06']}
    sc=Scene(odd,S(layers=layers,traffic=False))
    roles={e['role'] for e in sc.items};assert {'axis','pavement','domain','water','edge_line'}<=roles
    # Hidrografia do DXF entra na pintura de água.
    assert sc.hydro.polygons and 'DXF' in sc.hydro.source
    v=((500150,7800040),120);im=sc.frame(0,view=v)[0].astype(int)
    q=sc.screen(np.array([[500150,7800045]]),np.array(v[0]),v[1])[0].astype(int);px=im[q[1],q[0]]
    plain=Scene(odd,S(layers={k:v for k,v in layers.items() if k!='water'},traffic=False)).frame(0,view=v)[0].astype(int)[q[1],q[0]]
    assert px[2]-px[0]>plain[2]-plain[0]+10  # mais azul
    # Bordos do DXF substituem as linhas calculadas pelo contorno.
    net=sc.network;edges=[(a+b)/2 for (a,b,_),s in zip(net.markings,net.mark_src) if s==-2]
    assert edges and all(abs(abs(p[1]-7800000)-8.6)<.01 for p in edges)

def test_role_colors_change_overlay(junction):
    from app.render import Scene
    a=Scene(junction,S(traffic=False));b=Scene(junction,S(traffic=False,role_colors={'pavement':'#aa2222'}))
    v=((500200,7800000),120);fa=a.frame(0,view=v)[0].astype(int);fb=b.frame(0,view=v)[0].astype(int)
    q=a.screen(np.array([[500200,7799995]]),np.array(v[0]),v[1])[0].astype(int)
    assert fb[q[1],q[0],0]-fb[q[1],q[0],2]>fa[q[1],q[0],0]-fa[q[1],q[0],2]+20
    with pytest.raises(ValueError):S(role_colors={'pavement':'vermelho'})

def test_api_profiles_preview_and_apply(odd):
    with TestClient(app_()) as c:
        r=c.get('/api/layer_profiles').json();assert r['profiles'][0]['builtin'] and 'water' in r['roles']
        assert c.post('/api/layer_profiles',json={'name':'Outra empresa','rules':[{'pattern':'L01','role':'axis'},{'pattern':'L0[2]','role':'pavement'},{'pattern':'L02','role':'pavement'},{'pattern':'L03','role':'domain'}]}).status_code==200
        assert c.post('/api/layer_profiles',json={'name':'x','rules':[]}).status_code==422
        pid=c.post('/api/projects',json={**settings().model_dump(),'layers':{'axis':['L01'],'pavement':['L02']}}).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(odd/'input.dxf').read_bytes())})
        assert c.post(f'/api/projects/{pid}/layer_profiles/apply',json={'name':'Outra empresa'}).status_code==409
        assert c.get(f'/api/projects/{pid}/layers_preview.json').status_code==404
        j=wait(c,c.post(f'/api/projects/{pid}/analyze').json()['id']);assert j['state']=='done',j
        r=c.post(f'/api/projects/{pid}/layer_profiles/apply',json={'name':'Outra empresa'}).json()
        assert r['layers']=={'axis':['L01'],'pavement':['L02'],'domain':['L03']} and r['matched']==3 and r['total']==6
        prev=c.get(f'/api/projects/{pid}/layers_preview.json').json()
        assert prev['L03']['role'] is None and prev['L03']['p'] and prev['L01']['role']=='axis' and 'L04' not in prev  # texto não tem geometria
        assert c.delete('/api/layer_profiles/'+'Outra empresa').status_code==200 and c.delete('/api/layer_profiles/'+LP.BUILTIN['name']).status_code==404

def app_():
    from app.server import app
    return app

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_rotate_arrow_and_layer_tools(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    app=app_();port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
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
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('dialog',lambda d:d.accept('Perfil Teste'))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && editor && ready() && editor.arrows.length>0',timeout=20000)
            ev=page.evaluate;ev('fitView()')
            # Seta escolhida: a de uma via principal (pista de mão única no desenho de teste).
            a=ev("editor.arrows.find(a=>Math.abs(a[3])<.2)");assert a
            ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{a[0]},y:{a[1]}}});view.s=Math.min(60,canvas.width*mpp()/80);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}})()")
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            page.click('#toolbar button[data-tool="arrowrot"]');page.mouse.click(*W2C(a[0],a[1]))
            dm=ev('M.direction_marks');assert len(dm)==1
            v=np.array([dm[0]['end']['x']-dm[0]['start']['x'],dm[0]['end']['y']-dm[0]['start']['y']]);assert float(v@np.array(a[2:4]))<0  # invertida
            ev('undo()');assert ev('M.direction_marks.length')==0;ev('redo()');assert ev('M.direction_marks.length')==1
            page.click('#updFlows');page.wait_for_function("document.getElementById('message').textContent.includes('atualizados')",timeout=60000)
            e=c.get(f'/api/projects/{pid}/editor.json').json();            # O trecho da via onde estava a seta (até a próxima junção) passa a ter o sentido oposto.
            seg=min(e['segments'],key=lambda g:min(np.hypot(px-a[0],py-a[1]) for px,py in g['points']))
            xs=[px for px,_ in seg['points']];near=[x for x in e['arrows'] if min(xs)<=x[0]<=max(xs) and abs(x[3])<.2]
            assert near and all(np.dot(x[2:4],a[2:4])<0 for x in near)
            # Perfil de camadas: salvar o mapeamento atual e aplicar; “Ver” destaca a camada.
            ev("document.getElementById('layers').closest('details').open=true")
            page.click('#profileSave');page.wait_for_selector('#inputDlg[open]');page.fill('#inputValue','Perfil Teste');page.keyboard.press('Enter');page.wait_for_function("[...document.querySelectorAll('#layerProfile option')].some(o=>o.value==='Perfil Teste')",timeout=10000)
            page.select_option('#layerProfile','Perfil Teste');page.click('#profileApply');page.wait_for_function("document.getElementById('message').textContent.includes('Perfil aplicado')",timeout=10000)
            page.click('button[data-showlayer="PAVIMENTO"]');page.wait_for_function("layerShow && layerShow.name==='PAVIMENTO'",timeout=10000)
            page.select_option('select[data-layer="PAVIMENTO"]','existing_pavement');ev('scheduleSave()');page.wait_for_timeout(1300)
            cfg=c.get(f'/api/projects/{pid}').json()['config'];assert cfg['layers'].get('existing_pavement')==['PAVIMENTO'] and len(cfg['direction_marks'])==1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
