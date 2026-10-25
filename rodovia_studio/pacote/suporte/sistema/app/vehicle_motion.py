"""Análise geométrica ilustrativa de frente/traseira. Não é certificação CONTRAN.

Limites são parâmetros cinemáticos conservadores da frota do modelo, não valores
legais. Sentidos, canteiros e movimentos proibidos continuam vindo do projeto.
"""
import math
import numpy as np
from shapely.geometry import LineString
from shapely import contains_xy

# Entre-eixos e esterçamento equivalente; carreta usa um corpo rígido conservador.
PROFILES={'car':(4.5,1.8,2.7,35.),'pickup':(5.3,1.8,3.1,35.),
          'van':(5.4,1.8,3.3,35.),'moto':(2.1,.8,1.4,35.),
          'truck':(12.,3.,6.,32.),'bus':(12.4,3.,6.2,32.),
          'carreta':(18.6,3.,8.,30.)}


def prepare_points(points):
    p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all():
        raise ValueError('Coordenadas ausentes, incompletas ou não finitas.')
    d=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    keep=np.r_[True,np.diff(d)>1e-6]
    if not keep.all():p=p[keep];d=d[keep]
    if len(p)<2 or not math.isfinite(float(d[-1])) or d[-1]<=1e-5:raise ValueError('Comprimento nulo ou inválido.')
    return p,d


def interpolate(p,d,s):
    s=np.asarray(s,dtype=float);q=np.column_stack([np.interp(s,d,p[:,k]) for k in range(2)])
    # Prolonga as tangentes apenas para medir o corpo nas extremidades da rota.
    for mask,at,vec in [(s<0,0,p[1]-p[0]),(s>d[-1],-1,p[-1]-p[-2])]:
        if mask.any():q[mask]=p[at]+(s[mask]-d[at])[:,None]*vec/max(float(np.linalg.norm(vec)),1e-9)
    return q


def axle_geometry(points,vehicle='car',stations=None):
    p,d=prepare_points(points)
    return axle_geometry_prepared(p,d,vehicle,stations)


def axle_geometry_prepared(p,d,vehicle='car',stations=None):
    L,B,wb,_=PROFILES.get(vehicle,PROFILES['car'])
    s=d if stations is None else np.asarray(stations,float)
    center=interpolate(p,d,s);front_axle=interpolate(p,d,s+wb/2);rear_axle=interpolate(p,d,s-wb/2)
    delta=front_axle-rear_axle;heading=delta/np.maximum(np.linalg.norm(delta,axis=1)[:,None],1e-9)
    front=center+heading*L/2;rear=center-heading*L/2
    return {'center':center,'front':front,'rear':rear,'front_axle':front_axle,'rear_axle':rear_axle,'heading':heading,'stations':s,'width':B}


def analyze_motion(points,vehicle='car',allowed=None):
    try:p,d=prepare_points(points)
    except (ValueError,TypeError,OverflowError) as exc:return {'ok':False,'reasons':['geometria_invalida'],'message':str(exc),'max_steering_deg':None}
    L,B,wb,max_steer=PROFILES.get(vehicle,PROFILES['car'])
    # Passo <=0,5 m em percursos usuais; limite explícito protege memória.
    count=max(3,int(math.ceil(float(d[-1])/.5))+1)
    if count>200001:return {'ok':False,'reasons':['rota_excessiva'],'message':'Divida a rota antes da análise cinemática.','max_steering_deg':None}
    s=np.linspace(0,d[-1],count);g=axle_geometry(p,vehicle,s);h=g['heading']
    angle=np.unwrap(np.arctan2(h[:,1],h[:,0]));curvature=np.gradient(angle,s)
    steering=np.degrees(np.arctan(wb*np.abs(curvature)));peak=float(np.max(steering));critical=int(np.argmax(steering));reasons=[]
    line=LineString(p)
    if np.any(np.linalg.norm(h,axis=1)<.5):reasons.append('frente_traseira_degeneradas')
    if not line.is_simple:reasons.append('auto_intersecao')
    # Detecta cúspides que o vetor entre eixos poderia mascarar ao atravessar a dobra.
    v=np.diff(p,axis=0);v/=np.maximum(np.linalg.norm(v,axis=1)[:,None],1e-9)
    turn=np.degrees(np.arccos(np.clip(np.sum(v[:-1]*v[1:],axis=1),-1,1)))
    if len(turn) and np.max(turn)>55:
        reasons.append('mudanca_brusca');critical=int(np.argmin(np.abs(s-d[int(np.argmax(turn))+1])))
    if peak>max_steer+.5:reasons.append('esterco_excessivo')
    # Excursões alternadas de rumo em distância curta, não uma simples curva S longa.
    signs=np.sign(np.where(np.abs(curvature)>.008,curvature,0));runs=[];start=0
    for i in range(1,len(signs)+1):
        if i==len(signs) or signs[i]!=signs[start]:
            if signs[start]:runs.append((s[start],s[i-1],float(angle[i-1]-angle[start])))
            start=i
    for a,b,c in zip(runs,runs[1:],runs[2:]):
        if a[2]*b[2]<0 and b[2]*c[2]<0 and min(abs(a[2]),abs(b[2]),abs(c[2]))>math.radians(15) and c[1]-a[0]<max(20.,4*wb):
            reasons.append('ziguezague');break
    if allowed is not None and not allowed.is_empty:
        normal=np.column_stack([-h[:,1],h[:,0]])
        for x in (-L/2,0.,L/2):
            for y in (-B/2,0.,B/2):
                q=g['center']+h*x+normal*y
                inside=contains_xy(allowed,q[:,0],q[:,1])
                if not inside.all():
                    reasons.append('corpo_fora_da_pista');critical=int(np.flatnonzero(~inside)[0]);break
            if 'corpo_fora_da_pista' in reasons:break
    return {'ok':not reasons,'reasons':list(dict.fromkeys(reasons)),'message':'Trajetória cinemática válida.' if not reasons else 'Trajetória recusada: '+', '.join(dict.fromkeys(reasons))+'.',
            'max_steering_deg':round(peak,3),'vehicle':vehicle,'samples':count,'critical_station_m':round(float(s[critical]),3),'critical_center_xy':g['center'][critical].round(4).tolist(),'front_xy':g['front'][critical].round(4).tolist(),'rear_xy':g['rear'][critical].round(4).tolist()}
