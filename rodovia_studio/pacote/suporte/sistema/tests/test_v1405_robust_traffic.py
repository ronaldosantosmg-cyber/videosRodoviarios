import json, tempfile
from pathlib import Path
from app.models import Settings
from app.simulation import TrafficSim, TYPE_DYN
from app import store
from app.rotas import paginas

BASE=Path(__file__).resolve().parents[1]

def test_version_1405_and_new_defaults():
    v=json.loads((BASE/'VERSAO.json').read_text(encoding='utf-8'))
    assert tuple(map(int,v['version'].split('.'))) >= (1,40,5)
    s=Settings()
    assert s.heavy_vehicle_reaction is True
    assert s.queue_capacity_model is True
    assert 1500 <= s.traffic_capacity_vphpl <= 2200


def _capacity_sim():
    sim=TrafficSim.__new__(TrafficSim)
    sim.capacity_rate=[1900/3600]
    return sim


def test_heavy_vehicle_consumes_more_lane_capacity_than_car():
    sim=_capacity_sim()
    assert sim.admission_headway(0,'truck') > sim.admission_headway(0,'car')
    assert sim.admission_headway(0,'carreta') > sim.admission_headway(0,'truck')
    assert TYPE_DYN['truck']['heavy'] and TYPE_DYN['bus']['heavy'] and TYPE_DYN['carreta']['heavy']


def test_heavy_vehicle_has_slower_longitudinal_dynamics():
    assert TYPE_DYN['truck']['a'] < TYPE_DYN['car']['a']
    assert TYPE_DYN['carreta']['a'] < TYPE_DYN['truck']['a']
    assert TYPE_DYN['truck']['T'] > TYPE_DYN['car']['T']


def test_atomic_json_keeps_same_format_and_is_readable(tmp_path):
    f=tmp_path/'config.json'
    data=Settings(name='Projeto teste').model_dump()
    store.write_json(f,data)
    loaded=json.loads(f.read_text(encoding='utf-8'))
    assert loaded['name']=='Projeto teste'
    assert loaded['schema_version']==data['schema_version']
    assert not list(tmp_path.glob('config.json.tmp-*'))


def test_atomic_json_does_not_replace_valid_file_on_serialization_error(tmp_path):
    f=tmp_path/'config.json';store.write_json(f,{'ok':1})
    try:store.write_json(f,{'bad':float('nan')})
    except ValueError:pass
    assert json.loads(f.read_text(encoding='utf-8'))=={'ok':1}


def test_frontend_is_served_as_independent_modules():
    html=paginas.index()
    assert '/js/00_nucleo.js' in html
    assert '/js/51_shell_profissional.js' in html
    assert '<script src="/app.js"></script>' not in html


def test_guard_handles_missing_actions_without_throwing_bundle():
    s=(BASE/'app/js/00_nucleo.js').read_text(encoding='utf-8')
    assert "typeof fn!=='function'" in s
    assert 'safeCall' in s

def test_capacity_model_forms_queue_without_collisions():
    import numpy as np
    from types import SimpleNamespace
    x=np.linspace(0,400,401);pts=np.c_[x,np.zeros_like(x)];tan=np.tile([1.,0.],(len(x),1))
    path={'p':pts,'d':x.copy(),'t':tan,'length':400.,'kinds':['main'],'links':[(('e',0),0.,400.)]}
    net=SimpleNamespace(paths=[path],edges=[{'kind':'main'}])
    s=SimpleNamespace(traffic_speed_kmh=70,traffic_density=8,duration_s=20,lane_blocks=[],curve_speed=False,
                      traffic_capacity_vphpl=900,queue_capacity_model=True,heavy_vehicle_reaction=True)
    def vt(kinds,ident): return 'truck' if ident[1]%3==0 else 'car'
    sim=TrafficSim(net,s,vt,duration=20)
    r=sim.report()
    assert r['max_waiting_at_entries']>0
    assert r['queue_vehicle_seconds_by_lane'][0]>0
    assert r['queue_discharged_by_lane'][0]>0
    assert r['rear_collisions']==0

def test_updater_preflight_rejects_python_syntax_error(tmp_path):
    from atualizador import validate_package
    (tmp_path/'suporte/sistema/app/js').mkdir(parents=True)
    (tmp_path/'manifest.json').write_text('{"version":"x"}',encoding='utf-8')
    (tmp_path/'suporte/sistema/VERSAO.json').write_text('{"version":"x"}',encoding='utf-8')
    (tmp_path/'suporte/sistema/app/server.py').write_text('def quebrado(:\n pass',encoding='utf-8')
    try:
        validate_package(tmp_path,lambda *_:None)
    except RuntimeError as e:
        assert 'Sintaxe Python' in str(e)
    else:
        raise AssertionError('Pacote com sintaxe inválida deveria ser recusado')
