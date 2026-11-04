"""Produção de tráfego em blocos e replay isolado para montagem do vídeo."""
import copy
import functools
from pathlib import Path
import queue
import threading
import time
import uuid

from . import visual
from .simulation import TrafficSim,DT
from .traffic_cache import cache_key,cache_save,cache_load_into,prune_history,compact_cache
from .traffic_history import FrameArchive
from .fleet_policy import require_export

BLOCK_SECONDS=5.


def _shell(scene,duration):
    sim=TrafficSim.__new__(TrafficSim)
    sim.net=scene.network;sim.s=scene.s;sim.paths=scene.network.paths;sim.duration=float(duration)
    sim.vtype=functools.partial(visual.vehicle_type,mix=getattr(scene.s,'vehicle_mix','classico'))
    return sim


def _prepare(scene,duration,status):
    return TrafficSim(scene.network,scene.s,functools.partial(visual.vehicle_type,mix=getattr(scene.s,'vehicle_mix','classico')),
                      duration=duration,status=status,janela=getattr(scene,'sim_window',None),defer=True)


def cached_simulation(scene,status=lambda *a:None,duration=None):
    """Caminho completo para prévias, câmera com antecipação e vista 3D."""
    if getattr(scene.s,'traffic_export_scope','strict')=='validated_only':
        duration=max(float(duration or 0),float(scene.s.duration_s));scene.sim_window=None
    duration=float(duration if duration is not None else getattr(scene,'sim_duration',None) or scene.s.duration_s)
    directory=Path(scene.directory)/'cache_trafego';window=getattr(scene,'sim_window',None)
    key=cache_key(scene.network,scene.s,duration,window=window)
    sim=_shell(scene,duration)
    if cache_load_into(sim,directory,key,complete=True):
        sim.cache_info={'status':'hit','key':key,'scope':'window' if window is not None else 'full','resumed_at_s':0.}
        status(.25,'Tráfego validado reutilizado do cache local')
        return sim
    resumed=cache_load_into(sim,directory,key,complete=False)
    if not resumed:sim=_prepare(scene,duration,status)
    resumed_at=float(sim._continuation['block_start']) if resumed else 0.
    info={'status':'resumed' if resumed else 'miss','key':key,'scope':'window' if window is not None else 'full','resumed_at_s':resumed_at}
    try:
        for block in sim.run_blocks(status,BLOCK_SECONDS):
            require_export(sim,sim.s,allow_partial=True)
            cache_save(sim,directory,key,complete=block['complete'])
    finally:
        compact_cache(directory)
        archive=getattr(getattr(sim,'frames',None),'archive',None)
        prune_history(directory,active_roots=[archive.root] if archive else [])
    sim.cache_info=info
    require_export(sim,sim.s)
    return sim


class TrafficPipeline:
    """No máximo dois checkpoints aguardam montagem; o produtor nunca altera o replay."""
    def __init__(self,scene,status=lambda *a:None,cancel=lambda:False,duration=None):
        self.scene=scene;self.status=status;self.cancel=cancel
        self.duration=float(duration if duration is not None else scene.s.duration_s)
        self.directory=Path(scene.directory)/'cache_trafego'
        self.key=cache_key(scene.network,scene.s,self.duration,window=getattr(scene,'sim_window',None))
        self.stop=threading.Event();self.lock=threading.Lock();self.queue=queue.Queue(maxsize=2)
        self.available=-1.;self.complete=False;self.thread=None;self.sim_message='Preparando o primeiro bloco de tráfego'
        self.info={'status':'miss','key':self.key,'scope':'full','resumed_at_s':0.,'block_seconds':BLOCK_SECONDS,'max_pending_blocks':2,'streaming':True}
        existing=getattr(scene,'_sim',None)
        if existing is not None and getattr(existing,'simulation_complete',False) and existing.duration>=self.duration:
            self._use(existing);self.info.update(getattr(existing,'cache_info',{}));self.info['streaming']=False
            return
        sim=_shell(scene,self.duration)
        if cache_load_into(sim,self.directory,self.key,complete=True):
            self._use(sim);self.info.update(status='hit',streaming=False)
            self.status(.45,'Tráfego validado reutilizado do cache local')
            return
        resumed=cache_load_into(sim,self.directory,self.key,complete=False)
        if resumed:
            self.info.update(status='resumed',resumed_at_s=float(sim._continuation['block_start']))
            self._use(self._clone(sim))
        else:
            sim=_prepare(scene,self.duration,self._progress)
            archive=FrameArchive(self.directory/'histories'/uuid.uuid4().hex)
            sim._history_frames=archive.frames;sim._history_warnings=archive.warnings
        self.producer=sim
        self.thread=threading.Thread(target=self._produce,name='rodovia-trafego',daemon=True);self.thread.start()

    def _progress(self,p,message):
        if self.stop.is_set() or self.cancel():raise InterruptedError('Tráfego cancelado; último bloco validado preservado.')
        self.sim_message=message

    def _clone(self,sim):
        # Cópia de objetos já confiáveis em RAM; arquivos persistentes usam somente JSON/NPZ.
        clone=_shell(self.scene,self.duration)
        memo={id(sim):clone,id(sim.net):sim.net,id(sim.s):self.scene.s,id(sim.paths):sim.net.paths}
        archive=getattr(getattr(sim,'frames',None),'archive',None)
        if archive is not None:
            frozen=FrameArchive.from_state(archive.export_state(),base_directory=self.directory)
            memo.update({id(archive):frozen,id(sim.frames):frozen.frames,id(sim.warning_frames):frozen.warnings})
        clone.__dict__.update(copy.deepcopy(sim.__dict__,memo))
        clone.s=self.scene.s;clone.net=self.scene.network;clone.paths=self.scene.network.paths
        return clone

    def _use(self,sim):
        self.scene._sim=sim
        self.available=sim.t_first+(len(sim.frames)-1)*DT
        self.complete=bool(getattr(sim,'simulation_complete',False))
        self.render_until=self.duration if self.complete else float(sim._continuation['block_start'])

    def _publish(self,item):
        while not self.stop.is_set():
            try:self.queue.put(item,timeout=.1);return
            except queue.Full:continue
        raise InterruptedError('Produção em blocos cancelada.')

    def _produce(self):
        try:
            for block in self.producer.run_blocks(self._progress,BLOCK_SECONDS):
                self._progress(0,self.sim_message)
                require_export(self.producer,self.producer.s,allow_partial=True)
                archive=getattr(self.producer.frames,'archive',None)
                if archive is not None:archive.flush()
                with self.lock:
                    saved=cache_save(self.producer,self.directory,self.key,complete=block['complete'])
                    fallback=None if saved else self._clone(self.producer)
                self._publish((block,saved,fallback))
        except BaseException as error:
            try:self._publish(error)
            except InterruptedError:pass

    def ensure(self,t):
        required=min(self.duration+DT,float(t)+DT);last=0.
        while not self.complete and (self.available+1e-8<required or float(t)>=self.render_until-1e-8):
            if self.cancel():raise InterruptedError('Vídeo cancelado; checkpoint de tráfego preservado.')
            try:item=self.queue.get(timeout=.1)
            except queue.Empty:
                if self.thread is not None and not self.thread.is_alive() and self.queue.empty():raise RuntimeError('Produtor de tráfego terminou sem publicar o próximo bloco.')
                if time.monotonic()-last>.5:
                    self.status(.22,'Processando tráfego em blocos · '+self.sim_message);last=time.monotonic()
                continue
            self._consume(item)

    def _consume(self,item):
        if isinstance(item,BaseException):raise item
        block,saved,fallback=item
        if saved:
            clone=_shell(self.scene,self.duration)
            with self.lock:loaded=cache_load_into(clone,self.directory,self.key,complete=block['complete'])
            if not loaded:raise ValueError('Checkpoint de tráfego não passou na conferência; exportação interrompida.')
        else:
            clone=fallback;self.info['cache_write_failed']=True
        self._use(clone)

    def finish(self):
        while not self.complete:
            if self.cancel():raise InterruptedError('Exportação cancelada antes da validação final.')
            try:item=self.queue.get(timeout=.1)
            except queue.Empty:
                if self.thread is not None and not self.thread.is_alive():raise RuntimeError('Simulação não concluiu todos os blocos.')
                continue
            self._consume(item)
        require_export(self.scene._sim,self.scene.s)
        self.scene._sim.cache_info=dict(self.info)
        self.scene.report['traffic_simulation']=self.scene._sim.report()
        return self.scene._sim

    def close(self):
        self.stop.set()
        if self.thread is not None:self.thread.join(timeout=15)
        if self.thread is None or not self.thread.is_alive():
            compact_cache(self.directory)
            prune_history(self.directory)
