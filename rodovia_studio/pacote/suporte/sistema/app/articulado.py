"""2.46: intelligência de veículo articulado (carreta) vinda do simulador de demonstração — só cálculo, não altera desenho nem projeto.
O semirreboque obedece θt' = sin(θ−θt)/Lt ao longo do percurso (engate no eixo traseiro do cavalo): na curva, o eixo do semirreboque corta para
dentro da trajetória do cavalo (off-tracking). Resultado: off-tracking máximo, largura varrida e trechos em que o conjunto sai da pista."""
import math
import numpy as np
from shapely.geometry import LineString,Polygon

# Lt = engate → eixo do semirreboque; ov = balanço traseiro; W = largura. Dimensões de referência (CONTRAN: 18,6 m articulado); conferir com o contrato.
CONJUNTOS={'carreta':dict(Lt=12.2,ov=1.3,W=2.6),'SR':dict(Lt=10.5,ov=1.2,W=2.6)}

def rastro(points,conjunto='carreta',passo=.25,allowed=None):
    from .vehicle_motion import prepare_points,interpolate
    cfg=CONJUNTOS.get(conjunto) if isinstance(conjunto,str) else conjunto
    if not cfg:return {'disponivel':False,'motivo':'conjunto desconhecido'}
    p,d=prepare_points(points);pre=cfg['Lt']+cfg['ov']+2.;s=np.arange(-pre,d[-1]+1e-9,passo)   # prolonga a tangente antes da partida: o reboque já vem alinhado
    if d[-1]<passo*3:return {'disponivel':False,'motivo':'percurso curto'}
    q=interpolate(p,d,s);t=np.gradient(q,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9);th=np.unwrap(np.arctan2(t[:,1],t[:,0]))
    Lt=cfg['Lt'];tt=np.empty_like(th);tt[0]=th[0]
    for i in range(1,len(s)):                                  # Heun em s
        ds=s[i]-s[i-1];k1=math.sin(th[i-1]-tt[i-1])/Lt;pred=tt[i-1]+k1*ds;k2=math.sin(th[i]-pred)/Lt;tt[i]=tt[i-1]+(k1+k2)/2*ds
    eixo=q-np.column_stack([np.cos(tt),np.sin(tt)])*Lt          # eixo do semirreboque
    linha=LineString(q);pos=s>=0;off=np.array([linha.distance(__import__('shapely.geometry',fromlist=['Point']).Point(x,y)) for x,y in eixo])
    quina=eixo-np.column_stack([np.cos(tt),np.sin(tt)])*cfg['ov']
    fora=[]
    if allowed is not None and not allowed.is_empty:
        from shapely import contains_xy
        n=np.column_stack([-np.sin(tt),np.cos(tt)])
        ok=np.ones(len(s),bool)
        for x in (-cfg['W']/2,cfg['W']/2):
            for pt in (eixo,quina):
                z=pt+n*x;ok&=contains_xy(allowed,z[:,0],z[:,1])
        idx=np.flatnonzero((~ok)&pos)
        if len(idx):fora=[round(float(s[idx[0]]),1),round(float(s[idx[-1]]),1)]
    off=np.where(pos,off,0.);i=int(np.argmax(off));art=np.degrees(np.abs(np.unwrap(th)-np.unwrap(tt)))
    return {'disponivel':True,'conjunto':conjunto if isinstance(conjunto,str) else 'personalizado','offtracking_max_m':round(float(off[i]),2),'estaca_critica_m':round(float(s[i]),1),
            'largura_varrida_m':round(float(cfg['W']+off[i]),2),'angulo_articulacao_max_graus':round(float(art.max()),1),'fora_da_pista_m':fora,
            'ok':not fora,'aviso':None if not fora else f'Semirreboque sai da pista entre {fora[0]} m e {fora[1]} m (off-tracking {off[i]:.2f} m).'}
