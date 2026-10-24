"""Test the encoder, not merely its presence in the FFmpeg build."""
import os,subprocess
from pathlib import Path
import imageio_ffmpeg

def ffmpeg_exe():
    # Optional explicit override; imageio also honors IMAGEIO_FFMPEG_EXE.
    value=os.environ.get('RODOVIA_FFMPEG','').strip()
    if value:
        if not Path(value).is_file():raise ValueError('RODOVIA_FFMPEG aponta para arquivo inexistente.')
        return value
    return imageio_ffmpeg.get_ffmpeg_exe()

# 1.32: qualidade do vídeo. "padrao" = parâmetros de sempre (vídeos idênticos aos anteriores).
QUALITY={
 'padrao':{'nvenc':('p4','19','18M','36M',[]),'x264':(None,'16','18M','36M')},
 'alta':{'nvenc':('p6','16','35M','70M',['-spatial-aq','1','-aq-strength','8']),'x264':('medium','14','35M','70M')},
 'maxima':{'nvenc':('p7','14','60M','120M',['-spatial-aq','1','-aq-strength','8']),'x264':('slow','12','60M','120M')},
}

def options(encoder,cpu_preset='veryfast',quality='padrao'):
    q=QUALITY.get(quality,QUALITY['padrao'])
    if encoder=='h264_nvenc':
        preset,cq,maxrate,buf,extra=q['nvenc']
        return ['-c:v','h264_nvenc','-preset',preset,'-tune','hq','-rc','vbr','-cq',cq,'-b:v','0','-profile:v','high','-maxrate',maxrate,'-bufsize',buf]+extra
    threads=str(max(2,min(12,os.cpu_count() or 4)))
    preset,crf,maxrate,buf=q['x264']
    return ['-c:v','libx264','-preset',preset or cpu_preset,'-threads',threads,'-crf',crf,'-profile:v','high','-maxrate',maxrate,'-bufsize',buf]

def select_encoder(ff,width,height,fps,mode='auto',cpu_preset='veryfast',runner=None,quality='padrao'):
    runner=runner or subprocess.run
    q=QUALITY.get(quality,QUALITY['padrao'])
    reason='CPU selecionada na configuração.'
    if mode!='cpu':
        cmd=[ff,'-hide_banner','-v','error','-f','lavfi','-i',f'color=c=black:s={width}x{height}:r={fps}','-frames:v','3','-an']+options('h264_nvenc',quality=quality)+['-g','250','-pix_fmt','yuv420p','-f','null','-']
        try:
            r=runner(cmd,capture_output=True,timeout=25)
            if r.returncode==0:return {'encoder':'h264_nvenc','label':'NVIDIA NVENC','reason':'Teste real de codificação aprovado.','args':options('h264_nvenc',quality=quality),'quality':{'cq':int(q['nvenc'][1]),**({'nivel':quality} if quality!='padrao' else {})}}
            err=r.stderr.decode(errors='replace') if isinstance(r.stderr,bytes) else str(r.stderr)
            reason='NVENC indisponível; usando CPU. '+err.strip()[-700:]
        except (OSError,subprocess.TimeoutExpired) as e:reason='Teste NVENC não concluído; usando CPU. '+str(e)[:300]
    return {'encoder':'libx264','label':'CPU / H.264','reason':reason,'args':options('libx264',cpu_preset,quality),'quality':{'crf':int(q['x264'][1]),**({'nivel':quality} if quality!='padrao' else {})}}


def validate_mp4(ff,path,frames,width,height,fps,timeout=3600):
    """1.20: confere o MP4 gravado: decodifica o vídeo inteiro (erros), conta os quadros e lê codec,
    resolução, formato de pixel e taxa. Um processo encerrado não comprova sucesso."""
    import re,subprocess
    info=subprocess.run([ff,'-hide_banner','-i',str(path)],capture_output=True,text=True,timeout=120).stderr
    m=re.search(r'Video: (\w+).*?, (\w+)\(?.*?, (\d+)x(\d+)',info)
    r=re.search(r'([\d.]+) fps',info)
    dec=subprocess.run([ff,'-v','error','-nostats','-i',str(path),'-map','0:v:0','-f','null','-','-progress','pipe:1'],capture_output=True,text=True,timeout=timeout)
    counted=[int(x) for x in re.findall(r'^frame=(\d+)',dec.stdout,re.M)]
    out={'codec':m.group(1) if m else None,'pix_fmt':m.group(2) if m else None,'width':int(m.group(3)) if m else None,'height':int(m.group(4)) if m else None,
         'fps':float(r.group(1)) if r else None,'frames_decoded':counted[-1] if counted else None,'frames_expected':int(frames),'decode_errors':dec.stderr.strip()[:500],'faststart':None}
    try:
        head=open(path,'rb').read(1<<20);out['faststart']=0<=head.find(b'moov')<head.find(b'mdat') if b'mdat' in head else b'moov' in head
    except OSError:pass
    problems=[]
    if dec.returncode!=0 or out['decode_errors']:problems.append('erros ao decodificar')
    if out['frames_decoded']!=int(frames):problems.append(f"quadros {out['frames_decoded']} de {frames}")
    if (out['width'],out['height'])!=(width,height):problems.append(f"resolução {out['width']}x{out['height']}")
    if out['codec']!='h264' or out['pix_fmt']!='yuv420p':problems.append(f"codec {out['codec']}/{out['pix_fmt']}")
    if out['fps'] is not None and abs(out['fps']-fps)>.01:problems.append(f"taxa {out['fps']}")
    out['ok']=not problems;out['problems']=problems
    return out
