import subprocess,json
from types import SimpleNamespace
import cv2,numpy as np
from app.encoding import select_encoder
from app.models import Settings
from app.render import Scene,render
from test_workflow import drawing,settings

def test_probe_requires_real_success():
 good=lambda *a,**k:SimpleNamespace(returncode=0,stderr=b'')
 bad=lambda *a,**k:SimpleNamespace(returncode=1,stderr=b'no GPU')
 assert select_encoder('ff',1280,720,30,runner=good)['encoder']=='h264_nvenc'
 assert select_encoder('ff',1280,720,30,runner=bad)['encoder']=='libx264'
 def timeout(*a,**k):raise subprocess.TimeoutExpired('ff',25)
 assert select_encoder('ff',1280,720,30,runner=timeout)['encoder']=='libx264'
 assert select_encoder('ff',1280,720,30,'cpu',runner=lambda *a,**k:1)['encoder']=='libx264'

def test_cache_and_invalidation(drawing):
 cfg=settings();first=Scene(drawing,cfg);assert not first.geometry_cache_hit
 second=Scene(drawing,cfg);assert second.geometry_cache_hit
 assert np.array_equal(first.overlay,second.overlay)
 assert np.array_equal(first.stations,second.stations)
 third=Scene(drawing,cfg.model_copy(update={'reverse_axis':True}));assert not third.geometry_cache_hit

def test_midstream_nvenc_failure_restarts_cpu(drawing,monkeypatch):
 import app.render as m
 original=m.select_encoder
 def selector(ff,w,h,fps,mode='auto',cpu_preset='veryfast',**kw):
  if mode!='cpu':return {'encoder':'h264_nvenc','label':'GPU simulada com falha','reason':'Teste de retorno automático','args':['-c:v','encoder_inexistente'],'quality':{'cq':19}}
  return original(ff,w,h,fps,'cpu',cpu_preset)
 monkeypatch.setattr(m,'select_encoder',selector)
 out=render(drawing,settings());meta=json.loads((drawing/'video.json').read_text());assert meta['encoder']=='libx264';assert 'Retorno automático' in meta['encoder_reason']
 cap=cv2.VideoCapture(str(out));assert cap.get(cv2.CAP_PROP_FRAME_COUNT)==90;cap.release()
