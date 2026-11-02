"""1.17: imagem georreferenciada local de alta resolução (GeoTIFF/COG em blocos, JPEG2000, mosaico,
conversão ECW/MrSID pelo GDAL do computador) na aproximação do vídeo, no mosaico base e no editor."""
import io,os,json,stat,time,socket,threading
from pathlib import Path
import numpy as np,cv2,pytest,tifffile
from PIL import Image
from fastapi.testclient import TestClient
from test_workflow import settings,wait
from test_v110 import junction
from app.models import Settings

X0,Y1,PX=500090.,7800030.,.05   # canto superior esquerdo e 5 cm/pixel
W,H=2400,1200                   # 120 m × 60 m
DOT=(500150.,7800020.)

def geokeys(epsg=31983):return (1,1,0,3, 1024,0,1,1, 1025,0,1,1, 3072,0,1,epsg)

def ortho(color=(70,120,60)):
    a=np.zeros((H,W,3),np.uint8);a[:]=color
    yy,xx=np.mgrid[0:H,0:W];a[((xx//40+yy//40)%2)==0]=(color[0]+30,color[1]+30,color[2]+30)
    c=int((DOT[0]-X0)/PX),int((Y1-DOT[1])/PX);cv2.circle(a,c,4,(255,0,0),-1)
    return a

def write_geotiff(path,a,x0=X0,y1=Y1,px=PX,levels=2,compression='zlib'):
    tags=[(33550,'d',3,(px,px,0.)),(33922,'d',6,(0.,0.,0.,x0,y1,0.)),(34735,'H',16,geokeys())]
    with tifffile.TiffWriter(path) as tw:
        tw.write(a,tile=(256,256),compression=compression,photometric='rgb',subifds=levels,extratags=tags)
        b=a
        for _ in range(levels):
            b=cv2.pyrDown(b);tw.write(b,tile=(256,256),compression=compression,photometric='rgb',subfiletype=1)

def setup_local(d,files,crs=''):
    """Envia as imagens pela API como o usuário faria."""
    from app.server import app
    c=TestClient(app)
    pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
    return c,pid

def test_tiff_reader_windowed_and_levels(tmp_path):
    from app.local_tiles import TiffReader,open_reader
    a=ortho();write_geotiff(tmp_path/'o.tif',a)
    r=open_reader(tmp_path/'o.tif');assert isinstance(r,TiffReader) and r.windowed and len(r.levels)==3
    w=r.read(0,500,600,1000,1200);assert np.array_equal(w,a[500:600,1000:1200])
    assert len(r.cache)<=4                      # só os blocos necessários foram decodificados
    assert r.level_for(1.)==0 and r.level_for(2.2)==1 and r.level_for(9)==2
    # Compressão sem suporte nativo (LZW) cai para leitura completa (Pillow), com o mesmo resultado.
    Image.fromarray(a).save(tmp_path/'l.tif',compression='tiff_lzw');rl=open_reader(tmp_path/'l.tif')
    assert np.array_equal(rl.read(0,500,600,1000,1200),a[500:600,1000:1200])

def test_mosaic_georeference_priority_and_nodata(tmp_path):
    from app.models import LocalImagery,LocalSource
    from app.local_tiles import LocalMosaic
    d=tmp_path;(d/'imagem_local').mkdir()
    write_geotiff(d/'imagem_local'/'a.tif',ortho())
    b=ortho((150,90,40));b[:,:300]=0                       # colar preto (sem dados) à esquerda
    write_geotiff(d/'imagem_local'/'b.tif',b,x0=X0+60)       # sobrepõe a metade direita
    s=Settings(**{**settings().model_dump(),'local_imagery':LocalImagery(name='a',image='a.tif',others=[LocalSource(name='b',image='b.tif')]).model_dump()})
    m=LocalMosaic(d,s)
    out=m.sample_box([DOT[0]-5,DOT[1]-5,DOT[0]+5,DOT[1]+5],200,200)
    red=(out[:,:,0]>200)&(out[:,:,1]<60);ys,xs=np.nonzero(red)
    assert len(xs) and abs(xs.mean()-100)<1.5 and abs(ys.mean()-100)<1.5   # erro < 0,08 m
    # Prioridade: a principal (a) vale onde as duas cobrem; a segunda completa à direita; colar transparente.
    right=m.sample_box([X0+125,Y1-40,X0+135,Y1-20],50,50);assert right[:,:,3].min()==255 and right[25,25,0]>140
    mid=m.sample_box([X0+100,Y1-40,X0+110,Y1-20],50,50);assert mid[25,25,0]<130   # região da 'a'
    outside=m.sample_box([X0-50,Y1-40,X0-40,Y1-30],20,20);assert outside[:,:,3].max()==0
    s2=s.model_copy(update={'local_imagery':s.local_imagery.model_copy(update={'brightness':.3})});m2=LocalMosaic(d,s2)
    assert m2.key!=m.key and m2.sample_box([X0+40,Y1-40,X0+50,Y1-30],20,20)[:,:,:3].mean()>m.sample_box([X0+40,Y1-40,X0+50,Y1-30],20,20)[:,:,:3].mean()+30

def test_jpeg2000_world_file_and_geojp2(tmp_path):
    from app.local_imagery import georef
    from app.local_tiles import jp2_georef,LocalMosaic
    from app.models import LocalImagery
    a=ortho();Image.fromarray(a).save(tmp_path/'o.jp2',quality_mode='dB',quality_layers=[45])
    (tmp_path/'o.j2w').write_text(f'{PX}\n0\n0\n{-PX}\n{X0+PX/2}\n{Y1-PX/2}\n')
    g=georef(tmp_path/'o.jp2',tmp_path/'o.j2w',None,'EPSG:31983');assert np.allclose(g['gt'],(X0,PX,0,Y1,0,-PX)) and g['size']==(W,H)
    # GeoJP2: caixa uuid com um GeoTIFF degenerado anexada ao arquivo.
    b=io.BytesIO();tifffile.imwrite(b,np.zeros((1,1),np.uint8),extratags=[(33550,'d',3,(PX,PX,0.)),(33922,'d',6,(0.,0.,0.,X0,Y1,0.)),(34735,'H',16,geokeys())])
    payload=bytes.fromhex('b14bf8bd083d4b43a5ae8cd7d5a6ce03')+b.getvalue()
    data=(tmp_path/'o.jp2').read_bytes()
    jp=tmp_path/'g.jp2';jp.write_bytes(data+(8+len(payload)).to_bytes(4,'big')+b'uuid'+payload)
    gt,crs=jp2_georef(jp);assert np.allclose(gt,(X0,PX,0,Y1,0,-PX)) and crs.to_epsg()==31983
    d=tmp_path/'p';(d/'imagem_local').mkdir(parents=True);os.replace(jp,d/'imagem_local'/'g.jp2')
    s=Settings(**{**settings().model_dump(),'local_imagery':LocalImagery(name='g',image='g.jp2').model_dump()})
    out=LocalMosaic(d,s).sample_box([DOT[0]-5,DOT[1]-5,DOT[0]+5,DOT[1]+5],200,200)
    red=(out[:,:,0]>180)&(out[:,:,1]<90);ys,xs=np.nonzero(red);assert abs(xs.mean()-100)<2 and abs(ys.mean()-100)<2

def test_detail_layer_uses_local_imagery(junction):
    from app.render import Scene
    from app.models import LocalImagery
    (junction/'imagem_local').mkdir();write_geotiff(junction/'imagem_local'/'o.tif',ortho())
    s=Settings(**{**settings().model_dump(),'duration_s':30,'traffic':False,'imagery':'local','local_imagery':LocalImagery(name='o',image='o.tif').model_dump()})
    sc=Scene(junction,s);det=sc.detail
    assert det.local is not None and det.enabled_imagery and not det.esri_ok
    i=int((DOT[0]-det.x0)//(1024*det.R));j=int((det.y1-DOT[1])//(1024*det.R))
    img=det.imagery_tile(i,j);assert img is not None and img.shape[2]==4   # parcial: alfa = cobertura
    p=det.worldpx(i,j)(np.array([DOT]))[0].astype(int);pt=img[p[1]-2:p[1]+3,p[0]-2:p[0]+3].astype(int)
    assert (pt[:,:,0]-pt[:,:,1]).max()>60 and img[p[1],p[0],3]==255
    # No quadro aproximado o ponto vermelho aparece no lugar certo.
    v=(DOT,40);im=sc.frame(0,view=v)[0];q=sc.screen(np.array([DOT]),np.array(DOT),40)[0].astype(int)
    patch=im[q[1]-6:q[1]+7,q[0]-6:q[0]+7];assert ((patch[:,:,0]>170)&(patch[:,:,1]<110)).any()
    files=list((junction/'cache_detalhe').rglob('im_*.png'));assert files   # cache em disco (RGBA)

def test_base_mosaic_from_several_sources(junction):
    from app.imagery import mosaic,use_local_mosaic
    from app.models import LocalImagery,LocalSource
    (junction/'imagem_local').mkdir();write_geotiff(junction/'imagem_local'/'a.tif',ortho());write_geotiff(junction/'imagem_local'/'b.tif',ortho((150,90,40)),x0=X0+200)
    li=LocalImagery(name='a',image='a.tif',others=[LocalSource(name='b',image='b.tif')])
    s=Settings(**{**settings().model_dump(),'imagery':'local','imagery_pixels':2048,'local_imagery':li.model_dump()})
    assert use_local_mosaic(junction,li) and not use_local_mosaic(junction,LocalImagery(name='a',image='a.tif'))
    img,box,label=mosaic(junction,s,[[500000,7799960],[500400,7800120]])
    assert img.shape==(2048,2048,3) and '2 arquivo' in label and list((junction/'imagery').glob('local_*.png'))

def test_api_local_tiles_info_and_conversion(junction,tmp_path,monkeypatch):
    from app.server import app
    with TestClient(app) as c:api_flow(c,tmp_path,monkeypatch)

def api_flow(c,tmp_path,monkeypatch):
    pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
    a=ortho();buf=io.BytesIO();write_geotiff(tmp_path/'o.tif',a)
    r=c.post(f'/api/projects/{pid}/imagery',files=[('files',('o.tif',(tmp_path/'o.tif').read_bytes()))],data={'crs':'','mode':'replace'})
    assert r.status_code==200,r.text
    info=c.get(f'/api/projects/{pid}/local/info').json()
    assert len(info['sources'])==1 and abs(info['pixel_m']-.05)<.002 and info['max_zoom']>=21
    # Ladrilho Web Mercator que contém o ponto: PNG com o ponto vermelho; longe: 204.
    from pyproj import Transformer
    mx,my=Transformer.from_crs(31983,3857,always_xy=True).transform(*DOT);z=21;n=2**z;M=20037508.342789244
    x=int((mx+M)/(2*M)*n);y=int((M-my)/(2*M)*n)
    t=c.get(f'/api/projects/{pid}/local_tiles/{z}/{y}/{x}.png');assert t.status_code==200
    im=cv2.imdecode(np.frombuffer(t.content,np.uint8),cv2.IMREAD_UNCHANGED);assert im.shape==(256,256,4) and ((im[:,:,2]>200)&(im[:,:,1]<60)).any()
    assert c.get(f'/api/projects/{pid}/local_tiles/{z}/{y}/{x+500}.png').status_code==204
    # Segunda imagem no mosaico e retirada.
    write_geotiff(tmp_path/'b.tif',ortho((150,90,40)),x0=X0+60)
    assert c.post(f'/api/projects/{pid}/imagery',files=[('files',('b.tif',(tmp_path/'b.tif').read_bytes()))],data={'mode':'add'}).status_code==200
    assert len(c.get(f'/api/projects/{pid}/local/info').json()['sources'])==2
    assert c.delete(f'/api/projects/{pid}/imagery/1').status_code==200 and len(c.get(f'/api/projects/{pid}/local/info').json()['sources'])==1
    # ECW: guardado e convertido pelo GDAL do computador (aqui um gdal_translate simulado).
    fake=tmp_path/'gdalbin';fake.mkdir()
    sc=fake/'gdal_translate';sc.write_text('#!/bin/sh\nfor a; do last=$prev; prev=$a; done\ncp "'+str(tmp_path/'o.tif')+'" "$prev"\n');sc.chmod(0o755)
    monkeypatch.setenv('RODOVIA_GDAL_BIN',str(fake))
    r=c.post(f'/api/projects/{pid}/imagery',files=[('files',('voo.ecw',b'ECW-FAKE'))],data={'mode':'replace'}).json()
    assert r['needs_conversion'] and r['gdal']
    j=c.post(f'/api/projects/{pid}/imagery/convert').json();job=wait(c,j['id'],120)
    assert job['state']=='done',job
    conf=c.get(f'/api/projects/{pid}').json()['config']
    assert conf['local_imagery']['image']=='voo_convertido.tif' and conf['imagery']=='local'
    assert c.get(f'/api/projects/{pid}/local/info').json()['sources'][0]['file']=='voo_convertido.tif'
    # Sem GDAL: a tarefa falha com orientação clara.
    monkeypatch.setenv('RODOVIA_GDAL_BIN',str(tmp_path/'nada'));monkeypatch.setenv('PATH','/usr/bin:/bin')
    from app.local_tiles import find_gdal;assert find_gdal() is None

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_shows_local_imagery(junction,tmp_path):
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
    write_geotiff(tmp_path/'o.tif',ortho())
    assert c.post(f'/api/projects/{pid}/imagery',files=[('files',('o.tif',(tmp_path/'o.tif').read_bytes()))],data={'mode':'replace'}).status_code==200
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[];hits=[];tile=cv2.imencode('.jpg',np.full((256,256,3),70,np.uint8))[1].tobytes()
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1400,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('response',lambda r:hits.append(r.status) if '/local_tiles/' in r.url else None)
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=tile,headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined" && geo && localInfo && localInfo.sources.length===1 && ready()',timeout=20000)
            ev=page.evaluate
            ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{DOT[0]},y:{DOT[1]}}});view.s=Math.min(240,canvas.width*mpp()/30);view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}})()")
            page.wait_for_function('[...localTiles.values()].some(t=>t.ok)',timeout=20000)
            assert 200 in hits
            assert '1 imagem' in ev("document.getElementById('imgInfo').textContent"),ev("document.getElementById('imgInfo').textContent") and page.locator('[data-imgdel]').count()==1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not [e for e in errors if 'favicon' not in e and '204' not in e],errors

def test_schema_v16():
    s=Settings.model_validate({'schema_version':15,'km_start_m':0,'km_end_m':100,'local_imagery':{'name':'x','image':'x.tif'}})
    assert s.schema_version>=16 and s.local_imagery.others==[] and s.local_imagery.detail and s.local_imagery.nodata=='borda'   # 1.39: padrão passou a borda 255/0 ligada à beira
