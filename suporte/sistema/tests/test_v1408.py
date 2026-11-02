"""Rodovia Studio 1.40.8: KMZ protegido, rastreável e usado quando necessário."""
from pathlib import Path
import zipfile
import ezdxf
from app.models import Settings
from app.geometry import analyze


def settings(**kw):
    return Settings(coordinates_confirmed=True, hydrography=False, **kw)


def write_kmz(path: Path, with_line=True, with_poi=True):
    line = '<Placemark><name>Eixo KMZ</name><LineString><coordinates>-43,-19 -43.001,-19.001 -43.002,-19.0015</coordinates></LineString></Placemark>' if with_line else ''
    poi = '<Placemark><name>Referência</name><Point><coordinates>-43.001,-19.001</coordinates></Point></Placemark>' if with_poi else ''
    kml=f'<kml xmlns="http://www.opengis.net/kml/2.2"><Document>{line}{poi}</Document></kml>'
    with zipfile.ZipFile(path,'w') as z:z.writestr('doc.kml',kml)


def write_dxf_axis(path: Path):
    d=ezdxf.new();d.layers.new('EIXO');m=d.modelspace()
    # UTM 23S coordinates near lon/lat used in KMZ, adequate for independent CAD axis test.
    m.add_lwpolyline([(500000,7900000),(500200,7900000),(500400,7900030)],dxfattribs={'layer':'EIXO'})
    d.saveas(path)


def test_kmz_only_is_required_and_used_as_axis(tmp_path):
    write_kmz(tmp_path/'input.kmz')
    *_,r=analyze(tmp_path,settings())
    ks=r['kmz_status']
    assert ks['present'] and ks['read_ok'] and ks['used'] and ks['required']
    assert 'eixo_fallback' in ks['uses']
    assert r['routes'][0]['layer']=='KMZ'


def test_kmz_with_cad_axis_is_read_and_used_for_reference(tmp_path):
    write_dxf_axis(tmp_path/'input.dxf');write_kmz(tmp_path/'input.kmz')
    *_,r=analyze(tmp_path,settings())
    ks=r['kmz_status']
    assert ks['present'] and ks['read_ok']
    assert ks['used'] and not ks['required']
    assert 'georreferenciamento' in ks['uses']
    assert 'pois' in ks['uses']


def test_no_kmz_is_explicit_not_silent(tmp_path):
    write_dxf_axis(tmp_path/'input.dxf')
    *_,r=analyze(tmp_path,settings())
    ks=r['kmz_status']
    assert ks == {'present':False,'read_ok':False,'used':False,'required':False,'uses':[],'line_count':0,'poi_count':0,'message':'KMZ/KML não carregado.'}


def test_invalid_kmz_fails_with_clear_message(tmp_path):
    write_dxf_axis(tmp_path/'input.dxf');(tmp_path/'input.kmz').write_bytes(b'not-a-zip')
    try:
        analyze(tmp_path,settings())
    except ValueError as e:
        assert 'KMZ/KML presente, mas inválido' in str(e)
    else:
        raise AssertionError('KMZ inválido deveria interromper a análise.')


def test_ui_exposes_kmz_usage_status():
    js=Path(__file__).parents[1]/'app/js/29_arquivos_aparencia.js'
    text=js.read_text(encoding='utf-8')
    assert 'KMZ NECESSÁRIO' in text
    assert 'KMZ em uso' in text
    assert 'KMZ validado como referência' in text
    assert 'a análise atual depende deste KMZ' in text
