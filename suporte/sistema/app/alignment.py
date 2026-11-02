"""Ajuste DXF × imagem por pares de pontos de controle (ponto no DXF -> mesmo ponto na imagem).

translation: desloca pelo vetor médio (1 par basta).
similarity: translação + rotação + escala uniforme por mínimos quadrados (Umeyama, 2 pares ou mais).
O DXF original não é alterado: a transformação é aplicada em memória na leitura.
"""
import numpy as np

IDENTITY={'a':1.,'b':0.,'tx':0.,'ty':0.}

def fit(pairs,mode='translation'):
    use=[p for p in pairs if (p.get('enabled',True) if isinstance(p,dict) else p.enabled)]
    def xy(p,k):
        q=p[k] if isinstance(p,dict) else getattr(p,k)
        return (q['x'],q['y']) if isinstance(q,dict) else (q.x,q.y)
    src=np.array([xy(p,'dxf') for p in use],float).reshape(-1,2);dst=np.array([xy(p,'image') for p in use],float).reshape(-1,2)
    need=1 if mode=='translation' else 2
    if len(src)<need:raise ValueError(f'Ajuste {"por translação" if mode=="translation" else "por similaridade"} requer pelo menos {need} par(es) ativo(s).')
    if mode=='translation':
        t=(dst-src).mean(0);params={'a':1.,'b':0.,'tx':float(t[0]),'ty':float(t[1])}
    else:
        ms=src.mean(0);md=dst.mean(0);s=(src-ms)@[1,1j];d=(dst-md)@[1,1j]
        den=float(np.sum(np.abs(s)**2))
        if den<1e-6:raise ValueError('Pares de controle coincidentes: afaste os pontos para estimar rotação e escala.')
        z=np.sum(np.conj(s)*d)/den;t=md-apply(ms[None],{'a':z.real,'b':z.imag,'tx':0,'ty':0})[0]
        params={'a':float(z.real),'b':float(z.imag),'tx':float(t[0]),'ty':float(t[1])}
    res=np.linalg.norm(apply(src,params)-dst,axis=1)
    # Resíduo de todos os pares, inclusive desativados, para conferência.
    all_res=[]
    for p in pairs:
        a=np.array([xy(p,'dxf')]);b=np.array([xy(p,'image')]);all_res.append(float(np.linalg.norm(apply(a,params)-b)))
    return {**params,'mode':mode,'scale':float(np.hypot(params['a'],params['b'])),'rotation_deg':float(np.degrees(np.arctan2(params['b'],params['a']))),'residuals_m':all_res,'rms_m':float(np.sqrt(np.mean(res**2))) if len(res) else 0.,'pairs_used':len(src)}

def apply(points,params):
    p=np.asarray(points,float);a=params['a'];b=params['b']
    return np.column_stack([a*p[:,0]-b*p[:,1]+params['tx'],b*p[:,0]+a*p[:,1]+params['ty']])

def inverse(params):
    a=params['a'];b=params['b'];k=a*a+b*b;ia=a/k;ib=-b/k
    tx=-(ia*params['tx']-ib*params['ty']);ty=-(ib*params['tx']+ia*params['ty'])
    return {'a':ia,'b':ib,'tx':tx,'ty':ty}

def active(settings):
    al=settings.dxf_alignment
    if not al.applied or not al.pairs:return None
    return fit(al.pairs,al.mode)
