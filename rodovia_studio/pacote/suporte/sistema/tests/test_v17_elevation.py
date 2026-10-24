"""1.7: elevação (MDT local e web), sombreamento sem deformar a imagem, pista nivelada e cabine 3D."""
import io,math
import numpy as np
import pytest
import cv2
from PIL import Image
from pyproj import Transformer
from test_workflow import drawing,settings
from app.models import Settings,TrafficPath,Point
from app import elevation as E

def S(**kw):return Settings(**{**settings().model_dump(),**kw})

def test_terrarium_roundtrip():
    h=np.array([[-12.5,0.],[850.25,2999.75]],np.float32)
    assert np.allclose(E.decode_terrarium(E.encode_terrarium(h)),h,atol=1/256)

def test_web_dem_from_tiles_matches_known_surface(tmp_path):
    tr=Transformer.from_crs(4326,31983,always_xy=True)
    def z_of(lon,lat):x,y=tr.transform(lon,lat);return 700+.05*(np.asarray(x)-500000)-.02*(np.asarray(y)-7800000)
    def fetcher(z,x,y):
        n=2**z;px=(x+(np.arange(256)+.5)/256)/n;py=(y+(np.arange(256)+.5)/256)/n
        lon=px*360-180;lat=np.degrees(np.arctan(np.sinh(math.pi*(1-2*py))))
        L,A=np.meshgrid(lon,lat);b=io.BytesIO();Image.fromarray(E.encode_terrarium(z_of(L,A))).save(b,'PNG');return b.getvalue()
    box=[499500,7799500,500500,7800500];dem,label=E.web_dem(tmp_path,'EPSG:31983',box,256,fetcher)
    cell=(box[2]-box[0])/256
    for x,y in [(500000,7800000),(499800,7800300)]:
        j=int((x-box[0])/cell);i=int((box[3]-y)/cell);assert dem[i,j]==pytest.approx(700+.05*(x-500000)-.02*(y-7800000),abs=1.5)
    assert 'AWS Terrain Tiles' in label and list((tmp_path/'elevacao').glob('terrarium_*.png'))
    again,_=E.web_dem(tmp_path,'EPSG:31983',box,256,lambda *a:(_ for _ in ()).throw(AssertionError('cache')))  # usa o cache local
    assert np.allclose(again,dem)

def geotiff_dem(path,a,x0,y0,res):
    import tifffile
    keys=[1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,31983]
    tifffile.imwrite(path,a.astype(np.float32),extratags=[(33550,'d',3,(res,res,0.),False),(33922,'d',6,(0,0,0,x0,y0,0),False),(34735,'H',len(keys),keys,False),(42113,'s',0,'-9999',False)])

def test_local_dem_value_and_nodata(drawing):
    from app.models import Elevation
    base=drawing/'elevacao';base.mkdir()
    xx,yy=np.meshgrid(499900+np.arange(300)*2+1,7800100-np.arange(150)*2-1)
    a=(100+.1*(xx-499900)).astype(np.float32);a[0:5,0:5]=-9999
    geotiff_dem(base/'mdt.tif',a,499900,7800100,2.)
    dem,label=E.local_dem(drawing,Elevation(source='local',file='mdt.tif'),'EPSG:31983',[499950,7799950,500350,7800050],200)
    assert dem.min()>90 and 'mdt.tif' in label and '2.0 m/px' in label
    j=int((500150-499950)/2);i=int((7800050-7800000)/2);assert dem[i,j]==pytest.approx(100+.1*(500150-499900),abs=.3)

def test_hillshade_and_shading_do_not_move_the_image():
    flat=np.zeros((50,50),np.float32);assert np.ptp(E.hillshade(flat,2))<1e-6
    yy,xx=np.mgrid[0:50,0:50];nw=(-xx-yy).astype(np.float32)*2.;se=-nw  # rampas: subindo para NW e para SE
    assert E.hillshade(se,2).mean()<E.hillshade(nw,2).mean()+1  # orientação diferente, sombreamento diferente
    assert abs(E.hillshade(se,2).mean()-E.hillshade(nw,2).mean())>.05
    img=np.full((100,100,3),120,np.uint8);img[40:50,60:70]=(230,20,20)
    hill=(np.sin(np.mgrid[0:100,0:100][1]/8)*30).astype(np.float32);out=img.copy();E.shade_map(out,hill,1.,.5)
    red=lambda im:np.argwhere((im[:,:,0]>im[:,:,1]+60))
    assert np.array_equal(red(out),red(img))  # o marcador continua no mesmo lugar
    same=img.copy();E.shade_map(same,np.zeros((100,100),np.float32),1.,.5);assert np.array_equal(same,img)

def test_contours_follow_levels():
    img=np.zeros((101,101,3),np.uint8);dem=np.tile(np.arange(101,dtype=np.float32),(101,1))  # cota = coluna
    E.contours(img,dem,10,[0,0,101,101],lambda p:np.column_stack([p[:,0],101-p[:,1]]))
    cols=np.flatnonzero(img.max((0,2))>0);assert {10,20,50,90}<=set(cols.tolist()) or all(any(abs(c-v)<=1 for c in cols) for v in (10,20,50,90))

def test_terrain_levels_road_and_keeps_surroundings(drawing):
    from app.render import Scene
    sc=Scene(drawing,S());rng=np.random.default_rng(5)
    n=256;noise=(rng.standard_normal((n,n))*4+50).astype(np.float32)
    T=E.Terrain(noise,[float(v) for v in sc.box],'teste',sc.surface,sc.stations,sc.length,True)
    xs=np.linspace(500010,500290,60);road=T.sample(xs,np.full(60,7799995.));raw=T.sample(xs,np.full(60,7799995.),T.raw)
    assert np.std(np.diff(road))<np.std(np.diff(raw))*.3
    far=T.sample(np.array([500150.]),np.array([7800140.]));assert far[0]==pytest.approx(T.sample(np.array([500150.]),np.array([7800140.]),T.raw)[0],abs=1e-3)

def scene_with_hill(drawing,**kw):
    from app.render import Scene
    base=drawing/'elevacao';base.mkdir(exist_ok=True)
    xx,yy=np.meshgrid(499800+np.arange(400)*2+1,7800200-np.arange(200)*2-1)
    z=(np.exp(-((xx-500420)**2)/(2*40**2))*80).astype(np.float32)  # morro alto além do fim da pista
    geotiff_dem(base/'morro.tif',z,499800,7800200,2.)
    lane=[TrafficPath(name='Pista',kind='main',direction='growing',points=[Point(x=500005,y=7799995),Point(x=500295,y=7799995)]).model_dump()]
    return Scene(drawing,S(derive_traffic_paths=False,traffic_paths=lane,elevation={'source':'local','file':'morro.tif','hillshade':True},
        cabin={'enabled':True,'start':{'x':500040,'y':7799995},'duration_s':5},**kw))

def test_scene_with_dem_and_cursor_endpoint(drawing):
    from fastapi.testclient import TestClient
    from app.server import app
    sc=scene_with_hill(drawing);assert sc.terrain is not None and 'Elevação local' in sc.attribution
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        from app import store
        E.save_cache(store.ROOT/pid,sc.terrain)
        z=c.get(f'/api/projects/{pid}/elevation_at',params={"x":500420,"y":7800000}).json()['z'];assert z==pytest.approx(80,abs=2)
        assert c.get(f'/api/projects/{pid}/elevation_at',params={'x':0,'y':0}).json()['z'] is None

def test_cabin_drapes_image_on_terrain_without_distortion(drawing):
    from app.cabin import CabinView
    sc=scene_with_hill(drawing);sc.map=np.array(sc.map)
    # Marcador vermelho no chão, 60 m à frente: deve aparecer onde a projeção 3D (com a cota do MDT) indica.
    mx,my=500100.,7800030.;u,v=np.rint(sc.worldpx(np.array([[mx,my]]))[0]).astype(int);r=max(2,int(3/sc.px))
    sc.map[v-r:v+r,u-r:u+r]=(255,0,0)
    cv=CabinView(sc);pos,head,h,_=cv.state(0)
    im,meta=cv.frame(0);assert meta['terrain']
    zg=float(sc.terrain.sample(np.array([mx]),np.array([my]))[0]);q,d=cv.project2(np.array([[mx,my,zg]]))
    x,y=np.rint(q[0]).astype(int);patch=im[y-2:y+3,x-2:x+3].reshape(-1,3).astype(int)
    assert (patch[:,0]-patch[:,1]>80).any()
    # O morro (80 m) ocupa pixels acima do horizonte que no terreno plano seriam céu.
    flat=CabinView(__import__('app.render',fromlist=['Scene']).Scene(drawing,S(derive_traffic_paths=False,traffic_paths=[t.model_dump() for t in sc.s.traffic_paths],cabin=sc.s.cabin.model_dump())))
    a,_=flat.frame(0);hor=int(cv._hor)-10
    assert np.abs(im[sc.H//4:hor].astype(int)-a[sc.H//4:hor]).sum()>0
    assert np.isfinite(cv._depth[hor]).any()
