import io,json,time
import pytest
from PIL import Image
from app import store,capture3d
from app.scene3d import revision
from test_v1425_scene3d import project

@pytest.fixture
def capture(tmp_path,monkeypatch):
    monkeypatch.setattr(store,'ROOT',tmp_path);monkeypatch.setattr(store,'DB',tmp_path/'studio.sqlite3');store.init()
    d=tmp_path/('c'*32);d.mkdir();d,s=project(d)
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(d.name,s.name))
    # Codificação real; o teste não substitui o motor de vídeo por um mock.
    result=capture3d.begin(d,d.name,s,revision(d),{'position':[1,2,3],'target':[0,0,0],'light':'dia'},3)
    session=capture3d.session(result['id'],result['token'])
    for _ in range(300):
        if session.ready or session.ended:break
        time.sleep(.05)
    assert session.ready and not session.ended
    yield d,session,result
    if not session.ended:session.abort('Fim do teste.',cancelled=True)


def png(width=1280,height=720):
    f=io.BytesIO();Image.new('RGB',(width,height),(50,100,80)).save(f,format='PNG');return f.getvalue()


def test_bad_frame_sequence_aborts_without_publishing(capture):
    d,s,r=capture
    with pytest.raises(ValueError,match='sequência'):s.feed(1,png())
    assert s.ended and store.job(s.jid)['state']=='failed'
    assert not (d/'video3d.mp4').exists() and not s.output.exists()


def test_wrong_dimensions_and_unauthorized_session_are_rejected(capture):
    d,s,r=capture
    with pytest.raises(ValueError,match='inválida'):capture3d.session(r['id'],'outra chave')
    with pytest.raises(ValueError,match='aceito'):s.feed(0,png(64,64))
    assert s.ended and not s.output.exists()


def test_cancel_preserves_previous_video_and_stops_encoder(capture):
    d,s,r=capture;(d/'video3d.mp4').write_bytes(b'video anterior conservar');s.feed(0,png())
    s.abort('Cancelado pelo usuário.',cancelled=True)
    assert s.proc.poll() is not None and store.job(s.jid)['state']=='cancelled'
    assert (d/'video3d.mp4').read_bytes()==b'video anterior conservar' and not s.output.exists()
