"""1.21: tipo de pavimento — flexível (asfalto) ou rígido (placas de concreto com juntas transversais).

As juntas transversais ficam a cada `joint_spacing_m` (padrão 5 m) ao longo do eixo mais próximo, perpendiculares
a ele (radiais nas curvas), ancoradas nas coordenadas do projeto. Funciona igual no mosaico base, nos ladrilhos de
detalhe (0,2/0,1/0,05 m) e nos dois estilos de vídeo:
- técnico: concreto claro com juntas escuras desenhadas (largura de desenho) e pontilhado de concreto;
- artístico: concreto com variação de tom por placa e juntas seladas finas.
"""
import math,unicodedata
import numpy as np
from scipy.spatial import cKDTree

SURF_ROLES=('pavement','existing_pavement','shoulder')
RIGID_WORDS=('RIGID','CONCRET','CCP','PCC','WHITETOP')
FLEX_WORDS=('FLEXIV','ASFALT','CBUQ','CAUQ','TSD','TSS')

def _norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',str(s).upper()) if not unicodedata.combining(c))

def default_material(settings,role):
    if role=='pavement':return getattr(settings,'pavement_material','flexivel')
    if role=='existing_pavement':return getattr(settings,'existing_material','flexivel')
    return getattr(settings,'shoulder_material','flexivel')

def tag_materials(entities,settings):
    """Material de cada superfície: palavra no nome da camada (RIGIDO, CONCRETO, CCP… / FLEXIVEL, ASFALTO, CBUQ…)
    ou o padrão do projeto para o tipo. Marcações do editor podem definir o seu."""
    for e in entities:
        if e.get('role') not in SURF_ROLES or 'material' in e:continue
        n=_norm(e.get('layer',''))
        if any(w in n for w in RIGID_WORDS):e['material']='rigido'
        elif any(w in n for w in FLEX_WORDS):e['material']='flexivel'
        else:e['material']=default_material(settings,e['role'])
    return entities

def any_rigid(entities):return any(e.get('material')=='rigido' for e in entities if e.get('role') in SURF_ROLES)

class JointField:
    """Estaca ao longo do eixo mais próximo (todos os eixos do projeto), para as juntas transversais."""
    def __init__(self,axes,step=1.):
        Q=[];T=[];S=[];A=[]
        for k,a in enumerate(axes):
            p=np.asarray(a['points'] if isinstance(a,dict) else a,float)
            if len(p)<2:continue
            d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
            if d[-1]<2:continue
            s=np.arange(0,d[-1],step);q=np.column_stack([np.interp(s,d,p[:,0]),np.interp(s,d,p[:,1])])
            t=np.gradient(q,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9)
            Q.append(q);T.append(t);S.append(s);A.append(np.full(len(s),k))
        self.ok=bool(Q)
        if self.ok:
            self.Q=np.concatenate(Q);self.T=np.concatenate(T);self.S=np.concatenate(S);self.A=np.concatenate(A);self.tree=cKDTree(self.Q)
    @classmethod
    def from_network(cls,net,step=1.):
        """Centros de cada pista/ramo da rede (direção local correta em trevos, alças e acessos). Nas pistas
        paralelas ao eixo, a estaca é a do eixo do projeto: as juntas das duas pistas ficam alinhadas."""
        f=cls([]);Q=[];T=[];S=[];A=[]
        for k,r in enumerate(getattr(net,'raw_info',[]) or []):
            p=np.asarray(r['points'],float)
            if len(p)<3:continue
            d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
            if d[-1]<4:continue
            ss=np.arange(0,d[-1],step);q=np.column_stack([np.interp(ss,d,p[:,0]),np.interp(ss,d,p[:,1])])
            t=np.gradient(q,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9)
            st=ss
            if r.get('kind') in ('main','marginal'):
                ch=np.asarray(net.chain(q),float);sg=1. if ch[-1]>=ch[0] else -1.
                # Estaca do eixo (resolução de 2 m) suavizada pela distância percorrida: contínua e alinhada.
                st=sg*(ch[0]*sg+ss) if abs(ch[-1]-ch[0])>.65*d[-1] else ss
                if st is not ss:t=t*sg
            Q.append(q);T.append(t);S.append(st);A.append(np.full(len(ss),k))
        f.ok=bool(Q)
        if f.ok:f.Q=np.concatenate(Q);f.T=np.concatenate(T);f.S=np.concatenate(S);f.A=np.concatenate(A);f.tree=cKDTree(f.Q)
        return f
    def station(self,X,Y):
        P=np.column_stack([X,Y]);_,i=self.tree.query(P,workers=-1)
        return self.S[i]+np.einsum('ij,ij->i',P-self.Q[i],self.T[i]),self.A[i]

TECH_RIGID={'pavement':((190,192,186),(60,66,70)),'existing_pavement':((168,182,194),(62,74,86)),'shoulder':((182,178,164),(70,68,60))}
ART_RIGID={'pavement':(176,177,172),'existing_pavement':(160,162,158),'shoulder':(170,169,162)}
TECH_RIGID['oae']=((190,192,186),(60,66,70))
ART_RIGID['oae']=(182,183,178)

def _hash(a,b):
    h=(a.astype(np.int64)*73856093)^(b.astype(np.int64)*19349663);return ((h%1000+1000)%1000)/1000.

def paint_rigid(color,rmask,role,x0,y1,px,field,spacing=5.,tech=False):
    """Pinta as placas de concreto em `color` (H,W,3 uint8/float) onde rmask (bool) — mosaico ou ladrilho.
    x0,y1: canto superior esquerdo (m); px: metros por pixel. Retorna o novo array uint8."""
    out=np.array(color,np.float32,copy=True)
    if out.ndim==1:out=np.broadcast_to(out,rmask.shape+(3,)).copy()
    if not rmask.any():return out.astype(np.uint8)
    if role not in TECH_RIGID or role not in ART_RIGID:return np.clip(out,0,255).astype(np.uint8)
    if not np.isfinite([px,spacing,x0,y1]).all() or px<=0 or spacing<=0:raise ValueError('Escala e espaçamento das juntas devem ser positivos e finitos.')
    base=np.array(TECH_RIGID[role][0] if tech else ART_RIGID[role],np.float32)
    ys,xs=np.nonzero(rmask)
    vals=np.broadcast_to(base,(len(ys),3)).copy()
    if field is not None and field.ok and px<=1.2:
        X=x0+(xs+.5)*px;Y=y1-(ys+.5)*px;s,ax=field.station(X,Y)
        slab=np.floor(s/spacing)
        if not tech:
            # Variação de tom por placa (concreto real não é uniforme) e grão leve.
            tone=1+(_hash(slab,ax)-.5)*.07;vals*=tone[:,None]
        # Distância (m) até a junta transversal mais próxima.
        r=np.mod(s,spacing);dj=np.minimum(r,spacing-r)
        # Técnico: traço de desenho (≥10 cm); artístico: junta selada (~3 cm), com no mínimo meio pixel para aparecer.
        width=max(.10,.9*px) if tech else max(.04,.6*px)
        cover=np.clip((width/2-dj)/max(px,1e-6)+.5,0,1)
        joint=np.array(TECH_RIGID[role][1] if tech else (62,64,64),np.float32);k=.95 if tech else .8
        vals=vals*(1-cover[:,None]*k)+joint*cover[:,None]*k
        if tech and px<=.25:
            # Pontilhado de concreto (símbolo de desenho), ancorado nas coordenadas.
            # Pontos pequenos em posição aleatória (fixa) dentro de células de 0,6 m — como o símbolo de concreto do CAD.
            C=.6;gx=np.floor(X/C);gy=np.floor(Y/C);cx=(gx+.15+.7*_hash(gx,gy))*C;cy=(gy+.15+.7*_hash(gy+7,gx-3))*C
            r=max(.035,.55*px);dd=np.hypot(X-cx,Y-cy);dot=np.clip((r-dd)/max(px,1e-6)+.5,0,1)*(_hash(gx-11,gy+5)<.55)
            vals=vals*(1-dot[:,None]*.5)
    out[ys,xs]=vals
    return np.clip(out,0,255).astype(np.uint8)


# ---------------- 1.21: representação escolhida pelo usuário ----------------
PRESET_FILL={'pavement':(42,48,51),'existing_pavement':(111,130,145),'shoulder':(95,91,81)}
PRESET_HATCH={'pavement':(200,165,90),'existing_pavement':(183,199,212),'shoulder':(214,205,164)}

def _hex(h,default):
    return np.array([int(h[i:i+2],16) for i in (1,3,5)],np.float32) if h else np.array(default,np.float32)

def _lines(X,Y,ang,S,w,px):
    a=math.radians(ang);P=S
    u=(-math.sin(a))*X+math.cos(a)*Y          # distância medida na normal às linhas
    r=np.mod(u,P);d=np.minimum(r,P-r)
    return np.clip((w/2-d)/max(px,1e-6)+.5,0,1)

def paint_style(color,mask,role,x0,y1,px,st,field=None,spacing=5.):
    """Pinta a superfície (mask) com a representação escolhida: sólido, hachura diagonal, cruzada, pontilhado
    ou placas de concreto com juntas. Ancorado nas coordenadas do projeto."""
    out=np.array(color,np.float32,copy=True)
    if out.ndim==1:out=np.broadcast_to(out,mask.shape+(3,)).copy()
    if not mask.any() or st is None or st.pattern=='auto':return np.clip(out,0,255).astype(np.uint8)
    fill=_hex(st.fill,PRESET_FILL[role]);hc=_hex(st.hatch,PRESET_HATCH[role])
    ys,xs=np.nonzero(mask);vals=np.broadcast_to(fill,(len(ys),3)).copy()
    # Coordenadas reduzidas ao período (precisão em float64 com UTM).
    X=x0+(xs+.5)*px;Y=y1-(ys+.5)*px;Xr=X;Yr=Y   # float64: precisão sub-milimétrica em UTM
    w=max(st.line_m,.6*px);cov=None
    if st.pattern=='diagonal':cov=_lines(Xr,Yr,st.angle_deg,st.spacing_m,w,px)
    elif st.pattern=='cruzada':cov=np.maximum(_lines(Xr,Yr,st.angle_deg,st.spacing_m,w,px),_lines(Xr,Yr,st.angle_deg+90,st.spacing_m,w,px))
    elif st.pattern=='pontilhado':
        C=st.spacing_m/2;gx=np.floor(Xr/C);gy=np.floor(Yr/C);cx=(gx+.5)*C;cy=(gy+.5)*C
        r=max(st.line_m,.55*px);cov=np.clip((r-np.hypot(Xr-cx,Yr-cy))/max(px,1e-6)+.5,0,1)
    elif st.pattern=='placas' and field is not None and field.ok:
        s,_=field.station(X,Y);rr=np.mod(s,spacing);d=np.minimum(rr,spacing-rr)
        cov=np.clip((w/2-d)/max(px,1e-6)+.5,0,1)
    if cov is not None:vals=vals*(1-cov[:,None])+hc*cov[:,None]
    out[ys,xs]=vals
    return np.clip(out,0,255).astype(np.uint8)

def chosen(settings,role):
    st=(getattr(settings,'pavement_styles',None) or {}).get(role)
    return st if st is not None and st.pattern!='auto' else None
