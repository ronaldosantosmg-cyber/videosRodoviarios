"""1.21: pavimento flexível (asfalto) × rígido (concreto com juntas a cada 5 m), vídeo técnico × artístico e
contraste projeto × imagem."""
import os,json,socket,threading,time
import numpy as np,ezdxf,pytest,cv2
from shapely.geometry import Polygon
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})

def test_materials_from_layer_names_defaults_and_areas(tmp_path):
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAV_CONCRETO','PAV_CBUQ','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
    for lay,x0 in (('PAV_CONCRETO',500000),('PAV_CBUQ',500100),('PAVIMENTO',500200)):
        h=m.add_hatch(dxfattribs={'layer':lay});h.paths.add_polyline_path([(x0,7799991),(x0+100,7799991),(x0+100,7800009),(x0,7800009)],is_closed=True)
    d.saveas(tmp_path/'input.dxf')
    from app.geometry import analyze
    lay={'axis':['EIXO'],'pavement':['PAV_CONCRETO','PAV_CBUQ','PAVIMENTO']}
    mat=lambda items:{e['layer']:e['material'] for e in items if e['role']=='pavement'}
    assert mat(analyze(tmp_path,S(layers=lay))[0])=={'PAV_CONCRETO':'rigido','PAV_CBUQ':'flexivel','PAVIMENTO':'flexivel'}
    assert mat(analyze(tmp_path,S(layers=lay,pavement_material='rigido'))[0])['PAVIMENTO']=='rigido'
    # Área do editor com material próprio; o restante da superfície cortada mantém o material da camada.
    area={'name':'A','kind':'pavement','material':'rigido','points':[{'x':500120,'y':7799992},{'x':500180,'y':7799992},{'x':500180,'y':7800008},{'x':500120,'y':7800008}]}
    items=analyze(tmp_path,S(layers=lay,pavement_areas=[area]))[0]
    a=[e for e in items if e.get('mark')];assert a and all(e['material']=='rigido' for e in a)
    rest=[e for e in items if e['layer']=='PAV_CBUQ'];assert rest and all(e['material']=='flexivel' for e in rest)

def test_joints_every_5m_and_slab_tone():
    from app.pavement import JointField,paint_rigid
    f=JointField([np.array([[1000.,0],[1100.,0]])])
    px=.05;H,W=80,400                                   # 20 m × 4 m a 5 cm/pixel, começando em x=1000
    mask=np.ones((H,W),bool)
    art=paint_rigid(np.zeros(3,np.uint8),mask,'pavement',1000.,2.,px,f,5.,False).astype(int)
    tec=paint_rigid(np.zeros(3,np.uint8),mask,'pavement',1000.,2.,px,f,5.,True).astype(int)
    col=art[:,:,0].mean(0)
    dark=[x for x in range(W) if col[x]<col.max()-25]
    xs=sorted({round((1000+(x+.5)*px)%5,1)%5 for x in dark});assert set(xs)<={0.0,4.9,0.1}   # só nas juntas (a cada 5 m)
    assert len(dark)>=3
    slabs=[art[:,10:90,0].mean(),art[:,110:190,0].mean(),art[:,210:290,0].mean()];assert np.ptp(slabs)>.5   # tom varia por placa
    tcol=tec[:,:,0].mean(0);assert (tcol<120).sum()>=6                     # traço de desenho mais forte
    assert tec[:,10:90].std()>art[:,10:90].std()                            # pontilhado de concreto no técnico

def test_rigid_overlay_and_detail(junction):
    from app.render import Scene
    from app import visual
    sc=Scene(junction,S(imagery='neutral',width=1280,pavement_material='rigido'))
    assert sc.color('pavement')!=Scene(junction,S(imagery='neutral',width=1280)).color('pavement')
    assert (sc.surface==visual.SURF['oae']).sum()>(sc.surface==visual.SURF['pavement']).sum()
    i,j=[(i,j) for i,j in sc.detail.tiles_for(np.array([500200.,7800000.]),60,1280,720,sc.R)][0]
    ov,surf=sc.detail.overlay_tile(i,j)
    assert (surf==visual.SURF['oae']).any()
    # Juntas: colunas mais escuras dentro da pista, alinhadas a múltiplos de 5 m do eixo.
    im=sc.frame(0,view=((500150,7799996),20))[0];im2=Scene(junction,S(imagery='neutral',width=1280)).frame(0,view=((500150,7799996),20))[0]
    assert np.abs(im.astype(int)-im2.astype(int)).mean()>5

def test_project_contrast(junction):
    from app.render import Scene
    a=Scene(junction,S(imagery='neutral',width=1280));b=Scene(junction,S(imagery='neutral',width=1280,project_contrast=.8))
    fa=a.frame(0,view=((500200,7800000),300))[0].astype(int);fb=b.frame(0,view=((500200,7800000),300))[0].astype(int)
    h=int(157*a.scale)+40;bg=fa[h:h+60,:200].mean();bgb=fb[h:h+60,:200].mean()     # canto superior: só imagem
    assert bgb<bg*.75
    # Sobre a pista (centro) a diferença é pequena.
    c=fa.shape[0]//2,fa.shape[1]//2;assert abs(fa[c[0]-5:c[0]+5,c[1]-5:c[1]+5].mean()-fb[c[0]-5:c[0]+5,c[1]-5:c[1]+5].mean())<12

def test_technical_clean_hatch_and_migration(junction):
    from app.render import Scene
    base=dict(imagery='neutral',width=1280,style_profile='tecnico')
    clean=Scene(junction,S(**base)).frame(0,view=((500200,7799996),30))[0];tex=Scene(junction,S(**base,technical_textures=True)).frame(0,view=((500200,7799996),30))[0]
    assert np.abs(clean.astype(int)-tex.astype(int)).mean()>1
    s=Settings.model_validate({'schema_version':19,'km_start_m':0,'km_end_m':100,'style_profile':'tecnico'})
    assert s.schema_version>=20 and s.technical_textures is True
    n=Settings.model_validate({'schema_version':19,'km_start_m':0,'km_end_m':100})
    assert n.technical_textures is False and n.pavement_material=='flexivel' and n.joint_spacing_m==5 and n.project_contrast==0

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_material_fields(junction):
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
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && vec && ready() && axisData()',timeout=20000)
            ev=page.evaluate
            ev("(()=>{const [ix,iy]=worldToImg({x:500200,y:7800000});view.s=Math.min(60,canvas.width*mpp()/420);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()})()")
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            page.click('#toolbar button[data-tool="pavpick"]');page.select_option('#pavMat','rigido');page.mouse.click(*W2C(500200,7800060))
            assert ev('M.pavement_areas[0].material')=='rigido'
            for k,v in (('style_profile','tecnico'),('pavement_material','rigido'),('existing_material','flexivel')):ev(f"(()=>{{const e=document.getElementById('{k}');e.value='{v}';e.dispatchEvent(new Event('change',{{bubbles:true}}))}})()")
            ev("document.getElementById('joint_spacing_m').value='4.5';document.getElementById('project_contrast').value='0.4'")
            ev('save()');page.wait_for_timeout(600)
            conf=c.get(f'/api/projects/{pid}').json()['config']
            assert conf['style_profile']=='tecnico' and conf['pavement_material']=='rigido' and conf['joint_spacing_m']==4.5 and conf['project_contrast']==.4 and conf['pavement_areas'][0]['material']=='rigido'
            # Representação do pavimento: escolher e alterar.
            ev("(()=>{const s=document.querySelector('#pavStyles tr[data-role=existing_pavement] select[data-k=pattern]');s.value='cruzada';s.dispatchEvent(new Event('change',{bubbles:true}))})()")
            ev("(()=>{const s=document.querySelector('#pavStyles tr[data-role=existing_pavement] input[data-k=spacing_m]');s.value='1.5';s.dispatchEvent(new Event('change',{bubbles:true}))})()")
            page.wait_for_timeout(1500)
            conf=c.get(f'/api/projects/{pid}').json()['config'];st=conf['pavement_styles']['existing_pavement']
            assert st['pattern']=='cruzada' and st['spacing_m']==1.5 and st['fill']==''
            ev("(()=>{const s=document.querySelector('#pavStyles tr[data-role=existing_pavement] select[data-k=pattern]');s.value='auto';s.dispatchEvent(new Event('change',{bubbles:true}))})()")
            page.wait_for_timeout(1500);assert 'existing_pavement' not in c.get(f'/api/projects/{pid}').json()['config']['pavement_styles']
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e],errors

def test_pavement_representation_choices(junction):
    from app.pavement import paint_style
    from app.models import PavementStyle
    m=np.ones((100,100),bool)
    base=np.zeros(3,np.uint8)
    out={}
    for pat in ('solido','diagonal','cruzada','pontilhado'):
        st=PavementStyle(pattern=pat,fill='#202020',hatch='#e0e0e0',spacing_m=2,angle_deg=0,line_m=.2)
        out[pat]=paint_style(base,m,'pavement',0.,10.,.1,st).astype(int)[:,:,0]
    assert out['solido'].max()==32 and out['solido'].min()==32
    rows=out['diagonal'].mean(1);assert rows.max()>150 and (rows>150).sum()<=30         # linhas horizontais a cada 2 m
    assert (out['cruzada']>150).sum()>(out['diagonal']>150).sum()*1.6
    assert 0<(out['pontilhado']>150).mean()<.2
    from app.render import Scene
    s=S(imagery='neutral',width=1280,pavement_styles={'pavement':{'pattern':'cruzada','fill':'#103060','hatch':'#ffffff','spacing_m':2}})
    sc=Scene(junction,s);assert sc.color('pavement')=='#103060'
    im=sc.frame(0,view=((500150,7799996),20))[0];blue=(im[:,:,2].astype(int)-im[:,:,0])>25
    assert blue.mean()>.2
    assert Settings.model_validate({**s.model_dump()}).pavement_styles['pavement'].pattern=='cruzada'
