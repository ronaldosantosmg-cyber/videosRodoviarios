"""1.24: leitor ECW interno (GDAL para Python + plugin ECW instalados no Python portátil) e conversão que
confere a georreferência. Sem GDAL neste ambiente: o GDAL é simulado com a mesma interface (osgeo.gdal)."""
import json,subprocess
from pathlib import Path
import numpy as np,pytest,tifffile,cv2
from pyproj import CRS

X0,Y1,PX=500000.,7800000.,.05

class SRS:
    def __init__(self,epsg):self.epsg=epsg
    def IsSame(self,o):return getattr(o,'epsg',None)==self.epsg
    def Clone(self):return SRS(self.epsg)
    def MorphToESRI(self):pass
    def ExportToWkt(self):return CRS.from_epsg(self.epsg).to_wkt('WKT1_ESRI')

class Band:
    def __init__(self,ci):self.ci=ci
    def GetColorInterpretation(self):return self.ci

class DS:
    def __init__(self,g,path,arr,gt,srs,drv):self.g=g;self.path=path;self.arr=arr;self.gt=gt;self.srs=srs;self.drv=drv;self.ov=None
    RasterXSize=property(lambda s:s.arr.shape[1]);RasterYSize=property(lambda s:s.arr.shape[0]);RasterCount=property(lambda s:s.arr.shape[2])
    def GetGeoTransform(self,can_return_null=False):return self.gt
    def GetSpatialRef(self):return self.srs
    def GetDriver(self):return type('D',(),{'ShortName':self.drv})()
    def GetRasterBand(self,b):return Band(6 if (self.arr.shape[2]==4 and b==4) else 0)
    def BuildOverviews(self,how,levels,callback=None):
        self.ov=levels
        if callback:callback(1.,'',None)

class FakeGDAL:
    """Simula osgeo.gdal: abre o 'ECW' (matriz em memória), Translate grava GeoTIFF real (sem etiquetas geo)."""
    GCI_AlphaBand=6;GA_Update=1;__version__='3.11.3'
    def __init__(self,shift=0.,srs_out=None):self.files={};self.shift=shift;self.srs_out=srs_out;self.opts=None
    def UseExceptions(self):pass
    def SetConfigOption(self,k,v):pass
    def IdentifyDriver(self,p):return object() if str(p) in self.files else None
    def TranslateOptions(self,**kw):return kw
    def Open(self,p,mode=0):return self.files.get(str(p))
    def Translate(self,dst,ds,options=None):
        self.opts=options;arr=ds.arr[:,:,[b-1 for b in options['bandList']]]
        tifffile.imwrite(dst,arr,tile=(256,256),compression='zlib',photometric='rgb')
        gt=list(ds.gt);gt[0]+=self.shift
        self.files[str(dst)]=DS(self,dst,arr,tuple(gt),self.srs_out or ds.srs,'GTiff')
        options['callback'](1.,'',None);return self.files[str(dst)]

def ecw(tmp_path,bands=3):
    a=np.zeros((1200,2400,bands),np.uint8);a[:,:,:3]=(70,120,60)
    yy,xx=np.mgrid[0:1200,0:2400];a[((xx//40+yy//40)%2)==0,:3]=(110,150,90)
    cv2.circle(a,(1200,200),5,(255,0,0,255)[:bands],-1)          # ponto de controle em (X0+60, Y1-10)
    if bands==4:a[:,:,3]=255
    p=tmp_path/'imagem_local'/'drone.ecw';p.parent.mkdir(exist_ok=True);p.write_bytes(b'ECW')
    g=FakeGDAL();g.files[str(p)]=DS(g,p,a,(X0,PX,0.,Y1,0.,-PX),SRS(31983),'ECW');return g,p

def test_convert_keeps_georeference_and_writes_sidecars(tmp_path):
    from app.ecw_engine import convert_py
    from app.local_imagery import georef
    g,src=ecw(tmp_path);dst=src.with_name('drone_convertido.tif');steps=[]
    r=convert_py(src,dst,lambda f,m:steps.append((f,m)),gdal=g)
    assert dst.exists() and (dst.with_suffix('.tfw')).exists() and (dst.with_suffix('.prj')).exists()
    assert r['corner_deviation_m']==0 and r['same_crs'] and r['driver']=='ECW' and r['size']==[2400,1200]
    assert 'TILED=YES' in g.opts['creationOptions'] and 'COMPRESS=DEFLATE' in g.opts['creationOptions'] and any(x.ov and x.ov[0]==2 for x in g.files.values())
    tfw=[float(v) for v in dst.with_suffix('.tfw').read_text().split()]
    assert tfw==pytest.approx([PX,0,0,-PX,X0+PX/2,Y1-PX/2])
    info=georef(dst,dst.with_suffix('.tfw'),dst.with_suffix('.prj'),None)
    assert info['gt'][0]==pytest.approx(X0) and info['gt'][3]==pytest.approx(Y1) and info['gt'][1]==pytest.approx(PX)
    assert CRS.from_user_input(info['crs']).to_epsg()==31983
    assert steps[-1][0]>=.9 and not list(src.parent.glob('*.parcial*'))
    # Ponto de controle no mosaico do aplicativo: no lugar certo (< 1,5 px).
    from app.models import Settings,LocalImagery
    from test_workflow import settings
    from app.local_tiles import LocalMosaic
    s=Settings(**{**settings().model_dump(),'local_imagery':LocalImagery(name='d',image=dst.name,world=dst.with_suffix('.tfw').name,prj=dst.with_suffix('.prj').name).model_dump()})
    out=LocalMosaic(tmp_path,s).sample_box([X0+55,Y1-15,X0+65,Y1-5],200,200)
    red=(out[:,:,0]>200)&(out[:,:,1]<60);ys,xs=np.nonzero(red)
    assert abs(xs.mean()-100)<1.5 and abs(ys.mean()-100)<1.5

def test_convert_rejects_changed_georeference(tmp_path):
    from app.ecw_engine import convert_py
    g,src=ecw(tmp_path);g.shift=.5;dst=src.with_name('x.tif')
    with pytest.raises(ValueError,match='Georreferência alterada'):convert_py(src,dst,gdal=g)
    assert not dst.exists()
    g,src=ecw(tmp_path);g.srs_out=SRS(4326)
    with pytest.raises(ValueError,match='Sistema de coordenadas diferente'):convert_py(src,dst,gdal=g)
    g,src=ecw(tmp_path);g.files[str(src)].gt=(0.,1.,0.,0.,0.,1.)
    with pytest.raises(ValueError,match='não traz georreferência'):convert_py(src,dst,gdal=g)

def test_convert_keeps_alpha_band(tmp_path):
    from app.ecw_engine import convert_py
    g,src=ecw(tmp_path,bands=4);dst=src.with_name('a.tif')
    r=convert_py(src,dst,gdal=g);assert r['alpha'] and g.opts['bandList']==[1,2,3,4] and 'ALPHA=YES' in g.opts['creationOptions']

def test_install_online_offline_and_errors(tmp_path,monkeypatch):
    import app.ecw_engine as E
    calls=[]
    def run(cmd,**kw):calls.append(cmd);return subprocess.CompletedProcess(cmd,0,'ok','')
    monkeypatch.setattr(E,'status',lambda:{'ecw':True,'python_gdal':'3.11.3','ready':True})
    monkeypatch.setattr(E,'OFFLINE',tmp_path/'pacotes_ecw')
    st=E.install(run=run);assert st['ecw'] and len(calls)==2
    assert '--index-url' in calls[0] and E.GWI_INDEX in calls[0] and E.GDAL_SPEC in calls[0] and E.ECW_SPEC in calls[1]
    (tmp_path/'pacotes_ecw').mkdir();(tmp_path/'pacotes_ecw'/'GDAL-3.11.3-cp312-cp312-win_amd64.whl').write_bytes(b'x')
    calls.clear();E.install(run=run);assert len(calls)==1 and '--no-index' in calls[0] and str(tmp_path/'pacotes_ecw') in calls[0]
    def bad(cmd,**kw):return subprocess.CompletedProcess(cmd,1,'','ERROR: proxy')
    with pytest.raises(ValueError,match='pacotes_ecw'):E.install(run=bad)
    monkeypatch.setattr(E,'status',lambda:{'ecw':False,'python_gdal':'3.11.3','ready':False})
    with pytest.raises(ValueError,match='Visual C\\+\\+'):E.install(run=run)

def test_status_without_gdal(monkeypatch):
    import app.ecw_engine as E
    monkeypatch.setattr(E,'py_gdal',lambda:None)
    st=E.status();assert st['python_gdal'] is None and st['ecw'] is False and 'ready' in st

def test_worker_prefers_internal_reader(tmp_path,monkeypatch):
    """Envio de .ecw pela API e conversão pelo leitor interno (simulado), sem QGIS."""
    from fastapi.testclient import TestClient
    from app.server import app
    import app.store as store,app.ecw_engine as E,app.local_tiles as LT
    from test_workflow import settings
    with TestClient(app) as c:
        pid=c.post('/api/projects',json={**settings().model_dump(),'duration_s':10}).json()['id']
        d=store.ROOT/pid
        monkeypatch.setattr(LT,'find_gdal',lambda:None)
        g,_=ecw(tmp_path)
        arr=next(iter(g.files.values())).arr
        r=c.post(f'/api/projects/{pid}/imagery',files=[('files',('drone.ecw',b'ECW'))],data={'mode':'replace','crs':''});assert r.status_code==200
        j=r.json();assert j['needs_conversion'] and j['file']=='drone.ecw'
        src=d/'imagem_local'/'drone.ecw';g.files={str(src):DS(g,src,arr,(X0,PX,0.,Y1,0.,-PX),SRS(31983),'ECW')}
        monkeypatch.setattr(E,'py_gdal',lambda:g)
        # Executa a tarefa no próprio processo (o trabalhador real roda em subprocesso).
        from app import worker
        jid=c.post(f'/api/projects/{pid}/imagery/convert').json()['id']
        worker.run(jid) if hasattr(worker,'run') else worker.process(jid)
        conf=json.loads((d/'config.json').read_text(encoding='utf-8'))
        li=conf['local_imagery'];assert li['image']=='drone_convertido.tif' and li['world']=='drone_convertido.tfw' and li['prj']=='drone_convertido.prj' and conf['imagery']=='local'
        chk=json.loads((d/'imagem_local'/'drone_convertido_conferencia.json').read_text(encoding='utf-8'));assert chk['corner_deviation_m']==0
