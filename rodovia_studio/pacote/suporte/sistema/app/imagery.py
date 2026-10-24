import io,json,hashlib,time,urllib.request,urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import cv2
from PIL import Image
from pyproj import CRS

ASSETS=Path(__file__).resolve().parents[1]/'assets'
def enhance(a):
    lab=cv2.cvtColor(a,cv2.COLOR_RGB2LAB);l=lab[:,:,0];cl=cv2.createCLAHE(clipLimit=1.6,tileGridSize=(12,8)).apply(l)
    l=cv2.addWeighted(l,.45,cl,.55,0);blur=cv2.GaussianBlur(l,(0,0),1.4);lab[:,:,0]=cv2.addWeighted(l,1.55,blur,-.55,0)
    a=cv2.cvtColor(lab,cv2.COLOR_LAB2RGB);h=cv2.cvtColor(a,cv2.COLOR_RGB2HSV);s=h[:,:,1].astype(np.float32);h[:,:,1]=np.minimum(255,s*(1+.16*(1-s/255))).astype(np.uint8)
    return cv2.cvtColor(h,cv2.COLOR_HSV2RGB)

def mosaic(directory,settings,bounds,status=lambda *a:None,warnings=None):
    directory=Path(directory);lo,hi=np.array(bounds);padding=max(200,min(1000,np.max(hi-lo)*.08));lo-=padding;hi+=padding
    span=max(hi-lo);center=(hi+lo)/2;lo=center-span/2;hi=center+span/2
    if settings.imagery=='neutral':
        image=Image.new('RGB',(2048,2048),(58,73,64));return np.array(image),[lo[0],lo[1],hi[0],hi[1]],'Fundo neutro — sem imagem aérea'
    if settings.imagery=='local':
        from .local_imagery import render_local
        n=settings.imagery_pixels;box=[float(lo[0]),float(lo[1]),float(hi[0]),float(hi[1])]
        if use_local_mosaic(directory,settings.local_imagery):return mosaic_local(directory,settings,box,n,status)
        image,label=render_local(directory,settings,box,n,status);return image,box,label
    if settings.imagery=='cache':
        info=json.loads((ASSETS/'th57/map.json').read_text(encoding='utf-8'));b=info['bounds'];tr=CRS.from_user_input(settings.crs)
        if tr!=CRS.from_user_input(info['crs']) or lo[0]<b[0]-100 or lo[1]<b[1]-100 or hi[0]>b[2]+100 or hi[1]>b[3]+100:
            # Only the actual project extent must be inside; padding may exceed cache.
            bl,bh=np.array(bounds)
            if tr!=CRS.from_user_input(info['crs']) or bl[0]<b[0] or bl[1]<b[1] or bh[0]>b[2] or bh[1]>b[3]: raise ValueError('A imagem guardada no pacote (trecho de exemplo) não cobre este projeto. Selecione Esri ou fundo neutro.')
        return np.array(Image.open(ASSETS/'th57/map.jpg').convert('RGB')),b,'Esri, Vantor, Earthstar Geographics e GIS User Community'
    w=getattr(settings,'web_imagery',None)
    if w is not None and w.source!='esri':
        box=[float(lo[0]),float(lo[1]),float(hi[0]),float(hi[1])]
        return mosaic_tiles(directory,settings,box,settings.imagery_pixels,status,warnings=warnings)
    n=settings.imagery_pixels;tiles=max(1,n//2048);tile=n//tiles
    box=[float(lo[0]),float(lo[1]),float(hi[0]),float(hi[1])];epsg=CRS.from_user_input(settings.crs).to_epsg()
    if epsg is None: raise ValueError('A base Esri requer um CRS com código EPSG.')
    cache=directory/'imagery';cache.mkdir(exist_ok=True);key=hashlib.sha256(json.dumps([box,n,epsg]).encode()).hexdigest()[:16]
    def fetch(v):
        i,j=v;file=cache/f'{key}_{i}_{j}.jpg'
        if not file.exists():
            sub=[lo[0]+i*span/tiles,hi[1]-(j+1)*span/tiles,lo[0]+(i+1)*span/tiles,hi[1]-j*span/tiles]
            args={'bbox':','.join(map(str,sub)),'bboxSR':epsg,'imageSR':epsg,'size':f'{tile},{tile}','format':'jpg','f':'image'}
            url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?'+urllib.parse.urlencode(args)
            # 1.20: tentativas controladas (3, com espera crescente) e conferência do conteúdo, não só do status HTTP.
            err=None
            for attempt in range(3):
                try:
                    req=urllib.request.Request(url,headers={'User-Agent':'RodoviaStudio/1.0'})
                    with urllib.request.urlopen(req,timeout=60) as r:data=r.read()
                    im=Image.open(io.BytesIO(data));im.verify();break
                except Exception as e:
                    err=e
                    if attempt<2:time.sleep(1.5*(attempt+1))
            else:raise err
            tmp=file.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(file)
        return i,j,Image.open(file).convert('RGB')
    result=Image.new('RGB',(n,n));blank=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for k,(i,j,im) in enumerate(pool.map(fetch,[(i,j) for i in range(tiles) for j in range(tiles)])):
            if is_blank(np.asarray(im)):blank+=1
            result.paste(im,(i*tile,j*tile));status(.08+.12*(k+1)/(tiles*tiles),'Carregando imagem aérea')
    label='Esri, Vantor, Earthstar Geographics e GIS User Community'
    if blank and warnings is not None:warnings.append(f'{blank} bloco(s) da imagem aérea vieram sem imagem (área sem cobertura ou serviço indisponível). Confira o fundo nesses locais.')
    return enhance(np.array(result)),box,label

def is_blank(a):
    """Bloco sem imagem: quase uniforme ou mensagem de indisponibilidade (fundo claro, pouca cor)."""
    a=np.asarray(a)
    if a.ndim!=3 or a.size==0:return True
    small=cv2.resize(a,(64,64),interpolation=cv2.INTER_AREA).astype(np.float32)
    m=float(small.mean())
    if float(small.std())<1.5 and (m>230 or m<8):return True   # bloco branco ou preto uniforme (sem dados)
    hsv=cv2.cvtColor(small.astype(np.uint8),cv2.COLOR_RGB2HSV)
    return float(np.mean((hsv[:,:,1]<12)&(hsv[:,:,2]>175)))>.8

def use_local_mosaic(directory,li):
    """Uma imagem pequena em JPG/PNG/TIF segue o caminho anterior (resultado idêntico); mosaico, JPEG2000
    e arquivos grandes usam a leitura por blocos."""
    if not li.image:return False
    f=Path(directory)/'imagem_local'/li.image
    if any(o.enabled for o in getattr(li,'others',[]) or []):return True
    if (getattr(li,'shift_x',0),getattr(li,'shift_y',0),getattr(li,'rotation_deg',0),getattr(li,'scale',1))!=(0,0,0,1):return True  # 1.19: ajuste por grips
    if f.suffix.lower() in ('.jp2','.j2k','.jpx'):return True
    return f.exists() and f.stat().st_size>300*1024*1024

def mosaic_local(directory,settings,box,n,status=lambda *a:None):
    """1.17: mosaico base de várias imagens locais (ou de arquivo grande em blocos), com cache em disco."""
    from .local_tiles import LocalMosaic
    m=LocalMosaic(directory,settings);cache=Path(directory)/'imagery';cache.mkdir(exist_ok=True)
    key=hashlib.sha256(json.dumps([box,n,settings.crs,m.key]).encode()).hexdigest()[:16];out=cache/f'local_{key}.png'
    label=f"Imagem local: {len(m.sources)} arquivo(s) · {m.pixel_m():.2f} m/px"
    if out.exists():return np.array(Image.open(out).convert('RGB')),box,label
    rgba=m.render_base(box,n,status).astype(np.float32);a=rgba[:,:,3:4]/255
    img=(rgba[:,:,:3]*a+np.array((58,73,64),np.float32)*(1-a)).astype(np.uint8)
    tmp=out.with_suffix('.tmp.png');Image.fromarray(img).save(tmp);tmp.replace(out)
    return img,box,label


def mosaic_tiles(directory,settings,box,n,status=lambda *a:None,fetch=None,cache_root=None,warnings=None):
    """1.19: mosaico base montado a partir de ladrilhos Web Mercator da fonte escolhida (Wayback, XYZ, WMS),
    reprojetado para o CRS do projeto. Ladrilhos ficam no cache comum (_ladrilhos/<fonte>)."""
    import math
    from pyproj import Transformer
    from .webmap import web_source,tile,MERC_HALF
    src=web_source(settings);root=Path(cache_root) if cache_root else Path(directory).resolve().parent/'_ladrilhos'
    x0,y0,x1,y1=box;tr=Transformer.from_crs(CRS.from_user_input(settings.crs),3857,always_xy=True)
    res=(x1-x0)/n
    gy=gx=np.linspace(0,n-1,17);GX,GY=np.meshgrid(x0+(gx+.5)*res,y1-(gy+.5)*res)
    MX,MY=tr.transform(GX,GY);MX=np.asarray(MX);MY=np.asarray(MY)
    lat=math.degrees(2*math.atan(math.exp(float(MY.mean())/6378137))-math.pi/2)
    z=src.max_zoom
    while z>3 and 2*MERC_HALF/256/2**(z-1)*math.cos(math.radians(lat))<=res*1.2:z-=1
    while True:
        scale=256*2**z/(2*MERC_HALF);px=(MX+MERC_HALF)*scale;py=(MERC_HALF-MY)*scale
        tx0,tx1=int(px.min()//256),int(px.max()//256);ty0,ty1=int(py.min()//256),int(py.max()//256)
        if (tx1-tx0+1)*(ty1-ty0+1)<=1600 or z<=3:break
        z-=1
    W=(tx1-tx0+1)*256;H=(ty1-ty0+1)*256;canvas=np.zeros((H,W,3),np.uint8);jobs=[(tx,ty) for ty in range(ty0,ty1+1) for tx in range(tx0,tx1+1)];fails=0
    def get(v):
        tx,ty=v
        try:
            data=tile(root,z,ty,tx,fetch=fetch,timeout=20,source=src)
            a=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
            if a is None:return tx,ty,None
            a=cv2.cvtColor(cv2.resize(a,(256,256)) if a.shape[:2]!=(256,256) else a,cv2.COLOR_BGR2RGB)
            return tx,ty,(None if is_blank(a) else a)
        except Exception:return tx,ty,None
    with ThreadPoolExecutor(max_workers=8) as pool:
        for k,(tx,ty,a) in enumerate(pool.map(get,jobs)):
            if a is None:fails+=1;continue
            canvas[(ty-ty0)*256:(ty-ty0+1)*256,(tx-tx0)*256:(tx-tx0+1)*256]=a
            if k%20==0:status(.08+.12*(k+1)/len(jobs),'Carregando imagem aérea ('+src.attribution+')')
    if fails==len(jobs):raise ValueError('Nenhum ladrilho da fonte web escolhida pôde ser obtido (sem internet ou endereço incorreto). Volte para a Esri atual ou verifique o endereço.')
    from .local_tiles import _upsample
    mx=_upsample(px-tx0*256,gy,gx,n,n);my=_upsample(py-ty0*256,gy,gx,n,n)
    out=cv2.remap(canvas,mx-.5,my-.5,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    label=src.attribution
    if fails and warnings is not None:warnings.append(f'{fails} de {len(jobs)} ladrilho(s) da fonte web vieram vazios ou indisponíveis.')
    return enhance(out),box,label
