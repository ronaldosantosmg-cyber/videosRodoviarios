"""2.55: (1) transição obrigatória entre seções vizinhas (pista simples ↔ dupla, mudança de nº de faixas/acostamento/canteiro): comprimento mínimo
pela inclinação lateral máxima das faixas; (2) eixo amarelo duplo da pista simples de dois sentidos. Só geometria/pintura; nenhum dado do projeto é alterado."""
import numpy as np
from .road_sections import band_layout,lane_directions

DECLIVE=20.        # 1:20 — cada metro de deslocamento lateral pede 20 m de extensão (valor editável pela rota via taper_m maior)
TOL_EMENDA=1.0

def _offsets(section):
    return {k:v[0] for k,v in band_layout(section).items() if v[2]}

def _shift(la,lb):
    """maior deslocamento lateral que uma faixa sofre ao passar de a para b (faixa que some/aparece converge para a mais externa do mesmo sentido)."""
    shifts=[0.]
    for d in ('f','r'):
        ka={k:o for k,o in la.items() if k[0]==d};kb={k:o for k,o in lb.items() if k[0]==d}
        if not ka or not kb:continue
        outa=ka[max(ka,key=lambda c:c[1])];outb=kb[max(kb,key=lambda c:c[1])]
        for k,o in ka.items():shifts.append(abs(o-kb[k]) if k in kb else abs(o-outb))
        for k,o in kb.items():
            if k not in ka:shifts.append(abs(o-outa))
    return max(shifts)

def _sentidos(section):
    return sorted(lane_directions(section))

def transicoes(route):
    """lista de transições entre seções que se encontram. Cada item: ponto da emenda, janela [start,end] e se o comprimento atual (taper_m) basta."""
    secs=sorted(route.cross_sections,key=lambda s:s.start_m);out=[]
    taper=float(route.taper_m)
    for a,b in zip(secs[:-1],secs[1:]):
        if abs(b.start_m-a.end_m)>TOL_EMENDA:continue
        la,lb=_offsets(a),_offsets(b);shift=_shift(la,lb)
        mudou=(a.type!=b.type) or _sentidos(a)!=_sentidos(b) or len(la)!=len(lb) or shift>1e-6 or abs(a.median_m-b.median_m)>1e-6
        if not mudou:continue
        need=max(taper,DECLIVE*shift)
        tipo=('pista simples → pista dupla' if (a.type,b.type)==('simples','dupla') else 'pista dupla → pista simples' if (a.type,b.type)==('dupla','simples') else 'mudança de faixas/acostamento')
        out.append(dict(at_m=float(a.end_m),start_m=float(max(0,a.end_m-need/2)),end_m=float(b.start_m+need/2),from_section=a.name,to_section=b.name,
                        kind=tipo,shift_m=round(shift,2),required_m=round(need,1),taper_m=taper,sufficient=taper+1e-6>=DECLIVE*shift,
                        sentido_muda=_sentidos(a)!=_sentidos(b)))
    return out

def required_taper(route):
    """comprimento de transição efetivo para a rota: nunca menor que taper_m; sobe para atender à inclinação lateral máxima."""
    t=transicoes(route)
    return max([float(route.taper_m)]+[x['required_m'] for x in t])

def _eixo(route,step=2.):
    from .signage import resample
    P=np.array([[p.x,p.y] for p in route.points],float);Q,s=resample(P,step)
    if len(Q)<3:return None
    T=np.gradient(Q,axis=0);T/=np.maximum(np.linalg.norm(T,axis=1,keepdims=True),1e-9);N=np.column_stack([-T[:,1],T[:,0]])
    return Q,s,N

def eixo_transicao(route):
    """linha (pontos) do eixo de transição de cada emenda: trecho do alinhamento em que as faixas se deslocam; usada para mostrar/validar o desvio."""
    base=_eixo(route)
    if base is None:return []
    Q,s,_=base;res=[]
    for t in transicoes(route):
        sel=(s>=t['start_m'])&(s<=t['end_m'])
        if sel.sum()>=2:res.append(dict(t,points=Q[sel].tolist()))
    return res

def eixo_amarelo(route,step=2.):
    """segmentos (a,b) do eixo amarelo DUPLO das seções de pista simples com dois sentidos e sem canteiro."""
    if not getattr(route,'enabled',True) or not route.cross_sections:return []
    base=_eixo(route,step)
    if base is None:return []
    Q,s,N=base;seg=[]
    for sec in route.cross_sections:
        if sec.type!='simples' or sec.median_m!=0 or len(lane_directions(sec))!=2:continue
        idx=np.flatnonzero((s>=sec.start_m)&(s<=sec.end_m))
        if len(idx)<2:continue
        for off in (-.12,.12):
            P=Q[idx]+N[idx]*off
            seg+=[(P[i],P[i+1]) for i in range(len(P)-1)]
    return seg
