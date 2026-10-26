import errno,json,shutil
from pathlib import Path
import pytest
from app import project_state as P,project_integrity as I,store
from app.models import Settings

@pytest.fixture
def project(tmp_path):
 d=tmp_path/('a'*32);d.mkdir();P.save_config(d,Settings(name='Protegido').model_dump());return d

def test_missing_config_during_save_recovers_committed_state_instead_of_blank(project):
 before=P.read_config(project);(project/'config.json').unlink()
 P.save_config(project,{**before,'name':'Alterado'},P.revision(before))
 assert P.read_config(project)['name']=='Alterado' and len(P.history(project))==2

def test_corrupt_index_and_config_can_be_explicitly_recovered_without_discarding_bad_bytes(project):
 original=P.read_config(project);(project/'config.json').write_bytes(b'\xffbroken');(project/'.estado/config_atual.json').write_text('{')
 before=I.inspect(project);assert before['state']=='bloqueado' and before['copies']
 with pytest.raises(ValueError):P.read_config(project)
 result=I.recover(project,P.revision(original),before['report_id']);assert result['config_valid']
 assert any(f.read_bytes()==b'\xffbroken' for f in (project/'.estado/corrompidos').glob('*.json'))
 assert P.read_config(project)==original

def test_missing_project_is_not_recreated(tmp_path):
 d=tmp_path/'ausente'
 with pytest.raises(FileNotFoundError):P.read_config(d)
 assert not d.exists()

@pytest.mark.parametrize('content',['null','[]','"texto"','{','{"traffic_density":NaN}'])
def test_invalid_config_inspection_does_not_crash_or_write(project,content):
 p=project/'config.json';p.write_text(content);assert I.inspect(project)['state']=='bloqueado';assert p.read_text()==content

def test_missing_source_is_explicit_and_never_replaced_with_empty_file(project):
 store.write_json(project/'arquivos.json',{'dxf':{'name':'original.dxf'}})
 report=I.inspect(project);assert report['state']=='parcial' and any(x['file']=='input.dxf' for x in report['issues'])
 assert not (project/'input.dxf').exists()

def test_restore_refuses_obsolete_report_and_modified_copy(project):
 report=I.inspect(project);key=report['copies'][0]['revision'];(project/'config.json').write_text('{}')
 with pytest.raises(P.Conflict):I.recover(project,key,report['report_id'])
 report=I.inspect(project);(project/'.estado/historico'/(key+'.json')).write_text('{}')
 with pytest.raises(ValueError):I.recover(project,key,report['report_id'])

@pytest.mark.parametrize('error',[OSError(errno.ENOSPC,'Disco cheio'),PermissionError('Bloqueado pelo sistema'),InterruptedError('Gravação interrompida')])
def test_atomic_failures_preserve_previous_and_remove_only_own_temporary(project,monkeypatch,error):
 p=project/'valor.json';store._atomic_write_json(p,{'value':'anterior'});before=p.read_bytes()
 def fail(*a,**k):raise error
 monkeypatch.setattr(store,'replace',fail)
 with pytest.raises(type(error)):store._atomic_write_json(p,{'value':'novo'})
 assert p.read_bytes()==before and not list(project.glob('*.wip'))

def test_denied_read_does_not_attempt_restoration(project,monkeypatch):
 before=(project/'config.json').read_bytes();original=P._json
 def blocked(p):
  if Path(p)==project/'config.json':raise PermissionError('Leitura bloqueada')
  return original(p)
 monkeypatch.setattr(P,'_json',blocked)
 with pytest.raises(PermissionError):P.read_config(project)
 assert (project/'config.json').read_bytes()==before and not (project/'.estado/corrompidos').exists()

def test_symlinks_cannot_redirect_project_or_recovery(project,tmp_path):
 link=tmp_path/'link';link.symlink_to(project,target_is_directory=True)
 with pytest.raises(FileNotFoundError):P.read_config(link)
 outside=tmp_path/'outside';outside.mkdir();(project/'.estado/corrompidos').symlink_to(outside,target_is_directory=True)
 report=I.inspect(project)
 with pytest.raises(ValueError):I.recover(project,report['copies'][0]['revision'],report['report_id'])
 assert not list(outside.iterdir())

def test_server_rejects_cross_site_and_wrong_local_port():
 from app.server import app
 from fastapi.testclient import TestClient
 c=TestClient(app)
 assert c.post('/api/modelagem/validate',json={},headers={'Origin':'http://localhost:9999'}).status_code==403
 assert c.post('/api/modelagem/validate',json={},headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
 assert c.post('/api/modelagem/validate',json={},headers={'Origin':'http://testserver'}).status_code==200

def test_release_scripts_never_override_execution_policy_or_download_getpip():
 root=Path(__file__).resolve().parents[3]
 files=[*root.rglob('*.ps1'),*root.rglob('*.cmd'),root/'suporte/sistema/iniciador/RodoviaStudio.cs']
 for p in files:
  text=p.read_text(encoding='utf-8-sig')
  assert 'ExecutionPolicy Bypass' not in text and 'bootstrap.pypa.io' not in text,p
 text=(root/'suporte/sistema/preparar.py').read_text();assert '--only-binary=:all:' in text and '--isolated' in text
