"""Elevação do terreno (1.7): modelo digital local (GeoTIFF/arquivo de mundo) ou web (AWS Terrain Tiles).

A imagem aérea já é ortorretificada: em planta ela NÃO é deformada pela elevação. O relevo entra
como sombreamento e curvas de nível sobre a imagem (que continua no mesmo lugar) e, na vista da
cabine, como superfície 3D sobre a qual a imagem é “vestida” pelas próprias coordenadas X/Y
(cada pixel da ortofoto fica no seu X/Y; só ganha altura).
"""
import io,json,math,hashlib,urllib.request
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
from pyproj import CRS,Transformer
from scipy.ndimage import gaussian_filter1d,distance_transform_edt

TERRARIUM='https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
WEB_ATTRIBUTION='Elevação: AWS Terrain Tiles (Mapzen; SRTM, GMTED, ETOPO1 e outras fontes abertas)'

def decode_terrarium(rgb):
    a=rgb.astype(np.float64);return (a[:,:,0]*256+a[:,:,1]+a[:,:,2]/256-32768).astype(np.float32)

def encode_terrarium(h):
    v=np.asarray(h,np.float64)+32768;r=np.floor(v/256);g=np.floor(v-r*256);b=np.round((v-r*256-g)*256)
    return np.dstack([r,g,np.clip(b,0,255)]).astype(np.uint8)

def lonlat_to_tile(lon,lat,z):
    n=2**z;x=(lon+180)/360*n;lr=np.radians(lat);y=(1-np.log(np.tan(lr)+1/np.cos(lr))/math.pi)/2*n
    return x,y

def fetch_tile(cache,z,x,y,fetcher=None):
    f=Path(cache)/f'terrarium_{z}_{x}_{y}.png'
    if not f.exists():
        if fetcher:data=fetcher(z,x,y)
        else:
            req=urllib.request.Request(TERRARIUM.format(z=z,x=x,y=y),headers={'User-Agent':'RodoviaStudio/1.7'})
            with urllib.request.urlopen(req,timeout=40) as r:data=r.read()
        Image.open(io.BytesIO(data)).verify();tmp=f.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(f)
    return np.array(Image.open(f).convert('RGB'))

def web_dem(directory,crs,box,n,fetcher=None,status=lambda *a:None):
    """Grade n×n (mesmo enquadramento do mosaico) a partir dos ladrilhos Terrarium, com cache local."""
    cache=Path(directory)/'elevacao';cache.mkdir(exist_ok=True)
    tr=Transformer.from_crs(CRS.from_user_input(crs),4326,always_xy=True)
    x0,y0,x1,y1=box;lon0,lat0,lon1,lat1=tr.transform_bounds(x0,y0,x1,y1,densify_pts=21)
    span_m=x1-x0;z=int(np.clip(round(math.log2(40075016*math.cos(math.radians((lat0+lat1)/2))/256/max(span_m/n,15))),8,14))
    tx0,ty0=lonlat_to_tile(lon0,lat1,z);tx1,ty1=lonlat_to_tile(lon1,lat0,z)
    xs=range(int(tx0),int(tx1)+1);ys=range(int(ty0),int(ty1)+1)
    if len(xs)*len(ys)>64:raise ValueError('Área grande demais para a base de elevação web (mais de 64 ladrilhos).')
    mos=np.zeros((len(ys)*256,len(xs)*256),np.float32)
    for j,ty in enumerate(ys):
        for i,tx in enumerate(xs):
            mos[j*256:(j+1)*256,i*256:(i+1)*256]=decode_terrarium(fetch_tile(cache,z,tx,ty,fetcher))
        status(.04,'Carregando elevação web')
    span=(x1-x0)/n;out=np.empty((n,n),np.float32);xs_w=x0+np.arange(n)*span
    for r0 in range(0,n,256):
        r1=min(n,r0+256);X,Y=np.meshgrid(xs_w,y1-np.arange(r0,r1)*span);lon,lat=tr.transform(X,Y)
        px,py=lonlat_to_tile(np.asarray(lon),np.asarray(lat),z)
        out[r0:r1]=cv2.remap(mos,((px-xs[0])*256-.5).astype(np.float32),((py-ys[0])*256-.5).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    res=40075016*math.cos(math.radians((lat0+lat1)/2))/256/2**z
    return out,f'{WEB_ATTRIBUTION} · z{z} ≈ {res:.0f} m/px'

def local_dem(directory,el,crs,box,n):
    from .local_imagery import georef
    base=Path(directory)/'elevacao';image=base/el.file
    if not image.exists():raise ValueError('Arquivo de elevação ausente: envie o MDT novamente.')
    info=georef(image,base/el.world if el.world else None,base/el.prj if el.prj else None,el.crs)
    if image.suffix.lower() in ('.tif','.tiff'):
        import tifffile
        with tifffile.TiffFile(image) as tf:
            a=tf.pages[0].asarray();nod=tf.pages[0].tags.get(42113)
            nodata=float(str(nod.value).strip('\x00')) if nod is not None else None
    else:
        a=np.array(Image.open(image));nodata=None
    if a.ndim==3:a=a[:,:,0]
    a=a.astype(np.float32)
    bad=~np.isfinite(a)|(a<-1000)|(a>9000)
    if nodata is not None:bad|=a==nodata
    if bad.all():raise ValueError('O arquivo de elevação não tem valores válidos.')
    if bad.any():
        idx=distance_transform_edt(bad,return_distances=False,return_indices=True);a=a[tuple(idx)]
    gt=info['gt'];target=CRS.from_user_input(crs);tr=None if info['crs']==target else Transformer.from_crs(target,info['crs'],always_xy=True)
    det=gt[1]*gt[5]-gt[2]*gt[4];x0,y0,x1,y1=box;span=(x1-x0)/n;out=np.empty((n,n),np.float32);xs=x0+np.arange(n)*span
    for r0 in range(0,n,256):
        r1=min(n,r0+256);X,Y=np.meshgrid(xs,y1-np.arange(r0,r1)*span)
        if tr is not None:X,Y=tr.transform(X,Y)
        dx=np.asarray(X)-gt[0];dy=np.asarray(Y)-gt[3]
        c=(gt[5]*dx-gt[2]*dy)/det;r=(-gt[4]*dx+gt[1]*dy)/det
        out[r0:r1]=cv2.remap(a,(c-.5).astype(np.float32),(r-.5).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    from .local_imagery import pixel_size_m
    return out,f'Elevação local: {el.file} · {pixel_size_m(info,target):.1f} m/px'

def hillshade(dem,cell_m,azimuth=315.,altitude=45.,exaggeration=1.):
    gy,gx=np.gradient(dem.astype(np.float64)*exaggeration,cell_m)
    slope=np.arctan(np.hypot(gx,gy));aspect=np.arctan2(-gx,gy)
    az=math.radians(360-azimuth+90);alt=math.radians(altitude)
    return np.clip(np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-aspect),0,1).astype(np.float32)

def shade_map(image,dem,cell_m,opacity,exaggeration=1.):
    """Relevo sombreado multiplicado sobre a imagem: nada muda de lugar, só o brilho."""
    hs=hillshade(dem,cell_m,exaggeration=exaggeration)
    hs=cv2.resize(hs,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_LINEAR) if hs.shape!=image.shape[:2] else hs
    f=1+opacity*(hs/max(float(np.median(hs)),1e-3)-1)
    image[:]=np.clip(image.astype(np.float32)*f[:,:,None],0,255).astype(np.uint8)

def contours(image,dem,interval,box,worldpx):
    """Curvas de nível (mestras a cada 5 intervalos) desenhadas sobre o mosaico."""
    from skimage.measure import find_contours
    lo=math.ceil(float(dem.min())/interval)*interval;hi=float(dem.max());n=dem.shape[0];x0,y0,x1,y1=box;cell=(x1-x0)/n
    k=0
    for level in np.arange(lo,hi,interval):
        master=abs(round(level/interval))%5==0
        for c in find_contours(dem,level):
            w=np.column_stack([x0+c[:,1]*cell,y1-c[:,0]*cell])
            q=np.rint(worldpx(w)).astype(np.int32)
            cv2.polylines(image,[q],False,(244,226,170) if master else (226,214,180),2 if master else 1,cv2.LINE_AA)
        k+=1
        if k>400:break

class Terrain:
    """Grade de elevação alinhada ao mosaico, com pista nivelada pelo perfil suavizado do eixo."""
    def __init__(self,dem,box,label,surface=None,stations=None,length=1.,level_road=True,exaggeration=1.,oae=()):
        self.raw=dem.astype(np.float32);self.box=box;self.n=dem.shape[0];self.cell=(box[2]-box[0])/self.n;self.label=label;self.exaggeration=exaggeration
        h=self.raw.copy()
        if level_road and surface is not None and stations is not None:
            # Superfície de rolamento: perfil longitudinal suavizado (≈150 m) do terreno sob o eixo.
            k=surface.shape[0]/self.n
            surf=cv2.resize(((np.asarray(surface)>0)&(np.asarray(surface)<6)).astype(np.uint8),(self.n,self.n),interpolation=cv2.INTER_NEAREST)>0
            st=cv2.resize(np.asarray(stations),(self.n,self.n),interpolation=cv2.INTER_NEAREST)
            ok=surf&(st<65535)
            if ok.any():
                bins=np.clip((st[ok].astype(np.float64)/65534*length/5).astype(int),0,int(length/5)+1)
                sums=np.bincount(bins,weights=h[ok],minlength=int(length/5)+2);cnt=np.bincount(bins,minlength=int(length/5)+2)
                prof=np.where(cnt>0,sums/np.maximum(cnt,1),np.nan);idx=np.arange(len(prof));good=~np.isnan(prof)
                prof=np.interp(idx,idx[good],prof[good]);prof=gaussian_filter1d(prof,30,mode='nearest')
                # OAE: o tabuleiro vai reto entre os encontros (não acompanha o fundo do vale).
                for o in oae:
                    a,b=int(np.clip(o['chain'][0]/5,0,len(prof)-1)),int(np.clip(o['chain'][1]/5+1,0,len(prof)-1))
                    if b>a+1:prof[a:b+1]=np.linspace(prof[a],prof[b],b-a+1)
                road=np.zeros_like(h);road[ok]=prof[np.clip((st[ok].astype(np.float64)/65534*length/5).astype(int),0,len(prof)-1)]
                # Transição suave de ~15 m entre pista nivelada e terreno natural.
                d=distance_transform_edt(~ok)*self.cell;w=np.clip(1-d/15,0,1)
                near_idx=distance_transform_edt(~ok,return_distances=False,return_indices=True);road_ext=road[tuple(near_idx)]
                h=h*(1-w)+road_ext*w
        self.h=(h*exaggeration).astype(np.float32)
    def sample(self,x,y,grid=None):
        g=self.h if grid is None else grid
        u=((np.asarray(x,np.float64)-self.box[0])/self.cell).astype(np.float32);v=((self.box[3]-np.asarray(y,np.float64))/self.cell).astype(np.float32)
        shape=u.shape;flat_u=u.ravel();flat_v=v.ravel();m=len(flat_u);w=1024;pad=(-m)%w
        U=np.pad(flat_u,(0,pad)).reshape(-1,w);V=np.pad(flat_v,(0,pad)).reshape(-1,w)
        return cv2.remap(g,U,V,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).ravel()[:m].reshape(shape)
    def raw_at(self,x,y):
        u=float((x-self.box[0])/self.cell);v=float((self.box[3]-y)/self.cell)
        if not(0<=u<self.n-1 and 0<=v<self.n-1):return None
        return float(cv2.remap(self.raw,np.array([[u]],np.float32),np.array([[v]],np.float32),cv2.INTER_LINEAR)[0,0])

def save_cache(directory,terrain):
    d=Path(directory)/'elevacao';d.mkdir(exist_ok=True)
    np.save(d/'grade.npy',terrain.raw,allow_pickle=False);(d/'grade.json').write_text(json.dumps({'box':list(map(float,terrain.box)),'label':terrain.label}),encoding='utf-8')

def value_at(directory,x,y):
    d=Path(directory)/'elevacao'
    if not (d/'grade.npy').exists():return None
    meta=json.loads((d/'grade.json').read_text(encoding='utf-8'));g=np.load(d/'grade.npy',mmap_mode='r');n=g.shape[0];b=meta['box'];cell=(b[2]-b[0])/n
    u=(x-b[0])/cell;v=(b[3]-y)/cell
    if not(0<=u<n-1 and 0<=v<n-1):return None
    i,j=int(v),int(u);fu,fv=u-j,v-i
    return float(g[i,j]*(1-fu)*(1-fv)+g[i,j+1]*fu*(1-fv)+g[i+1,j]*(1-fu)*fv+g[i+1,j+1]*fu*fv)
