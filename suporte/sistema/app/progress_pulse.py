"""Batimento para etapas sem total conhecido: mantém a etapa e informa o tempo decorrido."""
from .falhas import registrar as _falha
import threading,time

_ACTIVE=[]

def stop_all():
    for p in list(_ACTIVE):p.stop()

class Pulse:
    def __init__(self,status,cancel,lo,hi,period=1.0):
        self.status=status;self.cancel=cancel;self.lo=lo;self.hi=hi;self.period=period
        self._stop=threading.Event();self._t=None;self.base=''
    def start(self,message):
        self.base=message;self.t0=time.monotonic()
        _ACTIVE.append(self)
        self._t=threading.Thread(target=self._run,daemon=True);self._t.start()
    def _run(self):
        while not self._stop.wait(self.period):
            e=time.monotonic()-self.t0
            # Sem total conhecido, tempo decorrido não representa trabalho concluído.
            try:self.status(self.lo,f'{self.base} · sem estimativa de término ({int(e)} s)')
            except Exception as _e:_falha(__name__,_e)
    def stop(self):
        self._stop.set()
        if self in _ACTIVE:_ACTIVE.remove(self)
        if self._t is not None:self._t.join(timeout=2)
