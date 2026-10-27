"""Montagem de quadros em vários processos (1.7).

O processo principal prepara a cena uma vez e grava um instantâneo (matrizes grandes em .npy
mapeadas na memória, compartilhadas pelo sistema). Cada processo auxiliar monta os quadros
k ≡ índice (mod N) e envia os pixels brutos pela saída padrão; o principal lê na ordem,
aplica as transições entre cenas e alimenta um único FFmpeg. Os quadros são os mesmos da
montagem em um processo; só o tempo muda.
"""
import os,sys,subprocess,ctypes,time,threading,queue
from pathlib import Path
import numpy as np

def available_memory():
    try:
        if os.name=='nt':
            class M(ctypes.Structure):
                _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),
                          ('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
            m=M();m.dwLength=ctypes.sizeof(M);ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m));return int(m.ullAvailPhys)
        for line in open('/proc/meminfo'):
            if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    except Exception:pass
    return 4*1024**3

def plan_workers(requested,W,H,frames,cpu_encoder,cores=None,memory=None):
    """Quantidade de processos: pedida, ou automática por núcleos livres e memória disponível."""
    cores=cores or os.cpu_count() or 2;memory=memory if memory is not None else available_memory()
    free_cores=max(1,cores-(1 if cpu_encoder else 0)-1)
    per=0.9*1024**3+W*H*3*40
    by_mem=max(1,int((memory-1.5*1024**3)//per))
    ceiling=max(1,min(free_cores,by_mem,12))
    if requested:
        wanted=max(1,min(int(requested),32));n=min(wanted,ceiling)
        return n,('definido na configuração' if n==wanted else f'pedido {wanted}, limitado a {n} por memória/núcleos disponíveis')
    if frames<120:return 1,'vídeo curto: um processo'
    return ceiling,f'automático: {cores} núcleos, {memory/1024**3:.1f} GB livres'

class Pool:
    def __init__(self,snapshot,n,first,last,mode,logdir,*,key,stall_timeout=1800):
        self.n=n;self.procs=[];self.logs=[];self.readers={};self.closed=threading.Event();self.stall_timeout=stall_timeout
        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        env['RODOVIA_SNAPSHOT_KEY']=key
        base=Path(__file__).resolve().parents[1]
        try:
            for i in range(n):
                log=open(Path(logdir)/f'processo_{i}.log','wb');self.logs.append(log)
                self.procs.append(subprocess.Popen([sys.executable,'-m','app.parallel',str(snapshot),str(i),str(n),str(first),str(last),mode],
                    cwd=base,stdout=subprocess.PIPE,stderr=log,env=env,bufsize=0))
        except BaseException:
            self.close(kill=True);raise
    def _reader(self,index,nbytes):
        results=queue.Queue(maxsize=1);state={'last':time.monotonic()}
        def publish(value):
            while not self.closed.is_set():
                try:results.put(value,timeout=.1);return
                except queue.Full:pass
        def read():
            try:
                while not self.closed.is_set():
                    buf=bytearray(nbytes);view=memoryview(buf);got=0
                    while got<nbytes:
                        n=self.procs[index].stdout.readinto(view[got:])
                        if not n:raise RuntimeError(f'Processo auxiliar {index} encerrou antes do próximo quadro. Consulte o log.')
                        got+=n;state['last']=time.monotonic()
                    publish(buf)
            except BaseException as error:publish(error)
        thread=threading.Thread(target=read,daemon=True);thread.start()
        self.readers[index]=(results,state,thread,nbytes)
        return self.readers[index]

    def frame(self,k,nbytes,shape,cancel=lambda:False):
        index=k%self.n
        results,state,thread,size=self.readers.get(index) or self._reader(index,nbytes)
        if size!=nbytes:raise ValueError('Dimensões mudaram durante a montagem.')
        while True:
            if cancel():raise InterruptedError('Geração cancelada enquanto aguardava processo auxiliar.')
            try:value=results.get(timeout=.1);break
            except queue.Empty:
                if time.monotonic()-state['last']>self.stall_timeout:
                    raise TimeoutError(f'Processo auxiliar {index} sem produzir dados por {self.stall_timeout:g} s. Consulte o log e reduza a qualidade/processos.')
        if isinstance(value,BaseException):raise value
        return np.frombuffer(value,np.uint8).reshape(shape)

    def close(self,kill=False):
        from .process_supervision import stop_process
        self.closed.set()
        for p in self.procs:
            if kill:stop_process(p,grace=2)
            else:
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:stop_process(p,grace=2)
        for _,_,thread,_ in self.readers.values():thread.join(timeout=2)
        for p in self.procs:
            try:p.stdout.close()
            except OSError:pass
        for l in self.logs:l.close()
        return [p.returncode for p in self.procs]

def main(snapshot,index,n,first,last,mode):
    import cv2
    cv2.setNumThreads(1)
    from .render import Scene
    sc=Scene.load_snapshot(snapshot,key=os.environ.pop('RODOVIA_SNAPSHOT_KEY',None));fps=sc.s.fps;out=sys.stdout.buffer
    cab=None
    if mode=='cabin':
        from .cabin import CabinView
        cab=CabinView(sc)
    sc.shown_poi=None;sc.poi_since=-100
    for k in range(first,last+1):
        t=k/fps
        if k%n==index:
            im=cab.frame(t)[0] if cab else sc.frame(t)[0]
            out.write(np.ascontiguousarray(im).tobytes())
        elif cab is None:sc.advance_state(t)
    out.flush()

if __name__=='__main__':
    a=sys.argv[1:];main(a[0],int(a[1]),int(a[2]),int(a[3]),int(a[4]),a[5])
