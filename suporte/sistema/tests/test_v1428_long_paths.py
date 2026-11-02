import errno,json
from pathlib import Path
import pytest
from app import store,project_state as ps
from app.models import Settings


def test_history_writes_within_classic_windows_limit_at_the_reported_path_length(tmp_path,monkeypatch):
    # Mesmo comprimento do caso relatado: definitivo 252; antigo temporário 289.
    directory=tmp_path/('p'*(182-len(str(tmp_path))-1));directory.mkdir()
    target=directory/('9'*64+'.json');assert len(str(target))==252
    old_temporary=target.with_name(target.name+'.tmp-'+'a'*32);assert len(str(old_temporary))==289
    original=Path.open;opened=[]
    def windows_open(path,*args,**kwargs):
        if len(str(path))>=260:raise FileNotFoundError(errno.ENOENT,'Limite clássico do caminho Windows',str(path))
        opened.append(str(path));return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',windows_open)
    with pytest.raises(FileNotFoundError):old_temporary.open('w')
    store._atomic_write_json(target,{'name':'Ronaldo Santos','value':42})
    assert json.loads(target.read_text())=={'name':'Ronaldo Santos','value':42}
    assert all(len(p)<260 for p in opened)
    assert not list(directory.glob('*.wip'))


def test_history_snapshot_uses_short_temporary_name_in_a_deep_project(tmp_path,monkeypatch):
    # A pasta .estado/historico fica com os mesmos 182 caracteres.
    project=tmp_path/('p'*(164-len(str(tmp_path))-1));project.mkdir()
    original=Path.open
    def windows_open(path,*args,**kwargs):
        if len(str(path))>=260:raise FileNotFoundError(errno.ENOENT,'MAX_PATH',str(path))
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',windows_open)
    data=Settings().model_dump();ps.save_config(project,data)
    assert ps.read_config(project)==data
    assert len(str(next((project/'.estado/historico').glob('*.json'))))==252


def test_disappearing_temporary_is_retried_without_exposing_a_partial_destination(tmp_path,monkeypatch):
    target=tmp_path/'config_data.json';store._atomic_write_json(target,{'value':'anterior'})
    original=store.replace;attempts=[]
    def disappearing(source,destination,*args,**kwargs):
        attempts.append(source)
        assert json.loads(target.read_text())=={'value':'anterior'}
        if len(attempts)==1:source.unlink();raise FileNotFoundError('temporário removido por sincronização simulada')
        return original(source,destination,*args,**kwargs)
    monkeypatch.setattr(store,'replace',disappearing)
    store._atomic_write_json(target,{'value':'novo'})
    assert len(attempts)==2 and attempts[0]!=attempts[1]
    assert json.loads(target.read_text())=={'value':'novo'}
    assert not list(tmp_path.glob('*.wip'))


def test_persistent_failure_keeps_the_previous_file_and_removes_own_temporaries(tmp_path,monkeypatch):
    target=tmp_path/'dados.json';store._atomic_write_json(target,{'value':'anterior'});before=target.read_bytes()
    def missing(*args,**kwargs):raise FileNotFoundError('indisponível')
    monkeypatch.setattr(store,'replace',missing)
    with pytest.raises(FileNotFoundError,match='versão anterior foi preservada'):store._atomic_write_json(target,{'value':'novo'})
    assert target.read_bytes()==before and not list(tmp_path.glob('*.wip'))
    with pytest.raises(ValueError):store._atomic_write_json(target,{'value':float('nan')})
    assert target.read_bytes()==before
