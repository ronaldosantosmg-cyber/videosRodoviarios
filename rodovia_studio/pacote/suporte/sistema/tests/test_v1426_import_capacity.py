import io,zipfile,json,math
import numpy as np
import pytest
from app.kmz_validation import validate
from app.geometry import read_kmz
from app.models import Settings
from app.simulation import TrafficSim
from test_v1426_transport import network

KML='<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>Referência</name><LineString><coordinates>-43,-19 -43.001,-19.001</coordinates></LineString></Placemark></Document></kml>'

def archive(path,kml=KML,media_mb=0):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('doc.kml',kml)
        if media_mb:
            with z.open('images/base.tif','w') as f:
                for _ in range(media_mb*16):f.write(b'\0'*65536)
    return path


def test_kmz_above_100mb_due_to_images_is_read_without_extracting_attachments(tmp_path):
    p=archive(tmp_path/'referencia.kmz',media_mb=101)
    with zipfile.ZipFile(p) as z:assert sum(i.file_size for i in z.infolist())>100*1024*1024
    assert validate(p)['attachments_extracted'] is False
    lines,pois=read_kmz(p,'EPSG:31983');assert len(lines)==1 and np.isfinite(lines[0]).all()
    assert set(x.name for x in tmp_path.iterdir())=={'referencia.kmz'}

@pytest.mark.parametrize('kml',[KML.replace('-43,-19','NaN,-19'),KML.replace('-43,-19','900,-19'),'<kml>','<!DOCTYPE kml [<!ENTITY x "aaa">]><kml>&x;</kml>'])
def test_invalid_xml_or_coordinates_rejected(tmp_path,kml):
    p=archive(tmp_path/'bad.kmz',kml)
    with pytest.raises(ValueError):read_kmz(p,'EPSG:31983')


def test_missing_kml_and_traversal_have_specific_messages(tmp_path):
    p=tmp_path/'bad.kmz'
    with zipfile.ZipFile(p,'w') as z:z.writestr('imagem.png',b'image')
    with pytest.raises(ValueError,match='não contém'):validate(p)
    with zipfile.ZipFile(p,'w') as z:z.writestr('../doc.kml',KML)
    with pytest.raises(ValueError,match='inseguro'):validate(p)


def test_kml_namespace_21_and_no_namespace_are_supported(tmp_path):
    for namespace in ['http://earth.google.com/kml/2.1','']:
        text=KML.replace('http://www.opengis.net/kml/2.2',namespace);p=archive(tmp_path/'reference.kmz',text)
        assert len(read_kmz(p,'EPSG:31983')[0])==1

@pytest.mark.parametrize('value',[3500,5000,10000,20000])
def test_high_positive_capacity_and_demand_are_accepted(value):
    s=Settings(traffic_capacity_vphpl=value,traffic_demand_vphpl=value)
    assert s.traffic_capacity_vphpl==value and s.traffic_demand_vphpl==value

@pytest.mark.parametrize('key',['traffic_capacity_vphpl','traffic_demand_vphpl'])
@pytest.mark.parametrize('value',[0,-1,'',float('nan'),float('inf'),20001])
def test_zero_and_invalid_traffic_inputs_are_rejected(key,value):
    with pytest.raises(ValueError):Settings(**{key:value})


def test_demand_3500_builds_queue_against_1900_without_forcing_3500_discharge():
    s=Settings(derive_traffic_paths=False,hydrography=False,duration_s=60,traffic_speed_kmh=40,traffic_demand_vphpl=3500,traffic_capacity_vphpl=1900)
    n=network(s);sim=TrafficSim(n,s,lambda *a:'car',duration=60);report=sim.report()
    assert report['rear_collisions']==0 and report['max_waiting_at_entries']>0
    assert report['saturation_indicator']['demand_capacity_ratio']==pytest.approx(3500/1900,abs=.001)
    assert 'F' in report['saturation_indicator']['status'] and 'não é classificação DNIT' in report['saturation_indicator']['scope']


def test_shared_itineraries_do_not_multiply_per_lane_demand():
    s=Settings(derive_traffic_paths=False,hydrography=False,traffic_demand_vphpl=3500,duration_s=3)
    n=network(s);n.paths.append(dict(n.paths[0]));sim=TrafficSim(n,s,lambda *a:'car',duration=3)
    assert sum(sim.rate)==pytest.approx(3500/3600)
