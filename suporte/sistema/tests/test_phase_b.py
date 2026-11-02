"""Fase B: camadas DXF, imagem georreferenciada local, exportação e reimportação."""
import io,json,zipfile
import numpy as np
import pytest
import ezdxf
from PIL import Image
from pyproj import CRS,Transformer
from test_workflow import drawing,settings,wait
from app.models import Settings,OverlayLayer
from app.chainage import Stationing

def overlay_dxf(path):
    d=ezdxf.new();m=d.modelspace()
    for l in ['PAVIMENTO_NOVO','CROQUI']:d.layers.new(l)
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO_NOVO'});h.paths.add_polyline_path([(500100,7800020),(500200,7800020),(500200,7800030),(500100,7800030)],is_closed=True)
    m.add_lwpolyline([(500100,7800040),(500200,7800040)],dxfattribs={'layer':'CROQUI'});m.add_text('nota',dxfattribs={'layer':'CROQUI'})
    d.saveas(path)

def test_overlay_layers_roles_offset_order_and_delete(drawing):
    from app.geometry import analyze
    from app.render import Scene
    (drawing/'camadas').mkdir();oid='a'*32;overlay_dxf(drawing/'camadas'/(oid+'.dxf'))
    ov=OverlayLayer(id=oid,name='Projeto vizinho',roles={'PAVIMENTO_NOVO':'pavement','CROQUI':''},color='#ff0000',opacity=1,line_width_m=1.5,
        alignment={'mode':'translation','pairs':[{'dxf':{'x':0,'y':0},'image':{'x':0,'y':-2}}],'applied':True})
    es,*_,rep=analyze(drawing,settings(overlays=[ov]))
    pav=[e for e in es if e.get('overlay')==oid and e['role']=='pavement'];sk=[e for e in es if e.get('overlay')==oid and e['role']=='overlay']
    assert pav and sk and np.isclose(pav[0]['points'][:,1].min(),7800018) and np.isclose(sk[0]['points'][0,1],7800038)
    assert rep['overlays'][0]['entities']==len(pav)+len(sk)
    sc=Scene(drawing,settings(overlays=[ov]));x,y=np.rint(sc.worldpx(np.array([[500150,7800038]]))[0]).astype(int)
    assert sc.overlay[y,x,0]>200 and sc.overlay[y,x,3]>200 and sc.overlay[y,x,1]<80
    off=Scene(drawing,settings(overlays=[ov.model_copy(update={'enabled':False})]));assert off.overlay[y,x,3]==0
    ign=analyze(drawing,settings(overlays=[ov.model_copy(update={'roles':{'PAVIMENTO_NOVO':'ignore','CROQUI':'ignore'}})]))[0]
    assert not any(e.get('overlay') for e in ign)
    # CRS próprio: a camada em WGS84 é reprojetada para o CRS do projeto.
    tr=Transformer.from_crs(31983,4326,always_xy=True);lon,lat=tr.transform(500150,7800040)
    d=ezdxf.new();d.layers.new('GEO');d.modelspace().add_lwpolyline([(lon,lat),(lon+.0001,lat)],dxfattribs={'layer':'GEO'});oid2='b'*32;d.saveas(drawing/'camadas'/(oid2+'.dxf'))
    es,*_=analyze(drawing,settings(overlays=[OverlayLayer(id=oid2,crs='EPSG:4326')]))
    g=[e for e in es if e.get('overlay')==oid2][0];assert np.allclose(g['points'][0],[500150,7800040],atol=1e-3)

def test_overlay_api_upload_list_delete(drawing):
    from fastapi.testclient import TestClient
    from app.server import app
    overlay_dxf(drawing/'extra.dxf')
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        assert c.post(f'/api/projects/{pid}/overlays',files={'file':('x.txt',b'a')}).status_code==415
        r=c.post(f'/api/projects/{pid}/overlays',files={'file':('vizinho.dxf',(drawing/'extra.dxf').read_bytes())});assert r.status_code==201,r.text
        oid=r.json()['overlay']['id'];assert {l['name'] for l in r.json()['layers']}>={'PAVIMENTO_NOVO','CROQUI'}
        cfg=c.get(f'/api/projects/{pid}').json()['config'];assert cfg['overlays'][0]['roles']['PAVIMENTO_NOVO']=='pavement'
        assert c.get(f'/api/projects/{pid}/overlays/{oid}/layers').status_code==200
        assert c.delete(f'/api/projects/{pid}/overlays/{oid}').status_code==200
        assert c.get(f'/api/projects/{pid}').json()['config']['overlays']==[]
        assert c.get(f'/api/projects/{pid}/overlays/{oid}/layers').status_code==404

def make_image(w=400,h=300):
    a=np.zeros((h,w,3),np.uint8);a[:]=(30,90,40);a[100:110,200:210]=(255,0,0);return a  # marcador: colunas 200-209, linhas 100-109

def marker_color(sc,x,y):
    px,py=np.floor(sc.worldpx(np.array([[x,y]]))[0]).astype(int);return sc.map[py,px]

def geotiff(path,a,x0,y0,res,epsg=31983,point=False):
    import tifffile
    keys=[1,1,0,3, 1024,0,1,1, 1025,0,1,2 if point else 1, 3072,0,1,epsg]
    shift=res/2 if point else 0
    tifffile.imwrite(path,a,photometric='rgb',extratags=[(33550,'d',3,(res,res,0.),False),(33922,'d',6,(0,0,0,x0+shift,y0-shift,0),False),(34735,'H',len(keys),keys,False)])

def scene_with(drawing,**kw):
    from app.render import Scene
    return Scene(drawing,Settings(**{**settings().model_dump(),'imagery':'local','imagery_pixels':2048,**kw}))

def test_geotiff_positioned_at_known_point(drawing):
    from app.models import LocalImagery
    base=drawing/'imagem_local';base.mkdir();a=make_image()
    # Pixel (col 200,lin 100) com 0,5 m: canto em X=499950+100, Y=7800075-50.
    geotiff(base/'ort.tif',a,499950,7800075,.5)
    sc=scene_with(drawing,local_imagery=LocalImagery(name='ort.tif',image='ort.tif'))
    assert tuple(marker_color(sc,500052.5,7800022.5))==(255,0,0)
    assert tuple(marker_color(sc,500040,7800022.5))!=(255,0,0)
    assert 'Imagem local: ort.tif' in sc.attribution and '0.50 m/px' in sc.attribution
    geotiff(base/'pt.tif',a,499950,7800075,.5,point=True)
    sc=scene_with(drawing,local_imagery=LocalImagery(name='pt.tif',image='pt.tif'));assert tuple(marker_color(sc,500052.5,7800022.5))==(255,0,0)

def test_world_file_and_prj_and_geographic(drawing):
    from app.models import LocalImagery
    base=drawing/'imagem_local';base.mkdir();a=make_image()
    Image.fromarray(a).save(base/'foto.png')
    # Arquivo de mundo: centro do pixel superior esquerdo.
    (base/'foto.pgw').write_text('0.5\n0\n0\n-0.5\n499950.25\n7800074.75\n')
    (base/'foto.prj').write_text(CRS.from_epsg(31983).to_wkt())
    sc=scene_with(drawing,local_imagery=LocalImagery(name='foto.png',image='foto.png',world='foto.pgw',prj='foto.prj'))
    assert tuple(marker_color(sc,500052.5,7800022.5))==(255,0,0)
    # Mesma imagem em graus (EPSG:4326 informado): o marcador cai no ponto reprojetado.
    tr=Transformer.from_crs(31983,4326,always_xy=True);lon,lat=tr.transform(500052.5,7800022.5)
    d=4.6e-6;(base/'geo.pgw').write_text(f'{d}\n0\n0\n{-d}\n{lon-205*d+d/2}\n{lat+105*d-d/2}\n')
    Image.fromarray(a).save(base/'geo.png')
    sc=scene_with(drawing,local_imagery=LocalImagery(name='geo.png',image='geo.png',world='geo.pgw',crs='EPSG:4326'))
    assert tuple(marker_color(sc,500052.5,7800022.5))==(255,0,0)

def test_reject_image_without_georeference(drawing):
    from app.local_imagery import georef
    from fastapi.testclient import TestClient
    from app.server import app
    b=io.BytesIO();Image.fromarray(make_image()).save(b,'PNG')
    (drawing/'semgeo.png').write_bytes(b.getvalue())
    with pytest.raises(ValueError,match='sem georreferência'):georef(drawing/'semgeo.png')
    (drawing/'x.pgw').write_text('0.5\n0\n0\n-0.5\n1\n2\n')
    with pytest.raises(ValueError,match='sistema de coordenadas'):georef(drawing/'semgeo.png',drawing/'x.pgw')
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        r=c.post(f'/api/projects/{pid}/imagery',files=[('files',('foto.png',b.getvalue()))]);assert r.status_code==422 and 'georreferência' in r.json()['detail']
        r=c.post(f'/api/projects/{pid}/imagery',files=[('files',('foto.png',b.getvalue())),('files',('foto.pgw',b'0.5\n0\n0\n-0.5\n499950.25\n7800074.75\n'))],data={'crs':'EPSG:31983'})
        assert r.status_code==200,r.text;assert c.get(f'/api/projects/{pid}').json()['config']['imagery']=='local'

MARKS=dict(chainage={'start':{'x':500030.,'y':7800000.}},
    direction_marks=[{'id':'d1','start':{'x':500100.,'y':7799995.},'end':{'x':500140.,'y':7799995.}}],
    flow_overrides=[{'id':'f1','x':500150.,'y':7800005.,'action':'disable'}],
    traffic_paths=[{'id':'t1','name':'Fluxo A','kind':'device','points':[{'x':500020.,'y':7800005.},{'x':500200.,'y':7800005.}]}],
    exclusions=[[{'x':500100.,'y':7799980.},{'x':500120.,'y':7799980.},{'x':500120.,'y':7799990.}]],
    oae_marks=[{'id':'o1','name':'Ponte','start':{'x':500100.,'y':7800000.},'end':{'x':500160.,'y':7800000.},'level_m':7.}],
    no_connection_zones=[{'id':'z1','kind':'point','point':{'x':500200.,'y':7800010.},'radius_m':12.},{'id':'z2','kind':'area','points':[{'x':500250.,'y':7800000.},{'x':500260.,'y':7800000.},{'x':500260.,'y':7800010.}]}],
    pois=[{'id':'a','title':'Obra A','kind':'passarela','x':500150.,'y':7800000.,'anchor':{'x':500155.,'y':7800020.}},{'id':'b','title':'Obra B','x':500250.,'y':7800000.,'km_mode':'manual','km_m':330500.}],
    works=[{'id':'w1','description':'Correção','km_start_m':100.,'km_end_m':150.,'kind':'correcao','x':500120.,'y':7800000.}])

def exported(drawing):
    from app.render import Scene
    from app.exporters import features
    s=settings(**MARKS);sc=Scene(drawing,s)
    return s,sc,features(s,sc.stationing,sc.axes,sc.network.raw_info,sc.oae)

def compare(a,b,tol):
    if isinstance(a,dict):
        assert set(a)==set(b),(a.keys(),b.keys())
        for k in a:compare(a[k],b[k],tol)
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y,tol)
    elif isinstance(a,float) and isinstance(b,(int,float)):assert abs(a-b)<=tol,(a,b)
    else:assert a==b,(a,b)

@pytest.mark.parametrize('fmt,tol',[('geojson',1e-6),('wgs84',2e-3),('kml',2e-3),('kmz',2e-3)])
def test_export_reimport_preserves_geometry_and_km(drawing,fmt,tol):
    from app import exporters
    s,sc,feats=exported(drawing)
    data={'geojson':lambda:exporters.geojson(feats,s.crs).encode(),'wgs84':lambda:exporters.geojson(feats,s.crs,True).encode(),'kml':lambda:exporters.kml(feats,s.crs).encode(),'kmz':lambda:exporters.kmz(feats,s.crs)}[fmt]()
    name={'geojson':'m.geojson','wgs84':'m.geojson','kml':'m.kml','kmz':'m.kmz'}[fmt]
    back=exporters.read_any(data,name,s.crs)
    blank=settings().model_dump();cfg,counts=exporters.apply_import(blank,back);s2=Settings.model_validate(cfg)
    keys=['chainage','direction_marks','flow_overrides','traffic_paths','exclusions','no_connection_zones','pois','works']
    for k in keys:compare(s.model_dump()[k],s2.model_dump()[k],tol)
    # OAE: extremos sobre o eixo, km iguais.
    st=Stationing(sc.axis,s2.km_start_m,s2.chainage.start);o=s2.oae_marks[0]
    assert st.km([o.start.x,o.start.y])==pytest.approx(sc.oae[0]['km_start_m'],abs=max(tol,1e-6)*10)
    assert st.km([o.end.x,o.end.y])==pytest.approx(sc.oae[0]['km_end_m'],abs=max(tol,1e-6)*10)
    # km exportado de cada intervenção = km recalculado na reimportação.
    kms={p['name']:p.get('km') for g,p in back if p.get('rs_type')=='intervencao'}
    assert float(kms['Obra A'])==pytest.approx(st.km([500150,500150*0+7800000]),abs=1e-3)
    assert float(kms['Obra B'])==330500

def test_export_dxf_and_csv(drawing,tmp_path):
    from app import exporters
    from app.per import read_csv
    s,sc,feats=exported(drawing)
    exporters.dxf(feats,tmp_path/'m.dxf');doc=ezdxf.readfile(tmp_path/'m.dxf')
    names={e.dxf.layer for e in doc.modelspace()}
    assert {'RS_EIXO','RS_TRAJETORIA','RS_SENTIDO','RS_EXCLUSAO','RS_OAE','RS_SEM_CONEXAO','RS_INTERVENCAO','RS_CHAMADA','RS_MARCO_KM','RS_INICIO_KM','RS_FLUXO_INCLUIDO','RS_FLUXO_OVERRIDE','RS_OBRA'}<=names
    e=next(e for e in doc.modelspace() if e.dxf.layer=='RS_OAE');x=json.loads(''.join(v for _,v in e.get_xdata('RODOVIA')));assert x['name']=='Ponte'
    text=exporters.works_csv(feats);rows=read_csv(text.encode('utf-8'))
    a=next(r for r in rows if r.description=='Obra A');b=next(r for r in rows if r.description=='Obra B');w=next(r for r in rows if r.description=='Correção')
    assert (a.x,a.y)==(500150,7800000) and round(a.km_start_m)==round(sc.stationing.km([500150,7800000]))
    assert b.km_start_m==330500 and (w.km_start_m,w.km_end_m)==(100,150)

def test_project_package_roundtrip_and_safety(drawing,tmp_path):
    from app.exporters import package,unpack
    import hashlib
    (drawing/'config.json').write_text(json.dumps(settings(**MARKS).model_dump()),encoding='utf-8')
    (drawing/'camadas').mkdir();overlay_dxf(drawing/'camadas'/('c'*32+'.dxf'))
    data=package(drawing,'1.4.0');out=tmp_path/'novo';out.mkdir();m=unpack(data,out)
    for f in m['files']:assert (out/f['path']).read_bytes()==(drawing/f['path']).read_bytes()
    bad=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as z,zipfile.ZipFile(bad,'w') as w:
        for i in z.infolist():w.writestr(i,z.read(i) if i.filename!='projeto/input.dxf' else b'alterado')
    with pytest.raises(ValueError,match='corrompido'):unpack(bad.getvalue(),tmp_path/'x')
    evil=io.BytesIO()
    with zipfile.ZipFile(evil,'w') as w:w.writestr('manifest.json',json.dumps({'files':[{'path':'../fora.txt','sha256':hashlib.sha256(b'x').hexdigest()}]}));w.writestr('projeto/../fora.txt','x')
    with pytest.raises(ValueError,match='não permitido'):unpack(evil.getvalue(),tmp_path/'y')

def test_api_export_package_import_and_png_sequence(drawing):
    from fastapi.testclient import TestClient
    from app.server import app
    with TestClient(app) as c:
        pid=c.post('/api/projects',json=settings(**MARKS,png_export={'start_s':1,'end_s':1.2,'every_n_frames':3,'rgba_layers':True}).model_dump()).json()['id']
        c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(drawing/'input.dxf').read_bytes())})
        j=wait(c,c.post(f'/api/projects/{pid}/export').json()['id']);assert j['state']=='done',j
        names={f['name'] for f in c.get(f'/api/projects/{pid}/exports').json()['files']}
        assert {'modelo_wgs84.geojson','modelo_EPSG31983.geojson','modelo.kml','modelo.kmz','marcacoes.dxf','obras.csv'}<=names
        kml=c.get(f'/api/projects/{pid}/exports/modelo.kml');assert kml.status_code==200 and b'<kml' in kml.content
        pkg=c.get(f'/api/projects/{pid}/package.zip');assert pkg.status_code==200
        new=c.post('/api/import_package',files={'file':('p.zip',pkg.content)});assert new.status_code==201,new.text
        assert new.json()['config']['oae_marks'][0]['name']=='Ponte'
        # Importar marcações no projeto novo (substitui pelo arquivo).
        nid=new.json()['id'];geo=c.get(f'/api/projects/{pid}/exports/modelo_wgs84.geojson').content
        r=c.post(f'/api/projects/{nid}/import_markings',files={'file':('m.geojson',geo)});assert r.status_code==200 and r.json()['imported']['pois']==2
        assert c.post(f'/api/projects/{nid}/import_markings',files={'file':('m.geojson',b'{"type":"FeatureCollection","features":[]}')}).status_code==422
        cfg=c.get(f'/api/projects/{pid}').json()['config'];cfg['coordinates_confirmed']=True;c.put(f'/api/projects/{pid}/config',json=cfg)
        j=wait(c,c.post(f'/api/projects/{pid}/frames').json()['id'],180);assert j['state']=='done',j
        from app import store
        seq=sorted((store.ROOT/pid/'quadros_png').iterdir())[-1];info=json.loads((seq/'sequencia.json').read_text(encoding='utf-8'))
        assert info['count']==3 and len(list(seq.glob('quadro_*.png')))==3 and len(list((seq/'camadas_rgba').glob('*.png')))==3
        layer=np.array(Image.open(next((seq/'camadas_rgba').glob('*.png'))));assert layer.shape[2]==4
        assert (layer[:,:,3]==0).any() and (layer[:,:,3]==255).any()
        assert (layer[:20,:,3]==255).all()  # cabeçalho opaco
