"""Visibilidade de veículos: não altera geometria, circulação, demanda ou restrições."""
import numpy as np
from collections import Counter
from . import visual


def visible(scene,t,cam,width,progress):
    stats={'time_s':round(float(t),3),'width_m':round(float(width),3),'enabled':bool(scene.s.traffic),'active':0,'drawn':0,'outside_view':0,'outside_revealed_section':0,'body_outside_allowed':0,'subpixel':0,'reveal_pending':float(getattr(scene,'reveal_opacity',1))<=.9}
    items=[]
    if not scene.s.traffic:return items,stats
    for pt,tan,vid,identity,j in scene.traffic_iter(t):
        stats['active']+=1
        ch=scene.ch[scene.tree.query(pt)[1]]
        if ch>progress*scene.length:stats['outside_revealed_section']+=1;continue
        q=scene.screen(pt[None],cam,width)[0]
        if not(5<q[0]<scene.W-5 and scene.H*.12<q[1]<scene.H*.88):stats['outside_view']+=1;continue
        vt=visual.vehicle_type(scene.network.paths[identity[0]]['kinds'],identity,getattr(scene.s,'vehicle_mix','classico'))
        if not scene.fits(identity[0],j,pt,tan,vt):stats['body_outside_allowed']+=1;continue
        if visual.TYPES[vt]['L']*scene.W/width<2:stats['subpixel']+=1
        items.append((pt,tan,vt,visual.vehicle_color(identity,vt)))
    if stats['reveal_pending']:items=[]
    stats['drawn']=len(items)
    return items,stats


def focus_pose(scene,t):
    """Segue um veículo real persistente; caso contrário, enquadra uma via válida."""
    if not scene.s.traffic:raise ValueError('O modo Tráfego exige Incluir veículos ativado.')
    if not scene.network.paths:raise ValueError('Não há itinerário válido para enquadrar veículos. Abra Diagnosticar veículos e corrija o eixo/seção; não remova as proteções.')
    width=float(np.clip(scene.s.view_width_m,80,750))
    if not hasattr(scene,'_traffic_camera_plan'):
        end=max(0.,scene.s.duration_s-1/scene.s.fps)
        first={tuple(v[3]):v for v in scene.traffic_iter(0)};last={tuple(v[3]):v for v in scene.traffic_iter(end)}
        common=sorted(set(first)&set(last))
        if common:plan={'identity':common[0],'center':first[common[0]][0].copy()}
        else:
            samples=[*first.values(),*last.values(),*scene.traffic_iter(scene.s.duration_s/2)]
            counts=Counter(int(v[3][0]) for v in samples)
            if not counts:raise ValueError('Nenhum veículo ativo no intervalo amostrado. Confira demanda, restrições e o diagnóstico de circulação; nada foi liberado artificialmente.')
            index=counts.most_common(1)[0][0];path=np.asarray(scene.network.paths[index]['p'])
            q=(path-path[0])@scene.R
            span=max(float(np.ptp(q[:,0])),float(np.ptp(q[:,1]))*scene.W/(scene.H*.65))
            if span<width*.8:center=(path.min(0)+path.max(0))/2
            else:center=next(v[0].copy() for v in samples if int(v[3][0])==index)
            plan={'identity':None,'center':center}
        scene._traffic_camera_plan=plan
    plan=scene._traffic_camera_plan;center=plan['center']
    if plan['identity'] is not None:
        match=next((v for v in scene.traffic_iter(float(t)) if tuple(v[3])==plan['identity']),None)
        if match is not None:center=match[0]
    return np.asarray(center,float),width,1.,None,'trafego'


def preflight(scene):
    if not scene.s.traffic:return {'enabled':False,'status':'desativado','samples':[],'notice':'Veículos desativados na configuração.'}
    end=max(0.,scene.s.duration_s-1/scene.s.fps);samples=[]
    previous_opacity=getattr(scene,'reveal_opacity',1.)
    try:
        for t in sorted(set([0.,scene.s.duration_s/2,end])):
            scene.reveal_opacity=1.
            if not scene.s.traffic_route_only and scene.s.duration_s<45 and scene.s.short_video_mode=='auto' and scene.s.camera_mode!='trafego':
                f=float(np.clip(t/max(1,min(8,scene.s.duration_s*.55)),0,1));scene.reveal_opacity=f*f*(3-2*f)
            cam,width,progress,*_=scene.pose(t)
            if scene.s.traffic_route_only:progress=1.
            _,row=visible(scene,t,cam,width,progress);samples.append(row)
    finally:scene.reveal_opacity=previous_opacity
    if not scene.network.paths:status,notice='sem_itinerarios','Nenhum itinerário válido; confira eixo, seção e bloqueios reais.'
    elif not any(r['active'] for r in samples):status,notice='sem_veiculos','Nenhum veículo ativo nos instantes amostrados. Confira demanda, faixa, restrições e a simulação.'
    elif not any(r['drawn'] for r in samples) and any(r['body_outside_allowed'] for r in samples):status,notice='corpo_fora_da_superficie','Há veículos simulados cujo corpo foi recusado fora da superfície permitida. Confira a seção e os limites físicos no diagnóstico.'
    elif not any(r['drawn'] for r in samples):status,notice='fora_do_enquadramento','Há veículos simulados, mas fora da área apresentada. Use o modo Tráfego para conferir.'
    elif all(r['drawn']==r['subpixel'] for r in samples if r['drawn']):status,notice='escala_ampla','Os veículos existem, mas têm menos de dois pixels nesta escala. Use o enquadramento de tráfego.'
    else:status,notice='visivel','Há veículos compatíveis com o enquadramento nos instantes amostrados.'
    return {'enabled':True,'status':status,'notice':notice,'samples':samples,'scope':'Amostras antes da exportação; não é contagem de todos os quadros nem garantia de visibilidade permanente.'}


def project_status(directory):
    """Leitura dos resultados atuais, sem gerar cálculo ao abrir a janela."""
    import json
    from pathlib import Path
    from .project_state import read_config
    from .artifacts import status
    d=Path(directory);config=read_config(d);states=status(d)
    def result(name,kind):
        p=d/name
        if states[kind]['state']!='ready' or not p.is_file() or p.is_symlink() or p.stat().st_size>64*1024*1024:return {}
        try:
            value=json.loads(p.read_text());return value if isinstance(value,dict) else {}
        except (OSError,ValueError):return {}
    editor=result('editor.json','editor');analysis=result('analysis.json','analysis');video=result('video.json','video');preview=result('preview.json','preview')
    presentation=video.get('traffic_presentation') or {};visibility=preview.get('traffic_visibility') or analysis.get('traffic_visibility') or {}
    simulation=video.get('motion_audit') or analysis.get('traffic_simulation') or {}
    current=bool(editor);paths=editor.get('itineraries') if current else None
    notices=[]
    if not config.get('traffic',True):notices.append('Incluir veículos está desativado. O botão de prévia de tráfego permite ativar a apresentação, sem reativar rotas desligadas manualmente.')
    if not current:notices.append('Atualize o diagnóstico das rotas para usar resultados desta revisão do projeto.')
    elif not paths:notices.append('Nenhum itinerário válido para circulação. Confira eixo, seção e as causas dos bloqueios; aumentar densidade não cria uma rota.')
    if presentation.get('notice'):notices.append(presentation['notice'])
    elif visibility.get('subpixel',0):notices.append('Há veículos com menos de dois pixels neste enquadramento. Use a prévia de tráfego em detalhe.')
    if visibility.get('outside_view',0):notices.append('Parte dos veículos está fora da região enquadrada na prévia.')
    if visibility.get('body_outside_allowed',0):notices.append('O desenho recusou corpos fora da superfície permitida. Localize o fluxo e confira a seção e os limites físicos.')
    if visibility.get('reveal_pending'):notices.append('A animação de entrada ainda não terminou neste quadro.')
    if simulation.get('motion_blocked_vehicles',0):notices.append('Parte da frota foi recusada pela análise do corpo/curva. Isso não significa que todos os veículos ou todas as rotas estejam bloqueados.')
    if paths and not simulation and visibility.get('active') is None:notices.append('Há itinerários, mas a simulação ainda não foi medida em uma prévia ou vídeo atual.')
    if visibility.get('active')==0:notices.append('Nenhum veículo ativo neste instante da prévia. Confira demanda, tempo e restrições antes de alterar a geometria.')
    return {'enabled':bool(config.get('traffic',True)),'editor_current':current,'itineraries':paths,'simulated_vehicles':simulation.get('vehicles'),'preview_active':visibility.get('active'),'preview_drawn':visibility.get('drawn'),'preview_width_m':visibility.get('width_m'),'camera_mode':config.get('camera_mode'),'presentation':presentation,'notices':notices,'segments':[{k:s.get(k) for k in ('id','source','technical_status','technical_message','disabled','technical_exclusion')} for s in editor.get('segments',[]) if s.get('technical_status')!='ok'][:100],'scope':'Somente resultados atuais; abrir esta janela não recalcula, não libera rotas e não altera a configuração.'}
