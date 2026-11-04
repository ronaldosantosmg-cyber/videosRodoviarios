import copy,hashlib,importlib.util,json,os
from pathlib import Path

spec=importlib.util.spec_from_file_location('rodovia_startup',Path(__file__).resolve().parents[1]/'suporte/sistema/run.py')
startup=importlib.util.module_from_spec(spec);spec.loader.exec_module(startup)


def health(tmp_path):
    (tmp_path/'app').mkdir();(tmp_path/'app/fleet_policy.py').write_bytes(b'new policy')
    (tmp_path/'VERSAO.json').write_text(json.dumps({'version':'3.23'}))
    return {'status':'ok','data':os.environ.get('RODOVIA_DATA',str(tmp_path/'data')),'runtime':{'program_root':str(tmp_path),'version_at_start':'3.23',
        'source_fingerprint_at_start':hashlib.sha256(b'new policy').hexdigest(),'disk_changed':False,'policy':{'probe':{'ok':True}}}}


def test_same_root_and_actual_policy_are_required(tmp_path):
    data=health(tmp_path);assert startup.session_state(data,tmp_path)=='compatible'
    old=copy.deepcopy(data);old['runtime']['version_at_start']='3.22'
    assert startup.session_state(old,tmp_path)=='stale_studio'
    old=copy.deepcopy(data);old['runtime']['source_fingerprint_at_start']='old'
    assert startup.session_state(old,tmp_path)=='stale_studio'
    old=copy.deepcopy(data);old['runtime']['policy']['probe']['ok']=False
    assert startup.session_state(old,tmp_path)=='stale_studio'


def test_another_installation_is_not_reused(tmp_path):
    data=health(tmp_path);data['runtime']['program_root']=str(tmp_path/'other')
    assert startup.session_state(data,tmp_path)=='other_installation'


def test_legacy_status_ok_is_not_proof_of_compatible_code():
    assert startup.session_state({'status':'ok','version':'3.23'})=='unverified_studio'
    assert startup.session_state(None)=='other_service'


def test_modified_files_are_not_reused(tmp_path):
    data=health(tmp_path);data['runtime']['disk_changed']=True
    assert startup.session_state(data,tmp_path)=='stale_studio'


def test_explicit_data_root_is_respected(tmp_path,monkeypatch):
    data=health(tmp_path);data['data']=str(tmp_path/'data1')
    monkeypatch.setenv('RODOVIA_DATA',str(tmp_path/'data2'))
    assert startup.session_state(data,tmp_path)=='other_installation'
