import importlib.util,sys,hashlib,os
from pathlib import Path
from types import SimpleNamespace
import pytest
import atualizar_portatil as U
import preparar as B


def test_updater_stages_known_script_without_network_or_shell(tmp_path):
 root=tmp_path/'Instalação ç';script=root/'sistema/programa/atualizador.py';script.parent.mkdir(parents=True);script.write_text('print("atualizador local")')
 stage=tmp_path/'stage';stage.mkdir();runner,copied=U.stage(root,stage)
 assert runner.is_file() and copied.read_bytes()==script.read_bytes()


def test_missing_installation_does_not_create_a_project(tmp_path):
 stage=tmp_path/'stage';stage.mkdir()
 with pytest.raises(ValueError):U.stage(tmp_path/'ausente',stage)
 assert not (tmp_path/'ausente').exists()


def test_preparation_creates_normal_venv_and_requires_hashed_wheels(tmp_path,monkeypatch):
 import venv
 monkeypatch.setattr(B,'BASE',tmp_path);monkeypatch.setattr(sys,'argv',['preparar.py','--preparar-apenas'])
 for name in ('requirements-windows.lock','requirements.txt','pip-bootstrap.lock'):(tmp_path/name).write_text('pip==26.2.2')
 class Builder:
  def __init__(self,**kwargs):assert kwargs['with_pip']
  def create(self,p):
   exe=p/('Scripts/python.exe' if os.name=='nt' else 'bin/python');exe.parent.mkdir(parents=True);exe.write_text('aprovado')
 monkeypatch.setattr(venv,'EnvBuilder',Builder);calls=[]
 def run(args,**kwargs):calls.append(args);return SimpleNamespace(returncode=0)
 monkeypatch.setattr(B.subprocess,'run',run);B.main()
 assert all('powershell.exe' not in str(c) for c in calls)
 assert any('--require-hashes' in c and str(tmp_path/'pip-bootstrap.lock') in c for c in calls)
 assert (tmp_path/'runtime/dependencias.ok').is_file()
 assert all(c[0].endswith('Scripts/python.exe' if os.name=='nt' else 'bin/python') for c in calls)


def test_matching_stamp_skips_installation_and_preserves_data(tmp_path,monkeypatch):
 monkeypatch.setattr(B,'BASE',tmp_path);monkeypatch.setattr(sys,'argv',['preparar.py','--preparar-apenas'])
 req=tmp_path/('requirements-windows.lock' if os.name=='nt' else 'requirements.txt');req.write_text('dependencias conferidas')
 runtime=tmp_path/'runtime';exe=runtime/('python.exe' if os.name=='nt' else 'bin/python');exe.parent.mkdir(parents=True);exe.write_text('aprovado');(runtime/'dependencias.ok').write_text(hashlib.sha256(req.read_bytes()).hexdigest())
 calls=[];monkeypatch.setattr(B.subprocess,'run',lambda a,**k:calls.append(a));B.main()
 assert len(calls)==1 and calls[0][-1].endswith('diagnostico.py')
