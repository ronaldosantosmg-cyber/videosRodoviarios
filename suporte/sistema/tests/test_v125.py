"""1.25: catálogo QuickMapServices — busca pela área do trecho, conversão para fonte XYZ/WMS, quadkey do Bing,
WMS 1.1.1/PNG, recusa de sistemas não Web Mercator, teste de nitidez no trecho e uso no projeto (API e tela).
A internet não é usada: as respostas do catálogo e os ladrilhos são simulados."""
import json,hashlib,socket,threading,time,urllib.parse
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app import qms,webmap
from app.models import Settings

LIST={'count':5,'next':None,'previous':None,'results':[
  {'id':1300,'name':'ESRI Satellite (ArcGIS/World_Imagery)','type':'tms','epsg':3857,'cumulative_status':'works','desc':'','extent':'SRID=4326;POLYGON ((-180 -85, -180 85, 180 85, 180 -85, -180 -85))'},
  {'id':77,'name':'Ortofoto MG 2024','type':'wms','epsg':3857,'cumulative_status':'works','desc':'','extent':'SRID=4326;POLYGON ((-46 -21, -46 -19, -44 -19, -44 -21, -46 -21))'},
  {'id':5976,'name':'Bing Maps Satellite Imagery','type':'tms','epsg':3857,'cumulative_status':'works','desc':'','extent':'SRID=4326;POLYGON ((-180 -85, -180 85, 180 85, 180 -85, -180 -85))'},
  {'id':9,'name':'OpenStreetMap Standard','type':'tms','epsg':3857,'cumulative_status':'works','desc':'','extent':'SRID=4326;POLYGON ((-180 -85, -180 85, 180 85, 180 -85, -180 -85))'},
  {'id':10,'name':'Some vector satellite WFS','type':'wfs','epsg':4326,'cumulative_status':'works','desc':'','extent':None},
  {'id':11,'name':'Yandex Satellite','type':'tms','epsg':3395,'cumulative_status':'works','desc':'','extent':'SRID=4326;POLYGON ((-180 -85, -180 85, 180 85, 180 -85, -180 -85))'}]}
DET={1300:{'id':1300,'name':'ESRI Satellite (ArcGIS/World_Imagery)','type':'tms','epsg':3857,'cumulative_status':'works','url':'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}','z_min':0,'z_max':19,'y_origin_top':True,'copyright_text':'','license_url':'','terms_of_use_url':''},
     77:{'id':77,'name':'Ortofoto MG 2024','type':'wms','epsg':3857,'cumulative_status':'works','url':'https://geo.exemplo.mg.gov.br/wms','params':'SERVICE=WMS&REQUEST=GetMap&SRS={proj}&HEIGHT={height}&WIDTH={width}&VERSION=1.1.1&BBOX={bbox}','layers':'orto2024','format':'image/png','turn_over':False,'z_max':21,'copyright_text':'Governo MG 2024','license_url':'https://exemplo/licenca','terms_of_use_url':''},
     5976:{'id':5976,'name':'Bing Maps Satellite Imagery','type':'tms','epsg':3857,'cumulative_status':'works','url':'https://t0.tiles.virtualearth.net/tiles/a{q}.jpeg?g=685&mkt=en-us&n=z','z_min':0,'z_max':19,'y_origin_top':True},
     11:{'id':11,'name':'Yandex Satellite','type':'tms','epsg':3395,'url':'https://sat01.maps.yandex.net/tiles?l=sat&x={x}&y={y}&z={z}','z_max':19,'y_origin_top':True},
     12:{'id':12,'name':'TMS de baixo para cima','type':'tms','epsg':None,'url':'https://{switch:a,b}.srv/x/{z}/{x}/{y}.png','z_max':25,'y_origin_top':False}}

class FakeHttp:
    def __init__(self):self.urls=[];self.fail=False
    def __call__(self,url,timeout=20):
        self.urls.append(url)
        if self.fail:raise OSError('sem rede')
        if '/geoservices/?' in url:return json.dumps(LIST).encode()
        sid=int(url.rstrip('/').split('/')[-1]);return json.dumps(DET[sid]).encode()

def test_quadkey_wms111_and_old_cache_key_kept():
    assert webmap.quadkey(3,3,5)=='213' and webmap.quadkey(1,0,0)=='0' and webmap.quadkey(0,0,0)==''
    s=webmap.WebSource('xyz','https://t0.tiles.virtualearth.net/tiles/a{q}.jpeg?g=685');assert s.tile_url(3,5,3).endswith('a213.jpeg?g=685')
    w=webmap.WebSource('wms','https://x/wms',None,'orto',19,'',version='1.1.1',fmt='image/png');q=dict(urllib.parse.parse_qsl(w.tile_url(10,300,400).split('?',1)[1]))
    assert q['VERSION']=='1.1.1' and q['SRS']=='EPSG:3857' and 'CRS' not in q and q['FORMAT']=='image/png'
    old=webmap.WebSource('wms','https://x/wms',None,'orto');assert old.cache=='wms_'+hashlib.sha256(b'https://x/wms|orto').hexdigest()[:12]   # cache da 1.19 preservado
    assert 'CRS=EPSG%3A3857' in old.tile_url(10,300,400) and w.cache!=old.cache
    with pytest.raises(ValueError):webmap.WebSource('xyz','https://srv/tiles.png')
    st=Settings.model_validate({**settings().model_dump(),'web_imagery':{'source':'wms','url':'https://x/wms','wms_layers':'orto'}})
    assert st.web_imagery.wms_version=='1.3.0' and st.web_imagery.qms_id is None and webmap.web_source(st).cache==old.cache

def test_search_area_filters_order_and_offline_cache(tmp_path):
    h=FakeHttp();r=qms.search(tmp_path,'satellite','todos',[-45.1,-20.1,-44.9,-19.9],True,True,fetch=h)
    p=dict(urllib.parse.parse_qsl(h.urls[0].split('?',1)[1]))
    assert p['search']=='satellite' and p['cumulative_status']=='works' and p['intersects_extent'].startswith('SRID=4326;POLYGON((-45.1 -20.1') and 'type' not in p
    ids=[x['id'] for x in r['results']]
    assert 10 not in ids and 9 not in ids            # WFS e mapa de ruas ficam fora
    assert ids[0]==77 and ids[-1]==11                 # local primeiro; EPSG:3395 por último
    assert [x for x in r['results'] if x['id']==11][0]['merc_ok'] is False and r['origem']=='online'
    h.fail=True;r2=qms.search(tmp_path,'satellite','todos',[-45.1,-20.1,-44.9,-19.9],True,True,fetch=h);assert r2['origem'].startswith('cache') and len(r2['results'])==len(r['results'])
    with pytest.raises(RuntimeError,match='QuickMapServices'):qms.search(tmp_path,'outra','tms',None,fetch=h)
    r3=qms.search(tmp_path,'','todos',None,True,False,fetch=FakeHttp());assert 9 in [x['id'] for x in r3['results']]

def test_to_web_imagery_conversions_and_refusals():
    a=qms.to_web_imagery(DET[1300]);assert a['source']=='xyz' and a['url'].endswith('/tile/{z}/{y}/{x}') and a['max_zoom']==19 and a['qms_id']==1300
    b=qms.to_web_imagery(DET[77]);assert b['source']=='wms' and b['url']=='https://geo.exemplo.mg.gov.br/wms' and b['wms_layers']=='orto2024' and b['wms_version']=='1.1.1' and b['wms_format']=='image/png'
    assert b['attribution'].startswith('Governo MG 2024') and 'QuickMapServices' in b['attribution'] and b['terms_url']=='https://exemplo/licenca' and b['max_zoom']==21
    c=qms.to_web_imagery(DET[5976]);assert '{q}' in c['url']
    d=qms.to_web_imagery(DET[12]);assert d['url']=='https://a.srv/x/{z}/{x}/{-y}.png' and d['max_zoom']==23
    with pytest.raises(ValueError,match='EPSG:3395'):qms.to_web_imagery(DET[11])
    with pytest.raises(ValueError,match='camada'):qms.to_web_imagery({**DET[77],'layers':'','params':''})
    s=qms.summary(DET[5976]);assert s['restricted'] and s['usable'];assert not qms.summary(DET[77])['restricted'];assert not qms.summary(DET[11])['usable']
    from app.models import WebImagery
    for k in (1300,77,5976,12):WebImagery.model_validate(qms.to_web_imagery(DET[k]))   # todos cabem no modelo do projeto

def _texture(seed,blur):
    rng=np.random.default_rng(seed);im=(rng.random((256,256,3))*255).astype(np.uint8)
    if blur:im=cv2.GaussianBlur(im,(0,0),blur)
    return cv2.imencode('.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,95])[1].tobytes()

def test_sample_sharpness_missing_and_scale(tmp_path):
    wi=qms.to_web_imagery(DET[1300]);calls=[]
    def sharp(root,z,y,x,source=None):calls.append(z);return _texture(x*7+y,0)
    def soft(root,z,y,x,source=None):return _texture(x*7+y,4)
    a=qms.sample(tmp_path,wi,-45.0,-19.95,tile_fn=sharp);b=qms.sample(tmp_path,wi,-45.0,-19.95,tile_fn=soft)
    assert a['nitidez']>3*b['nitidez'] and a['vazio']==0 and set(calls)=={19} and 4<=a['ladrilhos']<=9
    im=cv2.imdecode(np.frombuffer(__import__('base64').b64decode(a['jpeg_b64']),np.uint8),1);assert im.shape==(512,512,3)
    assert a['m_por_pixel_amostra']==pytest.approx(.2986*np.cos(np.radians(19.95)),abs=.002)
    low=qms.sample(tmp_path,{**wi,'max_zoom':17},-45.0,-19.95,tile_fn=sharp);assert low['zoom']==17 and low['ladrilhos']<=4 and low['nitidez']<a['nitidez']   # zoom menor = menos detalhe
    def holes(root,z,y,x,source=None):
        if (x+y)%2:raise OSError('404')
        return _texture(1,0)
    c=qms.sample(tmp_path,wi,-45.0,-19.95,tile_fn=holes);assert c['faltando']>=1 and c['vazio']>0 and c['erros']

def test_api_search_test_use_and_restricted(junction,monkeypatch):
    from app.server import app
    h=FakeHttp();monkeypatch.setattr(qms,'_http',h)
    monkeypatch.setattr(webmap,'tile',lambda root,z,y,x,source=None,**k:_texture(x+y,0))
    c=TestClient(app);pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
    assert c.get(f'/api/projects/{pid}/qms/buscar').status_code==409      # sem análise
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    from app import worker;worker.run(j['id'])
    r=c.get(f'/api/projects/{pid}/qms/buscar',params={'q':'ortofoto','tipo':'wms'}).json()
    p=dict(urllib.parse.parse_qsl(h.urls[-1].split('?',1)[1]));lon0,lat0,lon1,lat1=qms.ewkt_bbox(p['intersects_extent'])
    assert p['type']=='wms' and -46<lon0<lon1<-44 and -21<lat0<lat1<-19 and r['results'][0]['id']==77
    assert c.get(f'/api/projects/{pid}/qms/buscar',params={'tipo':'wfs'}).status_code==422
    t=c.get(f'/api/projects/{pid}/qms/77/teste').json();assert t['usable'] and t['nitidez']>0 and t['zoom']==19 and t['jpeg_b64']
    assert c.get(f'/api/projects/{pid}/qms/11/teste').json()['usable'] is False
    assert c.post(f'/api/projects/{pid}/qms/11/usar',json={}).status_code==422
    assert c.post(f'/api/projects/{pid}/qms/5976/usar',json={}).status_code==409
    assert c.post(f'/api/projects/{pid}/qms/5976/usar',json={'aceito_termos':True}).status_code==200
    u=c.post(f'/api/projects/{pid}/qms/77/usar',json={}).json()['web_imagery'];assert u['source']=='wms' and u['qms_id']==77 and u['wms_version']=='1.1.1'
    conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['web_imagery']['wms_layers']=='orto2024' and conf['web_imagery']['qms_name']=='Ortofoto MG 2024'
    src=webmap.web_source(Settings.model_validate(conf));assert 'SRS=EPSG%3A3857' in src.tile_url(18,1000,2000) and 'FORMAT=image%2Fpng' in src.tile_url(18,1000,2000)
    d=c.get('/api/qms/5976').json();assert d['restricted'] and d['usable']

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_qms_panel(junction,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    from app.server import app
    monkeypatch.setattr(qms,'_http',FakeHttp())
    monkeypatch.setattr(webmap,'tile',lambda root,z,y,x,source=None,**k:_texture(x+y,0 if 'orto' in (source.layers or '') else 5))
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60);pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            import os
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1200})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=200,body=_texture(1,0),headers={'content-type':'image/jpeg'}))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof cfg!=="undefined" && cfg && pid',timeout=20000)
            page.evaluate("document.getElementById('webBox').open=true;document.getElementById('webBox').closest('section').classList.remove('collapsed')")
            page.fill('#qmsQ','satellite');page.press('#qmsQ','Enter')                     # Enter busca
            page.wait_for_selector('#qmsList [data-qms]');ids=page.evaluate("[...document.querySelectorAll('#qmsList [data-qms]')].map(e=>+e.dataset.qms)")
            assert ids[0]==77 and 11 in ids and page.locator('#qmsList [data-qms="11"] button[data-qa=use]').is_disabled()
            page.click('#qmsTestTop');page.wait_for_function("document.getElementById('qmsInfo').textContent.includes('Mais nítido')",timeout=30000)
            assert page.evaluate("+document.querySelector('#qmsList [data-qms]').dataset.qms")==77 and page.locator('#qmsList img').count()>=3
            page.click('#qmsList [data-qms="5976"] button[data-qa=use]');page.wait_for_selector('#confirmDlg[open]');page.click('#confirmNo')
            assert c.get(f'/api/projects/{pid}').json()['config']['web_imagery']['source']=='esri'            # cancelado: nada muda
            page.click('#qmsList [data-qms="77"] button[data-qa=use]');page.wait_for_function("cfg.web_imagery.qms_id===77")
            assert 'QuickMapServices' in page.inner_text('#webInfo') and page.evaluate("document.querySelector('#qmsList [data-qms=\"77\"]').classList.contains('inuse')")
            conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['web_imagery']['qms_id']==77 and conf['web_imagery']['source']=='wms'
            # Reaplicar pelo formulário manual mantém versão/formato do WMS escolhido no catálogo.
            page.click('#webApply');page.wait_for_timeout(500);conf=c.get(f'/api/projects/{pid}').json()['config'];assert conf['web_imagery']['wms_version']=='1.1.1' and conf['web_imagery']['qms_id']==77
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
