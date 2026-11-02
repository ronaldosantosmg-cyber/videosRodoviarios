"""Fumaça limitada e reprodutível no relógio da cena; nunca emitida para a frente."""
import math
import numpy as np
MAX_SMOKE=240
PUFFS=10

def seed(identity):return sum((i+1)*ord(c) for i,c in enumerate(str(identity)))%65536

def parameters(identity,t,index,speed):
    if not all(isinstance(v,(int,float,np.integer,np.floating)) and math.isfinite(float(v)) for v in (identity,t,index,speed)) or not 0<=identity<=65535 or not 0<=index<PUFFS or not 0<=speed<=200:raise ValueError('Parâmetros da fumaça inválidos.')
    phase=(float(t)*.32+index*.61803398875)%1.;age=phase*4
    random=math.sin((int(identity)+index*17)*12.9898)*43758.5453
    return dict(back=.5+age*(1.5+max(0.,float(speed))),side=(2*(random-math.floor(random))-1)*age*.65,
                height=3.4+age*1.1,radius=.35+age*.32,alpha=.28*(1-phase))

def particles(parts,t,enabled=True):
    if not enabled:return []
    try:t=float(t)
    except (TypeError,ValueError,OverflowError):return []
    if not math.isfinite(t):return []
    result=[]
    for part in parts:
        if not part.get('locomotive'):continue
        h=np.asarray(part['heading'],float);norm=float(np.linalg.norm(h))
        if norm<1e-9 or not np.isfinite(h).all():continue
        center=np.asarray(part.get('p',[]),float)
        if center.shape!=(2,) or not np.isfinite(center).all():continue
        h=h/norm;normal=np.array([-h[1],h[0]])
        for j in range(PUFFS):
            if len(result)>=MAX_SMOKE:return result
            p=parameters(seed(part['id']),t,j,part.get('speed_mps',0))
            result.append(dict(p=center-h*p['back']+normal*p['side'],**p))
    return result
