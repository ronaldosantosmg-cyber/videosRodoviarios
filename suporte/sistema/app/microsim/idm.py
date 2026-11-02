"""IDM (Intelligent Driver Model) contínuo + frenagem de emergência por distância e por TTC."""
import math
from .params import IDMParams


def desired_gap(v,dv,p:IDMParams):
    return p.s0+max(0.,v*p.T+v*dv/(2*math.sqrt(p.a_max*p.b)))


def idm_accel(v,v0,gap,dv,p:IDMParams):
    """a(t)=a_max[1-(v/v0)^δ-(s*/s)²]. `gap` = distância líquida para o líder (None = via livre), `dv`=v-v_líder.
    Líderes virtuais (semáforo fechado, interdição, faixa com sinal fechado) entram como líder parado: v_líder=0."""
    free=1.-(v/v0)**p.delta if v0>1e-6 else -1.
    if gap is None:return max(p.a_max*free,-p.b_max)
    g=max(gap,1e-3);a=p.a_max*(free-(desired_gap(v,dv,p)/g)**2)
    if v>1e-3 and dv>0:                                   # TTC: frenagem cinemática necessária para não encostar
        b_req=dv*dv/(2*max(g-.3,.05))
        if g/dv<p.ttc_crit and b_req>.9*p.b:a=min(a,-min(p.b_max,1.1*b_req))
    if gap<p.s0 and v>1e-3 and dv>=0:a=-p.b_max           # s < s0 e sem abertura: parada forçada instantânea
    return max(a,-p.b_max)
