"""Atualização real em instalações isoladas, inclusive falhas durante a troca."""
import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import atualizador as U


def put(root, path, text):
    f=root/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf-8');return f


@pytest.fixture
def install(tmp_path):
    root=tmp_path/'Instalação com espaços ç'
    put(root,'sistema/programa/app/server.py','# anterior\n')
    put(root,'sistema/programa/VERSAO.json',json.dumps({'version':'1.42'}))
    put(root,'projetos/projeto/input.kmz','KMZ preservar')
    put(root,'projetos/_base_imagens/aa/imagem.tif','GeoTIFF persistente')
    put(root,'videos/projeto/video.mp4','vídeo preservar')
    return root


@pytest.fixture
def package(tmp_path):
    root=tmp_path/'fonte'/'pacote'
    put(root,'manifest.json',json.dumps({'app':'Rodovia Studio','version':'1.42.1'}))
    put(root,'suporte/sistema/app/server.py','# novo\n')
    put(root,'suporte/sistema/app/novo.py','valor=42\n')
    put(root,'suporte/sistema/VERSAO.json',json.dumps({'version':'1.42.1'}))
    return root


def zip_package(root,package,prefix='pacote/',name='RodoviaStudio_1_42_1_atualizacao.zip'):
    z=root/'atualizacoes'/name;z.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z,'w') as out:
        for f in package.rglob('*'):
            if f.is_file():out.write(f,prefix+f.relative_to(package).as_posix())
    return z


def unchanged_data(root):
    assert (root/'projetos/projeto/input.kmz').read_text()=='KMZ preservar'
    assert (root/'projetos/_base_imagens/aa/imagem.tif').read_text()=='GeoTIFF persistente'
    assert (root/'videos/projeto/video.mp4').read_text()=='vídeo preservar'


def test_apply_snapshot_rollback_and_relocation(install,package,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    result=U.apply(package,install,check_running=False)
    assert U.installed_version(install)=='1.42.1'
    journal=json.loads((Path(result['backup'])/'rollback.json').read_text())
    assert journal['state']=='applied' and len(journal['files'])==3
    relocated=tmp_path/'Outra pasta á';install.rename(relocated)
    U.restore_previous(relocated,check_running=False)
    assert U.installed_version(relocated)=='1.42'
    assert not (relocated/'sistema/programa/app/novo.py').exists()
    assert (relocated/'sistema/programa/app/server.py').read_text()=='# anterior\n'
    assert list((relocated/'sistema/backups').glob('antes_restaurar_*'))
    unchanged_data(relocated)


def test_failed_replace_restores_all_and_has_journal_before_write(install,package,monkeypatch):
    replace=U.os.replace;failed=False
    def failure(src,dst):
        nonlocal failed
        if str(dst).endswith('app/server.py') and str(src).endswith('.novo') and not failed:
            files=list((install/'sistema/backups').glob('antes_v*/rollback.json'))
            assert len(files)==1
            man=json.loads(files[0].read_text());assert man['state']=='applying'
            for e in man['files']:
                if e['had_previous']:assert (files[0].parent/e['backup']).is_file()
            failed=True;raise PermissionError('Arquivo em uso simulado')
        return replace(src,dst)
    monkeypatch.setattr(U.os,'replace',failure)
    with pytest.raises(RuntimeError,match='restaurada automaticamente'):U.apply(package,install,check_running=False)
    assert failed and U.installed_version(install)=='1.42'
    assert not (install/'sistema/programa/app/novo.py').exists()
    assert not list(install.rglob('*.novo'))
    unchanged_data(install)


def test_incomplete_backup_rejected_before_any_restore(install,package):
    result=U.apply(package,install,check_running=False)
    b=Path(result['backup']);man=json.loads((b/'rollback.json').read_text())
    e=next(e for e in man['files'] if e['had_previous'])
    (b/e['backup']).unlink()
    with pytest.raises(RuntimeError,match='Backup incompleto'):U.restore_previous(install,check_running=False)
    assert U.installed_version(install)=='1.42.1'
    assert (install/'sistema/programa/app/novo.py').exists()


@pytest.mark.parametrize('prefix',['','pacote/','RS142/pacote/'])
def test_zip_formats_apply_and_archive(install,package,prefix):
    z=zip_package(install,package,prefix)
    assert len(U.candidates(install)[0])==4
    U.search_and_apply(install,check_running=False)
    assert not z.exists() and (install/'atualizacoes/aplicadas'/z.name).exists()
    assert U.installed_version(install)=='1.42.1';unchanged_data(install)


def test_only_updates_directory_and_equivalent_versions(install,package):
    z=zip_package(install,package);z.rename(install/z.name)
    assert U.candidates(install)==[]
    U.organize_root(install)
    assert len(U.candidates(install))==1 and not (install/z.name).exists()
    assert U.version_tuple('1.42')==U.version_tuple('1.42.0')


@pytest.mark.parametrize('bad',['../../fora.py','C:/fora.py','..\\fora.py','/fora.py'])
def test_reject_zip_traversal_and_quarantine(install,package,bad):
    z=zip_package(install,package)
    with zipfile.ZipFile(z,'a') as f:f.writestr(bad,'danger')
    with pytest.raises(RuntimeError,match='recusado'):U.search_and_apply(install,check_running=False)
    assert (install/'atualizacoes/rejeitadas'/z.name).exists()
    assert U.installed_version(install)=='1.42'


def test_invalid_content_quarantined_and_valid_can_follow(install,package):
    put(package,'suporte/sistema/app/server.py','def invalid(:')
    z=zip_package(install,package)
    with pytest.raises(RuntimeError,match='recusado'):U.search_and_apply(install,check_running=False)
    assert not z.exists() and U.installed_version(install)=='1.42'


def test_bad_manifest_archived_even_with_valid_candidate(install,package):
    z=zip_package(install,package)
    bad=put(install,'atualizacoes/RodoviaStudio_bad_atualizacao.zip','corrompido')
    U.search_and_apply(install,check_running=False)
    assert not bad.exists() and (bad.parent/'rejeitadas'/bad.name).exists()
    assert not z.exists()


def test_snapshot_names_do_not_collide(install,package):
    first=U.apply(package,install,check_running=False)
    put(package,'suporte/sistema/app/server.py','# nova revisão\n')
    second=U.apply(package,install,check_running=False)
    assert first['backup']!=second['backup']


def test_target_symlink_cannot_change_persistent_data(install,package):
    target=install/'sistema/programa/app/novo.py'
    target.symlink_to(install/'projetos/projeto/input.kmz')
    with pytest.raises(ValueError,match='Link'):U.apply(package,install,check_running=False)
    unchanged_data(install)


def test_tampered_backup_target_is_rejected(install,package):
    result=U.apply(package,install,check_running=False)
    f=Path(result['backup'])/'rollback.json';man=json.loads(f.read_text())
    man['files'][0]['target']='projetos/projeto/input.kmz';f.write_text(json.dumps(man))
    with pytest.raises(ValueError,match='protegido'):U.restore_previous(install,check_running=False)
    unchanged_data(install)


def test_concurrent_update_is_rejected(install,package):
    with U._update_lock(install):
        with pytest.raises(RuntimeError,match='andamento'):U.apply(package,install,check_running=False)


def test_api_listing_real_candidate_and_rollback(install,package,monkeypatch):
    from app import store
    from app.server import app
    from app.rotas import sistema
    monkeypatch.setattr(store,'INSTALL',install)
    monkeypatch.setattr(sistema,'VERSION','1.42')
    zip_package(install,package)
    with TestClient(app) as client:
        r=client.get('/api/atualizacao');assert r.status_code==200,r.text
        assert r.json()['pode_atualizar'] and r.json()['encontradas'][0]['versao']=='1.42.1'
        assert client.post('/api/atualizacao/aplicar').status_code==409  # Linux cannot replace Windows launcher


def test_session_shutdown_requires_token_and_refuses_active_work(monkeypatch):
    from app import store
    from app.server import app
    from app.rotas.comum import maintenance_pending
    monkeypatch.setenv('RODOVIA_CONTROL_TOKEN','teste-sessao')
    closed=[];app.state.request_shutdown=lambda:closed.append(True)
    class ImmediateTimer:
        def __init__(self,delay,fn):self.fn=fn
        def start(self):self.fn()
    from app.rotas import sistema
    monkeypatch.setattr(sistema.threading,'Timer',ImmediateTimer)
    with TestClient(app) as client:
        assert client.post('/api/sessao/encerrar').status_code==403
        with store.connect() as c:c.execute("INSERT INTO jobs(id,project,kind,state) VALUES('teste-update','none','render','running')")
        try:
            headers={'X-Rodovia-Control':'teste-sessao'}
            assert client.post('/api/sessao/encerrar',headers=headers).status_code==409
            assert not closed
        finally:
            with store.connect() as c:c.execute("DELETE FROM jobs WHERE id='teste-update'")
        assert client.post('/api/sessao/encerrar',headers=headers).status_code==200
        assert closed==[True] and maintenance_pending.is_set()
    maintenance_pending.clear()


@pytest.mark.parametrize('bad',['nan','inf','-1'])
def test_invalid_wait_is_rejected(install,bad):
    assert U.main(['--raiz',str(install),'--aguardar',bad])==1


def test_failed_rollback_recovers_state_before_attempt(install,package,monkeypatch):
    U.apply(package,install,check_running=False)
    replace=U.os.replace;failed=False
    def failure(src,dst):
        nonlocal failed
        if str(src).endswith('server.py.restaurando') and not failed:
            failed=True;raise PermissionError('Falha de restauração simulada')
        return replace(src,dst)
    monkeypatch.setattr(U.os,'replace',failure)
    with pytest.raises(RuntimeError,match='estado anterior à tentativa foi recuperado'):
        U.restore_previous(install,check_running=False)
    assert U.installed_version(install)=='1.42.1'
    assert (install/'sistema/programa/app/novo.py').exists()
    assert (install/'sistema/programa/app/server.py').read_text()=='# novo\n'
    unchanged_data(install)


def test_recover_pending_update_after_process_crash(install,package,monkeypatch):
    result=U.apply(package,install,check_running=False)
    journal=Path(result['backup'])/'rollback.json';man=json.loads(journal.read_text())
    man['state']='applying';journal.write_text(json.dumps(man))
    monkeypatch.setattr(U,'app_running',lambda:None)
    U.recover_pending(install)
    assert U.installed_version(install)=='1.42'
    assert not (install/'sistema/programa/app/novo.py').exists()
    unchanged_data(install)


def test_hash_manifest_detects_tampering_and_unlisted_files(package):
    files={f.relative_to(package).as_posix():U._sha(f) for f in package.rglob('*') if f.is_file() and f.name!='manifest.json'}
    man={'app':'Rodovia Studio','version':'1.42.1','files':files};(package/'manifest.json').write_text(json.dumps(man))
    assert U.validate_package(package)
    put(package,'suporte/sistema/app/extra.py','# não listado')
    with pytest.raises(U.PackageError,match='Lista de arquivos'):U.validate_package(package)
    (package/'suporte/sistema/app/extra.py').unlink()
    put(package,'suporte/sistema/app/server.py','# alterado')
    with pytest.raises(U.PackageError,match='Hash divergente'):U.validate_package(package)
