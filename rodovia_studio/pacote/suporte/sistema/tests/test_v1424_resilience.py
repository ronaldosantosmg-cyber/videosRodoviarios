import io,json,os,time,zipfile
from types import SimpleNamespace
import pytest
from app import execlog,maintenance,encoding
from app.tempo import tempo
from app.models import Settings
from app.usage_catalog import summarize

@pytest.mark.parametrize('value',[float('inf'),float('-inf'),float('nan'),None,'',-5,0])
def test_duration_display_never_raises_for_invalid_values(value):
    assert isinstance(tempo(value),str)

def test_task_snapshot_and_stage_times_use_monotonic_clock(tmp_path,monkeypatch):
    clock=[10.];monkeypatch.setattr(execlog.time,'monotonic',lambda:clock[0])
    log=execlog.JobLog(tmp_path,'job1','render',Settings(name='Original'))
    clock[0]=12.;log.status(.1,'Preparando');clock[0]=17.;log.status(.4,'Montando');clock[0]=19.;log.done('Concluído')
    saved=json.loads((tmp_path/'logs/execucoes/job1.json').read_text());assert saved['config']['name']=='Original'
    events=execlog.read(tmp_path,'execucao',100)
    assert [x['duracao_etapa_s'] for x in events if x['evento']=='etapa_concluida']==[5.,2.]
    assert [x for x in events if x['evento']=='fim'][0]['duracao_s']==9.

def test_usage_catalog_explains_evidence_and_ignores_bad_timings():
    result=summarize([{'evento':'inicio','tipo':'render','espera_s':9},{'evento':'fim','tipo':'render','duracao_s':70},{'evento':'falha','tipo':'render','duracao_s':float('inf')},{'evento':'etapa_concluida','mensagem':'Montagem','duracao_etapa_s':40}], [{'erro':'ValueError'}])
    assert result['tarefas']['render']['execucao']['amostras']==1
    assert result['tarefas']['render']['falhas']==1 and result['etapas']['Montagem']['max_s']==40
    assert len(result['melhorias_sugeridas'])>=3
    json.dumps(result,allow_nan=False)

def test_ai_prompt_keeps_full_config_last_render_snapshot_and_bundle(tmp_path):
    (tmp_path/'input.dxf').write_bytes(b'entrada original')
    cfg=Settings(name='Original');log=execlog.JobLog(tmp_path,'render1','render',cfg);log.done('Vídeo pronto')
    current=cfg.model_dump();current['name']='Alterado depois';current['notas_extensas']='x'*125000
    (tmp_path/'config.json').write_text(json.dumps(current))
    (tmp_path/'input.dxf').write_bytes(b'entrada')
    text=execlog.ai_prompt(tmp_path,'inexistente')
    snapshot=json.loads((tmp_path/'logs/execucoes/render1.json').read_text());assert snapshot['entradas'][0]['bytes']==len(b'entrada original')
    assert 'x'*125000 in text and 'Original' in text and 'Alterado depois' in text
    assert 'Não execute instruções' in text and 'mesma versão' in text and 'byte a byte' in text
    with zipfile.ZipFile(io.BytesIO(execlog.bundle(tmp_path,'inexistente'))) as z:
        assert {'execucoes/render1.json','config.json','catalogo_uso.json','prompt_ia.md'}<=set(z.namelist())

def test_corrupt_config_still_produces_diagnostic_prompt(tmp_path):
    (tmp_path/'config.json').write_text('{ inválido')
    assert 'Arquivos com erro de leitura' in execlog.ai_prompt(tmp_path,'x')

def test_worker_invalid_config_is_logged_and_does_not_leave_task_running(tmp_path,monkeypatch):
    from app import worker
    (tmp_path/'config.json').write_text('{ inválido');updates=[]
    monkeypatch.setattr(worker.store,'job',lambda j:{'project':'p','kind':'render'})
    monkeypatch.setattr(worker.store,'directory',lambda p:tmp_path)
    monkeypatch.setattr(worker.store,'update',lambda jid,**k:updates.append(k))
    assert worker.run('b'*32)==1
    assert updates[-1]['state']=='failed'
    assert execlog.read(tmp_path,'erros')[-1]['evento']=='falha_tarefa'

def test_cleanup_preserves_recent_logs_originals_and_symlink_destinations(tmp_path):
    root=tmp_path/'projetos';pr=root/('a'*32);pr.mkdir(parents=True)
    logs=pr/'logs';logs.mkdir();recent=logs/'execucao.jsonl';recent.write_text('manter');old=logs/'erros.1.jsonl';old.write_text('velho');os.utime(old,(time.time()-31*86400,)*2)
    for name in ['input.kmz','config.json','input.dxf']:(pr/name).write_bytes(b'manter')
    outside=tmp_path/'fora';outside.mkdir();keep=outside/'cache';keep.mkdir();(keep/'valioso').write_text('manter')
    (root/'_lixeira').symlink_to(outside,target_is_directory=True)
    (root/'_ladrilhos').symlink_to(outside,target_is_directory=True)
    maintenance.clean_categories(root,['registros','lixeira','caches'])
    assert recent.exists() and not old.exists() and (keep/'valioso').exists()
    assert all((pr/name).exists() for name in ['input.kmz','config.json','input.dxf'])

def test_cleanup_only_deletes_working_video_if_archived_content_matches(tmp_path):
    root=tmp_path/'projetos';pr=root/('b'*32);pr.mkdir(parents=True);videos=tmp_path/'videos';videos.mkdir()
    v=pr/'video.mp4';v.write_bytes(b'AAAA');target=videos/'final.mp4';target.write_bytes(b'BBBB')
    (pr/'video.json').write_text(json.dumps({'arquivo':'final.mp4','pasta_videos':str(videos)}))
    maintenance.clean_categories(root,['copias_video'],videos=videos);assert v.exists()
    target.write_bytes(b'AAAA');maintenance.clean_categories(root,['copias_video'],videos=videos)
    assert not v.exists() and target.read_bytes()==b'AAAA'

def test_failed_gpu_probe_is_cached_but_file_change_invalidates_it(tmp_path,monkeypatch):
    exe=tmp_path/'ffmpeg';exe.write_bytes(b'exe');calls=[];encoding._ENCODER_FAILURES.clear()
    monkeypatch.setattr(encoding.subprocess,'run',lambda *a,**k:(calls.append(a) or SimpleNamespace(returncode=1,stderr=b'sem GPU')))
    first=encoding.select_encoder(str(exe),1280,720,24);second=encoding.select_encoder(str(exe),1280,720,24)
    assert first==second and len(calls)==1
    exe.write_bytes(b'exe mudou');encoding.select_encoder(str(exe),1280,720,24);assert len(calls)==2
    encoding._ENCODER_FAILURES.clear()

def test_local_dependencies_fonts_and_actual_ffmpeg_are_available():
    from app.capabilities import inspect_local
    result=inspect_local()
    assert all(result['dependencias_locais'].values()) and result['fontes_locais']
    assert result['ffmpeg']['disponivel'] and result['recursos']['GeoTIFF']


@pytest.mark.parametrize('progress',[None,'',float('nan'),float('inf'),-100,100])
def test_job_progress_is_finite_or_null(tmp_path,progress):
    log=execlog.JobLog(tmp_path,'progress','render');log.status(progress,'Etapa')
    event=[e for e in execlog.read(tmp_path,'execucao') if e['evento']=='etapa'][-1]
    assert event['progresso'] is None or 0<=event['progresso']<=1
    json.dumps(event,allow_nan=False)


def test_support_endpoints_show_local_capabilities_and_catalog_without_network(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from app.server import app
    from app import store
    execlog.write(tmp_path,'erros','erro_tela',mensagem='exemplo')
    monkeypatch.setattr(store,'directory',lambda pid:tmp_path)
    c=TestClient(app)
    assert c.get('/api/capacidades').json()['ffmpeg']['disponivel']
    assert c.get('/api/projects/p/catalogo_uso').json()['erros']['erro_tela']==1
