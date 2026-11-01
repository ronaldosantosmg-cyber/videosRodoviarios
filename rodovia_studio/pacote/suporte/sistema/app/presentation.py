"""Política de apresentação; não modifica geometria, rede ou simulação."""
import numpy as np

ART_COLORS={'cut':'#a85642','fill':'#54803e','terrain':'#6f8c55'}

def guides(settings):
    return settings.style_profile=='tecnico' or getattr(settings,'presentation_guides',False)

def strength(settings):
    return .55 if getattr(settings,'realism_profile','ultra_realista')=='realista' else 1.

def repair_reveal_stations(alpha,stations,transform,tree,chains,length):
    """Detalhe pode conter polígonos que não ocuparam um pixel do mosaico base.

    Só recupera pixels realmente desenhados; não cria áreas nem antecipa a obra.
    """
    missing=(stations==65535)&(alpha>0)
    if not missing.any():return stations
    if not np.isfinite(length) or length<=0:raise ValueError('Comprimento inválido para apresentação progressiva.')
    ys,xs=np.nonzero(missing);result=stations.copy()
    # Blocos limitam memória em vistas grandes; o mesmo eixo governa todas as camadas.
    for first in range(0,len(xs),65536):
        x=xs[first:first+65536];y=ys[first:first+65536]
        xy=np.c_[x,y]@np.asarray(transform)[:,:2].T+np.asarray(transform)[:,2]
        s=np.asarray(chains)[tree.query(xy)[1]]
        result[y,x]=np.clip(s/length*65534,0,65534).astype(np.uint16)
    return result


def source_segments(entity):
    """Apenas arestas reais; não exibe o fechamento virtual de uma hachura aberta."""
    points=np.asarray(entity['points'],float)
    if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():raise ValueError('Contorno DXF inválido.')
    if len(points)<2:return np.empty((0,2,2))
    if entity.get('closed') and np.linalg.norm(points[0]-points[-1])>1e-6:points=np.vstack([points,points[0]])
    from .dxf_trim import runs
    paths=runs(entity)
    if not paths:return np.empty((0,2,2))
    parts=np.concatenate([np.stack([p[:-1],p[1:]],axis=1) for p in paths]);keep=np.linalg.norm(parts[:,1]-parts[:,0],axis=1)>1e-8
    for virtual in entity.get('virtual') or []:
        chord=np.asarray(virtual,float)
        if chord.shape!=(2,2) or not np.isfinite(chord).all():raise ValueError('Fechamento DXF inválido.')
        v=chord[1]-chord[0];length2=float(v@v)
        if length2<1e-10:continue
        t=(parts-chord[0])@v/length2;projection=chord[0]+t[:,:,None]*v
        on=(np.linalg.norm(parts-projection,axis=2).max(1)<.05)&(t.min(1)>-1e-6)&(t.max(1)<1+1e-6)
        keep &= ~on
    return parts[keep]


def contour_runs(entity):
    segments=source_segments(entity);runs=[]
    for a,b in segments:
        if runs and np.linalg.norm(runs[-1][-1]-a)<1e-6:runs[-1].append(b)
        else:runs.append([a,b])
    return [np.asarray(r) for r in runs]


class DXFAdvance:
    """Janela de desenho adiante da frente de material, usando o mesmo eixo da animação."""
    ROLES={'axis','pavement','existing_pavement','shoulder','median','oae','cut','fill','terrain','barrier'}
    def __init__(self,items,tree,chains):
        parts=[source_segments(e) for e in items if e.get('role') in self.ROLES and not e.get('reference_only')]
        self.segments=np.concatenate(parts) if parts else np.empty((0,2,2))
        self.chains=np.asarray(chains)[tree.query(self.segments.reshape(-1,2))[1]].reshape(-1,2) if len(self.segments) else np.empty((0,2))
    def window(self,front,lead):
        if not np.isfinite([front,lead]).all() or lead<0:raise ValueError('Avanço DXF inválido.')
        if lead==0 or not len(self.segments):return np.empty((0,2,2))
        a,b=self.chains.T;delta=b-a
        take=(np.maximum(a,b)>=front)&(np.minimum(a,b)<=front+lead)
        segments=self.segments[take].copy();a=a[take];delta=delta[take]
        moving=np.abs(delta)>1e-8
        lo=np.zeros(len(a));hi=np.ones(len(a))
        u=(front-a[moving])/delta[moving];v=(front+lead-a[moving])/delta[moving]
        lo[moving]=np.clip(np.minimum(u,v),0,1);hi[moving]=np.clip(np.maximum(u,v),0,1)
        start=segments[:,0].copy();vector=segments[:,1]-start
        segments[:,0]=start+vector*lo[:,None];segments[:,1]=start+vector*hi[:,None]
        return segments[np.linalg.norm(segments[:,1]-segments[:,0],axis=1)>1e-8]


def dash_segments(points,dash=6.,gap=4.):
    """Tracejado sobre a polilinha original; não corta curvas/cantos por uma corda."""
    from .dxf_trim import path,at
    if not np.isfinite([dash,gap]).all() or dash<=0 or gap<0:raise ValueError('Tracejado inválido.')
    try:p,ds=path(points)
    except ValueError:return np.empty((0,2,2))
    segments=[]
    for start in np.arange(0,ds[-1],dash+gap):
        end=min(ds[-1],start+dash);inside=p[(ds>start+1e-9)&(ds<end-1e-9)];q=np.vstack([at(p,ds,start),inside,at(p,ds,end)])
        segments.extend(np.stack([q[:-1],q[1:]],axis=1))
    return np.asarray(segments,float).reshape(-1,2,2)


def resample_stroke(points,step=2.):
    """Insere amostras sem remover vértices reais nem ligar entidades independentes."""
    from .dxf_trim import path
    if not np.isfinite(step) or step<=0:raise ValueError('Passo inválido para traço.')
    p,ds=path(points);stations=np.unique(np.r_[ds,np.arange(0,ds[-1],step)])
    return np.column_stack([np.interp(stations,ds,p[:,k]) for k in range(2)])
