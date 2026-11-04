"""Publicação e igualdade de quadros do exportador com múltiplos blocos."""
import json
from pathlib import Path
import numpy as np
import pytest

from app import render as renderer
from app.simulation import TrafficSim
from app.traffic_pipeline import TrafficPipeline
from test_traffic_pipeline import project


def test_streaming_and_complete_replay_encode_identical_frames_with_two_workers(tmp_path,monkeypatch):
    settings=project(tmp_path);settings.duration_s=8.;settings.render_workers=2
    # Mantém a seleção determinística no teste, independentemente do host CI.
    monkeypatch.setattr('app.parallel.plan_workers',lambda *a,**k:(2,'teste de dois processos'))
    cold_log=tmp_path/'cold.frames';monkeypatch.setenv('RODOVIA_FRAME_LOG',str(cold_log))
    output=renderer.render(tmp_path,settings)
    cold=json.loads((tmp_path/'video.json').read_text(encoding='utf-8'))
    assert cold['validation']['ok'] and cold['validation']['frames_decoded']==192
    assert cold['traffic_processing']['streaming'] and cold['traffic_processing']['status']=='miss'
    assert not (tmp_path/'video.partial.mp4').exists()
    hot_log=tmp_path/'hot.frames';monkeypatch.setenv('RODOVIA_FRAME_LOG',str(hot_log))
    renderer.render(tmp_path,settings)
    hot=json.loads((tmp_path/'video.json').read_text(encoding='utf-8'))
    assert hot['traffic_processing']['status']=='hit' and not hot['traffic_processing']['streaming']
    assert cold_log.read_text()==hot_log.read_text()
    assert output.is_file()


def test_late_physics_failure_is_caught_before_drawing_or_replacing_video(tmp_path,monkeypatch):
    settings=project(tmp_path);settings.duration_s=8.
    old=tmp_path/'video.mp4';old.write_bytes(b'video anterior preservado')
    original=TrafficSim.run_blocks
    def fail_later(self,*args,**kwargs):
        for i,block in enumerate(original(self,*args,**kwargs)):
            yield block
            if i==0:raise ValueError('Falha tardia injetada')
    monkeypatch.setattr(TrafficSim,'run_blocks',fail_later)
    # Esta verificação testa transação/cancelamento, sem custo do desenho artístico.
    drawn=[]
    def fast_frame(self,t,*a,**kw):
        drawn.append(t)
        return np.zeros((self.H,self.W,3),np.uint8),{}
    monkeypatch.setattr(renderer.Scene,'frame',fast_frame)
    with pytest.raises(ValueError,match='Falha tardia'):renderer.render(tmp_path,settings)
    assert not drawn  # A auditoria integral agora antecede qualquer quadro/codificação.
    assert old.read_bytes()==b'video anterior preservado'
    assert not (tmp_path/'video.partial.mp4').exists()
