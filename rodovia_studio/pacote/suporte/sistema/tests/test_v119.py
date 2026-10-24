"""1.19: Enter encerra o comando, mover pontos, imagens locais (prioridade e ajuste por grips), prévia com zoom
forte, menus com ícones, limpar trabalho/retirar projeto, fontes web alternativas (Wayback, XYZ, WMS) e
atualizador com caminhos longos."""
import os,json,time,threading,socket,zipfile
from pathlib import Path
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from test_v117 import ortho,write_geotiff,DOT,X0,Y1,PX,W,H
from app.models import Settings

def red_center(out):
    red=(out[:,:,0]>200)&(out[:,:,1]<60)&(out[:,:,2]<60);ys,xs=np.nonzero(red)
    assert len(xs)>5;return xs.mean(),ys.mean()

def mosaic_settings(d,**adj):
    from app.models import LocalImagery
    (d/'imagem_local').mkdir(exist_ok=True)
    if not (d/'imagem_local'/'a.tif').exists():write_geotiff(d/'imagem_local'/'a.tif',ortho())
    return Settings(**{**settings().model_dump(),'local_imagery':LocalImagery(name='a',image='a.tif',**adj).model_dump()})

def test_local_image_adjust_shift_rotation_scale(tmp_path):
    from app.local_tiles import LocalMosaic
    m0=LocalMosaic(tmp_path,mosaic_settings(tmp_path))
    box=[DOT[0]-5,DOT[1]-5,DOT[0]+5,DOT[1]+5]
    x0,y0=red_center(m0.sample_box(box,200,200))                 # 0,05 m/pixel
    # Deslocamento: o ponto vermelho vai 2 m para leste e 1 m para norte.
    m=LocalMosaic(tmp_path,mosaic_settings(tmp_path,shift_x=2,shift_y=1))
    assert m.key!=m0.key and m.sources[0].adjusted and not m0.sources[0].adjusted
    x1,y1=red_center(m.sample_box([b+o for b,o in zip(box,(2,1,2,1))],200,200))
    assert abs(x1-x0)<1.5 and abs(y1-y0)<1.5
    # Rotação e escala em torno do centro: a posição bate com a transformação direta.
    m=LocalMosaic(tmp_path,mosaic_settings(tmp_path,rotation_deg=2,scale=1.01))
    s=m.sources[0];fx,fy=s.forward(DOT[0],DOT[1]);ix,iy=s.inverse(fx,fy)
    assert abs(ix-DOT[0])<1e-6 and abs(iy-DOT[1])<1e-6
    x2,y2=red_center(m.sample_box([fx-5,fy-5,fx+5,fy+5],200,200))
    assert abs(x2-x0)<1.5 and abs(y2-y0)<1.5
    # Cantos e limites acompanham o ajuste.
    c=s.corners(m.target);b=m.bbox[0]
    assert abs(c[:,0].min()-b[0])<1e-6 and abs(c[:,1].max()-b[3])<1e-6
    assert np.linalg.norm(c[1]-c[0])==pytest.approx(W*PX*1.01,rel=1e-6)

def test_identity_adjust_keeps_previous_key(tmp_path):
    """Sem ajuste, a chave do cache é a mesma da 1.18 (o cálculo não muda)."""
    import hashlib
    from app.local_tiles import LocalMosaic
    s=mosaic_settings(tmp_path);m=LocalMosaic(tmp_path,s);src=m.sources[0];st=src.path.stat();li=s.local_imagery
    h=hashlib.sha256();h.update(f'{src.path.name}|{st.st_size}|{st.st_mtime_ns}|{src.gt}|{src.crs.to_string()}'.encode())
    h.update(json.dumps([li.brightness,li.contrast,li.saturation,li.nodata,'1.17']).encode())
    assert m.key==h.hexdigest()[:16]

def test_api_order_adjust_and_info(junction,tmp_path):
    from app.server import app
    with TestClient(app) as c:
        pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
        write_geotiff(tmp_path/'a.tif',ortho());b=ortho((150,90,40));write_geotiff(tmp_path/'b.tif',b,x0=X0+60)
        assert c.post(f'/api/projects/{pid}/imagery',files=[('files',('a.tif',(tmp_path/'a.tif').read_bytes()))],data={'mode':'replace'}).status_code==200
        assert c.post(f'/api/projects/{pid}/imagery',files=[('files',('b.tif',(tmp_path/'b.tif').read_bytes()))],data={'mode':'add'}).status_code==200
        info=c.get(f'/api/projects/{pid}/local/info').json();assert [s['file'] for s in info['sources']]==['a.tif','b.tif'] and info['count']==2
        assert len(info['sources'][0]['corners'])==4 and info['sources'][0]['adjust']['scale']==1
        # Prioridade: b passa para cima.
        r=c.post(f'/api/projects/{pid}/imagery/order',json={'index':1,'to':0});assert r.status_code==200
        li=r.json()['local_imagery'];assert li['image']=='b.tif' and li['others'][0]['image']=='a.tif'
        info=c.get(f'/api/projects/{pid}/local/info').json();assert [s['file'] for s in info['sources']]==['b.tif','a.tif']
        # Ajuste por grips da segunda imagem (a.tif), gravado no CRS do projeto.
        r=c.put(f'/api/projects/{pid}/imagery/1/adjust',json={'shift_x':1.5,'shift_y':-.5,'rotation_deg':.2,'scale':1.001});assert r.status_code==200
        o=r.json()['local_imagery']['others'][0];assert o['shift_x']==1.5 and o['rotation_deg']==.2
        k2=c.get(f'/api/projects/{pid}/local/info').json();assert k2['key']!=info['key'] and k2['sources'][1]['adjust']['shift_x']==1.5
        assert c.put(f'/api/projects/{pid}/imagery/1/adjust',json={'shift_x':0,'rotation_deg':45}).status_code==422
        # Retirar a principal mantém o ajuste da que sobe.
        li=c.delete(f'/api/projects/{pid}/imagery/0').json()['local_imagery'];assert li['image']=='a.tif' and li['shift_x']==1.5 and li['others']==[]
        conf=json.loads((Path(os.environ['RODOVIA_DATA'])/pid/'config.json').read_text(encoding='utf-8')) if os.environ.get('RODOVIA_DATA') else None
        if conf:assert conf['schema_version']>=18

# ---------------- fontes web ----------------
def fake_tile_png(z,y,x,dot=None):
    a=np.full((256,256,3),(60,110,70),np.uint8)
    if dot:
        from app.webmap import MERC_HALF
        mx,my=dot;scale=256*2**z/(2*MERC_HALF);px=(mx+MERC_HALF)*scale-x*256;py=(MERC_HALF-my)*scale-y*256
        if -10<px<266 and -10<py<266:cv2.circle(a,(int(px),int(py)),3,(0,0,255),-1)   # BGR: vermelho
    return cv2.imencode('.png',a)[1].tobytes()

def test_web_sources_urls_and_cache(tmp_path):
    from app.webmap import WebSource,web_source,tile
    from app.models import WebImagery
    s=Settings(**settings().model_dump());assert web_source(s).kind=='esri' and web_source(s).cache=='esri'
    wb=WebSource('wayback',release=31144,label='2024-05-01');assert '/tile/31144/17/10/20' in wb.tile_url(17,10,20) and wb.cache=='wayback_31144'
    x=WebSource('xyz',url='https://exemplo.br/orto/{z}/{x}/{y}.jpg');assert x.tile_url(18,5,7)=='https://exemplo.br/orto/18/7/5.jpg'
    t=WebSource('xyz',url='https://exemplo.br/tms/{z}/{x}/{-y}.png');assert t.tile_url(2,1,3)=='https://exemplo.br/tms/2/3/2.png'
    w=WebSource('wms',url='https://exemplo.br/wms',layers='orto2023');u=w.tile_url(1,0,1)
    assert 'LAYERS=orto2023' in u and 'CRS=EPSG%3A3857' in u and 'BBOX=0.0%2C0.0%2C20037508' in u
    with pytest.raises(ValueError):WebSource('xyz',url='ftp://x')
    with pytest.raises(ValueError):WebSource('wayback')
    calls=[]
    def fetch(z,y,x_):calls.append((z,y,x_));return fake_tile_png(z,y,x_)
    a=tile(tmp_path,15,10,20,fetch=fetch,source=wb);b=tile(tmp_path,15,10,20,fetch=fetch,source=wb)
    assert a==b and len(calls)==1 and (tmp_path/'wayback_31144'/'15'/'10'/'20.jpg').exists() and not (tmp_path/'esri').exists()
    s2=Settings(**{**settings().model_dump(),'web_imagery':WebImagery(source='wayback',wayback_release=31144).model_dump()})
    assert web_source(s2).cache=='wayback_31144'

def test_wayback_release_list(tmp_path):
    from app.webmap import wayback_releases
    cfg={'10':{'itemTitle':'World Imagery (Wayback 2014-02-20)'},'31144':{'itemTitle':'World Imagery (Wayback 2024-05-01)'},'x':{}}
    r=wayback_releases(tmp_path,fetch=lambda u:json.dumps(cfg).encode())
    assert [d['release'] for d in r]==[31144,10] and r[0]['date']=='2024-05-01'
    # Sem internet: usa a cópia local.
    def off(u):raise OSError('sem rede')
    assert wayback_releases(tmp_path,fetch=off,max_age_s=0)[0]['release']==31144

def test_base_mosaic_from_web_tiles_is_georeferenced(tmp_path):
    from pyproj import Transformer
    from app.imagery import mosaic_tiles
    from app.models import WebImagery
    s=Settings(**{**settings().model_dump(),'web_imagery':WebImagery(source='xyz',url='https://exemplo.br/{z}/{x}/{y}.png',max_zoom=19).model_dump()})
    P=(500300.,7800010.);mx,my=Transformer.from_crs(s.crs,3857,always_xy=True).transform(*P)
    box=[P[0]-150,P[1]-150,P[0]+150,P[1]+150];n=600   # 0,5 m/pixel
    img,b,label=mosaic_tiles(tmp_path,s,box,n,fetch=lambda z,y,x:fake_tile_png(z,y,x,(mx,my)),cache_root=tmp_path/'_l')
    assert img.shape==(n,n,3) and b==box and 'usuário' in label
    red=(img[:,:,0]>150)&(img[:,:,1]<120);ys,xs=np.nonzero(red)
    assert len(xs)>0 and abs(xs.mean()-n/2)<3 and abs(ys.mean()-n/2)<3

def test_detail_key_unchanged_for_esri_and_new_for_other_source(junction):
    from app.render import Scene
    from app.models import WebImagery
    base={**settings().model_dump(),'duration_s':10,'imagery':'neutral'}
    s=Settings(**base);d=junction
    sc=Scene(d,s,lambda *a:None);k0=sc.detail.key;assert sc.detail.web.kind=='esri'
    s2=Settings(**{**base,'web_imagery':WebImagery(source='wayback',wayback_release=99).model_dump()})
    sc2=Scene(d,s2,lambda *a:None);assert sc2.detail.key!=k0 and sc2.detail.web.cache=='wayback_99'

# ---------------- limpar trabalho / retirar projeto ----------------
def test_reset_work_keeps_segment_and_undo(junction):
    from app.server import app
    import app.store as store
    with TestClient(app) as c:
        cfg={**settings().model_dump(),'duration_s':10,'km_start_m':325850,'km_end_m':326850,'pois':[{'id':'p1','title':'Obra','x':500300,'y':7800000}],
             'signs':[{'id':'s1','code':'R-1','point':{'x':500200,'y':7800005}}],'cities':[{'id':'c1','name':'Nova Era','point':{'x':500000,'y':7800000}}],
             'highlights':[{'id':'h1','name':'Poste','category':'poste','point':{'x':500250,'y':7800000}}]}
        pid=c.post('/api/projects',json=cfg).json()['id']
        g=c.get('/api/reset_groups').json()['groups'];assert {x['id'] for x in g}>={'obras','sinalizacao','geometria','fluxos','cidades'}
        r=c.post(f'/api/projects/{pid}/reset_work',json={'groups':['obras','sinalizacao']});assert r.status_code==200,r.text
        conf=r.json()['config'];assert conf['pois']==[] and conf['signs']==[] and conf['highlights']==[]
        assert conf['cities'] and conf['km_start_m']==325850 and conf['crs']==cfg['crs'] and r.json()['cleared']['pois']==1
        assert (store.ROOT/pid/r.json()['backup']).exists()
        assert c.post(f'/api/projects/{pid}/reset_work',json={'groups':['xx']}).status_code==422
        u=c.post(f'/api/projects/{pid}/reset_work/undo');assert u.status_code==200 and u.json()['config']['pois'][0]['title']=='Obra'
        assert c.post(f'/api/projects/{pid}/reset_work/undo').status_code==409
        # Retirar o projeto: sai da lista e a pasta vai para _lixeira.
        t=c.delete(f'/api/projects/{pid}');assert t.status_code==200
        assert pid not in [p['id'] for p in c.get('/api/projects').json()] and (store.ROOT/'_lixeira'/t.json()['trash']/'config.json').exists()
        assert c.get(f'/api/projects/{pid}').status_code in (404,422)

def test_schema_v18_migration():
    s=Settings.model_validate({'schema_version':17,'km_start_m':0,'km_end_m':100,'local_imagery':{'name':'x','image':'x.tif','others':[{'image':'y.tif'}]}})
    assert s.schema_version>=18 and s.web_imagery.source=='esri' and s.local_imagery.scale==1 and s.local_imagery.others[0].shift_x==0
    assert Settings(preview_width_m=8).preview_width_m==8

# ---------------- atualizador ----------------
def test_updater_long_path_helper(monkeypatch):
    import atualizador as U
    assert U.L('/tmp/x')=='/tmp/x'
    monkeypatch.setattr(U.os,'name','nt');monkeypatch.setattr(U.os.path,'abspath',lambda p:p)
    assert U.L('C:\\Users\\a\\b.txt')=='\\\\?\\C:\\Users\\a\\b.txt' and U.L('\\\\srv\\share\\x')=='\\\\?\\UNC\\srv\\share\\x'
    assert U.L('\\\\?\\C:\\x')=='\\\\?\\C:\\x'

# ---------------- editor ----------------
def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_enter_move_imgadjust_icons_preview(junction,tmp_path):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    cfg={**settings().model_dump(),'duration_s':10,'signs':[{'id':'s1','code':'R-1','point':{'x':DOT[0]-10,'y':DOT[1]}}]}
    pid=c.post('/api/projects',json=cfg).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    write_geotiff(tmp_path/'o.tif',ortho())
    assert c.post(f'/api/projects/{pid}/imagery',files=[('files',('o.tif',(tmp_path/'o.tif').read_bytes()))],data={'mode':'replace'}).status_code==200
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
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && localInfo && localInfo.sources.length===1 && ready()',timeout=20000)
            ev=page.evaluate
            # Menus: grupos com título e ícone vetorial em cada ferramenta; ícones nos títulos das seções.
            assert ev("document.querySelectorAll('#toolbar .tgroup').length")==6
            assert ev("[...document.querySelectorAll('#toolbar button[data-tool]')].every(b=>b.querySelector('svg'))")
            assert ev("document.querySelectorAll('section>h2 .ico svg').length")>=7
            ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{DOT[0]},y:{DOT[1]}}});view.s=Math.min(240,canvas.width*mpp()/60);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}})()")
            def W2C(x,y):
                q=ev(f'W2C({{x:{x},y:{y}}})');R=ev('(()=>{const r=canvas.getBoundingClientRect();return [r.left,r.top,r.width/canvas.width]})()');return R[0]+q[0]*R[2],R[1]+q[1]*R[2]
            # Enter encerra o comando e volta para Navegar.
            page.click('#toolbar button[data-tool="sign"]');page.focus('#canvas');page.keyboard.press('Enter');assert ev('tool')=='pan'
            # Placa: arrastar muda o ponto; desfazer volta.
            page.click('#toolbar button[data-tool="sign"]');page.mouse.move(*W2C(DOT[0]-10,DOT[1]));page.mouse.down();page.mouse.move(*W2C(DOT[0]-5,DOT[1]+3),steps=6);page.mouse.up()
            pt=ev('M.signs[0].point');assert abs(pt['x']-(DOT[0]-5))<.5 and abs(pt['y']-(DOT[1]+3))<.5 and ev('M.signs.length')==1
            ev('undo()');assert abs(ev('M.signs[0].point.x')-(DOT[0]-10))<1e-6
            # Ferramenta Mover.
            page.click('#toolbar button[data-tool="move"]');page.mouse.move(*W2C(DOT[0]-10,DOT[1]));page.mouse.down();page.mouse.move(*W2C(DOT[0]-12,DOT[1]-4),steps=6);page.mouse.up()
            assert abs(ev('M.signs[0].point.y')-(DOT[1]-4))<.5
            page.keyboard.press('Escape');page.wait_for_selector('#confirmDlg[open]');page.keyboard.press('Enter');assert ev('tool')=='pan'  # 1.24: Esc pede confirmação
            # Ajuste da imagem local por grips: arrastar dentro desloca; desfazer volta à posição original.
            ev("document.querySelector('[data-imgadj=\"0\"]').click()");assert ev('tool')=='imgadjust'
            ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{DOT[0]},y:{DOT[1]}}});view.s=Math.min(240,canvas.width*mpp()/60);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}})()")
            page.locator('#canvas').scroll_into_view_if_needed()
            page.mouse.move(*W2C(DOT[0],DOT[1]));page.mouse.down();page.mouse.move(*W2C(DOT[0]+1,DOT[1]+2),steps=6);page.mouse.up()
            page.wait_for_function('localInfo && localInfo.sources[0].adjust.shift_x>0.5',timeout=40000,polling=200)
            a=ev('localInfo.sources[0].adjust');assert abs(a['shift_x']-1)<.2 and abs(a['shift_y']-2)<.2
            conf=c.get(f'/api/projects/{pid}').json()['config'];assert abs(conf['local_imagery']['shift_x']-a['shift_x'])<1e-9
            page.wait_for_function("document.getElementById('message').textContent.startsWith('Imagem ajustada')",timeout=20000,polling=200)
            page.click('#adjUndo');page.wait_for_function('localInfo && localInfo.sources[0].adjust.shift_x===0',timeout=20000,polling=200)
            # Prévia com zoom forte (~10 m na tela): só o recorte visível é desenhado.
            ev("""(()=>{const c=document.createElement('canvas');c.width=4000;c.height=4000;const g=c.getContext('2d');g.fillStyle='#ff0000';g.fillRect(0,0,4000,4000);
                 window._cnt=0;const orig=ctx.drawImage.bind(ctx);ctx.drawImage=(...a)=>{if(a[0]===c){window._cnt++;window._args=a.slice(1)}return orig(...a)};baseImage=c;ctx.setTransform(1,0,0,1,0,0);view.s=400;view.ox=-1000*400;view.oy=-1000*400;drawPreviewImage();window._px=Array.from(ctx.getImageData(canvas.width/2,canvas.height/2,1,1).data)})()""")
            args=ev('window._args');assert ev('window._cnt')==1 and args[2]<20 and args[3]<20   # recorte pequeno da origem
            px=ev("window._px");assert px[0]>200 and px[1]<50
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e and '204' not in e],errors
