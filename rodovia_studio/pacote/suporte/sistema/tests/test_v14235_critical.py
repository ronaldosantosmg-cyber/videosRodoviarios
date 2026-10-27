import sys,time,threading,subprocess
import numpy as np
import pytest
from shapely.geometry import box
from app.models import Settings
from app.traffic import TrafficNetwork
from app.parallel import Pool,plan_workers
from app.process_supervision import stop_process,Heartbeat


def net(s):
    p=np.array([[0.,0.],[300.,0.]])
    return TrafficNetwork([box(-20,-15,320,15)],[],[dict(points=p,role='axis',layer='EIXO')],p,np.array([0.,300.]),s)


@pytest.mark.parametrize('classic',[False,True])
def test_axis_name_does_not_authorize_traffic_and_explicit_layer_does(classic):
    base=Settings(traffic_classic=classic,signage_detail='basic',hydrography=False)
    denied=net(base)
    assert not denied.paths and denied.native_axis_report['ignored_sources']==1
    assert any('eixo autorizado' in w for w in denied.warnings)
    allowed=net(base.model_copy(update={'layers':{'axis':['EIXO']}}))
    assert allowed.paths
    disabled=net(base.model_copy(update={'layers':{'axis':['EIXO']},'route_directions':{'0':'off'}}))
    assert not disabled.paths


def test_explicit_direction_registers_selected_axis():
    assert net(Settings(route_directions={'0':'forward'},signage_detail='basic')).paths


def pool_process(code,timeout=.2):
    p=Pool.__new__(Pool);p.n=1;p.logs=[];p.readers={};p.closed=threading.Event();p.stall_timeout=timeout
    p.procs=[subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,bufsize=0)]
    return p


def test_auxiliary_that_emits_nothing_has_deadline_and_is_reaped():
    p=pool_process('import time;time.sleep(60)');started=time.monotonic()
    try:
        with pytest.raises(TimeoutError,match='auxiliar'):p.frame(0,3,(1,1,3))
    finally:p.close(kill=True)
    assert time.monotonic()-started<5 and p.procs[0].poll() is not None


def test_cancel_is_observed_while_waiting_for_frame():
    p=pool_process('import time;time.sleep(60)',timeout=60);started=time.monotonic()
    try:
        with pytest.raises(InterruptedError):p.frame(0,3,(1,1,3),cancel=lambda:time.monotonic()-started>.1)
    finally:p.close(kill=True)
    assert time.monotonic()-started<5


def test_partial_auxiliary_bytes_preserve_frame_and_eof_detected():
    p=pool_process("import sys;sys.stdout.buffer.write(bytes([1,2,3]));sys.stdout.buffer.flush()",timeout=5)
    try:
        assert p.frame(0,3,(1,1,3)).tolist()==[[[1,2,3]]]
        with pytest.raises(RuntimeError):p.frame(1,3,(1,1,3))
    finally:p.close()


def test_heartbeat_lives_without_fabricating_progress_and_cleans(tmp_path):
    with Heartbeat(tmp_path,'a'*32) as heartbeat:assert heartbeat.path.is_file()
    assert not heartbeat.path.exists()


@pytest.mark.parametrize('width,height',[(1280,720),(3840,2160)])
def test_manual_workers_obey_memory_limit(width,height):
    n,reason=plan_workers(32,width,height,1000,True,cores=16,memory=3*1024**3)
    assert n==1 and 'limitado' in reason


def test_pool_startup_failure_reaps_already_started_auxiliary(tmp_path,monkeypatch):
    import app.parallel as module
    started=[];real=subprocess.Popen
    def create(*a,**kw):
        if started:raise OSError('Falha de inicialização simulada')
        p=real([sys.executable,'-c','import time;time.sleep(60)'],stdout=subprocess.PIPE,bufsize=0);started.append(p);return p
    monkeypatch.setattr(module.subprocess,'Popen',create)
    with pytest.raises(OSError,match='simulada'):Pool(tmp_path,2,0,10,'aerial',tmp_path,key='teste')
    assert started[0].poll() is not None


@pytest.mark.skipif(sys.platform=='win32',reason='Process groups POSIX; Windows requer homologação nativa')
def test_controlled_termination_ends_worker_process_group(tmp_path):
    # Rodado apenas no host POSIX: valida o mesmo grupo usado pelo dispatcher.
    marker=tmp_path/'child'
    code="import subprocess,sys,time;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);Path(sys.argv[1]).write_text(str(p.pid));time.sleep(60)"
    p=subprocess.Popen([sys.executable,'-c',code,str(marker)],start_new_session=True)
    try:
        deadline=time.monotonic()+5
        while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
        assert marker.exists();stop_process(p,tree=True);assert p.poll() is not None
    finally:
        if p.poll() is None:stop_process(p,tree=True)


def test_encoder_write_wait_observes_cancel_and_releases_thread():
    from app.process_supervision import PipeWriter
    event=threading.Event()
    class Slow:
        def write(self,data):event.wait(2)
        def close(self):pass
    started=time.monotonic();writer=PipeWriter(Slow(),cancel=lambda:time.monotonic()-started>.1)
    try:
        with pytest.raises(InterruptedError):writer.write(b'frame')
    finally:event.set();writer.join()
    assert not writer.thread.is_alive()


def test_encoder_write_has_stage_deadline():
    from app.process_supervision import PipeWriter
    event=threading.Event()
    class Slow:
        def write(self,data):event.wait(2)
        def close(self):pass
    writer=PipeWriter(Slow(),timeout=.1)
    try:
        with pytest.raises(TimeoutError):writer.write(b'frame')
    finally:event.set();writer.join()
    assert not writer.thread.is_alive()
