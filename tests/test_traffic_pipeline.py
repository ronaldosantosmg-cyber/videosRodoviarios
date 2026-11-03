"""Integração real: DXF → Scene → checkpoints seguros → replay para composição."""
import functools
import threading

import ezdxf
import numpy as np
import pytest

from app import traffic_pipeline, visual
from app.fleet_policy import require_export
from app.models import Settings
from app.render import Scene
from app.simulation import TrafficSim
from app.traffic_history import FrameArchive
from app.traffic_pipeline import TrafficPipeline


def project(directory):
    document=ezdxf.new()
    document.layers.new('EIXO');document.layers.new('PAVIMENTO')
    model=document.modelspace()
    model.add_lwpolyline([(500000,7800000),(500900,7800000)],dxfattribs={'layer':'EIXO'})
    hatch=model.add_hatch(dxfattribs={'layer':'PAVIMENTO'})
    hatch.paths.add_polyline_path([(500000,7799990),(500900,7799990),(500900,7800010),(500000,7800010)],is_closed=True)
    document.saveas(directory/'input.dxf')
    return Settings(width=1280,fps=24,duration_s=12,imagery='neutral',hydrography=False,
                    coordinates_confirmed=True,route_directions={'layer:EIXO':'forward'},
                    render_profile='rapido',render_workers=1,encoder='cpu',pedestrians=False,
                    traffic_density=3,vehicle_mix='classico',callout_layout='auto',
                    pois=[{'id':'a','title':'Obra A','kind':'outro','x':500300.,'y':7800000.},
                          {'id':'b','title':'Obra B','kind':'outro','x':500650.,'y':7800000.}])


def full_simulation(scene):
    return TrafficSim(scene.network,scene.s,functools.partial(visual.vehicle_type,mix=scene.s.vehicle_mix))


def assert_frames_equal(actual, expected):
    assert len(actual.frames)==len(expected.frames)
    for frame,reference in zip(actual.frames,expected.frames):
        for array,baseline in zip(frame,reference):np.testing.assert_array_equal(array,baseline)
    assert list(actual.warning_frames)==list(expected.warning_frames)
    assert actual.info==expected.info
    assert actual.exited_by_path==expected.exited_by_path
    assert actual.fleet_audit==expected.fleet_audit


def gated_blocks(monkeypatch):
    """Só o teste libera o produtor seguinte; primeiro checkpoint é de fato parcial."""
    permit=threading.Semaphore(0)
    original=TrafficSim.run_blocks
    def gated(self,*args,**kwargs):
        for block in original(self,*args,**kwargs):
            yield block
            if not block['complete'] and not permit.acquire(timeout=15):
                raise TimeoutError('O teste não liberou o próximo bloco.')
    monkeypatch.setattr(TrafficSim,'run_blocks',gated)
    return permit,original


def test_hot_cache_reuses_same_physics_after_visual_changes(tmp_path,monkeypatch):
    settings=project(tmp_path)
    warm=Scene(tmp_path,settings)
    pipeline=TrafficPipeline(warm)
    try:
        pipeline.ensure(0.);expected=pipeline.finish()
        states={t:expected.state(t) for t in [0.,4.9,5.1,11.8]}
    finally:pipeline.close()
    changed=settings.model_copy(update={'role_colors':{'pavement':'#775533'},'day_night':'night','width':1920,'fps':30})
    scene=Scene(tmp_path,changed)
    def forbidden(*args,**kwargs):raise AssertionError('Cache visual quente não pode executar run_blocks.')
    monkeypatch.setattr(TrafficSim,'run_blocks',forbidden)
    replay=TrafficPipeline(scene)
    try:
        replay.ensure(5.1);actual=replay.finish()
        assert replay.info['status']=='hit'
        assert replay.thread is None
        assert actual.s is changed
        assert {t:actual.state(t) for t in states}==states
        assert_frames_equal(actual,expected)
    finally:replay.close()


def test_partial_cancel_checkpoint_resumes_without_reseeding(tmp_path,monkeypatch):
    settings=project(tmp_path)
    scene=Scene(tmp_path,settings)
    expected=full_simulation(scene)
    permit,original=gated_blocks(monkeypatch)
    cancelled=threading.Event()
    pipeline=TrafficPipeline(scene,cancel=cancelled.is_set)
    try:
        pipeline.ensure(0.)
        assert not pipeline.complete
        resume_at=scene._sim._continuation['block_start']
        assert 0<resume_at<settings.duration_s
        cancelled.set();permit.release()
        with pytest.raises(InterruptedError):pipeline.ensure(resume_at)
    finally:
        permit.release();pipeline.close()
    monkeypatch.setattr(TrafficSim,'run_blocks',original)
    def forbidden_seed(*args,**kwargs):raise AssertionError('Retomada não pode semear novamente.')
    monkeypatch.setattr(TrafficSim,'semear_percurso',forbidden_seed)
    resumed=TrafficPipeline(Scene(tmp_path,settings))
    try:
        resumed.ensure(resume_at+.1);actual=resumed.finish()
        assert resumed.info['status']=='resumed'
        assert resumed.info['resumed_at_s']==resume_at
        assert_frames_equal(actual,expected)
    finally:resumed.close()


def test_auto_camera_and_callout_pixels_match_full_before_and_after_block_boundary(tmp_path,monkeypatch):
    settings=project(tmp_path)
    baseline=Scene(tmp_path,settings);baseline._sim=full_simulation(baseline)
    scene=Scene(tmp_path,settings)
    permit,_=gated_blocks(monkeypatch)
    pipeline=TrafficPipeline(scene)
    try:
        for times in ([0.,1.2,4.8],[5.,5.2,9.8],[10.,11.8]):
            if times[0]>=5:permit.release()
            for t in times:
                pipeline.ensure(t)
                if t==0.:assert not pipeline.complete
                actual=scene.frame(t)[0];expected=baseline.frame(t)[0]
                np.testing.assert_array_equal(actual,expected,err_msg=f'Quadro divergiu em t={t}')
        pipeline.finish()
    finally:
        for _ in range(4):permit.release()
        pipeline.close()


def test_late_invalid_fleet_cannot_be_accepted_as_final(tmp_path,monkeypatch):
    settings=project(tmp_path);scene=Scene(tmp_path,settings)
    original=TrafficSim.run_blocks
    def invalid_later(self,*args,**kwargs):
        first=True
        for block in original(self,*args,**kwargs):
            yield block
            if first:
                self.fleet_audit['violations'].append({'vehicle':0,'path':0,'station_m':100.,'time_s':6.,'reason':'teste_tardio'})
                first=False
    monkeypatch.setattr(TrafficSim,'run_blocks',invalid_later)
    pipeline=TrafficPipeline(scene)
    try:
        pipeline.ensure(0.)
        with pytest.raises(ValueError,match='Regra de ouro'):pipeline.finish()
        assert not pipeline.complete
        assert not (pipeline.directory/(pipeline.key+'.ready')).exists()
        with pytest.raises(ValueError):require_export(scene._sim,settings)
    finally:pipeline.close()


def test_frame_archive_has_two_block_lru_and_detects_modified_file(tmp_path):
    archive=FrameArchive(tmp_path/'histories'/'test')
    for i in range(5):
        archive.frames.append((np.array([i],np.int32),np.array([i+.5]),np.array([0],np.int32),
                               np.array([-1],np.int32),np.array([0.],np.float64)))
        archive.warnings.append({i});archive.flush()
    frozen=FrameArchive.from_state(archive.export_state(),base_directory=tmp_path)
    for i in range(5):
        assert frozen.frames[i][0].tolist()==[i]
        assert frozen.warnings[i]=={i}
        assert len(frozen._cache)<=2
    assert len(frozen._cache)==2
    row=frozen.segments[-1];path=frozen.root/row['name']
    data=bytearray(path.read_bytes());data[len(data)//2]^=1;path.write_bytes(data)
    with pytest.raises(ValueError,match='alterado'):frozen.frames[-1]


def test_cache_write_failure_uses_isolated_replay_without_changing_physics(tmp_path,monkeypatch):
    settings=project(tmp_path)
    baseline=full_simulation(Scene(tmp_path,settings))
    monkeypatch.setattr(traffic_pipeline,'cache_save',lambda *a,**kw:False)
    scene=Scene(tmp_path,settings)
    pipeline=TrafficPipeline(scene)
    try:
        pipeline.ensure(0.)
        result=pipeline.finish()
        assert pipeline.info['cache_write_failed']
        assert_frames_equal(result,baseline)
        require_export(result,settings)
    finally:pipeline.close()
