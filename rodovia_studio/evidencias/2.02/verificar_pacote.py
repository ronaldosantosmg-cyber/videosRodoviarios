import sys,tempfile,zipfile,shutil,hashlib,json,os
from pathlib import Path
root=Path(__file__).resolve().parents[3];system=root/'rodovia_studio/pacote/suporte/sistema'
sys.path.insert(0,str(system));import atualizador as U
old=root/'atualizacoes/RodoviaStudio_2_01_atualizacao.zip';new=root/'atualizacoes/RodoviaStudio_2_02_atualizacao.zip'
assert new.is_file();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='rodovia_pacote_real_') as temporary:
    base=Path(temporary);previous=base/'anterior';previous.mkdir()
    with zipfile.ZipFile(old) as z:
        assert z.testzip() is None
        z.extractall(previous)
    installation=base/'Instalação em outra pasta ç';installation.mkdir();shutil.copytree(previous/'pacote',installation,dirs_exist_ok=True)
    (installation/'projetos').mkdir()
    U.apply(previous/'pacote',installation,say=lambda *a:None,check_running=False)
    assert U.installed_version(installation)=='2.01'
    program=installation/'sistema/programa';index=sha(program/'app/index.html');prior_hashes={f.relative_to(program).as_posix():sha(f) for f in program.rglob('*') if f.is_file()}
    data={'projetos/'+('a'*32)+'/config.json':'{"name":"Projeto preservado ç","schema_version":31}',
          'projetos/'+('a'*32)+'/input.kmz':'Fonte KMZ preservada',
          'projetos/_base_imagens/cache/foto.tif':'Cache GeoTIFF persistente preservado',
          'videos/video-anterior.mp4':'Conteúdo do vídeo anterior preservado'}
    for name,text in data.items():
        f=installation/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf-8')
    hashes={name:sha(installation/name) for name in data}
    updates=installation/'atualizacoes';updates.mkdir(exist_ok=True);shutil.copy2(new,updates/new.name)
    result=U.search_and_apply(installation,say=lambda *a:None,check_running=False)
    assert U.installed_version(installation)=='2.02'
    assert (program/'app/index.html').is_file() and (program/'app/js/89_vista_previa_sessoes.js').is_file()
    updated_scripts=['app/assisted_execution.py','app/flow_diagnostics.py','app/flow_reconstruction.py','app/flow_recovery.py','app/traffic.py','app/js/53_interface_estudos.js','app/js/70_correcao_fluxos.js','app/js/79_execucao_protecao.js']
    with zipfile.ZipFile(new) as archive:
        for name in updated_scripts:
            assert sha(program/name)==hashlib.sha256(archive.read('pacote/suporte/sistema/'+name)).hexdigest()
    assert all(sha(installation/name)==digest for name,digest in hashes.items())
    assert U.rollback_candidates(installation) and (updates/'aplicadas'/new.name).is_file()
    U.restore_previous(installation,say=lambda *a:None,check_running=False)
    assert U.installed_version(installation)=='2.01' and sha(program/'app/index.html')==index
    assert all(sha(installation/name)==digest for name,digest in hashes.items())
    assert all(sha(program/name)==digest for name,digest in prior_hashes.items())
    output=dict(package=new.name,sha256=sha(new),apply_version='2.02',rollback_version='2.01',preserved_files=list(data),index_restored=True,all_previous_program_hashes_restored=True,zip_archived=True,updated_scripts=updated_scripts,platform='Linux; ensaio isolado, não Windows nativo',data_scope='Fixtures de preservação de bytes; MP4s reais foram conferidos nos testes de renderização.',controlled_shutdown='Protocolo do servidor verificado separadamente por test_v142_runtime',native_windows=False)
    target=root/'rodovia_studio/evidencias/2.02/pacote-real.json';target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(output,ensure_ascii=False))
