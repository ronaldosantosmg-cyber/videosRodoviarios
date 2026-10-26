"""Curvas paramétricas em metros, independentes da tesselação de apresentação.

Arcos circulares são analíticos; NURBS usam avaliação racional e integração
numérica com tolerância explícita. Não é um substituto de um kernel CAD 3D.
"""
import math
import numpy as np
from scipy.interpolate import BSpline
from scipy.integrate import quad
from scipy.optimize import minimize_scalar


def transformed(curve,params):
    from .alignment import apply
    import copy
    c=copy.deepcopy(curve)
    if c['kind']=='composite':c['parts']=[transformed(p,params) for p in c['parts']]
    elif c['kind']=='line':
        c['start_point'],c['end_point']=apply([c['start_point'],c['end_point']],params).tolist()
    elif c['kind']=='arc':
        c['center']=apply([c['center']],params)[0].tolist()
        c['radius']*=math.hypot(params['a'],params['b']);c['start']+=math.atan2(params['b'],params['a'])
    else:c['control_points']=apply(c['control_points'],params).tolist()
    return c


def bounds(curve):
    if curve['kind']=='arc':
        c=np.asarray(curve['center']);r=curve['radius'];return np.r_[c-r,c+r]
    if curve['kind']=='composite':
        boxes=np.asarray([bounds(p) for p in curve['parts']]);return np.r_[boxes[:,:2].min(0),boxes[:,2:].max(0)]
    p=np.asarray([curve['start_point'],curve['end_point']] if curve['kind']=='line' else curve['control_points'])
    return np.r_[p.min(0),p.max(0)]


def from_entity(entity,units=1.):
    if not math.isfinite(units) or units<=0:raise ValueError('Unidade CAD inválida.')
    kind=entity.dxftype()
    if kind=='LINE':
        a,b=entity.dxf.start,entity.dxf.end
        return dict(kind='line',start_point=[a.x*units,a.y*units],end_point=[b.x*units,b.y*units])
    if kind in ('LWPOLYLINE','POLYLINE') and entity.has_arc:
        parts=[from_entity(part,units) for part in entity.virtual_entities()]
        if not parts or any(part is None for part in parts):return None
        if kind=='LWPOLYLINE':
            first=next(iter(entity.get_points('xy')));first=entity.ocs().to_wcs((first[0],first[1],entity.dxf.elevation))
        else:first=entity.ocs().to_wcs(entity.vertices[0].dxf.location)
        cursor=np.array([first.x,first.y])*units
        for part in parts:
            if part['kind']=='arc' and np.linalg.norm(evaluate(part,1)-cursor)<np.linalg.norm(evaluate(part,0)-cursor):
                part['start']+=part['sweep'];part['sweep']=-part['sweep']
            cursor=evaluate(part,1)
        return dict(kind='composite',parts=parts)
    if kind in ('ARC','CIRCLE'):
        # Circunferência oblíqua não pode ser descrita como círculo em planta.
        normal=entity.dxf.extrusion
        if abs(normal.x)>1e-10 or abs(normal.y)>1e-10 or normal.z<0:return None
        start=math.radians(entity.dxf.start_angle) if kind=='ARC' else 0.
        sweep=(math.radians(entity.dxf.end_angle)-start)%(2*math.pi) if kind=='ARC' else 2*math.pi
        center=entity.dxf.center
        return dict(kind='arc',center=[center.x*units,center.y*units],radius=entity.dxf.radius*units,start=start,sweep=sweep)
    if kind=='SPLINE':
        curve=entity.construction_tool()
        return dict(kind='nurbs',degree=curve.degree,control_points=[[p.x*units,p.y*units] for p in curve.control_points],
                    knots=list(curve.knots()),weights=list(curve.weights()) or [1.]*curve.count)
    return None


def _spline(curve):
    p=np.asarray(curve['control_points'],float);w=np.asarray(curve['weights'],float)
    knots=np.asarray(curve['knots'],float);degree=curve['degree']
    if p.ndim!=2 or p.shape[1]!=2 or len(p)>10000 or not 1<=degree<=10 or len(w)!=len(p) or len(knots)!=len(p)+degree+1:
        raise ValueError('NURBS fora dos limites.')
    if not np.isfinite(p).all() or not np.isfinite(w).all() or not np.isfinite(knots).all() or np.any(w<=0) or np.any(np.diff(knots)<0):
        raise ValueError('Coordenadas, pesos ou nós inválidos.')
    a,b=knots[degree],knots[-degree-1]
    if b<=a:raise ValueError('Domínio nulo da curva.')
    origin=p[0].copy()
    spline=BSpline(knots,np.column_stack([(p-origin)*w[:,None],w]),degree,extrapolate=False)
    return spline,float(a),float(b),origin


def evaluate(curve,t):
    t=float(t)
    if not math.isfinite(t) or not 0<=t<=1:raise ValueError('Parâmetro da curva deve estar entre zero e um.')
    if curve['kind']=='line':
        a=np.asarray(curve['start_point'],float);b=np.asarray(curve['end_point'],float)
        if a.shape!=(2,) or b.shape!=(2,) or not np.isfinite([a,b]).all():raise ValueError('Linha inválida.')
        return a+(b-a)*t
    if curve['kind']=='composite':
        parts=curve['parts'];lengths=np.asarray([length(p) for p in parts]);total=lengths.sum()
        if not np.isfinite(total) or total<=0:raise ValueError('Polilinha de comprimento nulo.')
        station=t*total;ends=np.cumsum(lengths);index=min(len(parts)-1,int(np.searchsorted(ends,station,side='right')))
        return evaluate(parts[index],float(np.clip((station-(ends[index]-lengths[index]))/max(lengths[index],1e-15),0,1)))
    if curve['kind']=='arc':
        center=np.asarray(curve['center'],float);r=float(curve['radius']);a=float(curve['start'])+t*float(curve['sweep'])
        if not np.isfinite(center).all() or not np.isfinite([r,a,curve['sweep']]).all() or r<=0:raise ValueError('Arco inválido.')
        return center+r*np.array([math.cos(a),math.sin(a)])
    spline,a,b,origin=_spline(curve);v=spline(a+t*(b-a))
    return origin+v[:2]/v[2]


def length(curve):
    if curve['kind']=='line':return float(np.linalg.norm(evaluate(curve,1)-evaluate(curve,0)))
    if curve['kind']=='composite':return sum(length(p) for p in curve['parts'])
    if curve['kind']=='arc':
        evaluate(curve,0);return abs(float(curve['radius'])*float(curve['sweep']))
    spline,a,b,_=_spline(curve);derivative=spline.derivative()
    def speed(u):
        h=spline(u);dh=derivative(u)
        return float(np.linalg.norm((dh[:2]*h[2]-h[:2]*dh[2])/h[2]**2))
    # Quebras nos nós são tratadas como intervalos separados.
    knots=np.unique(spline.t[(spline.t>=a)&(spline.t<=b)])
    return sum(quad(speed,x,y,epsabs=1e-7,epsrel=1e-10,limit=100)[0] for x,y in zip(knots,knots[1:]))


def closest(curve,point):
    p=np.asarray(point,float)
    if p.shape!=(2,) or not np.isfinite(p).all():raise ValueError('Ponto de consulta inválido.')
    if curve['kind']=='line':
        a=evaluate(curve,0);ab=evaluate(curve,1)-a;den=float(ab@ab)
        candidates=[float(np.clip((p-a)@ab/max(den,1e-30),0,1))]
    elif curve['kind']=='composite':
        best=None;cursor=0.;total=length(curve)
        if total<=0:raise ValueError('Polilinha de comprimento nulo.')
        for i,part in enumerate(curve['parts']):
            match=closest(part,p);part_length=length(part)
            if best is None or match['distance_m']<best['distance_m']:
                best={**match,'part':i,'parameter':(cursor+part_length*match['parameter'])/total}
            cursor+=part_length
        return best
    elif curve['kind']=='arc':
        c=np.asarray(curve['center']);angle=math.atan2(*(p-c)[::-1]);sweep=float(curve['sweep'])
        if not np.isfinite(sweep) or abs(sweep)<1e-15:raise ValueError('Amplitude nula do arco.')
        delta=(angle-float(curve['start'])) if sweep>0 else (float(curve['start'])-angle)
        t=(delta%(2*math.pi))/abs(sweep)
        candidates=[0.,1.]+([t] if t<=1 else [])
    else:
        spline,a,b,origin=_spline(curve)
        # Busca em todos os vãos, incluindo mínimos nos próprios nós.
        grid=np.unique(np.r_[np.linspace(0,1,65),(spline.t[(spline.t>=a)&(spline.t<=b)]-a)/(b-a)])
        if len(grid)>2048:raise ValueError('Curva excessiva para seleção interativa.')
        def objective(t):
            v=spline(a+t*(b-a));return float(np.sum((origin+v[:2]/v[2]-p)**2))
        candidates=list(grid)
        for x,y in zip(grid,grid[1:]):
            r=minimize_scalar(objective,bounds=(x,y),method='bounded',options={'xatol':1e-12})
            candidates.append(float(r.x))
    t=min(candidates,key=lambda t:np.linalg.norm(evaluate(curve,t)-p));q=evaluate(curve,t)
    return dict(point=q.tolist(),parameter=float(t),distance_m=float(np.linalg.norm(q-p)),method='curva_parametrica')
