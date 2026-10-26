import pickle
from pathlib import Path
import pytest
from app.snapshot_auth import sign,verify
from app.render import Scene,render
from app.encoding import validate_mp4,ffmpeg_exe
from test_v1425_scene3d import project


def test_modified_snapshot_is_refused_before_any_deserialization(tmp_path,monkeypatch):
 folder=tmp_path/'ipc';folder.mkdir();(folder/'scene.pkl').write_bytes(pickle.dumps({}));key=sign(folder,['scene.pkl'])
 (folder/'scene.pkl').write_bytes(b'alterado')
 def forbidden(*a,**kw):raise AssertionError('Desserialização não pode ocorrer')
 monkeypatch.setattr(pickle,'loads',forbidden)
 with pytest.raises(ValueError,match='alterado'):Scene.load_snapshot(folder,key=key)
 with pytest.raises(ValueError,match='chave'):Scene.load_snapshot(folder)


def test_changed_matrix_or_manifest_is_refused(tmp_path):
 (tmp_path/'scene.pkl').write_bytes(pickle.dumps({}));(tmp_path/'map.npy').write_bytes(b'original');key=sign(tmp_path,['scene.pkl','map.npy'])
 (tmp_path/'map.npy').write_bytes(b'corrompido')
 with pytest.raises(ValueError,match='Matriz'):verify(tmp_path,key,['scene.pkl','map.npy'])
 with pytest.raises(ValueError):verify(tmp_path,'a'*64,['scene.pkl','map.npy'])


def test_real_two_process_video_uses_authenticated_snapshot_and_decodes(tmp_path):
 d,s=project(tmp_path,traffic=False);s.render_workers=2
 result=render(d,s);info=validate_mp4(ffmpeg_exe(),result,72,1280,720,24);assert info['ok']
 if __import__('os').environ.get('VISUAL_ARTIFACTS'):
  import json
  Path(__import__('os').environ['VISUAL_ARTIFACTS'],'video_paralelo.json').write_text(json.dumps(info,indent=2))
