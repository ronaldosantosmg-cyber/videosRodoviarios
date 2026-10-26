"""Aplicativo fornece evidências; regras propõem; motor valida e executa ações permitidas."""
import json,shutil,tempfile,uuid,time,re,hashlib
from pathlib import Path
from .models import Settings
from .project_state import read_config,save_config,revision,locked,restore,Conflict
from .dependencies import revisions
from .store import write_json

ACTIONS={'recover','reconstruct'}

def signature(d):
    d=Path(d);sources=[];total=0
    for name in ('input.dxf','input.kmz','camadas','imagem_local','elevacao'):
        source=d/name
        if source.is_symlink():raise ValueError('Fonte por link recusada.')
        files=[source] if source.is_file() else sorted(source.rglob('*')) if source.is_dir() else []
        for f in files:
            if f.is_symlink():raise ValueError('Fonte por link recusada.')
            if not f.is_file():continue
            total+=f.stat().st_size
            if total>512*1024*1024 or len(sources)>10000:raise ValueError('Assistência limitada a 512 MiB de fontes; use edição manual para este projeto.')
            h=hashlib.sha256()
            with f.open('rb') as stream:
                while chunk:=stream.read(1024*1024):h.update(chunk)
            sources.append([f.relative_to(d).as_posix(),h.hexdigest()])
    return revision([d.name,revision(read_config(d)),revisions(d)['editor'],sources])

def folder(d):
    p=Path(d)/'.estado/assistencia'
    if p.is_symlink() or p.parent.is_symlink():raise ValueError('Pasta de assistência inválida.')
    p.mkdir(exist_ok=True);return p

def load(d,key):
    if not re.fullmatch('[a-f0-9]{32}',key):raise ValueError('Proposta inválida.')
    p=folder(d)/(key+'.json')
    if p.is_symlink() or p.stat().st_size>8*1024*1024:raise ValueError('Arquivo de proposta inválido.')
    data=json.loads(p.read_text())
    if data['project']!=Path(d).name:raise Conflict('Proposta de outro projeto.')
    return data

def preview(d,request,status=lambda *a:None,cancel=lambda:False):
    from .render import Scene
    from .flow_diagnostics import flow_diagnostics
    from .vehicle_motion import analyze_motion
    from .artifacts import require_current
    d=Path(d);initial=signature(d)
    if request['signature']!=initial:raise Conflict('O projeto mudou. Refaça o diagnóstico.')
    require_current(d,'editor')
    doc=json.loads((d/'editor.json').read_text());segment=next((s for s in doc['segments'] if s['id']==request['segment']),None)
    if not segment:raise ValueError('Segmento ausente no resultado atual.')
    if segment['disabled'] or segment['length_m']<read_config(d).get('min_route_segment_m',50):raise ValueError('Desligamento manual ou rota independente curta preservados.')
    if segment['technical_status']=='ok':raise ValueError('O trecho já está validado; não há correção a aplicar.')
    action=request.get('action','auto')
    if action=='auto':action='reconstruct' if any(x in (segment.get('technical_reasons') or []) for x in ('ziguezague','mudanca_brusca','esterco_excessivo','auto_intersecao')) else 'recover'
    if action not in ACTIONS:raise ValueError('Ação não cadastrada.')
    before=read_config(d);candidate=json.loads(json.dumps(before));origin=segment.get('origin_key')
    if not origin or not re.fullmatch('[a-f0-9]{64}',origin):raise ValueError('Origem do trecho indisponível; recalcule.')
    existing=next((r for r in candidate.get('flow_recoveries',[]) if r.get('target_key')==origin and r.get('enabled',True)),None)
    mark=existing or {'id':uuid.uuid4().hex,'target_key':origin,'x':segment['mid'][0],'y':segment['mid'][1],'enabled':True}
    mark['reconstruct']=action=='reconstruct'
    if existing is None:candidate.setdefault('flow_recoveries',[]).append(mark)
    settings=Settings.model_validate(candidate);status(.1,'Montando prévia isolada; projeto original preservado')
    with tempfile.TemporaryDirectory(prefix='rodovia_proposta_') as temporary:
        sandbox=Path(temporary);files=[]
        for name in ('input.dxf','input.kmz','camadas','imagem_local','elevacao','contexto_imagem'):
            source=d/name
            if source.is_symlink():raise ValueError('Fonte não pode ser um link.')
            files.extend([source] if source.is_file() else list(source.rglob('*')) if source.is_dir() else [])
        files=[f for f in files if f.is_file()]
        if len(files)>10000 or sum(f.stat().st_size for f in files)>512*1024*1024:raise ValueError('Prévia assistida excede 512 MiB/10.000 arquivos. Use edição manual e recalcule.')
        for f in files:
            if f.is_symlink() or any(p.is_symlink() for p in f.parents if p!=d and d in p.parents):raise ValueError('Fonte externa por link recusada.')
            if cancel():raise InterruptedError('Proposta cancelada; projeto preservado.')
            target=sandbox/f.relative_to(d);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
        (sandbox/'config.json').write_text(settings.model_dump_json())
        def step(p,message):
            if cancel():raise InterruptedError('Proposta cancelada; projeto preservado.')
            status(.2+.65*p,message)
        scene=Scene.light(sandbox,settings,step);diagnostics=flow_diagnostics(scene.network)
        selected=[diag for raw,diag in zip(scene.network.raw_info,diagnostics) if raw.get('origin_key')==origin]
        enabled=any(r.get('technical_circulation',{}).get('enabled') for r in selected)
        valid=all(analyze_motion(path['p'],allowed=scene.network.allowed)['ok'] for path in scene.network.paths)
        after=[{'status':r['technical_status'],'message':r['technical_message'],'circulation':r.get('technical_circulation',{})} for r in selected]
        geometry=[]
        bases={raw['base'] for raw in scene.network.raw_info if raw.get('origin_key')==origin}
        for path in scene.network.paths:
            if any(scene.network.edges[i]['base'] in bases for i in path.get('edges',[])):
                points=path['p'];step=max(1,len(points)//1000);q=points[::step].tolist()
                if q[-1]!=points[-1].tolist():q.append(points[-1].tolist())
                geometry.append(q)
            if len(geometry)>=20:break
    if cancel():raise InterruptedError('Proposta cancelada; projeto preservado.')
    if signature(d)!=initial:raise Conflict('O projeto mudou durante a prévia. Resultado descartado.')
    key=uuid.uuid4().hex
    result={'id':key,'project':d.name,'signature':initial,'action':action,'segment':segment['id'],'origin_key':origin,'mark':mark,'before_revision':revision(before),'before':{'status':segment['technical_status'],'message':segment['technical_message'],'geometry':segment['points']},'after':after,'geometry':geometry,'can_apply':bool(enabled and valid and candidate!=before),'state':'proposta','created':time.time(),'checks':{'all_paths_motion_valid':valid,'circulation_available':enabled,'physical_rules_preserved':True},'notice':'A prévia valida trajetórias no motor real. Partes excluídas não são religadas. A simulação completa e o diagnóstico devem ser atualizados após aplicar.'}
    write_json(folder(d)/(key+'.json'),result);status(1,'Proposta pronta para revisão; nenhuma correção aplicada')
    return result

def apply(d,key):
    from .execlog import write
    d=Path(d)
    with locked(d):
        plan=load(d,key)
        if plan['state']!='proposta' or signature(d)!=plan['signature']:raise Conflict('Proposta consumida ou desatualizada. Gere outra prévia.')
        if not plan['can_apply'] or plan['action'] not in ACTIONS or not all(plan['checks'].values()):raise ValueError('O motor não encontrou uma correção segura; use edição manual.')
        data=read_config(d);marks=data.setdefault('flow_recoveries',[])
        mark=plan['mark']
        if mark.get('target_key')!=plan['origin_key'] or mark.get('reconstruct')!=(plan['action']=='reconstruct') or mark.get('enabled') is not True:raise ValueError('Contrato da ação inválido.')
        from .models import FlowRecovery
        mark=FlowRecovery.model_validate(mark).model_dump()
        old=next((r for r in marks if r.get('target_key')==plan['origin_key'] and r.get('enabled',True)),None)
        if old:old.update(mark)
        else:marks.append(mark)
        plan.update(state='confirmada_aguardando_gravacao',applied_revision=revision(data))
        write_json(folder(d)/(key+'.json'),plan)
        warning=None
        try:result=save_config(d,data,plan['before_revision'])
        except OSError:
            # A troca primária pode ter concluído antes de falhar o índice auxiliar.
            from .project_state import _json
            if revision(_json(d/'config.json'))!=plan['applied_revision']:raise
            result={'revision':plan['applied_revision']};warning='Configuração aplicada, mas metadados auxiliares precisam ser conferidos em Proteção de dados.'
        plan.update(state='aplicada_pendente_revalidacao',applied_revision=result['revision'])
        try:write_json(folder(d)/(key+'.json'),plan)
        except OSError:warning='Configuração aplicada; recibo anterior preservado. Confira Proteção de dados antes de continuar.'
    write(d,'execucao','correcao_assistida_aplicada',proposta=key,acao=plan['action'],antes=plan['before_revision'],depois=result['revision'])
    return {'revision':result['revision'],'state':plan['state'],'notice':warning or 'Correção aplicada. Atualize e confira o resultado; ainda não declarada resolvida.'}

def outcome(d,key):
    from .artifacts import require_current
    plan=load(d,key)
    if plan.get('applied_revision')!=revision(read_config(d)):raise Conflict('Há alterações posteriores; resultado da proposta não pode ser atribuído a esta revisão.')
    require_current(d,'editor');doc=json.loads((Path(d)/'editor.json').read_text())
    rows=[r for r in doc['segments'] if r.get('origin_key')==plan['origin_key']]
    resolved=bool(rows) and all(r['technical_status']=='ok' and r.get('technical_circulation',{}).get('enabled') for r in rows)
    return {'resolved':resolved,'state':'resolvida' if resolved else 'aplicada_com_pendencias','segments':[{'id':r['id'],'status':r['technical_status'],'message':r['technical_message']} for r in rows]}

def undo(d,key):
    d=Path(d)
    with locked(d):
        plan=load(d,key)
        if plan.get('applied_revision')!=revision(read_config(d)):raise Conflict('O projeto mudou depois da correção. Use o histórico para preservar as edições posteriores.')
        result=restore(d,plan['before_revision'],plan['applied_revision']);plan['state']='desfeita';write_json(folder(d)/(key+'.json'),plan)
        return result
