"""Ficha técnica de vídeo: dados do arquivo + métricas de imagem medidas em quadros amostrados.

Substitui o MP4 de referência TH57 (456 MB) por um JSON pequeno usado só para comparação:
resolução, taxa, duração, codec, taxa de bits e métricas de nitidez, contraste, cor e sinalização.
As métricas são relativas (mesmo método nos dois vídeos), não uma nota absoluta de qualidade.
"""
import json,re,subprocess,hashlib
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import cv2
from .encoding import ffmpeg_exe

def probe(path):
    """Lê os dados do contêiner pela saída do FFmpeg (o pacote imageio-ffmpeg não traz ffprobe)."""
    r=subprocess.run([ffmpeg_exe(),'-hide_banner','-i',str(path)],capture_output=True,timeout=60)
    t=r.stderr.decode('utf-8','replace');info={'bytes':Path(path).stat().st_size}
    m=re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)',t)
    if m:info['duration_s']=round(int(m[1])*3600+int(m[2])*60+float(m[3]),3)
    m=re.search(r'bitrate:\s*(\d+)\s*kb/s',t)
    if m:info['bitrate_kbps']=int(m[1])
    v=re.search(r'Stream #\S+.*?Video:\s*(\w+)\s*(?:\(([^)]*)\))?.*?,\s*(\w+)(?:\([^)]*\))?,\s*(\d+)x(\d+)',t)
    if v:info.update(codec=v[1],profile=v[2] or '',pix_fmt=v[3],width=int(v[4]),height=int(v[5]))
    f=re.search(r'([\d.]+)\s*fps',t)
    if f:info['fps']=float(f[1])
    if 'duration_s' in info and 'fps' in info:info['frames']=int(round(info['duration_s']*info['fps']))
    if 'duration_s' in info:info['bitrate_avg_mbps']=round(info['bytes']*8/info['duration_s']/1e6,3)
    if all(k in info for k in ('bitrate_avg_mbps','width','height','fps')):info['bits_per_pixel']=round(info['bitrate_avg_mbps']*1e6/(info['width']*info['height']*info['fps']),4)
    return info

def frame_at(path,t,width=None):
    cmd=[ffmpeg_exe(),'-v','error','-ss',f'{t:.3f}','-i',str(path),'-frames:v','1','-f','image2pipe','-vcodec','png','-']
    r=subprocess.run(cmd,capture_output=True,timeout=120)
    if r.returncode or not r.stdout:return None
    im=cv2.imdecode(np.frombuffer(r.stdout,np.uint8),cv2.IMREAD_COLOR)
    return None if im is None else cv2.cvtColor(im,cv2.COLOR_BGR2RGB)

def image_metrics(rgb,header_frac=157/1440,footer_frac=154/1440):
    """Métricas na área do mapa (sem cabeçalho e rodapé), em escala 1440p para comparar resoluções diferentes."""
    H,W=rgb.shape[:2];y0=int(H*header_frac)+1;y1=H-int(H*footer_frac);a=rgb[y0:y1]
    if H!=1440:a=cv2.resize(a,(int(a.shape[1]*1440/H),int(a.shape[0]*1440/H)),interpolation=cv2.INTER_AREA if H>1440 else cv2.INTER_CUBIC)
    g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(np.float32)
    lap=cv2.Laplacian(g,cv2.CV_32F)
    edges=cv2.Canny(g.astype(np.uint8),60,140)
    r,gg,b=[a[:,:,k].astype(np.float32) for k in range(3)];rg=r-gg;yb=.5*(r+gg)-b
    colorful=float(np.hypot(rg.std(),yb.std())+.3*np.hypot(rg.mean(),yb.mean()))
    hsv=cv2.cvtColor(a,cv2.COLOR_RGB2HSV)
    # Sinalização: traços claros, pouco saturados e finos (top-hat), como faixas de pintura.
    tophat=cv2.morphologyEx(g,cv2.MORPH_TOPHAT,cv2.getStructuringElement(cv2.MORPH_RECT,(9,9)))
    marks=(tophat>35)&(hsv[:,:,1]<70)&(g>150)
    mark_contrast=float(tophat[marks].mean()) if marks.any() else 0.
    # Pavimento aproximado: cinza escuro/médio pouco saturado.
    pav=(hsv[:,:,1]<45)&(g>45)&(g<150)
    return {'sharpness_lap_var':round(float(lap.var()),2),'edge_density':round(float((edges>0).mean()),5),'brightness':round(float(g.mean()),2),
            'contrast_std':round(float(g.std()),2),'colorfulness':round(colorful,2),'marking_pixels_pct':round(float(marks.mean()*100),4),
            'marking_contrast':round(mark_contrast,2),'pavement_like_pct':round(float(pav.mean()*100),3),
            'pavement_texture_std':round(float(g[pav].std()),2) if pav.any() else 0.}

def profile(path,instants=(14,40,96),extra_samples=12,label='',sha=True):
    info=probe(path);dur=info.get('duration_s',0)
    times=sorted(set([t for t in instants if t<dur]+[round(dur*(k+.5)/extra_samples,2) for k in range(extra_samples)])) if dur else list(instants)
    samples={}
    for t in times:
        im=frame_at(path,t)
        if im is not None:samples[f'{t:g}']=image_metrics(im)
    keys=next(iter(samples.values())).keys() if samples else []
    summary={k:round(float(np.median([s[k] for s in samples.values()])),4) for k in keys}
    out={'label':label or Path(path).name,'created':datetime.now(timezone.utc).isoformat(),'file':info,'image_median':summary,'samples':samples,
         'method':'Métricas na área do mapa, reamostrada para 1440p; mediana dos quadros amostrados. Comparação relativa, não nota absoluta.'}
    if sha:
        h=hashlib.sha256()
        with open(path,'rb') as f:
            while b:=f.read(8*1024*1024):h.update(b)
        out['file']['sha256']=h.hexdigest()
    return out

LABELS={'width':'Largura (px)','height':'Altura (px)','fps':'Quadros/s','duration_s':'Duração (s)','frames':'Quadros','codec':'Codec','profile':'Perfil','pix_fmt':'Formato de pixel',
        'bitrate_avg_mbps':'Taxa média (Mbit/s)','bits_per_pixel':'Bits por pixel por quadro','bytes':'Tamanho (bytes)',
        'sharpness_lap_var':'Nitidez (variância do Laplaciano)','edge_density':'Densidade de bordas','brightness':'Brilho médio','contrast_std':'Contraste (desvio do brilho)',
        'colorfulness':'Colorido (Hasler-Süsstrunk)','marking_pixels_pct':'Sinalização visível (% de pixels)','marking_contrast':'Contraste da sinalização',
        'pavement_like_pct':'Área com aparência de pavimento (%)','pavement_texture_std':'Textura do pavimento (desvio)'}

def compare(reference,current):
    rows=[]
    for group in ('file','image_median'):
        for k,label in LABELS.items():
            a=reference.get(group,{}).get(k);b=current.get(group,{}).get(k)
            if a is None and b is None:continue
            delta=None
            if isinstance(a,(int,float)) and isinstance(b,(int,float)) and not isinstance(a,bool) and a:delta=round((b-a)/abs(a)*100,1)
            rows.append({'key':k,'label':label,'reference':a,'current':b,'delta_pct':delta})
    return rows
