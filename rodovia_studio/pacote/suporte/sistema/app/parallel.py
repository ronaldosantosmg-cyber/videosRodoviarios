"""Montagem de quadros em vários processos (1.7).

O processo principal prepara a cena uma vez e grava um instantâneo (matrizes grandes em .npy
mapeadas na memória, compartilhadas pelo sistema). Cada processo auxiliar monta os quadros
k ≡ índice (mod N) e envia os pixels brutos pela saída padrão; o principal lê na ordem,
aplica as transições entre cenas e alimenta um único FFmpeg. Os quadros são os mesmos da
montagem em um processo; só o tempo muda.
"""
import os,sys,subprocess,ctypes
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
    if requested:return max(1,min(int(requested),32)),'definido na configuração'
    if frames<120:return 1,'vídeo curto: um processo'
    free_cores=cores-(1 if cpu_encoder else 0)-1  # um núcleo para o processo principal
    per=0.9*1024**3+W*H*3*40                       # objetos da cena + buffers por quadro
    by_mem=int((memory-1.5*1024**3)//per)
    n=max(1,min(free_cores,by_mem,12))
    why=f'automático: {cores} núcleos, {memory/1024**3:.1f} GB livres'
    return n,why

class Pool:
    def __init__(self,snapshot,n,first,last,mode,logdir):
        self.n=n;self.procs=[];self.logs=[]
        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        base=Path(__file__).resolve().parents[1]
        for i in range(n):
            log=open(Path(logdir)/f'processo_{i}.log','wb');self.logs.append(log)
            self.procs.append(subprocess.Popen([sys.executable,'-m','app.parallel',str(snapshot),str(i),str(n),str(first),str(last),mode],
                cwd=base,stdout=subprocess.PIPE,stderr=log,env=env,bufsize=0))
    def frame(self,k,nbytes,shape):
        p=self.procs[k%self.n];buf=bytearray(nbytes);view=memoryview(buf);got=0
        while got<nbytes:
            r=p.stdout.readinto(view[got:])
            if not r:raise RuntimeError(f'Processo auxiliar {k%self.n} encerrou antes do quadro {k}. Consulte render_tmp/processo_{k%self.n}.log.')
            got+=r
        return np.frombuffer(buf,np.uint8).reshape(shape)
    def close(self,kill=False):
        for p in self.procs:
            if kill and p.poll() is None:p.kill()
            try:p.stdout.close()
            except Exception:pass
            p.wait()
        for l in self.logs:l.close()
        return [p.returncode for p in self.procs]

def main(snapshot,index,n,first,last,mode):
    import cv2
    cv2.setNumThreads(1)
    from .render import Scene
    sc=Scene.load_snapshot(snapshot);fps=sc.s.fps;out=sys.stdout.buffer
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
