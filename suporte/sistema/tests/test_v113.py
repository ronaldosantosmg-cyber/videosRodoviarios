"""1.13: transição dia/noite (faróis, lanternas, sinalização refletiva) e duas janelas sincronizadas."""
import os,socket,threading,time
import numpy as np,pytest,cv2
from test_workflow import settings,wait
from test_v110 import junction
from app.models import Settings
from app import visual

def S(**kw):return Settings(**{**settings().model_dump(),**kw})

def test_night_factor_transition():
    s=S(day_night='transition',night_start_s=10,night_transition_s=4,duration_s=30)
    f=[visual.night_factor(s,t) for t in (0,10,11,12,13,14,20)]
    assert f[0]==0 and f[1]==0 and 0<f[2]<f[3]<f[4]<1 and f[5]==1 and f[6]==1
    assert visual.night_factor(S(),12)==0 and visual.night_factor(S(day_night='night'),0)==1

def test_night_darkens_scene_and_lights_signage_and_vehicles(junction):
    from app.render import Scene
    day=Scene(junction,S(duration_s=30,traffic_density=3));night=Scene(junction,S(duration_s=30,traffic_density=3,day_night='night'))
    v=((500200,7800000),160);t=20.
    a=day.frame(t,view=v)[0].astype(float);b=night.frame(t,view=v)[0].astype(float)
    hdr=int(157*day.scale);ftr=day.H-int(154*day.scale)
    assert b[hdr:ftr].mean()<a[hdr:ftr].mean()*.55  # cena escura
    # Sinalização: pixels da pintura continuam claros à noite.
    m=day.markings;cam=np.array(v[0]);near=np.linalg.norm(m.mean(1)-cam,axis=1)<60
    q=day.screen(m[near].mean(1),cam,v[1]).astype(int);q=q[(q[:,1]>hdr+5)&(q[:,1]<ftr-5)&(q[:,0]>5)&(q[:,0]<day.W-5)]
    lum=lambda im,p:im[p[:,1],p[:,0]].mean(1)
    assert np.median(lum(b,q))>np.median(lum(b,q+np.array([0,25])))+30
    # Veículos: faróis e lanternas acendem (pixels quase brancos e vermelhos fortes só à noite).
    items=list(night.traffic_iter(t));assert items
    red=lambda im:((im[:,:,0]>200)&(im[:,:,1]<90)&(im[:,:,2]<80))[hdr:ftr].sum()
    assert red(b)>red(a)
    # 'Dia' sem alteração: fator 0 não aplica nada (mesmo quadro duas vezes).
    assert np.array_equal(day.frame(t,view=v)[0],Scene(junction,S(duration_s=30,traffic_density=3)).frame(t,view=v)[0])

def test_schema_v12():
    s=Settings.model_validate({'schema_version':11,'km_start_m':0,'km_end_m':100})
    assert s.schema_version>=12 and s.day_night=='off' and s.night_signage_glow

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_two_windows_stay_in_sync(junction):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
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
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);ctx=b.new_context(viewport={'width':1400,'height':1000})
            ctx.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            ctx.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            cfgw=ctx.new_page();vis=ctx.new_page()
            for pg in (cfgw,vis):
                pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            cfgw.goto(base+'/?janela=config');vis.goto(base+'/?janela=visual')
            for pg in (cfgw,vis):pg.wait_for_function('typeof pid!=="undefined" && pid && cfg && cfg.name',timeout=20000)
            vis.wait_for_function('typeof geo!=="undefined" && geo && ready()',timeout=20000)
            assert not cfgw.is_visible('#editorSection') and vis.is_visible('#editorSection') and not vis.is_visible('#projects')
            assert 'configuração' in cfgw.inner_text('#winLabel') and 'visualização' in vis.inner_text('#winLabel')
            # Marcação feita na visualização chega à configuração (sem ser sobrescrita no próximo salvamento).
            vis.evaluate("checkpoint();M.cities.push({id:'c1',name:'Vila Sync',point:{x:500200,y:7800030},kind:'',population:null,source:'manual',show:true});changed('ok')")
            cfgw.wait_for_function("M.cities.length===1 && M.cities[0].name==='Vila Sync'",timeout=10000)
            # Campo alterado na configuração chega à visualização e não apaga a marcação.
            cfgw.fill('#name','Trecho Sincronizado');cfgw.dispatch_event('#name','change');cfgw.evaluate('scheduleSave()')
            vis.wait_for_function("cfg.name==='Trecho Sincronizado'",timeout=10000)
            assert vis.evaluate('M.cities.length')==1
            conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['name']=='Trecho Sincronizado' and conf['cities'][0]['name']=='Vila Sync'
            # Processamento iniciado na configuração aparece na visualização.
            cfgw.evaluate("start('analyze')");cfgw.wait_for_function("lastPolled!==''",timeout=10000);jid=cfgw.evaluate('lastPolled')
            vis.wait_for_function(f"lastPolled==='{jid}'",timeout=30000)
            cfgw.wait_for_function("task===''",timeout=60000)
            # Botão "Janela única" volta ao modo normal.
            vis.click('#oneWindow');vis.wait_for_function("document.body.dataset.janela==='unica'",timeout=10000)
            assert vis.is_visible('#projects') and vis.is_visible('#editorSection')
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors
