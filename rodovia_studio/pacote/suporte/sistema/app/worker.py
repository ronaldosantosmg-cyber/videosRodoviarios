import json,sys,traceback,shutil
import numpy as np
from pathlib import Path
from . import store
from .models import Settings
from .geometry import analyze
from .render import Scene,render,ASSETS
from PIL import Image

def run(jid):
    j=store.job(jid);d=store.directory(j['project'])
    from .execlog import JobLog
    jl=JobLog(d,jid,j['kind'])   # 1.26: registro de execução do projeto
    def status(p,msg):
        if float(p)<1 and store.job(jid)['state']=='cancel_requested':raise InterruptedError('Atualização cancelada.')
        store.update(jid,progress=float(p),message=msg);jl.status(p,msg)
    def cancel():return store.job(jid)['state']=='cancel_requested'
    end_message='Concluído';ticket=None
    try:
        from .project_state import read_config,locked
        from .artifacts import begin,finish
        with locked(d):
            s=Settings.model_validate(read_config(d))
            from .artifacts import status as artifact_status
            current=artifact_status(d)
            reusable=j['kind']=='analyze' and all(current[k]['state']=='ready' for k in ('analysis','editor','vectors'))
            ticket=None if reusable else begin(d,jid,j['kind'],s)
        jl.capture(s)
        if j.get('created'):
            from datetime import datetime,timezone
            try:
                wait=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(j['created']).replace(tzinfo=timezone.utc)).total_seconds())
                from .execlog import write
                write(d,'execucao','inicio',tarefa=jid,tipo=j['kind'],espera_s=round(wait,3))
            except (ValueError,TypeError):pass
        if reusable:
            end_message='Fluxos e geometria já estão atualizados; nenhum recálculo necessário'
            status(1,end_message)
        elif j['kind']=='assisted_plan':
            from .assisted_execution import preview,folder
            request=json.loads((folder(d)/'pedido.json').read_text())
            plan=preview(d,request,status,cancel);store.write_json(folder(d)/'ultima.json',{'id':plan['id']})
            end_message='Proposta pronta; revise e confirme antes de aplicar'
        elif j['kind']=='traffic_check':
            from .traffic_check import run as check_traffic
            check_traffic(d,s,status,cancel);end_message='Conferência de circulação pronta'
        elif j['kind']=='image_context':
            from .image_context import run as image_run
            request=json.loads((d/'contexto_imagem/pedido.json').read_text(encoding='utf-8'))
            image_run(d,s,request,status,cancel,jid);end_message='Contornos sugeridos; revise os grupos antes de aplicar'
        elif j['kind']=='scene3d':
            from .scene3d import build
            build(d,s,status,cancel);end_message='Cena 3D pronta'
        elif j['kind']=='analyze':
            status(.02,'Lendo DXF e preparando camadas e hachuras')
            unmapped=[];hp={};geometry=analyze(d,s,preview=unmapped,hatch_preview=hp)
            items,axis,_,_,r=geometry;status(.35,'Geometria lida; preparando o editor');store.write_json(d/'analysis.json',r)
            try:(d/'hachuras_previa.json').write_text(json.dumps({k:v['p'] for k,v in hp.items()},separators=(',',':')),encoding='utf-8')
            except Exception:pass
            try:
                from .geometry import write_layer_preview
                write_layer_preview(d,items,unmapped)
            except Exception as exc:r['warnings'].append('Prévia das camadas não gerada: '+str(exc)[:120])
            from .webmap import write_vectors
            try:write_vectors(d,items,axis,s.crs)
            except Exception as exc:r['warnings'].append('Vetores do editor não gerados: '+str(exc)[:160])
            # 1.11: fluxos, sentidos e sinalização para o editor, sem precisar da prévia.
            try:
                status(.4,'Calculando fluxos e sinalização para o editor')
                lt=Scene.light(d,s,lambda p,m:status(.4+.55*p,m),_geometry=geometry);store.write_json(d/'editor.json',lt.editor_data())
            except InterruptedError:raise
            except Exception as exc:r['warnings'].append('Fluxos do editor não calculados: '+str(exc)[:160])
            store.write_json(d/'analysis.json',r)
            status(1,'Análise concluída')
        elif j['kind'] in ('preview','refresh','rebuild'):
            sc=Scene(d,s,status);s=sc.s
            view=None
            if s.preview_mode=='custom' and s.preview_center is not None:view=((s.preview_center.x,s.preview_center.y),s.preview_width_m or s.view_width_m)
            if s.cabin.enabled and s.preview_mode=='video':
                from .cabin import CabinView
                cab=CabinView(sc);cim,cm=cab.frame(min(s.cabin.duration_s-1/s.fps,s.preview_time_s))
                tmp=d/'preview_cabin.tmp.png';Image.fromarray(cim).save(tmp);store.replace(tmp,d/'preview_cabin.png')
                # O editor continua na vista geral (coordenadas em planta) para posicionar marcações.
                im,meta=sc.frame(0,overview=True);meta={**meta,'cabin':cm}
            else:
                if s.preview_mode!='overview' and getattr(sc,'detail',None) is not None:
                    cw=(np.asarray(view[0],float),float(view[1])) if view else sc.pose(min(s.duration_s-1/s.fps,s.preview_time_s))[:2]
                    try:sc.detail.prefetch([cw],status)
                    except Exception:pass
                im,meta=sc.frame(min(s.duration_s-1/s.fps,s.preview_time_s),overview=s.preview_mode=='overview',view=view)
            tmp=d/'preview.tmp.png';Image.fromarray(im).save(tmp);store.replace(tmp,d/'preview.png')
            store.write_json(d/'preview.json',meta);store.write_json(d/'analysis.json',sc.report);store.write_json(d/'editor.json',sc.editor_data())
            from .webmap import write_vectors
            try:write_vectors(d,sc.items,sc.axis,s.crs)
            except Exception:pass
            status(1,'Prévia pronta')
        elif j['kind']=='reference':
            source=ASSETS/'th57/referencia.mp4';tmp=d/'video.partial.mp4'
            if not source.exists():raise FileNotFoundError('O vídeo de referência foi substituído pela ficha técnica; não há cópia para exportar.')
            with source.open('rb') as fi,tmp.open('wb') as fo:
                done=0
                while b:=fi.read(4*1024*1024):
                    if cancel():raise InterruptedError('Exportação cancelada.')
                    fo.write(b);done+=len(b);status(done/source.stat().st_size,'Exportando o arquivo aprovado sem alterações')
            store.replace(tmp,d/'video.mp4');store.write_json(d/'video.json',{'mode':'reference','note':'Cópia binária do vídeo aprovado; não é uma nova renderização.'})
        elif j['kind'] in ('reference_profile','reference_profile_remove'):
            from .video_profile import profile
            source=ASSETS/'th57/referencia.mp4';target=ASSETS/'th57/referencia_ficha.json'
            if not source.exists():raise FileNotFoundError('O vídeo de referência já não está na pasta do aplicativo; a ficha técnica existente continua valendo.')
            status(.05,'Medindo o vídeo de referência (dados do arquivo, SHA-256 e quadros amostrados)')
            old=json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
            prof=profile(source,label='Vídeo TH57 aprovado (referência histórica)')
            prof['status']='completa';prof['note']='Ficha medida a partir do arquivo referencia.mp4. Comparação relativa: mesmo método aplicado aos vídeos gerados.'
            known=old.get('file',{}).get('sha256')
            prof['sha256_matches_1_0']=(known==prof['file'].get('sha256')) if known else None
            store.write_json(target,prof);status(.95,'Ficha técnica gravada')
            if j['kind']=='reference_profile_remove':
                if json.loads(target.read_text(encoding='utf-8')).get('status')!='completa':raise RuntimeError('Ficha não confirmada; o vídeo não foi removido.')
                source.unlink();end_message='Ficha técnica gravada e vídeo de referência removido (456 MB liberados)'
            else:end_message='Ficha técnica da referência gravada'
        elif j['kind']=='compare':
            from .video_profile import profile,compare
            from .videos import current
            video=current(d)
            if video is None:raise FileNotFoundError('Gere um vídeo antes de comparar.')
            status(.1,'Medindo o vídeo gerado');cur=profile(video,label='Vídeo gerado',sha=False)
            ref=json.loads((ASSETS/'th57/referencia_ficha.json').read_text(encoding='utf-8'))
            store.write_json(d/'video_ficha.json',cur);store.write_json(d/'comparacao.json',{'reference':ref.get('label'),'reference_status':ref.get('status'),'rows':compare(ref,cur)})
            end_message='Comparação com a referência pronta'
        elif j['kind']=='export':
            from .exports_job import run_export
            run_export(d,s,status);end_message='Exportação concluída'
        elif j['kind']=='convert_imagery':
            # 1.17: ECW/MrSID/... -> GeoTIFF em blocos com o GDAL do computador (QGIS/OSGeo4W).
            from .local_tiles import find_gdal,convert
            from .local_imagery import georef
            from .models import LocalImagery,LocalSource
            from .imagery_cache import lookup,register,materialize,session_temp
            req=json.loads((d/'imagem_local'/'_converter.json').read_text(encoding='utf-8'))
            # 1.40.7: reaproveita GeoTIFF validado da base compartilhada quando o mesmo arquivo-fonte já foi convertido.
            from .ecw_engine import py_gdal,convert_py
            src=d/'imagem_local'/req['file'];dst=src.with_name(src.stem+'_convertido.tif');world=prj=None;check=None
            key,cached=lookup(src)
            if cached is not None:
                status(.12,'GeoTIFF já existe na base de imagens; reutilizando sem nova conversão')
                dst,linked=materialize(cached,d,dst.name)
                cm=cached.get('meta') or {};world=(dst.stem+'.tfw') if cm.get('world') else None;prj=(dst.stem+'.prj') if cm.get('prj') else None
                check=cm.get('check');status(.72,'Base de imagens reutilizada')
            else:
                # conversão sempre nasce em temporário de sessão; só uma saída validada entra na base.
                work=session_temp()/('imagery_'+key[:16]);work.mkdir(parents=True,exist_ok=True)
                tmpdst=work/'convertido.tif'
                pg=py_gdal()
                if pg is not None and pg.IdentifyDriver(str(src)) is not None:
                    check=convert_py(src,tmpdst,status,gdal=pg);world=check.get('world');prj=check.get('prj')
                else:
                    g=find_gdal()
                    if not g:raise ValueError('Leitor ECW não disponível. Use “Instalar leitor ECW interno” (uma vez, sem administrador) ou instale o QGIS com suporte a ECW.')
                    convert(g,src,tmpdst,status)
                # valida a conversão antes de publicá-la na base compartilhada.
                georef(tmpdst,work/world if world else None,work/prj if prj else None,req.get('crs') or None)
                entry=register(src,tmpdst,world=work/world if world else None,prj=work/prj if prj else None,check=check,extra={'format':'GeoTIFF'})
                dst,linked=materialize(entry,d,dst.name)
                world=(dst.stem+'.tfw') if entry['meta'].get('world') else None;prj=(dst.stem+'.prj') if entry['meta'].get('prj') else None
            base=d/'imagem_local'
            info=georef(dst,base/world if world else None,base/prj if prj else None,req.get('crs') or None)
            # A referência só é publicada após validar o GeoTIFF; mescla sobre a configuração mais recente.
            with locked(d):
                s=Settings.model_validate(read_config(d))
                if req.get('mode')=='add' and s.local_imagery.image:
                    s.local_imagery.others.append(LocalSource(name=req['file'],image=dst.name,world=world,prj=prj,crs=req.get('crs') or None))
                else:
                    s.local_imagery=LocalImagery(name=req['file'],image=dst.name,world=world,prj=prj,crs=req.get('crs') or None,others=s.local_imagery.others)
                    s.imagery='local'
                store.write_json(d/'config.json',s.model_dump())
            if check:store.write_json(d/'imagem_local'/(dst.stem+'_conferencia.json'),check)
            (d/'imagem_local'/'_converter.json').unlink(missing_ok=True)
            if 'work' in locals():shutil.rmtree(work,ignore_errors=True)
            end_message=f'Convertido: {dst.name} ({info["size"][0]}×{info["size"][1]} px)'
        elif j['kind']=='install_ecw':
            from .ecw_engine import install
            st=install(status);end_message=f"Leitor ECW interno instalado: GDAL {st['python_gdal']} com ECW."
        elif j['kind']=='frames':
            from .exports_job import run_frames
            out=run_frames(d,s,status,cancel);end_message='Sequência PNG pronta em '+str(out)
        else:
            import time as _t;t0=_t.monotonic()
            render(d,s,status,cancel)
            info=json.loads((d/'video.json').read_text(encoding='utf-8'));end_message='Concluído · '+info.get('encoder','H.264')
            # 1.32: cada geração fica guardada em <videos>/<projeto> (o vídeo anterior não é substituído).
            try:
                from .videos import archive
                saved=archive(d,j['project'],s,info,_t.monotonic()-t0)
                if saved is not None:
                    info['arquivo']=saved.name;info['pasta_videos']=str(saved.parent);store.write_json(d/'video.json',info)
                    end_message+=f' · guardado em videos\\{saved.parent.name}\\{saved.name}'
            except Exception as exc:
                end_message+=' · aviso: o vídeo não foi copiado para a pasta de vídeos ('+str(exc)[:120]+')'
        finish(d,ticket)
        store.update(jid,state='done',progress=1,message=end_message);jl.done(end_message)
    except BaseException as e:
        from .artifacts import finish
        finish(d,ticket,False)
        (d/'video.partial.mp4').unlink(missing_ok=True)
        tb=traceback.format_exc();(d/'error.log').write_text(tb,encoding='utf-8')
        if isinstance(e,InterruptedError):jl.done('Cancelado: '+str(e))
        else:jl.failed(e,tb)
        store.update(jid,state='cancelled' if isinstance(e,InterruptedError) else 'failed',message=str(e)[:400],error=type(e).__name__)
        if not isinstance(e,InterruptedError):return 1
    return 0
_run_job=run
def run(jid):
    from .full_update import complete_update
    with complete_update(store.job(jid)['kind']=='rebuild'):
        from .process_supervision import Heartbeat
        with Heartbeat(store.directory(store.job(jid)['project']),jid):return _run_job(jid)

if __name__=='__main__':raise SystemExit(run(sys.argv[1]))
