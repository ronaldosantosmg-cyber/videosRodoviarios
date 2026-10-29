"""Reconstrução contínua derivada: busca limitada no corredor físico, sem alterar CAD."""
import numpy as np
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString, Point
from shapely.prepared import prep
from shapely.ops import nearest_points
from shapely import contains_xy, line_locate_point, points as make_points
from .vehicle_motion import prepare_points, analyze_motion, interpolate


def reconstruct(points, allowed, minimum=50., max_deviation=8.):
    report={'status':'blocked','strategy':'reconstrucao_continua','attempts':0,'continuous':False,'endpoints_preserved':False}
    try:
        p,d=prepare_points(points)
        minimum=float(minimum);max_deviation=float(max_deviation)
        if not np.isfinite([minimum,max_deviation]).all() or minimum<=0 or not 0<max_deviation<=8:
            raise ValueError('Limites de reconstrução inválidos.')
    except (ValueError,TypeError,OverflowError):
        report['reason']='geometria_ou_limite_invalido';return None,report
    if allowed is None or allowed.is_empty or d[-1]<minimum or d[-1]>20000 or len(p)>20000:
        report['reason']='superficie_ausente_ou_limite_excedido';return None,report
    original=LineString(p)
    if not original.is_simple:
        report['reason']='auto_intersecao_ambigua';return None,report
    if analyze_motion(p,allowed=allowed)['ok']:
        report.update(status='unchanged',max_deviation_m=0.,continuous=True,endpoints_preserved=True,length_m=float(d[-1]));return p.copy(),report
    # A origem pode ter um defeito fora da superfície. Só a derivação validada circula.
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
                      endpoints_preserved=True,continuous=True,method='suavizacao_validada',audit=audit)
        return candidate,report
    return _corridor_search(p,d,allowed,minimum,max_deviation,report)


def _corridor_search(p,d,allowed,minimum,max_deviation,report):
    """Programação dinâmica por estações, sem salto de superfície ou retorno longitudinal.

    O grafo é apenas uma proposta. A aceitação exige a conferência contínua e
    cinemática do percurso completo. Orçamento <= 42.517 posições / 250 mil ligações.
    """
    original=LineString(p)
    connected=None
    for clearance in (2.,1.4,.96):
        domain=allowed.buffer(-clearance).intersection(original.buffer(max_deviation))
        components=[g for g in getattr(domain,'geoms',[domain]) if g.geom_type=='Polygon']
        connected=next((g for g in components if g.covers(Point(p[0])) and g.covers(Point(p[-1]))),None)
        if connected is not None:report['search_clearance_m']=clearance;break
    if connected is None:
        start=next((g for g in components if g.covers(Point(p[0]))),None)
        end=next((g for g in components if g.covers(Point(p[-1]))),None)
        if start is not None and end is not None:
            a,b=nearest_points(start,end);point=[(a.x+b.x)/2,(a.y+b.y)/2]
        else:point=p[0].tolist() if start is None else p[-1].tolist()
        report.update(reason='extremidades_sem_corredor_fisico_continuo',critical_point=point,critical_station_m=float(original.project(Point(point))))
        return None,report
    coverage=prep(connected)
    count=min(2501,max(3,int(np.ceil(d[-1]/2.))+1));stations=np.linspace(0.,d[-1],count);step=stations[1]-stations[0]
    base=interpolate(p,d,stations)
    reference=gaussian_filter1d(base,max(1.,4./step),axis=0,mode='nearest')
    u=(stations/d[-1])[:,None];reference+=(1-u)*(p[0]-reference[0])+u*(p[-1]-reference[-1])
    tangent=np.gradient(reference,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    normals=np.column_stack([-tangent[:,1],tangent[:,0]])
    offsets=np.linspace(-max_deviation,max_deviation,17);middle=len(offsets)//2
    grid=reference[:,None,:]+normals[:,None,:]*offsets[None,:,None]
    grid[0,middle]=p[0];grid[-1,middle]=p[-1]
    valid=contains_xy(connected,grid[:,:,0],grid[:,:,1]);valid[0,:]=False;valid[-1,:]=False
    valid[0,middle]=connected.covers(Point(p[0]));valid[-1,middle]=connected.covers(Point(p[-1]))
    progress=line_locate_point(original,make_points(grid.reshape(-1,2))).reshape(count,-1)
    costs=np.full(len(offsets),np.inf);costs[middle]=0.;previous=np.full(valid.shape,-1,dtype=np.int16);links=0
    for i in range(1,count):
        fresh=np.full_like(costs,np.inf)
        for j in np.flatnonzero(valid[i]):
            choices=[k for k in np.flatnonzero(np.isfinite(costs)) if abs(offsets[j]-offsets[k])<=max(1.,step*.65) and -.01<=progress[i,j]-progress[i-1,k]<=step*5+1]
            choices.sort(key=lambda k:costs[k]+4*(offsets[j]-offsets[k])**2)
            for k in choices:
                links+=1
                if links>250000:
                    report.update(reason='orcamento_de_busca_excedido',search_links=links);return None,report
                if not coverage.covers(LineString([grid[i-1,k],grid[i,j]])):continue
                fresh[j]=costs[k]+4*(offsets[j]-offsets[k])**2+.05*offsets[j]**2;previous[i,j]=k;break
        costs=fresh
        if not np.isfinite(costs).any():
            report.update(reason='corredor_sem_passagem_nesta_estacao',critical_point=base[i].tolist(),critical_station_m=float(stations[i]),search_links=links);return None,report
    if not np.isfinite(costs[middle]):report['reason']='extremidade_final_inacessivel';return None,report
    indices=[middle]
    for i in range(count-1,0,-1):indices.append(int(previous[i,indices[-1]]))
    path=grid[np.arange(count),indices[::-1]]
    dense_s=np.linspace(0.,d[-1],int(np.ceil(d[-1]/.5))+1)
    path=np.column_stack([np.interp(dense_s,stations,path[:,k]) for k in range(2)])
    report.update(search_positions=int(valid.size),search_links=links)
    for sigma in (1.,2.,4.,6.,8.,12.):
        report['attempts']+=1
        candidate=gaussian_filter1d(path,sigma/(dense_s[1]-dense_s[0]),axis=0,mode='nearest')
        v=(dense_s/d[-1])[:,None];candidate+=(1-v)*(p[0]-candidate[0])+v*(p[-1]-candidate[-1]);candidate[0]=p[0];candidate[-1]=p[-1]
        line=LineString(candidate);deviation=line.hausdorff_distance(original)
        if deviation>max_deviation or line.length<minimum or not line.is_simple:continue
        if not allowed.covers(line.buffer(.9,cap_style='flat')):continue
        if np.any(np.diff(line_locate_point(original,make_points(candidate)))<-.01):continue
        audit=analyze_motion(candidate,allowed=allowed)
        if not audit['ok']:continue
        report.update(status='reconstructed',continuous=True,endpoints_preserved=True,method='busca_no_corredor_validada',length_m=float(line.length),max_deviation_m=float(deviation),audit=audit)
        return candidate,report
    report['reason']='passagem_encontrada_mas_cinematica_reprovada';return None,report


def _continuity_evidence_uncached(network,origin_key):
    """Prova por origem e sentido: nenhuma recuperação parcial conta como rota completa."""
    records=[r for r in network.raw_info if r.get('origin_key')==origin_key]
    reports=[report for r in records for report in r.get('recovery_reports',[])]
    result={'complete':False,'scope':'Geometria e itinerários do eixo cadastrado; não é certificação normativa.','directions':[],
            'reports':reports,'reason':'reconstrucao_nao_solicitada'}
    if not records or not all(r.get('reconstruction_requested') and not r.get('disabled') for r in records):return result
    if not reports or any(r.get('status') not in ('reconstructed','unchanged') for r in reports):
        result['reason']='reconstrucao_integral_recusada';return result
    groups={}
    for i,e in enumerate(network.edges):
        if e.get('origin_key')==origin_key and not e.get('disabled'):
            groups.setdefault(e.get('reconstruction_direction',e.get('route_dir',e.get('sign'))),set()).add(i)
    if not groups:result['reason']='nenhum_itinerario_continuo';return result
    for direction,required in groups.items():
        found=any(required.issubset(set(path.get('edges',[]))) for path in network.paths)
        result['directions'].append({'direction':str(direction),'required_edges':len(required),'itinerary_found':found})
    result['complete']=all(r['itinerary_found'] for r in result['directions'])
    result['reason']='continuidade_integral_revalidada' if result['complete'] else 'ligacao_entre_subtrechos_nao_revalidada'
    return result


REASONS={
 'reconstrucao_nao_solicitada':'Reconstrução não solicitada ou desligamento manual preservado.',
 'reconstrucao_integral_recusada':'Há um trecho sem reconstrução integral válida.',
 'nenhum_itinerario_continuo':'Nenhum itinerário contínuo foi aprovado.',
 'continuidade_integral_revalidada':'Itinerário completo conferido em cada sentido solicitado.',
 'ligacao_entre_subtrechos_nao_revalidada':'Nenhum itinerário cobre todos os subtrechos no mesmo sentido. Confira os nós e suas ligações.',
 'extremidades_sem_corredor_fisico_continuo':'As extremidades não têm uma passagem física contínua com folga. Confira seção e pavimento; preserve barreiras reais.',
 'corredor_sem_passagem_nesta_estacao':'O corredor está interrompido no ponto indicado. Confira a seção e os limites físicos.',
 'passagem_encontrada_mas_cinematica_reprovada':'Existe passagem, mas a curva não passou na análise do veículo. Edite a curva ou a seção.',
 'auto_intersecao_ambigua':'O eixo cruza a si mesmo. Corrija os pontos ou defina explicitamente a passagem desejada.',
 'recorte_manual_preservado':'Há um recorte manual. Revise-o explicitamente; a reconstrução não o reativa.',
 'superficie_ausente_ou_limite_excedido':'Confira pavimento/seção e os limites: até 20 km e 20 mil vértices por trajetória.',
 'geometria_ou_limite_invalido':'Corrija as coordenadas e os limites numéricos antes de reconstruir.',
 'orcamento_de_busca_excedido':'A busca atingiu o orçamento de análise. Divida o trecho ou ajuste a geometria.',
 'extremidade_final_inacessivel':'O ponto final não pôde ser alcançado no corredor permitido.'}


def continuity_evidence(network,origin_key):
    token=(origin_key,id(network.paths),id(network.edges),len(network.paths),len(network.edges))
    cache=getattr(network,'_continuity_evidence_cache',None)
    if cache is None:cache={};network._continuity_evidence_cache=cache
    if token not in cache:
        result=_continuity_evidence_uncached(network,origin_key)
        result['message']=REASONS.get(result['reason'],result['reason'])
        for report in result['reports']:
            reconstruction=report.get('reconstruction',{})
            if reconstruction.get('reason'):reconstruction['message']=REASONS.get(reconstruction['reason'],reconstruction['reason'])
        cache[token]=result
    return cache[token]
