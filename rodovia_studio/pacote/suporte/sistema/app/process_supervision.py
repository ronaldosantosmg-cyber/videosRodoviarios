"""Encerramento limitado e sinal de vida separado do progresso real da operação."""
import subprocess,threading,time,re,os,signal,queue
from pathlib import Path

def stop_process(process,grace=5,tree=False):
    if process.poll() is not None:return
    group=tree and os.name!='nt' and os.getpgid(process.pid)==process.pid
    if tree and os.name=='nt':
        try:subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],timeout=grace,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        except (OSError,subprocess.TimeoutExpired):process.kill()
    elif group:os.killpg(process.pid,signal.SIGTERM)
    else:process.terminate()
    try:process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        process.kill();process.wait(timeout=grace)
    finally:
        if group:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass

def heartbeat_path(directory,jid):
    if not re.fullmatch('[0-9a-f]{32}',jid):raise ValueError('Tarefa inválida.')
    folder=Path(directory)/'.estado'/'tarefas'
    if folder.is_symlink() or folder.parent.is_symlink():raise ValueError('Pasta de supervisão inválida.')
    folder.mkdir(parents=True,exist_ok=True);path=folder/(jid+'.vida')
    if path.is_symlink():raise ValueError('Sinal de vida inválido.')
    return path

class Heartbeat:
    def __init__(self,directory,jid):self.path=heartbeat_path(directory,jid);self.stop=threading.Event()
    def __enter__(self):
        self.path.touch()
        def run():
            while not self.stop.wait(2):
                try:self.path.touch()
                except OSError:pass
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start();return self
    def __exit__(self,*args):
        self.stop.set();self.thread.join(timeout=3);self.path.unlink(missing_ok=True)

class PipeWriter:
    """Uma escrita pendente, com cancelamento observável mesmo se o encoder parar."""
    def __init__(self,stream,cancel=lambda:False,timeout=600):
        self.stream=stream;self.cancel=cancel;self.timeout=timeout;self.stopping=threading.Event();self.requests=queue.Queue(maxsize=1);self.results=queue.Queue(maxsize=1)
        def run():
            while not self.stopping.is_set():
                try:data=self.requests.get(timeout=.1)
                except queue.Empty:continue
                try:
                    if data is None:self.stream.close()
                    else:self.stream.write(data)
                    self.results.put(None)
                except BaseException as e:self.results.put(e);return
                if data is None:return
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
    def _send(self,data):
        if self.cancel():raise InterruptedError('Exportação cancelada durante envio ao encoder.')
        self.requests.put_nowait(data);started=time.monotonic()
        while True:
            if self.cancel():raise InterruptedError('Exportação cancelada durante envio ao encoder.')
            try:result=self.results.get(timeout=.1);break
            except queue.Empty:
                if time.monotonic()-started>self.timeout:raise TimeoutError('Encoder sem receber dados no prazo da etapa. Consulte ffmpeg.log.')
        if isinstance(result,BaseException):raise result
    def write(self,data):self._send(data)
    def finish(self):self._send(None);self.thread.join(timeout=2)
    def join(self):self.stopping.set();self.thread.join(timeout=2)
