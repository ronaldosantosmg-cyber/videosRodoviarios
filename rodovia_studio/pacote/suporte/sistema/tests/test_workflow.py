import os,tempfile,time,zipfile
os.environ['RODOVIA_DATA']=tempfile.mkdtemp(prefix='rodovia_test_')
import ezdxf,numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from app.models import Settings
from app.geometry import analyze
from app.render import render
from app.server import app
@pytest.fixture
def drawing(tmp_path):
 d=ezdxf.new();m=d.modelspace()
 for l in ['EIXO','PAVIMENTO','CANTEIRO','FAIXA_DOMINIO','OFFSET-CORTE']:d.layers.new(l)
 m.add_lwpolyline([(500000,7800000),(500180,7800000),(500300,7800030)],dxfattribs={'layer':'EIXO'})
 for y0,y1 in [(-9,-1),(1,9)]:
  h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7800000+y0),(500300,7800000+y0),(500300,7800000+y1),(500000,7800000+y1)],is_closed=True)
 h=m.add_hatch(dxfattribs={'layer':'CANTEIRO'});h.paths.add_polyline_path([(500000,7799999),(500300,7799999),(500300,7800001),(500000,7800001)],is_closed=True)
 for y in [-25,25]:m.add_lwpolyline([(499990,7800000+y),(500310,7800000+y)],dxfattribs={'layer':'FAIXA_DOMINIO'})
 m.add_arc((500150,7800000),35,0,180,dxfattribs={'layer':'OFFSET-CORTE'});d.saveas(tmp_path/'input.dxf');return tmp_path
def settings(**kw):return Settings(width=1280,duration_s=3,imagery='neutral',coordinates_confirmed=True,hydrography=False,**kw)
def wait(c,jid,timeout=90):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  j=c.get('/api/jobs/'+jid).json()
  if j['state'] in ['done','failed','interrupted','cancelled']:return j
  time.sleep(.15)
 raise AssertionError('Timeout: '+str(j))
def test_settings():
 with pytest.raises(ValueError):Settings(km_start_m=2000,km_end_m=1000)
 with pytest.raises(ValueError):Settings(duration_s=0)
 with pytest.raises(ValueError):Settings(exclusions=[[{'x':0,'y':0}]])
def test_geometry_curves(drawing):
 es,a,ds,axes,r=analyze(drawing,settings());curve=next(e for e in es if e['role']=='cut');assert len(curve['points'])>10;assert len([e for e in es if e['role']=='domain'])==2;assert r['geometric_length_m']>300

def test_kmz_crs(tmp_path):
 with zipfile.ZipFile(tmp_path/'input.kmz','w') as z:z.writestr('doc.kml','<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><LineString><coordinates>-43,-19 -43.001,-19.001</coordinates></LineString></Placemark><Placemark><name>OAE</name><Point><coordinates>-43,-19</coordinates></Point></Placemark></Document></kml>')
 _,_,ds,_,r=analyze(tmp_path,settings());assert ds[-1]>100;assert r['kmz_pois'][0]['title']=='OAE'
 with pytest.raises(ValueError):analyze(tmp_path,settings(crs='EPSG:4326'))
def test_video_encoder(drawing):
 p=render(drawing,settings());cap=cv2.VideoCapture(str(p));assert cap.isOpened();assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==90;assert cap.get(cv2.CAP_PROP_FPS)==30;assert cap.get(cv2.CAP_PROP_FRAME_WIDTH)==1280
 ok,first=cap.read();assert ok;cap.set(cv2.CAP_PROP_POS_FRAMES,89);ok,last=cap.read();assert ok;assert not np.array_equal(first,last);cap.release()
def test_api_complete(drawing):
 with TestClient(app) as c:
  assert c.get('/api/health').json()['ffmpeg'];assert c.post('/api/projects',json={'km_start_m':1000,'km_end_m':0}).status_code==422
  assert c.post('/api/projects',json={},headers={'Origin':'https://externo.example'}).status_code==403
  r=c.post('/api/projects',json=settings().model_dump());assert r.status_code==201;pid=r.json()['id']
  assert c.post(f'/api/projects/{pid}/files',files={'file':('x.exe',b'x')}).status_code==415
  assert c.post(f'/api/projects/{pid}/files',files={'file':('x.kmz',b'not zip')}).status_code==422
  assert c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())}).status_code==200
  job=c.post(f'/api/projects/{pid}/analyze').json();j=wait(c,job['id']);assert j['state']=='done',j
  assert c.get(f'/api/projects/{pid}').json()['analysis']['routes']
  job=c.post(f'/api/projects/{pid}/preview').json();j=wait(c,job['id']);assert j['state']=='done',j
  assert c.get(f'/api/projects/{pid}/preview.png').status_code==200
  assert c.post(f'/api/projects/{pid}/render').status_code==422
  conf=c.get(f'/api/projects/{pid}').json()['config'];conf['coordinates_confirmed']=True;assert c.put(f'/api/projects/{pid}/config',json=conf).status_code==200
  job=c.post(f'/api/projects/{pid}/render').json();j=wait(c,job['id']);assert j['state']=='done',j
  data=c.get(f'/api/projects/{pid}/video.mp4').content;assert data[4:8]==b'ftyp'
  job=c.post(f'/api/projects/{pid}/preview').json();c.post('/api/jobs/'+job['id']+'/cancel');j=wait(c,job['id']);assert j['state'] in ['cancelled','done'],j
  assert c.get('/api/projects/'+'0'*32).status_code==404


def test_exclusions_and_body(drawing):
 from app.render import Scene
 cfg=settings(pois=[{'id':'P1','title':'Passarela 1','kind':'passarela','x':500150,'y':7800000}],exclusions=[[{'x':500100,'y':7799980},{'x':500200,'y':7799980},{'x':500200,'y':7800020},{'x':500100,'y':7800020}]])
 sc=Scene(drawing,cfg);im,meta=sc.frame(1.5);assert im.shape==(720,1280,3);assert meta['width_m']>0
 from shapely.geometry import Point
 for lane,tt,ok,L,rid in sc.routes:
  assert all(not sc.exclusion.contains(Point(*p)) for p in lane[ok])

def test_non_finite_coordinates():
 with pytest.raises(ValueError):Settings(pois=[{'title':'x','x':float('nan'),'y':0}])
