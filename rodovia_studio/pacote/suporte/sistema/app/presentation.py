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
