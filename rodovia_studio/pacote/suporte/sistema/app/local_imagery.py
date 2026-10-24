"""Imagem georreferenciada local: GeoTIFF ou imagem + arquivo de mundo (.tfw/.jgw/.pgw/.wld) + .prj/CRS.

A imagem é reprojetada para o CRS do projeto, recortada à área de interesse e guardada em cache.
Arquivos sem georreferência são rejeitados com mensagem clara.
Transformação afim no padrão GDAL (canto superior esquerdo do pixel):
    X = c + a*col + b*lin ;  Y = f + d*col + e*lin
"""
import hashlib,json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
from pyproj import CRS,Transformer

IMAGE_EXT={'.tif','.tiff','.jpg','.jpeg','.png','.jp2','.j2k','.jpx'}
CONVERT_EXT={'.ecw','.sid','.img','.vrt','.ntf'}  # 1.17: lidos com o GDAL do computador (QGIS), convertidos para GeoTIFF
WORLD_EXT={'.tfw','.tifw','.tiffw','.jgw','.jpgw','.jpegw','.pgw','.pngw','.wld','.j2w','.jpw'}
NEUTRAL=(58,73,64)
NO_GEOREF=('Arquivo sem georreferência. Envie um GeoTIFF com tags GeoTIFF, ou a imagem junto com o arquivo '
           'de mundo (.tfw/.jgw/.pgw/.wld) e o .prj — ou informe o CRS.')

def parse_world(text):
    v=[float(x.replace(',','.')) for x in text.split()]
    if len(v)<6:raise ValueError('Arquivo de mundo inválido: são esperadas 6 linhas numéricas.')
    A,D,B,E,C,F=v[:6]
    if A==0 and B==0 or D==0 and E==0:raise ValueError('Arquivo de mundo com escala nula.')
    # O arquivo de mundo referencia o CENTRO do pixel superior esquerdo.
    return (C-A/2-B/2,A,B,F-D/2-E/2,D,E)

def _geokeys(tags):
    raw=tags.get(34735)
    if raw is None:return {}
    v=list(raw.value);keys={}
    for i in range(4,4+4*v[3],4):
        kid,loc,count,val=v[i:i+4]
        if loc==0:keys[kid]=val
    return keys

def geotiff_georef(path):
    import tifffile
    with tifffile.TiffFile(path) as tf:
        page=tf.pages[0];tags=page.tags;h,w=page.shape[:2]
        keys=_geokeys(tags)
        if 34264 in tags:
            m=np.array(tags[34264].value,float).reshape(4,4);gt=(m[0,3],m[0,0],m[0,1],m[1,3],m[1,0],m[1,1])
        elif 33550 in tags and 33922 in tags:
            sx,sy=tags[33550].value[:2];tp=tags[33922].value;i,j,_,x,y,_=tp[:6]
            gt=(x-i*sx,sx,0.,y+j*sy,0.,-sy)
        else:return None,None,(w,h)
        if keys.get(1025)==2:  # PixelIsPoint: desloca meio pixel para o canto.
            gt=(gt[0]-gt[1]/2-gt[2]/2,gt[1],gt[2],gt[3]-gt[4]/2-gt[5]/2,gt[4],gt[5])
        epsg=keys.get(3072) or keys.get(2048)
        crs=CRS.from_epsg(int(epsg)) if epsg and int(epsg) not in (0,32767) else None
        return gt,crs,(w,h)

def georef(image,world=None,prj=None,crs=None):
    """Retorna {'gt','crs','size'} ou lança ValueError (sem georreferência / CRS ausente)."""
    image=Path(image);gt=None;found=None;size=None
    if image.suffix.lower() in ('.tif','.tiff'):gt,found,size=geotiff_georef(image)
    if image.suffix.lower() in ('.jp2','.j2k','.jpx') and not world:
        from .local_tiles import jp2_georef
        gt,found=jp2_georef(image)
    if world:gt=parse_world(Path(world).read_text(encoding='utf-8',errors='replace'))
    if gt is None:raise ValueError(NO_GEOREF)
    if prj:found=CRS.from_user_input(Path(prj).read_text(encoding='utf-8',errors='replace'))
    if crs:found=CRS.from_user_input(crs)
    if found is None:raise ValueError('Georreferência sem sistema de coordenadas: envie o .prj ou informe o CRS (ex.: EPSG:31983).')
    if size is None:
        with Image.open(image) as im:size=im.size
    return {'gt':tuple(float(v) for v in gt),'crs':found,'size':size}

def read_pixels(image):
    image=Path(image)
    if image.suffix.lower() in ('.tif','.tiff'):
        import tifffile
        try:a=tifffile.imread(image,key=0)
        except Exception as exc:raise ValueError('Não foi possível ler o GeoTIFF ('+str(exc)[:160]+'). Compressões JPEG/WEBP dentro do TIFF exigem conversão para LZW/Deflate ou sem compressão.')
    else:
        Image.MAX_IMAGE_PIXELS=1_500_000_000
        with Image.open(image) as im:a=np.array(im.convert('RGBA') if im.mode in ('RGBA','LA','P') else im.convert('RGB'))
    if a.ndim==3 and a.shape[0] in (3,4) and a.shape[2] not in (3,4):a=np.moveaxis(a,0,-1)
    if a.ndim==2:a=np.repeat(a[:,:,None],3,2)
    if a.shape[2]>4:a=a[:,:,:3]
    if a.dtype!=np.uint8:
        f=a[:,:,:3].astype(np.float32);lo,hi=np.percentile(f[::max(1,f.shape[0]//512),::max(1,f.shape[1]//512)],[1,99])
        rgb=np.clip((f-lo)/max(hi-lo,1e-6)*255,0,255).astype(np.uint8)
        a=np.dstack([rgb,(a[:,:,3]>0).astype(np.uint8)*255]) if a.shape[2]==4 else rgb
    return a

def pixel_size_m(info,target_crs):
    gt=info['gt'];c=info['crs']
    if c.is_geographic:
        tr=Transformer.from_crs(c,target_crs,always_xy=True);w,h=info['size']
        x0,y0=gt[0]+gt[1]*w/2,gt[3]+gt[5]*h/2;a=np.array(tr.transform(x0,y0));b=np.array(tr.transform(x0+gt[1],y0))
        return float(np.linalg.norm(b-a))
    return float(np.hypot(gt[1],gt[4])*c.axis_info[0].unit_conversion_factor)

def render_local(directory,settings,box,n,status=lambda *a:None):
    """Mosaico n×n do quadro box=[x0,y0,x1,y1] no CRS do projeto, a partir da imagem local."""
    li=settings.local_imagery;base=Path(directory)/'imagem_local'
    if not li.image:raise ValueError('Selecione Imagem local: envie a imagem georreferenciada no projeto.')
    image=base/li.image;world=base/li.world if li.world else None;prj=base/li.prj if li.prj else None
    if not image.exists():raise ValueError('Imagem local ausente na pasta do projeto: envie-a novamente.')
    info=georef(image,world,prj,li.crs);target=CRS.from_user_input(settings.crs)
    h=hashlib.sha256()
    for f in [image,world,prj]:
        if f and f.exists():h.update(f.read_bytes() if f.stat().st_size<64e6 else (str(f.stat().st_size)+str(f.stat().st_mtime_ns)).encode())
    h.update(json.dumps([box,n,settings.crs,li.crs,'v1']).encode());cache=Path(directory)/'imagery';cache.mkdir(exist_ok=True)
    out=cache/f'local_{h.hexdigest()[:16]}.png';res=pixel_size_m(info,target)
    label=f'Imagem local: {li.name or image.name} · {res:.2f} m/px'
    if out.exists():return np.array(Image.open(out).convert('RGB')),label
    status(.1,'Reprojetando imagem local')
    src=read_pixels(image);gt=info['gt'];H,W=src.shape[:2]
    x0,y0,x1,y1=box;span=(x1-x0)/n
    tr=None if info['crs']==target else Transformer.from_crs(target,info['crs'],always_xy=True)
    det=gt[1]*gt[5]-gt[2]*gt[4]
    if abs(det)<1e-18:raise ValueError('Georreferência degenerada.')
    def to_px(X,Y):
        if tr is not None:X,Y=tr.transform(X,Y)
        dx=np.asarray(X)-gt[0];dy=np.asarray(Y)-gt[3]
        return (gt[5]*dx-gt[2]*dy)/det,(-gt[4]*dx+gt[1]*dy)/det
    # Cobertura e resolução estimadas numa grade grossa.
    g=np.linspace(0,n-1,33);GX,GY=np.meshgrid(x0+g*span,y1-g*span);col,row=to_px(GX,GY)
    if np.nanmax(col)<0 or np.nanmin(col)>W or np.nanmax(row)<0 or np.nanmin(row)>H:
        raise ValueError('A imagem local não cobre a área do projeto. Confira o CRS e o arquivo de mundo.')
    step_src=float(np.hypot(np.diff(col,axis=1).mean(),np.diff(row,axis=1).mean()))/(g[1]-g[0])
    # Reduz a origem quando ela é muito mais detalhada que o mosaico (evita serrilhado e o limite de 32767 px do OpenCV).
    k=max(1.,step_src/1.2,max(H,W)/32000)
    if k>1.01:src=cv2.resize(src,(max(1,int(W/k)),max(1,int(H/k))),interpolation=cv2.INTER_AREA)
    sx=src.shape[1]/W;sy=src.shape[0]/H
    rgb=np.ascontiguousarray(src[:,:,:3]);alpha_src=np.ascontiguousarray(src[:,:,3]) if src.shape[2]==4 else None
    out_img=np.empty((n,n,3),np.uint8);xs=x0+np.arange(n)*span
    for r0 in range(0,n,256):
        r1=min(n,r0+256);X,Y=np.meshgrid(xs,y1-np.arange(r0,r1)*span)
        c,r=to_px(X,Y);mx=(c*sx-.5).astype(np.float32);my=(r*sy-.5).astype(np.float32)
        part=cv2.remap(rgb,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=NEUTRAL)
        if alpha_src is not None:
            al=cv2.remap(alpha_src,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)[:,:,None]/255.
            part=(part*al+np.array(NEUTRAL)*(1-al)).astype(np.uint8)
        out_img[r0:r1]=part
        status(.1+.1*r1/n,'Reprojetando imagem local')
    tmp=out.with_suffix('.tmp.png');Image.fromarray(out_img).save(tmp);tmp.replace(out)
    return out_img,label

def describe(directory,li,target_crs):
    base=Path(directory)/'imagem_local';info=georef(base/li.image,base/li.world if li.world else None,base/li.prj if li.prj else None,li.crs)
    gt=info['gt'];w,h=info['size'];corners=np.array([[gt[0]+gt[1]*c+gt[2]*r,gt[3]+gt[4]*c+gt[5]*r] for c,r in [(0,0),(w,0),(w,h),(0,h)]])
    tgt=CRS.from_user_input(target_crs);tr=Transformer.from_crs(info['crs'],tgt,always_xy=True);x,y=tr.transform(corners[:,0],corners[:,1])
    return {'size':[w,h],'crs':info['crs'].to_string(),'pixel_m':pixel_size_m(info,tgt),'bounds':[float(min(x)),float(min(y)),float(max(x)),float(max(y))]}
