import json
import uuid
import pytest
from app import store,worker
from app.artifacts import status
from test_traffic_pipeline import project


@pytest.mark.parametrize('fail',[False,True])
def test_prepare_validates_fleet_and_keeps_editor_editable(tmp_path,monkeypatch,fail):
    settings=project(tmp_path)
    (tmp_path/'config.json').write_text(settings.model_dump_json())
    pid=uuid.uuid4().hex;jid=uuid.uuid4().hex
    monkeypatch.setattr(store,'directory',lambda _:tmp_path)
    with store.connect() as db:
        db.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'prepare','running','Teste'))
    if fail:
        def reject(*args,**kwargs):raise ValueError('Falha da frota injetada')
        monkeypatch.setattr('app.fleet_policy.require_export',reject)
    result=worker.run(jid)
    assert result==(1 if fail else 0)
    report=json.loads((tmp_path/'traffic_preparation.json').read_text())
    assert report['state']==('failed' if fail else 'validated')
    assert all(status(tmp_path)[k]['state']=='ready' for k in ('analysis','editor','vectors'))
    assert not (tmp_path/'video.mp4').exists()
