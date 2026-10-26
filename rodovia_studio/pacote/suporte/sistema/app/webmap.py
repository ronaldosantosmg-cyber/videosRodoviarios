"""Editor sobre imagem web (1.9): ladrilhos Esri World Imagery com cache local e vetores simplificados.

O navegador trabalha em Web Mercator (como os ladrilhos). A conversão entre o CRS do projeto e
Web Mercator usa polinômios de 3º grau ajustados pelo pyproj na área do projeto (erro informado,
tipicamente milimétrico), para que o editor siga gravando tudo no CRS do projeto.
"""
import json,urllib.request,threading
from pathlib import Path
import numpy as np
from pyproj import CRS,Transformer
from shapely.geometry import LineString,Polygon

ESRI='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
ATTRIBUTION='Esri, Maxar, Earthstar Geographics e GIS User Community'
R0=.25  # metros Web Mercator por pixel do "espaço de imagem" do editor
_lock=threading.Lock()

def _terms(u,v):
    return np.column_stack([np.ones_like(u),u,v,u*u,u*v,v*v,u**3,u*u*v,u*v*v,v**3])

def fit(crs,bounds,margin=.35,n=25):
    """Polinômios CRS<->Web Mercator na área (com margem). Retorna coeficientes e erros máximos (m)."""
    (x0,y0),(x1,y1)=bounds;w=max(x1-x0,50);h=max(y1-y0,50);x0-=w*margin;x1+=w*margin;y0-=h*margin;y1+=h*margin
    tr=Transformer.from_crs(CRS.from_user_input(crs),3857,always_xy=True)
    X,Y=np.meshgrid(np.linspace(x0,x1,n),np.linspace(y0,y1,n));X=X.ravel();Y=Y.ravel();MX,MY=tr.transform(X,Y);MX=np.asarray(MX);MY=np.asarray(MY)
    c=[(x0+x1)/2,(y0+y1)/2];s=[(x1-x0)/2,(y1-y0)/2];mc=[MX.mean(),MY.mean()];ms=[np.ptp(MX)/2,np.ptp(MY)/2]
    A=_terms((X-c[0])/s[0],(Y-c[1])/s[1]);B=_terms((MX-mc[0])/ms[0],(MY-mc[1])/ms[1])
    fx=np.linalg.lstsq(A,MX,rcond=None)[0];fy=np.linalg.lstsq(A,MY,rcond=None)[0];ix=np.linalg.lstsq(B,X,rcond=None)[0];iy=np.linalg.lstsq(B,Y,rcond=None)[0]
    # Erro em pontos fora da grade de ajuste.
    rng=np.random.default_rng(0);TX=rng.uniform(x0,x1,400);TY=rng.uniform(y0,y1,400);TMX,TMY=tr.transform(TX,TY)
    at=_terms((TX-c[0])/s[0],(TY-c[1])/s[1]);ef=float(np.max(np.hypot(at@fx-TMX,at@fy-TMY)))
    bt=_terms((np.asarray(TMX)-mc[0])/ms[0],(np.asarray(TMY)-mc[1])/ms[1]);ei=float(np.max(np.hypot(bt@ix-TX,bt@iy-TY)))
    # Fator de escala Mercator/CRS no centro (para converter metros do terreno em pixels).
    d=1.;cx,cy=tr.transform([c[0],c[0]+d],[c[1],c[1]]);k=float(np.hypot(cx[1]-cx[0],cy[1]-cy[0])/d)
    mx0,my1=tr.transform(x0,y1);mx1,my0=tr.transform(x1,y0)
    m0x=float(min(mx0,mx1));m0y=float(max(my0,my1))
    return {'crs':crs,'c':c,'s':s,'mc':mc,'ms':ms,'fx':fx.tolist(),'fy':fy.tolist(),'ix':ix.tolist(),'iy':iy.tolist(),'err_fwd_m':ef,'err_inv_m':ei,
            'k':k,'R0':R0,'m0x':m0x,'m0y':m0y,'img_w':float(abs(mx1-mx0)/R0),'img_h':float(abs(my1-my0)/R0),'mpp_crs':R0/k,'attribution':ATTRIBUTION,
            'bounds_padded':[x0,y0,x1,y1]}

def to_merc(g,x,y):
    a=_terms((np.asarray(x,float)-g['c'][0])/g['s'][0],(np.asarray(y,float)-g['c'][1])/g['s'][1]);return a@np.array(g['fx']),a@np.array(g['fy'])

def to_crs(g,mx,my):
    b=_terms((np.asarray(mx,float)-g['mc'][0])/g['ms'][0],(np.asarray(my,float)-g['mc'][1])/g['ms'][1]);return b@np.array(g['ix']),b@np.array(g['iy'])

# ---------------- 1.19: outras fontes web (Esri Wayback por data, XYZ ou WMS indicados pelo usuário) ----------------
WAYBACK_CONFIG='https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json'
WAYBACK_TILE='https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{release}/{z}/{y}/{x}'
MERC_HALF=20037508.342789244

class WebSource:
    """Fonte de ladrilhos Web Mercator 256 px. 'esri' é a de sempre (mesmo cache e mesma URL)."""
    def __init__(self,kind='esri',url='',release=None,layers='',max_zoom=19,attribution='',label='',version='1.3.0',fmt='image/jpeg'):
        import hashlib
        self.kind=kind;self.url=url;self.release=release;self.layers=layers;self.max_zoom=int(max_zoom);self.label=label
        self.version='1.1.1' if str(version).startswith('1.1') else '1.3.0';self.fmt='image/png' if 'png' in str(fmt).lower() else 'image/jpeg'
        if kind=='esri':self.cache='esri';self.attribution=ATTRIBUTION;self.max_zoom=min(self.max_zoom,19)
        elif kind=='wayback':
            if not release:raise ValueError('Escolha a data (versão) da Esri Wayback.')
            self.cache=f'wayback_{int(release)}';self.attribution='Esri World Imagery Wayback'+(f' ({label})' if label else '')
            if not url:self.url=WAYBACK_TILE.replace('{release}',str(int(release)))
        elif kind in ('xyz','wms'):
            u=(url or '').strip()
            if not u.lower().startswith(('http://','https://')):raise ValueError('Informe o endereço (http/https) do serviço de imagens.')
            if kind=='xyz' and not (all(t in u for t in ('{z}','{x}')) or '{q}' in u):raise ValueError('O endereço XYZ precisa conter {z}, {x} e {y} (ou {-y}), ou {q} (quadkey).')
            extra='' if (self.version,self.fmt)==('1.3.0','image/jpeg') else '|'+self.version+'|'+self.fmt  # mantém o cache das versões anteriores
            self.url=u;self.cache=kind+'_'+hashlib.sha256((u+'|'+layers+extra).encode()).hexdigest()[:12];self.attribution=attribution or 'Fonte indicada pelo usuário'
        else:raise ValueError('Fonte de imagem web desconhecida.')
    @property
    def key(self):return self.cache
    def tile_url(self,z,y,x):
        if self.kind=='esri':return ESRI.format(z=z,y=y,x=x)
        if self.kind=='wms':
            import urllib.parse
            size=2*MERC_HALF/2**z;x0=-MERC_HALF+x*size;y1=MERC_HALF-y*size
            q={'SERVICE':'WMS','REQUEST':'GetMap','VERSION':self.version,'LAYERS':self.layers,'STYLES':'','CRS' if self.version=='1.3.0' else 'SRS':'EPSG:3857','BBOX':f'{x0},{y1-size},{x0+size},{y1}','WIDTH':256,'HEIGHT':256,'FORMAT':self.fmt}
            return self.url+('&' if '?' in self.url else '?')+urllib.parse.urlencode(q)
        u=self.url
        if '{q}' in u:u=u.replace('{q}',quadkey(z,x,y))
        for k,v in (('{z}',z),('{x}',x),('{y}',y),('{-y}',2**z-1-y),('{level}',z),('{row}',y),('{col}',x)):u=u.replace(k,str(v))
        return u.replace('{s}','a')

def quadkey(z,x,y):
    """Chave de ladrilho do Bing (quadkey)."""
    q=''
    for i in range(z,0,-1):
        m=1<<(i-1);q+=str((1 if x&m else 0)+(2 if y&m else 0))
    return q

def web_source(settings):
    """Fonte configurada no projeto (padrão: Esri atual, como antes)."""
    w=getattr(settings,'web_imagery',None)
    if w is None or w.source=='esri':return WebSource('esri')
    return WebSource(w.source,w.url if w.source!='wayback' else '',w.wayback_release,w.wms_layers,w.max_zoom,w.attribution,w.wayback_label,
                     version=getattr(w,'wms_version','1.3.0'),fmt=getattr(w,'wms_format','image/jpeg'))

def wayback_releases(cache_root,fetch=None,timeout=15,max_age_s=86400):
    """Lista de versões (datas) da Esri Wayback, da mais nova para a mais antiga; guarda cópia local."""
    import time,re
    f=Path(cache_root)/'wayback_config.json'
    data=None
    if f.exists() and time.time()-f.stat().st_mtime<max_age_s:data=f.read_bytes()
    if data is None:
        try:
            if fetch:data=fetch(WAYBACK_CONFIG)
            else:
                req=urllib.request.Request(WAYBACK_CONFIG,headers={'User-Agent':'RodoviaStudio/1.19'})
                with urllib.request.urlopen(req,timeout=timeout) as r:data=r.read()
            json.loads(data);f.parent.mkdir(parents=True,exist_ok=True);tmp=f.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(f)
        except Exception:
            if f.exists():data=f.read_bytes()
            else:raise
    cfg=json.loads(data);out=[]
    for k,v in cfg.items():
        try:r=int(k)
        except ValueError:continue
        t=str(v.get('itemTitle','')) if isinstance(v,dict) else '';m=re.search(r'(\d{4}-\d{2}-\d{2})',t)
        out.append({'release':r,'date':m.group(1) if m else '','title':t})
    out.sort(key=lambda d:(d['date'],d['release']),reverse=True);return out

def tile(cache_root,z,y,x,fetch=None,timeout=12,source=None):
    """Ladrilho JPEG/PNG da fonte web com cache em disco (funciona sem internet para áreas já vistas)."""
    src=source or WebSource('esri')
    if not(0<=z<=min(23,max(20,src.max_zoom)) and 0<=x<2**z and 0<=y<2**z):raise ValueError('Ladrilho fora do intervalo.')
    f=Path(cache_root)/src.cache/str(z)/str(y)/f'{x}.jpg'
    if f.exists():return f.read_bytes()
    if fetch:data=fetch(z,y,x)
    else:
        req=urllib.request.Request(src.tile_url(z,y,x),headers={'User-Agent':'RodoviaStudio/1.9'})
        with urllib.request.urlopen(req,timeout=timeout) as r:data=r.read()
    if not data[:3]==b'\xff\xd8\xff' and not data[:8]==b'\x89PNG\r\n\x1a\n':raise ValueError('Resposta de ladrilho inválida.')
    with _lock:
        f.parent.mkdir(parents=True,exist_ok=True);tmp=f.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(f)
    return data

STYLE_ORDER=['water','cut','fill','existing_pavement','pavement','shoulder','median','barrier','oae','edge_line','sign_h','domain','axis','overlay']

def vectors(items,axis,kmz_lines=(),tol=.25):
    """Contornos simplificados por classe (CRS do projeto), para desenhar rápido sobre a imagem web."""
    out={r:[] for r in STYLE_ORDER};count=0;lnames={}
    for e in items:
        role=e['role'];role=role if role in out else 'overlay'
        rings=[e['points']]+list(e.get('holes',[]))
        for r in rings:
            r=np.asarray(r)
            if len(r)<2:continue
            g=LineString(r).simplify(tol,preserve_topology=False)
            p=np.round(np.asarray(g.coords),2)
            if len(p)>=2:
                rec={'p':p.tolist(),'c':bool(e.get('closed')),'l':lnames.setdefault(str(e.get('layer','')),len(lnames))}
                if e.get('frozen'):rec['z']=1
                if role=='overlay' and e.get('style'):rec['color']=e['style']['color']
                out[role].append(rec);count+=len(p)
    out['kmz']=[{'p':np.round(np.asarray(LineString(l).simplify(tol).coords),2).tolist(),'c':False} for l in kmz_lines if len(l)>=2]
    a=np.asarray(axis);ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(a,axis=0),axis=1))]
    ss=np.arange(0,ds[-1],2.);ax=np.column_stack([np.interp(ss,ds,a[:,0]),np.interp(ss,ds,a[:,1])]);ax=np.vstack([ax,a[-1:]])
    return {'layers':out,'axis_main':np.round(ax,3).tolist(),'points':count,'layer_names':list(lnames)}

def write_vectors(directory,items,axis,crs):
    from .geometry import read_kmz
    kmz=Path(directory)/'input.kmz'
    lines=read_kmz(kmz,CRS.from_user_input(crs))[0] if kmz.exists() else []
    data=vectors(items,axis,lines)
    f=Path(directory)/'vectors.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8');tmp.replace(f)
    write_snap(directory,items)
    write_lines(directory,items)
    return data

def write_snap(directory,items):
    """1.24: vértices e pontos médios EXATOS do desenho (sem simplificação), para o snap do editor."""
    V=[];Mid=[]
    for e in items:
        if e.get('frozen'):continue   # 1.26: camada congelada não atrai o snap
        for r in [e['points']]+list(e.get('holes',[])):
            r=np.asarray(r,float)
            if len(r)<1:continue
            V.append(r)
            if len(r)>=2:Mid.append((r[1:]+r[:-1])/2)
    V=np.concatenate(V) if V else np.zeros((0,2));Mid=np.concatenate(Mid) if Mid else np.zeros((0,2))
    if len(V):V=np.unique(np.round(V,4),axis=0)
    if len(Mid):Mid=np.unique(np.round(Mid,4),axis=0)
    f=Path(directory)/'snap.npz';tmp=Path(directory)/'snap_tmp.npz'
    np.savez_compressed(tmp,v=V,m=Mid);tmp.replace(f)

_snap_cache={}
def snap_points(directory,x0,y0,x1,y1,limit=8000):
    f=Path(directory)/'snap.npz'
    if not f.exists():return {'v':[],'m':[],'truncated':False,'available':False}
    key=(str(f),f.stat().st_mtime_ns);d=_snap_cache.get(key)
    if d is None:
        z=np.load(f);d=(z['v'],z['m']);_snap_cache.clear();_snap_cache[key]=d
    out={}
    trunc=False
    for k,A in zip(('v','m'),d):
        sel=A[(A[:,0]>=x0)&(A[:,0]<=x1)&(A[:,1]>=y0)&(A[:,1]<=y1)] if len(A) else A
        if len(sel)>limit:sel=sel[:limit];trunc=True
        out[k]=np.round(sel,4).tolist()
    out['truncated']=trunc;out['available']=True
    return out

# ---------------- 1.26: linhas exatas do DXF para selecionar o alinhamento ----------------
def write_lines(directory,items):
    xy=[];off=[0];lay=[];names={};closed=[];roles=[];curves=[]
    for e in items:
        if e.get('frozen') or e.get('role') in ('sign_v',):continue
        r=np.asarray(e['points'],float)
        if len(r)<2:continue
        xy.append(r);off.append(off[-1]+len(r));lay.append(names.setdefault(str(e.get('layer','')),len(names)));closed.append(bool(e.get('closed')));roles.append(str(e.get('role','')))
        curves.append(json.dumps(e.get('cad_curve'),allow_nan=False))
    f=Path(directory)/'linhas.npz';tmp=Path(directory)/'linhas_tmp.npz'
    np.savez_compressed(tmp,xy=np.concatenate(xy) if xy else np.zeros((0,2)),off=np.asarray(off,np.int64),lay=np.asarray(lay,np.int32),
                        closed=np.asarray(closed,bool),names=np.asarray(list(names) or [''],dtype=str),roles=np.asarray(roles or [''],dtype=str),curves=np.asarray(curves,dtype=str));tmp.replace(f)

_lines_cache={}
def _lines(directory):
    f=Path(directory)/'linhas.npz'
    if not f.exists():raise FileNotFoundError('Analise os arquivos de novo para selecionar linhas do desenho (1.26).')
    key=(str(f),f.stat().st_mtime_ns);d=_lines_cache.get(key)
    if d is None:
        z=np.load(f);xy=z['xy'];off=z['off']
        lines=[xy[off[i]:off[i+1]] for i in range(len(off)-1)]
        box=np.array([[l[:,0].min(),l[:,1].min(),l[:,0].max(),l[:,1].max()] for l in lines]) if lines else np.zeros((0,4))
        d={'lines':lines,'box':box,'lay':z['lay'],'closed':z['closed'],'names':[str(v) for v in z['names']],'roles':[str(v) for v in z['roles']] if 'roles' in z.files else ['']*len(lines)}
        _lines_cache.clear();_lines_cache[key]=d
        d['curves']=[json.loads(str(c)) for c in z['curves']] if 'curves' in z.files else [None]*len(lines)
        from .cad_curves import bounds
        for i,c in enumerate(d['curves']):
            if c:d['box'][i]=bounds(c)
    return d

def _dist(line,p):
    a=line[:-1];b=line[1:];ab=b-a;L=(ab**2).sum(1);t=np.clip(((p-a)*ab).sum(1)/np.where(L>0,L,1),0,1)
    q=a+ab*t[:,None];dd=np.hypot(*(q-p).T);k=int(dd.argmin());return float(dd[k]),k,float(t[k])

def pick_line(directory,x,y,tol=5.):
    """Linha (polilinha completa, vértices exatos) mais próxima do ponto clicado."""
    d=_lines(directory);p=np.array([x,y],float);B=d['box']
    if not len(B):return None
    cand=np.flatnonzero((B[:,0]-tol<=x)&(B[:,2]+tol>=x)&(B[:,1]-tol<=y)&(B[:,3]+tol>=y))
    best=None
    from .cad_curves import closest,length as curve_length
    for i in cand:
        dist,_,_=_dist(d['lines'][i],p)
        curve=d['curves'][i]
        if curve:dist=closest(curve,p)['distance_m']
        if dist<=tol and (best is None or dist<best[0]):best=(dist,i)
    if best is None:return None
    i=best[1];L=d['lines'][i];pts=L.tolist()
    if d['closed'][i] and np.hypot(*(L[0]-L[-1]))>1e-6:pts.append(pts[0])
    result={'index':int(i),'points':pts,'layer':d['names'][int(d['lay'][i])],'distance_m':float(best[0]),'length_m':float(np.hypot(*np.diff(np.asarray(pts),axis=0).T).sum()),'closed':bool(d['closed'][i])}
    if d['curves'][i]:
        result.update(cad_curve=d['curves'][i],curve_projection=closest(d['curves'][i],p),length_m=curve_length(d['curves'][i]))
    return result

def chain_lines(directory,x,y,tol=5.,join=.05,max_parts=500):
    """Seleção contínua: a linha clicada e as que continuam dela (pontas coincidentes, sem bifurcação), na ordem."""
    first=pick_line(directory,x,y,tol)
    if first is None:return None
    d=_lines(directory);lines=d['lines'];used={first['index']}
    ends=np.array([[l[0][0],l[0][1],l[-1][0],l[-1][1]] for l in lines])
    path=[np.asarray(first['points'])];parts=[first['index']]
    def extend(at_end):
        nonlocal path
        while len(parts)<max_parts:
            tip=(path[-1][-1] if at_end else path[0][0])
            m0=np.hypot(ends[:,0]-tip[0],ends[:,1]-tip[1])<=join;m1=np.hypot(ends[:,2]-tip[0],ends[:,3]-tip[1])<=join
            nxt=[i for i in np.flatnonzero(m0|m1) if i not in used and not d['closed'][i]]
            if len(nxt)!=1:return   # fim ou bifurcação: para (o usuário escolhe o próximo trecho clicando)
            i=nxt[0];L=lines[i];used.add(i);parts.append(int(i))
            if at_end:path.append((L if m0[i] else L[::-1])[1:])
            else:path.insert(0,(L[::-1] if m0[i] else L)[:-1])
    if not first['closed']:extend(True);extend(False)
    P=np.concatenate(path)
    return {'points':P.tolist(),'parts':len(parts),'layers':sorted({d['names'][int(d['lay'][i])] for i in parts}),'length_m':round(float(np.hypot(*np.diff(P,axis=0).T).sum()),3)}

def pick_area(directory,x,y):
    """1.27: menor área fechada do desenho (vértices exatos) que contém o ponto, com camada e tipo."""
    from shapely import contains_xy
    from shapely.geometry import Polygon
    d=_lines(directory);B=d['box']
    if not len(B):return None
    cand=np.flatnonzero((B[:,0]<=x)&(B[:,2]>=x)&(B[:,1]<=y)&(B[:,3]>=y)&d['closed'])
    best=None
    for i in cand:
        L=d['lines'][i]
        if len(L)<3:continue
        try:g=Polygon(L)
        except Exception:continue
        if not g.is_valid:g=g.buffer(0)
        if g.is_empty or not contains_xy(g,x,y):continue
        a=float(g.area)
        if best is None or a<best[0]:best=(a,i)
    if best is None:return None
    a,i=best;L=d['lines'][i];P=L[:-1] if len(L)>3 and np.hypot(*(L[0]-L[-1]))<1e-6 else L
    if len(P)>5000:P=np.asarray(Polygon(P).simplify(.02).exterior.coords)[:-1]
    return {'points':np.round(P,4).tolist(),'layer':d['names'][int(d['lay'][i])],'role':d['roles'][i] if i<len(d['roles']) else '','area_m2':round(a,2),'perimeter_m':round(float(np.hypot(*np.diff(np.vstack([P,P[:1]]),axis=0).T).sum()),2)}
