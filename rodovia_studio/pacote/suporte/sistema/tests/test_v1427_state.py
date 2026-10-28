"""Concorrência, recuperação e invalidação independente de qualquer projeto."""
import json
import pytest
from app.models import Settings
from app import store,project_state as ps,dependencies as dep,artifacts

@pytest.fixture
def project(tmp_path):
    d=tmp_path/'projeto';d.mkdir();store.write_json(d/'config.json',Settings().model_dump());return d

def test_compare_and_swap_preserves_last_committed_configuration(project):
    d=project;first=ps.read_config(d);key=ps.revision(first)
    second={**first,'name':'Nova identificação'};ps.save_config(d,second,key)
    with pytest.raises(ps.Conflict):ps.save_config(d,{**first,'name':'Cliente atrasado'},key)
    assert ps.read_config(d)==second
    assert len(ps.history(d))==2

def test_corruption_recovers_last_good_and_archives_bad_bytes(project):
    d=project;good=ps.read_config(d);(d/'config.json').write_text('{incompleto')
    assert ps.read_config(d)==good
    assert len(list((d/'.estado/corrompidos').glob('*.json')))==1
    assert ps.state(d)['recovery']['revision']==ps.revision(good)

def test_history_restore_uses_revision_guard(project):
    d=project;old=ps.read_config(d);old_key=ps.revision(old)
    new={**old,'name':'Alterado'};ps.save_config(d,new,old_key)
    ps.restore(d,old_key,ps.revision(new));assert ps.read_config(d)==old
    with pytest.raises(ps.Conflict):ps.restore(d,old_key,ps.revision(new))

def test_domains_do_not_recalculate_routes_for_camera_or_texture(project):
    d=project;s=ps.read_config(d);a=dep.revisions(d,s)
    b=dep.revisions(d,{**s,'texture_style':'realistic' if s['texture_style']!='realistic' else 'artistico'})
    assert a['traffic']==b['traffic'] and a['editor']==b['editor'] and a['scene3d']!=b['scene3d']
    c=dep.revisions(d,{**s,'traffic_speed_kmh':s['traffic_speed_kmh']+5})
    assert a['geometry']==c['geometry'] and a['traffic']!=c['traffic']
    c=dep.revisions(d,{**s,'preview_time_s':1})
    assert a['video']==c['video'] and a['preview']!=c['preview']

def test_old_job_and_file_replacement_cannot_be_advertised_current(project):
    d=project;s=ps.read_config(d);ticket=artifacts.begin(d,'job','analyze',s)
    for name in ('analysis.json','editor.json','vectors.json'):store.write_json(d/name,{'job':'job'})
    artifacts.finish(d,ticket);assert artifacts.status(d)['editor']['state']=='ready'
    ps.save_config(d,{**s,'lane_width_m':s['lane_width_m']+.1})
    assert artifacts.status(d)['editor']['state']=='stale'
    ps.save_config(d,s);store.write_json(d/'editor.json',{'outro':'resultado'})
    assert artifacts.status(d)['editor']['state']=='stale'

def test_failed_import_restores_inputs_config_and_metadata(project,monkeypatch):
    d=project;(d/'input.dxf').write_bytes(b'original');store.write_json(d/'arquivos.json',{'dxf':{'name':'original'}})
    before={n:(d/n).read_bytes() for n in ('input.dxf','config.json','arquivos.json')}
    source=d/'upload';source.write_bytes(b'novo');original=ps._write
    def fail(path,data):
        if path==d/'arquivos.json':raise OSError('falha de disco simulada')
        return original(path,data)
    monkeypatch.setattr(ps,'_write',fail)
    with pytest.raises(OSError):ps.import_files(d,{'input.dxf':source},{'dxf':{'name':'novo'}})
    assert all((d/n).read_bytes()==v for n,v in before.items())
    assert not (d/'.estado/importacao_pendente.json').exists()

def test_import_is_recovered_after_process_stops_between_file_changes(project):
    d=project;(d/'input.dxf').write_bytes(b'original');base=d/'.estado';identity='a'*32;folder=base/'importacoes'/identity;folder.mkdir(parents=True)
    (folder/'input.dxf').write_bytes(b'original')
    store.write_json(base/'importacao_pendente.json',{'id':identity,'state':'prepared','files':[{'name':'input.dxf','existed':True,'sha256':ps._file_hash(folder/'input.dxf')}]})
    (d/'input.dxf').write_bytes(b'interrompido');ps.read_config(d)
    assert (d/'input.dxf').read_bytes()==b'original'


def _competing_writer(directory,name,barrier,queue):
    data=ps.read_config(directory);key=ps.revision(data);data['name']=name;barrier.wait(timeout=10)
    try:ps.save_config(directory,data,key);queue.put('saved')
    except ps.Conflict:queue.put('conflict')


def test_two_processes_cannot_silently_overwrite_each_other(project):
    import multiprocessing
    ctx=multiprocessing.get_context('spawn');barrier=ctx.Barrier(2);queue=ctx.Queue()
    children=[ctx.Process(target=_competing_writer,args=(project,name,barrier,queue)) for name in ('Primeiro','Segundo')]
    for child in children:child.start()
    try:
        outcomes=[queue.get(timeout=20) for _ in children]
        assert sorted(outcomes)==['conflict','saved']
        for child in children:child.join(timeout=10);assert child.exitcode==0
        assert ps.read_config(project)['name'] in ('Primeiro','Segundo')
    finally:
        for child in children:
            if child.is_alive():child.terminate();child.join()


@pytest.mark.parametrize('failure',['config.json','config_atual.json'])
def test_interrupted_configuration_commit_recovers_a_complete_revision(project,monkeypatch,failure):
    d=project;old=ps.read_config(d);new={**old,'name':'Gravação interrompida'};original=ps._write
    def fail(path,data):
        if path.name==failure:raise OSError('interrupção simulada')
        return original(path,data)
    monkeypatch.setattr(ps,'_write',fail)
    with pytest.raises(OSError):ps.save_config(d,new)
    monkeypatch.setattr(ps,'_write',original)
    assert ps.read_config(d)==(old if failure=='config.json' else new)
    assert not (d/'.estado/config_pendente.json').exists()


def test_analysis_reuses_valid_results_after_a_presentation_change(project,monkeypatch):
    from app import worker
    from app.execlog import JobLog
    d=project;s=Settings.model_validate(ps.read_config(d));ticket=artifacts.begin(d,'previous','analyze',s)
    for name in ('analysis.json','editor.json','vectors.json'):store.write_json(d/name,{'result':'preservado'})
    artifacts.finish(d,ticket);ps.save_config(d,{**s.model_dump(),'texture_style':'realistic'})
    before={p.name:p.stat().st_mtime_ns for p in d.glob('*.json') if p.name!='config.json'}
    monkeypatch.setattr(store,'directory',lambda _:d)
    monkeypatch.setattr(store,'job',lambda _:{'project':'p','kind':'analyze','state':'running'})
    outcomes=[];monkeypatch.setattr(store,'update',lambda *a,**kw:outcomes.append(kw))
    monkeypatch.setattr(worker,'analyze',lambda *a,**kw:pytest.fail('Não deve recalcular a geometria para alterar textura.'))
    assert worker.run('a'*32)==0
    assert any(o.get('state')=='done' for o in outcomes)
    assert all((d/n).stat().st_mtime_ns==stamp for n,stamp in before.items())
