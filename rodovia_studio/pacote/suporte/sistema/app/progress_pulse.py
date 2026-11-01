"""2.17: batimento de progresso para etapas longas sem andamento próprio (download de imagem, rasterização).
Mantém barra e sinal de vida andando; nunca lança exceção para a tarefa principal."""
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
            f=1-1/(1+e/45.)            # aproxima-se de hi sem nunca chegar (não promete fim)
            try:self.status(self.lo+(self.hi-self.lo)*f,f'{self.base} ({int(e)} s)')
            except Exception as _e:_falha(__name__,_e)
    def stop(self):
        self._stop.set()
        if self in _ACTIVE:_ACTIVE.remove(self)
        if self._t is not None:self._t.join(timeout=2)
