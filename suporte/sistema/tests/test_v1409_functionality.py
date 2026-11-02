"""Rodovia Studio 1.40.9 — matriz ampliada de funcionamento e robustez."""
from pathlib import Path
from types import SimpleNamespace
import json, zipfile
import numpy as np
import ezdxf
import pytest

from app.models import Settings
from app.geometry import analyze
from app.simulation import TrafficSim
from app import store

BASE=Path(__file__).resolve().parents[1]

def settings(**kw):
    return Settings(coordinates_confirmed=True, hydrography=False, **kw)

def dxf_axis(path:Path):
    d=ezdxf.new();d.layers.new('EIXO');m=d.modelspace()
    m.add_lwpolyline([(500000,7900000),(500100,7900000),(500200,7900020)],dxfattribs={'layer':'EIXO'})
    d.saveas(path)

def kmz(path:Path, line=True, point=True):
    l='<Placemark><name>Eixo ref</name><LineString><coordinates>-43,-19 -43.001,-19.001 -43.002,-19.0015</coordinates></LineString></Placemark>' if line else ''
    p='<Placemark><name>POI ref</name><Point><coordinates>-43.001,-19.001</coordinates></Point></Placemark>' if point else ''
    with zipfile.ZipFile(path,'w') as z:z.writestr('doc.kml',f'<kml xmlns="http://www.opengis.net/kml/2.2"><Document>{l}{p}</Document></kml>')

def test_kmz_required_used_and_invalid_fails_closed(tmp_path):
    kmz(tmp_path/'input.kmz');*_,r=analyze(tmp_path,settings())
    assert r['kmz_status']['required'] and 'eixo_fallback' in r['kmz_status']['uses']
    (tmp_path/'input.kmz').write_bytes(b'corrompido')
    with pytest.raises(ValueError,match='KMZ/KML presente, mas inválido'):analyze(tmp_path,settings())

def test_kmz_reference_is_used_with_valid_cad_axis(tmp_path):
    dxf_axis(tmp_path/'input.dxf');kmz(tmp_path/'input.kmz');*_,r=analyze(tmp_path,settings())
    s=r['kmz_status'];assert s['read_ok'] and s['used'] and not s['required']
    assert 'georreferenciamento' in s['uses'] and 'pois' in s['uses']

def test_atomic_save_survives_invalid_replacement(tmp_path):
    f=tmp_path/'config.json';store.write_json(f,{'name':'válido','n':1})
    before=f.read_bytes()
    with pytest.raises(ValueError):store.write_json(f,{'bad':float('nan')})
    assert f.read_bytes()==before and json.loads(f.read_text())['name']=='válido'
    assert not list(tmp_path.glob('*.tmp-*'))

def _net(length=500):
    x=np.linspace(0,length,int(length)+1);pts=np.c_[x,np.zeros_like(x)];tan=np.tile([1.,0.],(len(x),1))
    return SimpleNamespace(paths=[{'p':pts,'d':x.copy(),'t':tan,'length':float(length),'kinds':['main'],'links':[(('e',0),0.,float(length))]}],edges=[{'kind':'main'}])

def test_heavy_traffic_queue_forms_and_dissipates_without_collision():
    s=SimpleNamespace(traffic_speed_kmh=70,traffic_density=10,duration_s=25,lane_blocks=[],curve_speed=False,
        traffic_capacity_vphpl=850,queue_capacity_model=True,heavy_vehicle_reaction=True)
    sim=TrafficSim(_net(),s,lambda kinds,ident:'carreta' if ident[1]%4==0 else ('truck' if ident[1]%3==0 else 'car'),duration=25)
    r=sim.report();assert r['max_waiting_at_entries']>0 and r['queue_discharged_by_lane'][0]>0
    assert r['rear_collisions']==0 and r['min_gap_m']>=0

def test_lane_change_entire_maneuver_must_fit_allowed_zone():
    sim=TrafficSim.__new__(TrafficSim)
    sim.paths=[{'length':1000,'lane_change':'marked','lane_change_sections':[{'start_m':100,'end_m':300,'mode':'allow'}]}]
    assert sim.lane_change_window_allowed(0,120,100)
    assert not sim.lane_change_window_allowed(0,250,100)
    sim.paths[0]['lane_change_sections'].append({'start_m':180,'end_m':220,'mode':'deny'})
    assert not sim.lane_change_window_allowed(0,120,100)

def test_no_project_specific_tokens_in_professional_workspace():
    text='\n'.join((BASE/'app/js/50_desktop_workspace.js').read_text(encoding='utf-8').splitlines()+
                   (BASE/'app/js/51_shell_profissional.js').read_text(encoding='utf-8').splitlines())
    for token in ('BR-381','TH57','Nova 381','nova381'):
        assert token.lower() not in text.lower()

def test_all_python_sources_compile():
    import py_compile
    for p in (BASE/'app').rglob('*.py'):py_compile.compile(str(p),doraise=True)

def test_all_javascript_sources_parse_with_node_when_available():
    import shutil, subprocess
    node=shutil.which('node')
    for p in (BASE/'app/js').glob('*.js'):
        s=p.read_text(encoding='utf-8');assert '\x00' not in s,p.name
        if node:
            r=subprocess.run([node,'--check',str(p)],capture_output=True,text=True)
            assert r.returncode==0, f'{p.name}: {r.stderr}'
