"""Orientação explícita dos alinhamentos; não executa outro motor de tráfego."""
import math
import numpy as np
from shapely.geometry import LinearRing

ROLES={'automatico':'Automático existente','principal':'Principal','acesso':'Acesso','retorno':'Retorno','dispositivo':'Dispositivo','rotatoria':'Rotatória'}


def direction(route):
    """+1 crescente, -1 decrescente, 0 mantém as faixas da seção existente."""
    a,b=route.flow_start,route.flow_end
    forward=a=='entrada' or b in ('saida','fim')
    reverse=b=='entrada' or a in ('saida','fim')
    if forward and reverse:raise ValueError('Nós contraditórios: indique entrada e saída em extremidades opostas do percurso.')
    node=1 if forward else -1 if reverse else 0
    explicit={'automatico':0,'crescente':1,'decrescente':-1,'ambos':0}[route.flow_direction]
    if node and (route.flow_direction=='ambos' or explicit and explicit!=node):raise ValueError('O sentido selecionado contradiz os nós de entrada e saída.')
    result=node or explicit
    if route.flow_role!='rotatoria' and route.roundabout_rotation!='cadastro':raise ValueError('O giro só se aplica a eixos classificados como rotatória.')
    if route.flow_role=='rotatoria' and route.roundabout_rotation!='cadastro':
        p=np.array([[v.x,v.y] for v in route.points],float)
        if len(p)<4 or np.linalg.norm(p[0]-p[-1])>.25:raise ValueError('Para definir o giro, selecione um eixo fechado e completo da rotatória.')
        p=np.vstack([p,p[0]]) if not np.array_equal(p[0],p[-1]) else p
        q=p-p[0];area=float(np.sum(q[:-1,0]*q[1:,1]-q[1:,0]*q[:-1,1]))/2
        if not math.isfinite(area) or abs(area)<1 or not LinearRing(p).is_simple:raise ValueError('Eixo da rotatória degenerado ou cruzando a si mesmo; corrija antes de definir o giro.')
        rotation=1 if (area>0)==(route.roundabout_rotation=='anti_horario') else -1
        if result and result!=rotation:raise ValueError('O giro da rotatória contradiz os nós ou o sentido selecionado.')
        result=rotation
    if route.flow_role=='acesso' and route.flow_direction=='ambos':raise ValueError('O acesso sobre o eixo exige um sentido por percurso; cadastre o sentido oposto separadamente.')
    return result or (1 if route.flow_role in ('acesso','retorno','dispositivo','rotatoria') else 0)


def orient_offsets(route,offsets):
    sense=direction(route)
    if not sense:return offsets
    wanted='f' if sense>0 else 'r';other='r' if sense>0 else 'f';result=[]
    for row in offsets:
        kept={k:v for k,v in row.items() if k[0]==wanted}
        # Uma seção unidirecional pode ser percorrida no sentido inverso sem
        # apagar seu cadastro; as faixas são espelhadas na derivação.
        if not kept and row and route.type=='unico' and not route.cross_sections and not route.sections and all(k[0]==other for k in row):kept={(wanted,k[1]):-v for k,v in row.items()}
        if route.flow_role=='acesso' and kept:
            if len(kept)>1:raise ValueError('Acesso sobre o eixo: habilite uma única faixa na seção desse percurso.')
            kept={next(iter(kept)):0.}
        elif route.flow_role in ('retorno','dispositivo','rotatoria'):
            kept={k:(1 if sense>0 else -1)*(abs(v) if abs(v)>1e-6 else route.lane_width_m*(k[1]+.5)) for k,v in kept.items()}
        result.append(kept)
    return result


def endpoint_kind(edge,start):
    """Metadado relativo à extremidade do eixo original, não aos cortes internos."""
    reverse=edge.get('route_dir')=='r'
    return edge.get('flow_end' if start==reverse else 'flow_start','automatico')
