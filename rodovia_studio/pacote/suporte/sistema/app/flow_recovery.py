"""Recuperação explícita de circulação; nunca altera nem une partes do eixo original."""
import numpy as np
from shapely.geometry import LineString
from shapely.ops import substring
from shapely import STRtree
from .vehicle_motion import prepare_points,analyze_motion


def _preview(p):
    step=max(1,int(np.ceil(len(p)/500)))
    q=p[::step]
    if not np.array_equal(q[-1],p[-1]):q=np.vstack([q,p[-1]])
    return np.round(q,3).tolist()


def recover_sections(points,allowed,minimum=50.,reconstruct=False):
    """Localiza falhas com janelas sobrepostas e revalida integralmente cada resto.

    Falhas não localizadas e geometria inválida permanecem bloqueadas.
    O eixo original permanece intacto. A trajetória derivada admite correção de
    até 0,5 m revalidada; partes excluídas nunca são ligadas por atalhos.
    """
    report={'status':'blocked','excluded':[],'retained':[],'reasons':[],'retained_geometry':[],'excluded_geometry':[]}
    try:p,d=prepare_points(points)
    except (ValueError,TypeError,OverflowError):report['reasons']=['geometria_invalida'];return [],report
    if allowed is None or allowed.is_empty:
        report['reasons']=['pavimento_ausente'];return [],report
    minimum=float(minimum)
    if not np.isfinite(minimum) or minimum<=0:raise ValueError('Limite de recuperação deve ser positivo e finito.')
    line=LineString(p);total=float(d[-1]);audit=analyze_motion(p,allowed=allowed)
    report['reasons']=audit['reasons']
    if total<minimum:report['reasons']=['abaixo_do_limite'];return [],report
    if audit['ok']:
        report.update(status='unchanged',retained=[[0.,total]],retained_geometry=[_preview(p)]);return [p.copy()],report
    if reconstruct:
        from .flow_reconstruction import reconstruct as rebuild
        candidate,reconstruction=rebuild(p,allowed,minimum)
        report['reconstruction']=reconstruction
        if candidate is not None:
            report.update(status='reconstructed',strategy='reconstrucao_continua_validada',
                          retained=[[0.,total]],retained_geometry=[_preview(candidate)])
            return [candidate],report
    if total>100000 or len(p)>50000:
        report['message']='Extensão excessiva: divida a análise antes de recuperar.';return [],report
    # Primeiro tenta uma correção leve da trajetória derivada, limitada a 0,5 m.
    # O eixo CAD não é movido; só é aceita se corpo e movimento passarem integralmente.
    if allowed is not None and not allowed.is_empty:
        from .traffic import steady_path
        from shapely import line_locate_point,points as make_points
        candidate,_=steady_path(p,allowed,sigma_m=.8)
        if candidate is not None and len(candidate)>=2:
            deviation=LineString(candidate).hausdorff_distance(line)
            progress=line_locate_point(line,make_points(candidate))
            if deviation<=.5 and float(np.linalg.norm(np.diff(candidate,axis=0),axis=1).sum())>=minimum and np.all(np.diff(progress)>=-.1) and analyze_motion(candidate,allowed=allowed)['ok']:
                report.update(status='smoothed',strategy='suavizacao_leve_validada',max_deviation_m=round(deviation,4),retained=[[0.,total]],retained_geometry=[_preview(candidate)])
                return [candidate],report
    bad=[]
    if not line.is_simple:
        segments=[LineString([a,b]) for a,b in zip(p,p[1:])]
        pairs=STRtree(segments).query(segments,predicate='intersects')
        for i,j in zip(*pairs):
            if j<=i+1:continue
            crossing=segments[i].intersection(segments[j])
            if crossing.is_empty:continue
            c=crossing.centroid
            a=float(d[i]+segments[i].project(c));b=float(d[j]+segments[j].project(c))
            bad.append((max(0.,min(a,b)-15.),min(total,max(a,b)+15.)))
    # Sobreposição evita perder uma falha situada na fronteira de duas janelas.
    for station in np.arange(0.,total+5.,5.):
        a=max(0.,station-10.);b=min(total,station+10.)
        if b-a<1:continue
        q=np.asarray(substring(line,a,b).coords)
        if not analyze_motion(q,allowed=allowed)['ok']:bad.append((max(0.,a-5.),min(total,b+5.)))
    if not bad:
        report['message']='Falha não localizada com segurança: ajuste manual necessário.';return [],report
    merged=[]
    for a,b in sorted(bad):
        if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
        else:merged.append([a,b])
    kept=[];cursor=0.
    for a,b in merged+[[total,total]]:
        if a-cursor>=minimum:
            q=np.asarray(substring(line,cursor,a).coords)
            if analyze_motion(q,allowed=allowed)['ok']:
                kept.append(q);report['retained'].append([cursor,a])
        cursor=max(cursor,b)
    # Inclui na exclusão também restos curtos ou que reprovaram na conferência integral.
    cursor=0.
    for a,b in report['retained']+[[total,total]]:
        if a>cursor:report['excluded'].append([cursor,a])
        cursor=b
    report['retained_geometry']=[_preview(q) for q in kept]
    report['excluded_geometry']=[_preview(np.asarray(substring(line,a,b).coords)) for a,b in report['excluded']]
    report['status']='partial' if kept else 'blocked'
    report['message']='Somente trechos revalidados recebem veículos; não há travessia das lacunas.'
    return kept,report
