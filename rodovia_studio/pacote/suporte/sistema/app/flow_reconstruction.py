"""Reconstrução limitada de uma derivação; não remove restrições nem altera o CAD."""
import numpy as np
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString
from .vehicle_motion import prepare_points, analyze_motion, interpolate


def reconstruct(points, allowed, minimum=50., max_deviation=8.):
    report={'status':'blocked','strategy':'reconstrucao_continua','attempts':0}
    try:
        p,d=prepare_points(points)
        minimum=float(minimum);max_deviation=float(max_deviation)
        if not np.isfinite([minimum,max_deviation]).all() or minimum<=0 or not 0<max_deviation<=8:
            raise ValueError('Limites de reconstrução inválidos.')
    except (ValueError,TypeError,OverflowError):
        report['reason']='geometria_ou_limite_invalido';return None,report
    if allowed is None or allowed.is_empty or d[-1]<minimum or d[-1]>5000 or len(p)>20000:
        report['reason']='superficie_ausente_ou_limite_excedido';return None,report
    original=LineString(p)
    if not original.is_simple:
        report['reason']='auto_intersecao_ambigua';return None,report
    if analyze_motion(p,allowed=allowed)['ok']:
        report.update(status='unchanged',max_deviation_m=0.);return p.copy(),report
    # Não procura desvios ao redor de barreiras ou entre componentes desconectados.
    if not allowed.covers(original):
        report['reason']='eixo_fora_da_superficie_ou_barreira';return None,report
    s=np.linspace(0.,d[-1],int(np.ceil(d[-1]/.5))+1)
    base=interpolate(p,d,s);step=s[1]-s[0]
    # Extensão linear evita mover as pontas ou mudar suas tangentes ao filtrar.
    pad=int(np.ceil(64/step));left=base[0]+np.arange(-pad,0)[:,None]*(base[1]-base[0])
    right=base[-1]+np.arange(1,pad+1)[:,None]*(base[-1]-base[-2])
    extended=np.vstack([left,base,right])
    for sigma_m in (1.,2.,4.,6.,8.,12.,16.):
        report['attempts']+=1
        candidate=gaussian_filter1d(extended,sigma_m/step,axis=0,mode='nearest')[pad:pad+len(base)].copy()
        # Correção afim mantém as extremidades exatamente nas coordenadas recebidas.
        u=(s/d[-1])[:,None]
        candidate+=(1-u)*(p[0]-candidate[0])+u*(p[-1]-candidate[-1])
        candidate[0]=p[0];candidate[-1]=p[-1]
        line=LineString(candidate);deviation=line.hausdorff_distance(original)
        if deviation>max_deviation or not line.is_simple or line.length<minimum:continue
        # Conferência contínua da largura, além das amostras do corpo do veículo.
        if not allowed.covers(line.buffer(.9,cap_style='flat')):continue
        # Progressão monotônica impede inversões, atalhos e laços.
        from shapely import line_locate_point,points as make_points
        progress=line_locate_point(original,make_points(candidate))
        if np.any(np.diff(progress)<-.01):continue
        audit=analyze_motion(candidate,allowed=allowed)
        if not audit['ok']:continue
        report.update(status='reconstructed',max_deviation_m=float(deviation),length_m=line.length,
                      endpoints_preserved=True,audit=audit)
        return candidate,report
    report['reason']='nenhuma_ligacao_continua_revalidada';return None,report
