"""Exportação WebGL por quadros: fila limitada, FFmpeg local e publicação só após validar."""
from pathlib import Path
import io,json,math,secrets,subprocess,threading,time,uuid
from PIL import Image
from . import store
from .encoding import ffmpeg_exe,select_encoder,validate_mp4
from .execlog import JobLog

_lock=threading.RLock()
_current=None


def active():
    with _lock:return _current is not None and not _current.ended


def abort_all():
    with _lock:session=_current
    if session and not session.ended:session.abort('Aplicação encerrada.',cancelled=True)


def session(jid,token):
    with _lock:s=_current
    if s is None or s.jid!=jid or not secrets.compare_digest(s.token,str(token or '')):raise ValueError('Sessão de exportação 3D inválida.')
    return s


class Capture:
    def __init__(self,d,pid,jid,settings,revision,camera,frames):
        self.d=d;self.pid=pid;self.jid=jid;self.s=settings;self.revision=revision;self.camera=camera;self.frames=frames;self.count=0;self.token=secrets.token_urlsafe(32)
        self.ended=False;self.ready=False;self.proc=None;self.logfile=None;self.last=time.monotonic();self.t0=self.last;self.state_lock=threading.RLock();self.feed_lock=threading.Lock();self.output=d/'video3d.partial.mp4';self.result=None
        self.log=JobLog(d,jid,'render3d',settings)
        threading.Thread(target=self.initialize,daemon=True).start();threading.Thread(target=self.watch,daemon=True).start()
    def initialize(self):
        try:
            store.update(self.jid,message='Verificando codificador para o vídeo 3D…');self.ff=ffmpeg_exe();self.encoder=select_encoder(self.ff,self.s.width,self.s.width*9//16,self.s.fps,self.s.encoder,self.s.cpu_preset,quality=self.s.video_quality)
            with self.state_lock:
                if self.ended:return
                self.logfile=(self.d/'ffmpeg3d.log').open('wb')
                args=[self.ff,'-y','-hide_banner','-loglevel','error','-f','image2pipe','-framerate',str(self.s.fps),'-vcodec','png','-i','pipe:0','-an',*self.encoder['args'],'-frames:v',str(self.frames),'-pix_fmt','yuv420p','-movflags','+faststart',str(self.output)]
                self.proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.logfile);self.ready=True;self.last=time.monotonic()
                store.update(self.jid,message='Pronto para receber quadros 3D.',progress=.02)
        except Exception as exc:self.abort(str(exc))
    def watch(self):
        while not self.ended:
            time.sleep(.5)
            try:
                if store.job(self.jid)['state']=='cancel_requested':self.abort('Exportação 3D cancelada.',cancelled=True);return
                if time.monotonic()-self.last>120:self.abort('Exportação 3D sem resposta do navegador por 120 segundos.');return
            except Exception:continue
    def feed(self,index,data):
        with self.feed_lock:
            if self.ended:raise ValueError('Exportação 3D encerrada.')
            if not self.ready:raise ValueError('Codificador ainda não está pronto.')
            if index!=self.count or index>=self.frames:
                self.abort('Quadro fora da sequência da exportação.');raise ValueError('Quadro fora da sequência da exportação.')
            if len(data)>16*1024*1024 or not data.startswith(b'\x89PNG\r\n\x1a\n'):
                self.abort('Quadro PNG inválido ou acima de 16 MB.');raise ValueError('Quadro PNG inválido ou acima de 16 MB.')
            try:
                with Image.open(io.BytesIO(data)) as im:
                    if im.size!=(self.s.width,self.s.width*9//16):raise ValueError('Dimensões do quadro não correspondem à exportação.')
                    im.verify()
                self.proc.stdin.write(data);self.proc.stdin.flush()
            except (OSError,ValueError) as exc:self.abort('Não foi possível receber o quadro: '+str(exc));raise ValueError('Quadro não aceito.') from exc
            self.count+=1;self.last=time.monotonic();progress=.02+.86*self.count/self.frames;message=f'Vídeo 3D: quadro {self.count} de {self.frames}'
            store.update(self.jid,progress=progress,message=message)
            if self.count==1 or self.count%max(1,self.s.fps)==0:self.log.status(progress,message)
            return {'accepted':self.count,'frames':self.frames}
    def finish(self):
        try:
            with self.feed_lock:
                if self.ended:raise ValueError('Exportação 3D encerrada.')
                if self.count!=self.frames:raise ValueError('A exportação ainda não recebeu todos os quadros.')
                self.last=time.monotonic();store.update(self.jid,progress=.9,message='Conferindo o vídeo 3D completo…');self.log.status(.9,'Conferindo o vídeo 3D completo')
                self.proc.stdin.close();code=self.proc.wait(timeout=120)
                if self.logfile:self.logfile.close()
                if code:raise ValueError('O codificador não concluiu. Consulte ffmpeg3d.log.')
                check=validate_mp4(self.ff,self.output,self.frames,self.s.width,self.s.width*9//16,self.s.fps)
                if not check['ok']:raise ValueError('Vídeo 3D reprovado: '+', '.join(check['problems']))
                with self.state_lock:
                    if self.ended:raise ValueError('Exportação cancelada antes da publicação.')
                    from .scene3d import revision
                    if revision(self.d)!=self.revision:raise ValueError('Projeto alterado durante a exportação. Reconstrua o 3D.')
                    final=self.d/'video3d.mp4';store.replace(self.output,final)
                    info={'motor':'WebGL 3D','width':self.s.width,'height':self.s.width*9//16,'fps':self.s.fps,'frames':self.frames,'duration_s':self.frames/self.s.fps,'encoder':self.encoder['encoder'],'validation':check,'scene3d_revision':self.revision,'camera3d':self.camera,'total_seconds':round(time.monotonic()-self.t0,3)}
                    from .videos import archive
                    saved=archive(self.d,self.pid,self.s,info,time.monotonic()-self.t0,source_name='video3d.mp4')
                    if saved:info.update(arquivo=saved.name,pasta_videos=str(saved.parent))
                    store.write_json(self.d/'video3d.json',info);self.result=info;self.ended=True
                    store.update(self.jid,state='done',progress=1,message='Vídeo 3D conferido e guardado.');self.log.done('Vídeo 3D conferido e guardado.')
                    return info
        except Exception as exc:
            self.abort(str(exc));raise
    def abort(self,message,cancelled=False):
        with self.state_lock:
            if self.ended:return
            self.ended=True;proc=self.proc
        if proc is not None:
            try:
                if proc.poll() is None:proc.kill()
                proc.wait(timeout=10)
            except (OSError,subprocess.TimeoutExpired):pass
            try:proc.stdin.close()
            except (OSError,ValueError):pass
        if self.logfile:
            try:self.logfile.close()
            except OSError:pass
        try:self.output.unlink(missing_ok=True)
        except OSError:pass
        store.update(self.jid,state='cancelled' if cancelled else 'failed',message=message[:400])
        if cancelled:self.log.done('Cancelado: '+message)
        else:self.log.failed(ValueError(message),message)


def begin(d,pid,settings,revision,camera,duration):
    global _current
    with _lock:
        if active():raise ValueError('Já existe uma exportação 3D em andamento.')
        with store.connect() as c:
            if c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone():raise ValueError('Aguarde a tarefa atual terminar.')
            jid=uuid.uuid4().hex;c.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'render3d','running','Preparando exportação 3D'))
        frames=round(duration*settings.fps);s=settings.model_copy(update={'duration_s':frames/settings.fps})
        _current=Capture(d,pid,jid,s,revision,camera,frames)
        return {'id':jid,'token':_current.token,'frames':frames,'fps':s.fps,'width':s.width,'height':s.width*9//16}
