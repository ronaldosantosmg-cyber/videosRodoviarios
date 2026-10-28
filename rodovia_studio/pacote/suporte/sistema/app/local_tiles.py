"""1.17: imagem georreferenciada local de alta resolução (ortofoto, drone) em ladrilhos.

Fontes: GeoTIFF/COG (leitura por blocos, sem carregar o arquivo inteiro quando é em blocos com compressão
Deflate/sem compressão; usa as visões reduzidas do COG), JPEG2000 (.jp2 com GeoJP2/GML ou arquivo de mundo),
JPG/PNG/TIF com arquivo de mundo e, com um GDAL instalado no computador (QGIS/OSGeo4W), ECW, MrSID e outros
formatos convertidos uma vez para GeoTIFF em blocos.

Várias imagens formam um mosaico (a primeira da lista tem prioridade). A amostragem gera ladrilhos no CRS do
projeto (camada de detalhe do vídeo e mosaico base) e em Web Mercator (editor, igual ao Google Earth).
"""
import io,os,re,json,math,shutil,hashlib,threading,subprocess,collections
from pathlib import Path
import numpy as np
import cv2
from pyproj import CRS,Transformer

GEOJP2_UUID=bytes.fromhex('b14bf8bd083d4b43a5ae8cd7d5a6ce03')
MAX_FULL_PIXELS=700_000_000   # acima disso, leitura completa é recusada (converta para GeoTIFF em blocos)

# ---------------- georreferência JPEG2000 ----------------
def _jp2_boxes(data,start=0,end=None):
    end=len(data) if end is None else end;i=start
    while i+8<=end:
        L=int.from_bytes(data[i:i+4],'big');t=data[i+4:i+8];h=8
        if L==1:L=int.from_bytes(data[i+8:i+16],'big');h=16
        elif L==0:L=end-i
        if L<h:break
        yield t,i+h,i+L;i+=L

def jp2_georef(path):
    """(gt, crs) de um .jp2 com caixa GeoJP2 (TIFF degenerado) ou GMLJP2; (None,None) se não houver."""
    with open(path,'rb') as f:data=f.read(4*1024*1024)
    for t,a,b in _jp2_boxes(data):
        if t==b'uuid' and data[a:a+16]==GEOJP2_UUID:
            import tifffile
            from .local_imagery import _geokeys
            with tifffile.TiffFile(io.BytesIO(data[a+16:b])) as tf:
                tags=tf.pages[0].tags;keys=_geokeys(tags)
                if 34264 in tags:
                    m=np.array(tags[34264].value,float).reshape(4,4);gt=(m[0,3],m[0,0],m[0,1],m[1,3],m[1,0],m[1,1])
                elif 33550 in tags and 33922 in tags:
                    sx,sy=tags[33550].value[:2];tp=tags[33922].value;i,j,_,x,y,_=tp[:6];gt=(x-i*sx,sx,0.,y+j*sy,0.,-sy)
                else:continue
                if keys.get(1025)==2:gt=(gt[0]-gt[1]/2-gt[2]/2,gt[1],gt[2],gt[3]-gt[4]/2-gt[5]/2,gt[4],gt[5])
                epsg=keys.get(3072) or keys.get(2048)
                return gt,(CRS.from_epsg(int(epsg)) if epsg and int(epsg) not in (0,32767) else None)
    # GMLJP2: origem e vetores de deslocamento (centro do pixel).
    txt=data.decode('latin-1')
    m=re.search(r'<gml:origin>.*?<gml:pos>([^<]+)</gml:pos>',txt,re.S) or re.search(r'<gml:pos>([^<]+)</gml:pos>',txt)
    vec=re.findall(r'<gml:offsetVector[^>]*>([^<]+)</gml:offsetVector>',txt)
    if m and len(vec)>=2:
        o=[float(v) for v in m.group(1).split()];a=[float(v) for v in vec[0].split()];b=[float(v) for v in vec[1].split()]
        srs=re.search(r'srsName="([^"]+)"',txt);crs=None
        if srs:
            e=re.search(r'(\d{4,5})\s*$',srs.group(1))
            crs=CRS.from_epsg(int(e.group(1))) if e else None
        flip=crs is not None and crs.is_geographic
        if flip:o=o[::-1];a=a[::-1];b=b[::-1]
        gt=(o[0]-a[0]/2-b[0]/2,a[0],b[0],o[1]-a[1]/2-b[1]/2,a[1],b[1])
        return gt,crs
    return None,None

# ---------------- leitores ----------------
class TiffReader:
    """GeoTIFF por blocos/faixas: decodifica só os segmentos necessários; usa as visões reduzidas (COG)."""
    def __init__(self,path):
        import tifffile
        self.path=str(path);self.tf=tifffile.TiffFile(self.path);self.lock=threading.Lock();self.cache=collections.OrderedDict()
        s=self.tf.series[0];levels=getattr(s,'levels',None) or [s]
        self.levels=[]
        W0=None
        for lv in levels:
            p=lv.pages[0] if hasattr(lv,'pages') else lv.keyframe
            h,w=p.shape[:2]
            if W0 is None:W0=w
            self.levels.append((p,w,h,W0/w))
        p=self.levels[0][0]
        self.windowed=all(lp.compression in (1,8,32946,32773) for lp,_,_,_ in self.levels)
        self.size=(self.levels[0][1],self.levels[0][2]);self.bands=p.samplesperpixel
    def level_for(self,step):
        best=0
        for k,(_,w,h,f) in enumerate(self.levels):
            if f<=step*1.01:best=k
        return best
    def _segment(self,k,i):
        key=(k,i)
        with self.lock:
            if key in self.cache:self.cache.move_to_end(key);return self.cache[key]
            p=self.levels[k][0];fh=self.tf.filehandle;fh.seek(p.dataoffsets[i]);data=fh.read(p.databytecounts[i])
        seg,idx,shape=p.decode(data,i)
        seg=None if seg is None else np.asarray(seg)
        with self.lock:
            self.cache[key]=(seg,idx,shape)
            while len(self.cache)>96:self.cache.popitem(last=False)
        return seg,idx,shape
    def read(self,k,r0,r1,c0,c1):
        """Janela [r0:r1, c0:c1] do nível k (coordenadas do nível)."""
        p,w,h,_=self.levels[k];r0=max(0,r0);c0=max(0,c0);r1=min(h,r1);c1=min(w,c1)
        if r1<=r0 or c1<=c0:return None
        out=np.zeros((r1-r0,c1-c0,p.samplesperpixel),p.dtype)
        if p.is_tiled:
            tw,th=p.tilewidth,p.tilelength;nx=(w+tw-1)//tw
            for ty in range(r0//th,(r1-1)//th+1):
                for tx in range(c0//tw,(c1-1)//tw+1):
                    seg,_,_=self._segment(k,ty*nx+tx)
                    if seg is None:continue
                    s=seg.reshape(th,tw,-1)
                    ya,yb=max(r0,ty*th),min(r1,(ty+1)*th);xa,xb=max(c0,tx*tw),min(c1,(tx+1)*tw)
                    out[ya-r0:yb-r0,xa-c0:xb-c0]=s[ya-ty*th:yb-ty*th,xa-tx*tw:xb-tx*tw]
        else:
            rps=p.rowsperstrip or h
            for si in range(r0//rps,(r1-1)//rps+1):
                seg,_,_=self._segment(k,si)
                if seg is None:continue
                s=seg.reshape(-1,w,p.samplesperpixel);ya,yb=max(r0,si*rps),min(r1,si*rps+s.shape[0])
                out[ya-r0:yb-r0]=s[ya-si*rps:yb-si*rps,c0:c1]
        return out
    def close(self):
        try:self.tf.close()
        except Exception:pass

class ArrayReader:
    """Imagem carregada inteira (JPG/PNG/JP2/TIF comprimido sem 'imagecodecs'), com pirâmide sob demanda."""
    def __init__(self,path):
        from .local_imagery import read_pixels
        path=Path(path)
        if path.suffix.lower() in ('.jp2','.j2k','.jpx'):
            from PIL import Image
            Image.MAX_IMAGE_PIXELS=MAX_FULL_PIXELS
            with Image.open(path) as im:
                if im.size[0]*im.size[1]>MAX_FULL_PIXELS:raise ValueError('JPEG2000 grande demais para leitura direta: converta para GeoTIFF em blocos (botão Converter, com QGIS instalado).')
                a=np.array(im.convert('RGB'))
        else:
            from PIL import Image
            try:
                with Image.open(path) as im:
                    if im.size[0]*im.size[1]>MAX_FULL_PIXELS:raise ValueError('Imagem grande demais para leitura completa: converta para GeoTIFF em blocos (Deflate) ou COG.')
            except ValueError:raise
            except Exception:pass
            try:a=read_pixels(path)
            except ValueError:
                Image.MAX_IMAGE_PIXELS=MAX_FULL_PIXELS
                with Image.open(path) as im:a=np.array(im.convert('RGBA') if 'A' in im.mode else im.convert('RGB'))
        self.levels=[(a,a.shape[1],a.shape[0],1.)];self.size=(a.shape[1],a.shape[0]);self.windowed=True;self.lock=threading.Lock()
        while min(self.levels[-1][1],self.levels[-1][2])>512:
            b=cv2.pyrDown(self.levels[-1][0]);f=self.size[0]/b.shape[1];self.levels.append((b,b.shape[1],b.shape[0],f))
    def level_for(self,step):
        best=0
        for k,(_,w,h,f) in enumerate(self.levels):
            if f<=step*1.01:best=k
        return best
    def read(self,k,r0,r1,c0,c1):
        a,w,h,_=self.levels[k];r0=max(0,r0);c0=max(0,c0);r1=min(h,r1);c1=min(w,c1)
        return None if r1<=r0 or c1<=c0 else a[r0:r1,c0:c1]
    def close(self):pass

def open_reader(path):
    path=Path(path)
    if path.suffix.lower() in ('.tif','.tiff'):
        try:
            r=TiffReader(path)
            if r.windowed:return r
            r.close()
        except Exception:pass
    return ArrayReader(path)

def to_rgb8(a):
    """Converte a janela para RGB(A) uint8 (bandas extras, 16 bits e cinza)."""
    if a.ndim==2:a=a[:,:,None]
    if a.shape[2]==1:a=np.repeat(a,3,2)
    elif a.shape[2]==2:a=np.dstack([np.repeat(a[:,:,:1],3,2),a[:,:,1:2]])
    elif a.shape[2]>4:a=a[:,:,:3]
    if a.dtype!=np.uint8:
        f=a[:,:,:3].astype(np.float32);lo,hi=np.percentile(f[::4,::4],[1,99]) if f.size else (0,1)
        rgb=np.clip((f-lo)/max(hi-lo,1e-6)*255,0,255).astype(np.uint8)
        a=np.dstack([rgb,(a[:,:,3]>0).astype(np.uint8)*255]) if a.shape[2]==4 else rgb
    return np.ascontiguousarray(a)

def nd_exact(a):
    """1.39: pixels de borda “sem dados”: todas as bandas exatamente no branco máximo (255 em 8 bits) ou no preto (0).
    Um pixel 254 (ou qualquer cor abaixo do branco puro) já é imagem."""
    if a.ndim==2:a=a[:,:,None]
    b=a[:,:,:3] if a.shape[2]>=3 else a[:,:,:1]
    top=np.iinfo(b.dtype).max if np.issubdtype(b.dtype,np.integer) else None
    lo=b.max(2)==0
    return (lo|(b.min(2)==top)) if top is not None else lo

def collar_mask(reader,limit=2048):
    """1.39: máscara reduzida das bordas: só as regiões branco 255/preto 0 ligadas à beira da imagem.
    Branco puro no meio da imagem (telhado, pintura, nuvem) continua imagem. Devolve (máscara uint8, escala)."""
    k=len(reader.levels)-1;_,w,h,f=reader.levels[k]
    st=max(1,int(np.ceil(max(w,h)/limit)));rows=[]
    strip=max(st,(max(1,int(4e7//max(w,1)))//st)*st)   # ~40 Mpx por faixa (TIFF grande sem visões reduzidas)
    for r0 in range(0,h,strip):
        a=reader.read(k,r0,min(h,r0+strip),0,w)
        if a is None:return None
        nd=nd_exact(a)
        if a.ndim==3 and a.shape[2] in (2,4):nd|=a[:,:,-1]==0
        rows.append(nd[::st,::st])
    nd=np.concatenate(rows,0).astype(np.uint8)
    n,lab=cv2.connectedComponents(nd,connectivity=4)
    edge=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]]))
    edge=edge[edge>0]
    m=np.isin(lab,edge).astype(np.uint8)
    m=cv2.dilate(m,np.ones((5,5),np.uint8))   # cobre a mistura da visão reduzida junto à divisa
    return m,(m.shape[1]/(w*f),m.shape[0]/(h*f))

# ---------------- fontes e mosaico ----------------
def _upsample(G,gy,gx,H,W):
    """Interpolação bilinear de uma grade amostrada nas linhas gy e colunas gx (inclusive as bordas)."""
    xs=np.arange(W,dtype=np.float64);ys=np.arange(H,dtype=np.float64)
    A=np.stack([np.interp(xs,gx,G[r]) for r in range(G.shape[0])])          # (len(gy), W)
    k=np.clip(np.searchsorted(gy,ys,side='right')-1,0,len(gy)-2) if len(gy)>1 else np.zeros(H,int)
    if len(gy)==1:return np.repeat(A,H,0).astype(np.float32)
    t=((ys-gy[k])/np.maximum(gy[k+1]-gy[k],1e-9))[:,None]
    return (A[k]*(1-t)+A[k+1]*t).astype(np.float32)

class Source:
    def __init__(self,directory,src):
        from .local_imagery import georef
        base=Path(directory)/'imagem_local';self.path=base/src.image
        if not self.path.exists():raise ValueError(f'Imagem local ausente: {src.image}. Envie-a novamente.')
        world=base/src.world if src.world else None;prj=base/src.prj if src.prj else None
        info=georef(self.path,world,prj,src.crs);gt,crs,size=info['gt'],info['crs'],info['size']
        self.gt=tuple(float(v) for v in gt);self.crs=crs;self.name=src.name or src.image;self._reader=None;self._size=size
        det=self.gt[1]*self.gt[5]-self.gt[2]*self.gt[4]
        if abs(det)<1e-18:raise ValueError('Georreferência degenerada.')
        self.det=det;self.nodata=getattr(src,'nodata','borda');self._collar=False
        # 1.19: ajuste por grips (deslocamento, rotação, escala) no CRS do projeto.
        self.adj=(float(getattr(src,'shift_x',0) or 0),float(getattr(src,'shift_y',0) or 0),float(getattr(src,'rotation_deg',0) or 0),float(getattr(src,'scale',1) or 1))
        self.center=None
    @property
    def adjusted(self):return self.adj!=(0.,0.,0.,1.)
    def raw_corners(self,target):
        w,h=self.size;gt=self.gt
        c=np.array([[gt[0]+gt[1]*x+gt[2]*y,gt[3]+gt[4]*x+gt[5]*y] for x,y in [(0,0),(w,0),(w,h),(0,h),(w/2,0),(w,h/2),(w/2,h),(0,h/2)]])
        tr=Transformer.from_crs(self.crs,target,always_xy=True);x,y=tr.transform(c[:,0],c[:,1])
        return np.column_stack([x,y]).astype(float)
    def set_center(self,target):
        c=self.raw_corners(target);self.center=(float((c[:,0].min()+c[:,0].max())/2),float((c[:,1].min()+c[:,1].max())/2))
    def forward(self,X,Y):
        """Posição ajustada (projeto) de um ponto original (projeto)."""
        dx,dy,rot,k=self.adj;cx,cy=self.center;a=np.radians(rot);ca,sa=np.cos(a)*k,np.sin(a)*k
        u=np.asarray(X,float)-cx;v=np.asarray(Y,float)-cy
        return cx+ca*u-sa*v+dx,cy+sa*u+ca*v+dy
    def inverse(self,X,Y):
        dx,dy,rot,k=self.adj;cx,cy=self.center;a=np.radians(rot);ca,sa=np.cos(a)/k,np.sin(a)/k
        u=np.asarray(X,float)-cx-dx;v=np.asarray(Y,float)-cy-dy
        return cx+ca*u+sa*v,cy-sa*u+ca*v
    def corners(self,target):
        """Quatro cantos da imagem já ajustada, no CRS do projeto (para os grips do editor)."""
        c=self.raw_corners(target)[:4]
        if self.adjusted:x,y=self.forward(c[:,0],c[:,1]);c=np.column_stack([x,y])
        return c
    @property
    def reader(self):
        if self._reader is None:self._reader=open_reader(self.path)
        return self._reader
    @property
    def size(self):
        if self._size is None:self._size=self.reader.size
        return self._size
    def __getstate__(self):
        d=dict(self.__dict__);d['_reader']=None;return d
    @property
    def collar(self):
        if self._collar is False:
            # Calculada uma vez por imagem e guardada ao lado (os processos paralelos reaproveitam).
            st=self.path.stat();cache=self.path.with_name(f'.{self.path.name}.borda_v2_{st.st_size}_{st.st_mtime_ns}.npz')
            try:
                z=np.load(cache);self._collar=(z['m'],tuple(float(v) for v in z['s']));return self._collar
            except Exception:pass
            try:self._collar=collar_mask(self.reader)
            except Exception:self._collar=None
            if self._collar is not None:
                try:
                    tmp=cache.with_name(cache.name+f'.{os.getpid()}.tmp.npz');np.savez_compressed(tmp,m=self._collar[0],s=np.array(self._collar[1]));os.replace(tmp,cache)
                except Exception:pass
        return self._collar
    def to_px(self,X,Y):
        gt=self.gt;dx=np.asarray(X)-gt[0];dy=np.asarray(Y)-gt[3]
        return (gt[5]*dx-gt[2]*dy)/self.det,(-gt[4]*dx+gt[1]*dy)/self.det
    def bounds(self,target):
        c=self.raw_corners(target);x,y=c[:,0],c[:,1]
        if self.adjusted:x,y=self.forward(x,y)
        return float(np.min(x)),float(np.min(y)),float(np.max(x)),float(np.max(y))
    def pixel_m(self,target):
        from .local_imagery import pixel_size_m
        return pixel_size_m({'gt':self.gt,'crs':self.crs,'size':self.size},target)

def adjust(rgb,li):
    b=float(getattr(li,'brightness',0) or 0);c=float(getattr(li,'contrast',0) or 0);s=float(getattr(li,'saturation',0) or 0)
    if not(b or c or s):return rgb
    f=rgb.astype(np.float32)
    if c:f=(f-128)*(1+c)+128
    if b:f=f+b*255
    if s:
        g=f.mean(2,keepdims=True);f=g+(f-g)*(1+s)
    return np.clip(f,0,255).astype(np.uint8)

class LocalMosaic:
    """Mosaico de imagens locais; sample() devolve RGBA no grid pedido (alfa = cobertura, com borda suave)."""
    def __init__(self,directory,settings):
        li=settings.local_imagery;self.li=li;self.target=CRS.from_user_input(settings.crs)
        srcs=[li]+[o for o in getattr(li,'others',[]) or [] if o.enabled]
        self.sources=[Source(directory,s) for s in srcs if s.image];self.li_nodata=getattr(li,'nodata','borda')
        if not self.sources:raise ValueError('Nenhuma imagem local enviada.')
        # 1.19: ordem de prioridade nas sobreposições (lista 'order' = índices; 0 = principal).
        self.index=[i for i,s in enumerate(srcs) if s.image]
        for s in self.sources:s.set_center(self.target)
        self._tr={}
        self.lock=threading.Lock()
        h=hashlib.sha256()
        for s in self.sources:
            st=s.path.stat();h.update(f'{s.path.name}|{st.st_size}|{st.st_mtime_ns}|{s.gt}|{s.crs.to_string()}'.encode())
            if s.adjusted:h.update(repr(s.adj).encode())
        h.update(json.dumps([getattr(li,'brightness',0),getattr(li,'contrast',0),getattr(li,'saturation',0),getattr(li,'nodata','borda'),'borda-alpha-v2']).encode())
        self.key=h.hexdigest()[:16]
        self.bbox=[s.bounds(self.target) for s in self.sources]
    def __getstate__(self):
        d=dict(self.__dict__);d['_tr']={};d['lock']=None;return d
    def __setstate__(self,d):
        self.__dict__.update(d);self.lock=threading.Lock()
    def covers(self,box):
        x0,y0,x1,y1=box
        return any(not(b[2]<x0 or b[0]>x1 or b[3]<y0 or b[1]>y1) for b in self.bbox)
    def pixel_m(self):return min(s.pixel_m(self.target) for s in self.sources)
    def sample(self,X,Y,src_crs=None):
        """X,Y: matrizes (H,W) de coordenadas no CRS 'src_crs' (padrão: o do projeto). RGBA uint8."""
        H,W=X.shape;out=np.zeros((H,W,4),np.uint8);crs=src_crs or self.target
        # Grade grossa para a transformação (precisa em ladrilhos de até ~1 km).
        gy=np.linspace(0,H-1,min(H,17)).astype(int);gx=np.linspace(0,W-1,min(W,17)).astype(int)
        GX=X[np.ix_(gy,gx)];GY=Y[np.ix_(gy,gx)]
        for s in self.sources:
            if out[:,:,3].min()==255:break
            if s.adjusted:
                # 1.19: ponto pedido -> projeto -> posição original (inverso do ajuste) -> CRS da imagem.
                PX,PY=(GX,GY) if crs==self.target else Transformer.from_crs(crs,self.target,always_xy=True).transform(GX,GY)
                PX,PY=s.inverse(PX,PY)
                tr=Transformer.from_crs(self.target,s.crs,always_xy=True)
                sx,sy=tr.transform(PX,PY)
            else:
                tr=Transformer.from_crs(crs,s.crs,always_xy=True)
                sx,sy=tr.transform(GX,GY)
            sx=np.asarray(sx,float);sy=np.asarray(sy,float)
            if not(np.isfinite(sx).all() and np.isfinite(sy).all()):continue
            col,row=s.to_px(sx,sy)
            w,h=s.size
            if col.max()<0 or col.min()>w or row.max()<0 or row.min()>h:continue
            col=_upsample(col,gy,gx,H,W);row=_upsample(row,gy,gx,H,W)
            # Pixels da fonte por pixel de saída (escolhe a visão reduzida adequada).
            step=float(np.hypot(np.mean(np.diff(col,axis=1)) if W>1 else 1.,np.mean(np.diff(row,axis=1)) if W>1 else 0.))
            rd=s.reader;k=rd.level_for(max(step,1e-6));f=rd.levels[k][3]
            c=col/f;r=row/f
            pad=3;c0=int(np.floor(np.nanmin(c)))-pad;c1=int(np.ceil(np.nanmax(c)))+pad;r0=int(np.floor(np.nanmin(r)))-pad;r1=int(np.ceil(np.nanmax(r)))+pad
            win=rd.read(k,r0,r1,c0,c1)
            if win is None:continue
            rc0=max(0,c0);rr0=max(0,r0)
            raw=win;win=to_rgb8(win)
            alpha=win[:,:,3].copy() if win.shape[2]==4 else np.full(win.shape[:2],255,np.uint8)
            mode=self.li_nodata
            if mode=='auto':
                nd=(win[:,:,:3].max(2)<=3)|(win[:,:,:3].min(2)>=253)
                alpha[nd]=0
            elif mode=='borda':
                nd=nd_exact(raw)
                cm=s.collar
                if cm is not None:
                    m,(fx,fy)=cm
                    ci=np.clip(((np.arange(win.shape[1])+rc0+.5)*f*fx).astype(int),0,m.shape[1]-1)
                    ri=np.clip(((np.arange(win.shape[0])+rr0+.5)*f*fy).astype(int),0,m.shape[0]-1)
                    nd&=m[np.ix_(ri,ci)].astype(bool)
                    alpha[nd]=0
                # Sem máscara confiável, preservar imagem e alfa originais.
            win=np.dstack([win[:,:,:3],alpha])
            # Pixel do nível: centro do pixel em (c-0.5).
            mx=(c-rc0-.5).astype(np.float32);my=(r-rr0-.5).astype(np.float32)
            smooth=step/f>1.6
            src=cv2.GaussianBlur(win,(0,0),min(3.,.5*step/f)) if smooth else win
            px=cv2.remap(src,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
            inside=((c>=0)&(c<=rd.levels[k][1])&(r>=0)&(r<=rd.levels[k][2])).astype(np.uint8)*255
            a=np.minimum(px[:,:,3],inside)
            a=cv2.erode(a,np.ones((3,3),np.uint8));a=cv2.GaussianBlur(a,(0,0),1.2)
            need=(255-out[:,:,3]).astype(np.float32)/255;take=a.astype(np.float32)/255*need
            rgb=adjust(px[:,:,:3],self.li)
            out[:,:,:3]=np.clip(out[:,:,:3]*(1-take[:,:,None])+rgb*take[:,:,None],0,255).astype(np.uint8)
            out[:,:,3]=np.clip(out[:,:,3]+take*255,0,255).astype(np.uint8)
        return out
    def sample_box(self,box,W,H):
        x0,y0,x1,y1=box;xs=x0+(np.arange(W)+.5)*(x1-x0)/W;ys=y1-(np.arange(H)+.5)*(y1-y0)/H
        X,Y=np.meshgrid(xs,ys);return self.sample(X,Y)
    def render_base(self,box,n,status=lambda *a:None,chunk=512):
        """Mosaico base n×n (em faixas, sem carregar a imagem inteira quando ela é em blocos)."""
        out=np.zeros((n,n,4),np.uint8);x0,y0,x1,y1=box;span=(y1-y0)/n
        for r in range(0,n,chunk):
            rb=min(n,r+chunk);out[r:rb]=self.sample_box([x0,y1-rb*span,x1,y1-r*span],n,rb-r)
            status(.1+.1*rb/n,'Montando imagem local')
        return out

# ---------------- Web Mercator (editor) ----------------
MERC=20037508.342789244
def web_tile(mosaic,z,x,y,size=256):
    n=2**z;s=2*MERC/n;mx0=-MERC+x*s;my1=MERC-y*s
    xs=mx0+(np.arange(size)+.5)*s/size;ys=my1-(np.arange(size)+.5)*s/size;X,Y=np.meshgrid(xs,ys)
    return mosaic.sample(X,Y,CRS.from_epsg(3857))

# ---------------- GDAL externo (QGIS/OSGeo4W) ----------------
def find_gdal():
    """Procura um gdal_translate instalado (QGIS/OSGeo4W no Windows, ou no PATH). Retorna dict ou None."""
    cands=[]
    if os.environ.get('RODOVIA_GDAL_BIN'):cands.append(Path(os.environ['RODOVIA_GDAL_BIN']))
    w=shutil.which('gdal_translate')
    if w:cands.append(Path(w).parent)
    if os.name=='nt':
        for root in [os.environ.get('ProgramFiles',r'C:\Program Files'),os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)')]:
            if root and Path(root).exists():cands+=sorted(Path(root).glob('QGIS*/bin'),reverse=True)
        cands+=[Path(r'C:\OSGeo4W\bin'),Path(r'C:\OSGeo4W64\bin')]
    for b in cands:
        exe=b/('gdal_translate.exe' if os.name=='nt' else 'gdal_translate')
        if exe.exists():
            env=b/'o4w_env.bat'
            return {'bin':str(b),'translate':str(exe),'env':str(env) if env.exists() else None,'addo':str(b/('gdaladdo.exe' if os.name=='nt' else 'gdaladdo')),'info':str(b/('gdalinfo.exe' if os.name=='nt' else 'gdalinfo'))}
    return None

def _run(g,args,timeout=3600):
    if g.get('env') and os.name=='nt':
        cmd='call "'+g['env']+'" >nul && '+subprocess.list2cmdline(args)
        return subprocess.run(['cmd','/c',cmd],capture_output=True,text=True,timeout=timeout)
    env=dict(os.environ);env['PATH']=g['bin']+os.pathsep+env.get('PATH','')
    return subprocess.run(args,capture_output=True,text=True,timeout=timeout,env=env)

def gdal_formats(g):
    try:r=_run(g,[g['info'],'--formats'],timeout=60);return r.stdout
    except Exception:return ''

def convert(g,src,dst,status=lambda *a:None):
    """Converte qualquer formato que o GDAL leia (ECW, MrSID, JP2...) para GeoTIFF em blocos (Deflate) com visões."""
    dst=Path(dst);tmp=dst.with_suffix('.tmp.tif')
    status(.1,'Convertendo com o GDAL do computador (pode levar minutos)')
    r=_run(g,[g['translate'],'-of','GTiff','-co','TILED=YES','-co','COMPRESS=DEFLATE','-co','BIGTIFF=IF_SAFER','-co','PHOTOMETRIC=RGB','-b','1','-b','2','-b','3',str(src),str(tmp)])
    if r.returncode!=0 or not tmp.exists():
        r2=_run(g,[g['translate'],'-of','GTiff','-co','TILED=YES','-co','COMPRESS=DEFLATE','-co','BIGTIFF=IF_SAFER',str(src),str(tmp)])
        if r2.returncode!=0 or not tmp.exists():raise ValueError('GDAL não converteu o arquivo: '+((r2.stderr or r.stderr) or '').strip()[-400:])
    status(.7,'Gerando visões reduzidas · percentual indisponível nesta etapa')
    if Path(g['addo']).exists():
        _run(g,[g['addo'],'-r','average','--config','COMPRESS_OVERVIEW','DEFLATE',str(tmp),'2','4','8','16','32','64'])
    tmp.replace(dst);return dst
