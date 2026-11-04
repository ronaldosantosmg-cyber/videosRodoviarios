"""Reparação deve conferir arquivos e preservar a possibilidade de restauração."""
import hashlib
import json
from pathlib import Path
import zipfile
import pytest
import atualizador as U


def fixture_package(tmp_path,version='3.22.0'):
    root=tmp_path/'install';program=root/'sistema/programa'
    (program/'app').mkdir(parents=True)
    (program/'app/server.py').write_text('# server\n')
    (program/'VERSAO.json').write_text(json.dumps({'version':'3.22.0'}))
    package=tmp_path/'package'
    files={'suporte/sistema/app/server.py':b'# server\n','suporte/sistema/app/fleet_policy.py':b'# novo\n','suporte/sistema/VERSAO.json':json.dumps({'version':version}).encode()}
    for name,data in files.items():
        path=package/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    (package/'manifest.json').write_text(json.dumps({'version':version,'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}))
    updates=root/'atualizacoes';updates.mkdir()
    archive=updates/'RodoviaStudio_3_22_atualizacao.zip'
    with zipfile.ZipFile(archive,'w') as output:
        for path in package.rglob('*'):
            if path.is_file():output.write(path,path.relative_to(package))
    return root,program,archive


@pytest.mark.parametrize('missing',[False,True])
def test_same_version_repairs_with_backup(tmp_path,missing):
    root,program,archive=fixture_package(tmp_path);policy=program/'app/fleet_policy.py'
    if not missing:policy.write_text('# antigo\n')
    result=U.search_and_apply(root,say=lambda message:None,check_running=False)
    assert result['repaired'] is True
    assert policy.read_text()=='# novo\n'
    assert json.loads((Path(result['backup'])/'rollback.json').read_text())['state']=='applied'
    assert not archive.exists()


def test_identical_same_version_verified_without_backup(tmp_path):
    root,program,archive=fixture_package(tmp_path)
    (program/'app/fleet_policy.py').write_text('# novo\n')
    assert U.search_and_apply(root,say=lambda message:None,check_running=False) is None
    assert not (root/'sistema/backups').exists()
    assert (root/'atualizacoes/aplicadas'/archive.name).exists()


def test_lower_version_never_downgrades(tmp_path):
    root,program,archive=fixture_package(tmp_path,'3.21.0')
    policy=program/'app/fleet_policy.py';policy.write_text('# instalado\n')
    assert U.search_and_apply(root,say=lambda message:None,check_running=False) is None
    assert policy.read_text()=='# instalado\n'
    assert json.loads((program/'VERSAO.json').read_text())['version']=='3.22.0'


def test_final_hash_mismatch_rolls_back_without_success_archive(tmp_path,monkeypatch):
    root,program,archive=fixture_package(tmp_path)
    policy=program/'app/fleet_policy.py';policy.write_text('# antigo\n')
    original=U._sha
    def mismatched(path):
        if path==policy and path.read_text()=='# novo\n':return 'corrompido'
        return original(path)
    monkeypatch.setattr(U,'_sha',mismatched)
    with pytest.raises(RuntimeError,match='versão anterior foi restaurada'):
        U.search_and_apply(root,say=lambda message:None,check_running=False)
    assert policy.read_text()=='# antigo\n'
    assert archive.exists()
    assert not (root/'atualizacoes/aplicadas'/archive.name).exists()


def test_changed_python_with_same_mtime_and_size_does_not_reuse_old_bytecode(tmp_path):
    import importlib.util
    import os
    import py_compile
    root,program,_=fixture_package(tmp_path)
    package=tmp_path/'package'
    source=program/'app/fleet_policy.py'
    incoming=package/'suporte/sistema/app/fleet_policy.py'
    source.write_text('VALUE=1\n')
    incoming.write_text('VALUE=2\n')
    timestamp=1700000000
    os.utime(source,(timestamp,timestamp))
    os.utime(incoming,(timestamp,timestamp))
    py_compile.compile(str(source),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
    manifest=package/'manifest.json'
    data=json.loads(manifest.read_text())
    data['files']['suporte/sistema/app/fleet_policy.py']=hashlib.sha256(incoming.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data))
    result=U.apply(package,root,say=lambda message:None,check_running=False)
    assert result['copied']>0
    assert source.stat().st_mtime==timestamp
    cache=Path(importlib.util.cache_from_source(str(source)))
    assert int.from_bytes(cache.read_bytes()[4:8],'little')==3
    spec=importlib.util.spec_from_file_location('repaired_policy',source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.VALUE==2


def test_legacy_without_html_filename_is_discovered_and_repaired(tmp_path):
    root,program,archive=fixture_package(tmp_path)
    legacy=archive.with_name('RodoviaStudio_3_22_sem_html.zip')
    archive.rename(legacy)
    (program/'app/fleet_policy.py').write_text('# antigo\n')
    candidates=U.candidates(root)
    assert len(candidates)==1 and candidates[0][1]==legacy
    result=U.search_and_apply(root,say=lambda message:None,check_running=False)
    assert result['repaired'] is True
    assert (program/'app/fleet_policy.py').read_text()=='# novo\n'
    assert (root/'atualizacoes/aplicadas'/legacy.name).exists()


@pytest.mark.parametrize('name',['RodoviaStudio_3_22_teste_index.zip','RodoviaStudio_3_22_ajuda.zip','RodoviaStudio_teste_sem_html.zip'])
def test_non_update_archive_names_remain_excluded(tmp_path,name):
    root,_,archive=fixture_package(tmp_path)
    archive.rename(archive.with_name(name))
    assert U.candidates(root)==[]
