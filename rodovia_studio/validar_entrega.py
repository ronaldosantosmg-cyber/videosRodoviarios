#!/usr/bin/env python3
"""Valida a revisão e só depois produz o ZIP em atualizacoes/. Sem publicação."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import time
import signal
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validacao_incremental import product_digest,test_hashes,plan as resume_plan,merge as merge_reports

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT/'pacote'
SYSTEM=PACKAGE/'suporte/sistema'
EVIDENCE=ROOT/'evidencias'/json.loads((PACKAGE/'manifest.json').read_text())['version']
# Perfil de regressão 2.63: alterações e dependências diretas da base 2.62.
# A auditoria histórica ampla é registrada à parte e não aprova esta revisão.
TESTS=['tests/test_v263_backend.py', 'tests/test_v263_ui.py', 'tests/test_v135.py', 'tests/test_v142_update.py', 'tests/test_v1428_long_paths.py', 'tests/test_v1427_state.py', 'tests/test_v1427_state_ui.py', 'tests/test_v1429_layer_reading.py', 'tests/test_v1425_scene3d.py', 'tests/test_v1425_live_3d.py', 'tests/test_v1425_capture3d.py', 'tests/test_v1424_flow_limit.py', 'tests/test_v14231_flow_nodes.py', 'tests/test_v14230_flow_rules.py', 'tests/test_v14229_shoulder_probe.py', 'tests/test_v14248_pista_dupla_mesmo_sentido.py', 'tests/test_v14249_contorno_hachura.py', 'tests/test_v14264_sentido_previa_secao.py', 'tests/test_v14265_uniformidade_sentido.py', 'tests/test_v14266_setas_uniformes_navegador.py', 'tests/test_v14267_secao_segue_km.py', 'tests/test_v14268_apresentacao_segue_km.py', 'tests/test_v14270_eixo_nao_paralelo.py', 'tests/test_v14271_fluxo_tela_completo.py', 'tests/test_v14272_cobertura_secoes.py', 'tests/test_v14273_varias_secoes_no_eixo.py', 'tests/test_v14274_textura_ao_vivo.py', 'tests/test_v14275_frota_realista.py', 'tests/test_v14278_articulado.py', 'tests/test_v14279_atmosfera_foto.py', 'tests/test_v14280_sprites_exatidao.py', 'tests/test_v14281_relevo_texturas.py', 'tests/test_v14282_passarela_tinta.py', 'tests/test_v14283_transicao_secoes.py', 'tests/test_v14284_dialogo_secoes.py', 'tests/test_v14288_agua_blocos.py', 'tests/test_v14289_mascara_roi.py', 'tests/test_v14290_hausdorff_rapido.py', 'tests/test_v14291_cache_analise.py', 'tests/test_v14292_varredura_rapida.py', 'tests/test_v14293_legenda_terreno.py', 'tests/test_v14294_redimensionar_sem_balancar.py']
DESELECT=[]
CRITICAL=[
 'tests/test_v268_zebrados_dxf.py','tests/test_v268_zebrados_ui.py','tests/test_v1429_layer_reading.py','tests/test_v115.py::test_crosswalk_hatch_signs_and_clean_areas',
 'tests/test_v267_zebrados.py','tests/test_v267_zebrados_ui.py',
 'tests/test_v264_presentation.py','tests/test_v264_ui.py','tests/test_v265_dxf_advance.py',
 'tests/test_v14281_relevo_texturas.py','tests/test_v14282_passarela_tinta.py',
 'tests/test_v263_ui.py','tests/test_v142_update.py',
 'tests/test_v263_backend.py::test_vehicle_body_must_be_entirely_on_pavement_without_changing_routes',
 'tests/test_v263_backend.py::test_empty_pavement_hides_vehicle_including_classic_mode',
 'tests/test_v263_backend.py::test_per_position_uses_true_stationing_and_does_not_clip_outside_to_endpoint',
 'tests/test_v263_backend.py::test_per_coordinates_and_off_stationing_are_explicit',
 'tests/test_v263_backend.py::test_import_preview_api_uses_current_draft_and_preserves_saved_config',
 'tests/test_v14231_flow_nodes.py::test_real_typed_y_junction_preserves_connections_and_conservation',
 'tests/test_v14294_redimensionar_sem_balancar.py',
 '../../../verificacao/test_gate_curto.py',
]




def run(args,env,log):
    result=subprocess.run([str(a) for a in args],cwd=SYSTEM,env=env,stdout=log,stderr=subprocess.STDOUT)
    log.flush()
    if result.returncode:raise RuntimeError(f'Verificação falhou: {args[0]}. Consulte {log.name}.')


def test_process(args,env,log,limit):
    proc=subprocess.Popen([str(a) for a in args],cwd=SYSTEM,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=os.name!='nt')
    try:return proc.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        if os.name!='nt':os.killpg(proc.pid,signal.SIGTERM)
        else:proc.terminate()
        try:proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if os.name!='nt':os.killpg(proc.pid,signal.SIGKILL)
            else:proc.kill()
            proc.wait()
        raise RuntimeError(f'Testes excederam {limit} s; execução encerrada e pacote bloqueado. Consulte a última etapa no log.')
    finally:log.flush()


def digest():
    h=hashlib.sha256()
    for f in sorted(PACKAGE.rglob('*')):
        if f.is_file() and not any(x in f.parts for x in ['__pycache__','.pytest_cache']):
            h.update(f.relative_to(PACKAGE).as_posix().encode());h.update(f.read_bytes())
    return h.hexdigest()


def native_checks(env,log):
    env=dict(env,DISPLAY=os.environ.get("RODOVIA_SPLASH_DISPLAY",":91"))
    mono_root=Path(os.environ['MONO_ROOT']) if os.environ.get('MONO_ROOT') else None
    mono=mono_root/'usr/bin/mono-sgen' if mono_root else shutil.which('mono')
    compiler=mono_root/'usr/lib/mono/4.5/mcs.exe' if mono_root else shutil.which('mcs')
    libs=Path(os.environ.get('WEBVIEW2_LIB',''))
    if not mono or not compiler or not (libs/'Microsoft.Web.WebView2.Core.dll').is_file():
        raise RuntimeError('Faltam Mono e DLLs WebView2 para validar o iniciador. Nenhum pacote foi gerado.')
    if mono_root:
        env.update(MONO_PATH=str(mono_root/'usr/lib/mono/4.5'),MONO_CFG_DIR=str(mono_root/'etc'),LD_LIBRARY_PATH=str(mono_root/'usr/lib')+':'+str(mono_root/'usr/lib/x86_64-linux-gnu'))
    cmd=[mono,compiler] if mono_root else [compiler]
    common=['-r:System.Windows.Forms','-r:System.Drawing']
    with tempfile.TemporaryDirectory(prefix='rs_compile_') as tmp:
        tmp=Path(tmp)
        run(cmd+common+['-define:WEBVIEW2',f'-r:{libs/"Microsoft.Web.WebView2.Core.dll"}',f'-r:{libs/"Microsoft.Web.WebView2.WinForms.dll"}',f'-out:{tmp/"RodoviaStudio.exe"}','iniciador/RodoviaStudio.cs'],env,log)
        run(cmd+common+['-main:SplashValidation',f'-out:{tmp/"SplashValidation.exe"}','iniciador/RodoviaStudio.cs',ROOT/'verificacao/SplashValidation.cs'],env,log)
        from PIL import Image
        # A arte original é preservada; Mono exige um ICO BMP alinhado em 32 px.
        Image.open(SYSTEM/'rodovia.ico').convert('RGB').save(tmp/'logo.ico',format='ICO',sizes=[(32,32)],bitmap_format='bmp')
        xvfb=mono_root/'usr/bin/xvfb-run' if mono_root else shutil.which('xvfb-run')
        if not xvfb:raise RuntimeError('Xvfb é necessário para validar o splash.')
        if mono_root:env['PATH']=str(mono_root/'usr/bin')+os.pathsep+env.get('PATH','')
        run([xvfb,'-a','-e',EVIDENCE/'xvfb.log',mono,tmp/'SplashValidation.exe',tmp/'logo.ico',EVIDENCE,json.loads((PACKAGE/'manifest.json').read_text())['version']],env,log)


def main():
    global EVIDENCE
    started=time.perf_counter()
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=1,choices=range(1,5),help='Processos de teste isolados, com os mesmos testes obrigatórios.');parser.add_argument('--retomar',default='',help='Retoma relatório anterior do mesmo produto; repete módulos alterados, dependentes e falhas.');parser.add_argument('--evidencias',default='',help='Subpasta desta tentativa; preserva relatórios anteriores.');parser.add_argument('--gerar',action='store_true');parser.add_argument('--amplo',action='store_true',help='Regressão ampliada; automática se o núcleo ou um contrato sensível mudar.');parser.add_argument('--rapido',action='store_true',help='Diagnóstico curto; não autoriza gerar pacote.');args=parser.parse_args()
    if args.evidencias:
        if not args.evidencias.replace('-','').replace('_','').isalnum():parser.error('Nome de pasta de evidências inválido.')
        EVIDENCE=EVIDENCE/args.evidencias
    if args.rapido and args.gerar:parser.error('--rapido não pode gerar pacote; execute a validação completa.')
    from gate_profiles import assess
    risk=assess(ROOT.parent,SYSTEM)
    broad=args.amplo or risk['requires_broad']
    selected=list(dict.fromkeys(TESTS+CRITICAL)) if broad else CRITICAL
    if args.rapido:
        EVIDENCE=EVIDENCE/'diagnostico_rapido'
        selected=['tests/test_v14210_flow_tools.py','tests/test_v14210_engineering_assets.py','tests/test_v14210_flow_recovery.py','tests/test_v1429_layer_reading.py','tests/test_v1429_layers_ui.py','tests/test_v1429_route_recovery.py','tests/test_v1429_mouse.py','tests/test_v1429_project_imagery.py']
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,CHROMIUM='/usr/bin/chromium',PYTHONPYCACHEPREFIX=str(ROOT.parent.parent/'.cache/pycache'),XDG_CACHE_HOME=str(ROOT.parent.parent/'.cache'),VISUAL_ARTIFACTS=str(EVIDENCE),RODOVIA_DATA=tempfile.mkdtemp(prefix='rodovia_gate_data_'))
    # Chromium headless/SwiftShader falha se herdar o DISPLAY do teste Mono.
    env.pop('DISPLAY',None)
    for name in ['projetos','videos','dados']:
        if (PACKAGE/name).exists():raise RuntimeError(f'Dados locais não devem integrar a entrega: {name}')
    initial=digest();report=EVIDENCE/'pytest-resultados.xml'
    if args.retomar and Path(args.retomar).resolve()==EVIDENCE.resolve():raise RuntimeError('Use outra subpasta para preservar a execução de origem.')
    report.unlink(missing_ok=True)
    (EVIDENCE/'perfil.json').write_text(json.dumps({'profile':'amplo' if broad else 'curto_por_risco','risk':risk,'limit_seconds':900 if broad else 180},ensure_ascii=False,indent=2)+'\n')
    origin={'product_sha256':product_digest(PACKAGE),'package_sha256':initial,'tests':test_hashes(SYSTEM),'selected':selected}
    (EVIDENCE/'origem.json').write_text(json.dumps(origin,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (EVIDENCE/'validacao.log').open('w',encoding='utf-8') as log:
        run([sys.executable,'-m','pip','check'],env,log)
        run([sys.executable,'-m','compileall','-q','app','tests','atualizador.py','run.py'],env,log)
        node=shutil.which('node')
        if not node:raise RuntimeError('Node é necessário para validar JavaScript.')
        for f in sorted((SYSTEM/'app/js').glob('*.js'))+sorted((SYSTEM/'app/webgl').glob('*.mjs'))+sorted((SYSTEM/'app/vendor/three').rglob('*.js')):run([node,'--check',f],env,log)
        # Coleta todas as regressões numa execução; qualquer falha continua bloqueando o ZIP.
        parallel=['-n',str(args.workers),'--dist','loadfile'] if args.workers>1 else []
        state=resume_plan(PACKAGE,SYSTEM,selected,args.retomar,env,log) if args.retomar else None
        if state:
            inherited={}
            for artifact in Path(args.retomar).iterdir():
                if artifact.is_file() and artifact.suffix in {'.png','.json'} and artifact.name not in {'origem.json','resultado.json','retomada.json','evidencias_reutilizadas.json'}:
                    shutil.copy2(artifact,EVIDENCE/artifact.name)
                    inherited[artifact.name]=hashlib.sha256(artifact.read_bytes()).hexdigest()
            (EVIDENCE/'evidencias_reutilizadas.json').write_text(json.dumps({'origin':state['origin'],'product_sha256':state['product_sha256'],'files':inherited,'scope':'Artefatos do mesmo produto; testes repetidos substituem suas saídas. A aprovação depende do relatório final, não da presença de imagens.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        arguments=state['arguments'] if state else selected
        fresh=EVIDENCE/'pytest-reexecutados.xml' if state else report
        if arguments:
            result_code=test_process([sys.executable,'-m','pytest','-v','-p','no:cacheprovider',*parallel,'--durations=10',*arguments,*[item for case in DESELECT for item in ['--deselect',case]],f'--junitxml={fresh}'],env,log,900 if broad else 180)
            if not fresh.exists():raise RuntimeError('Testes não produziram relatório; pacote bloqueado.')
        if state:
            merge_reports(state,fresh if arguments else None,report)
            if arguments and result_code:raise RuntimeError('Execução de testes incompleta; pacote bloqueado.')
        if not state and result_code:raise RuntimeError('Há falhas na suíte completa; consulte o relatório. Nenhum ZIP gerado.')
        suites=ET.parse(report).getroot().findall('.//testsuite')
        counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
        if not counts['tests'] or any(counts[k] for k in ['failures','errors','skipped']):raise RuntimeError('Há falhas, erros, testes ausentes ou ignorados. Pacote bloqueado.')
        if not args.rapido:native_checks(env,log)
    if digest()!=initial:raise RuntimeError('Os fontes mudaram durante a validação. Execute novamente.')
    if args.rapido:
        (EVIDENCE/'resultado.json').write_text(json.dumps({'mode':'diagnostico_rapido','release_approved':False,'pytest':counts},ensure_ascii=False,indent=2)+'\n')
        print(f"Diagnóstico rápido aprovado: {counts['tests']} testes. Entrega exige validação completa.");return
    metadata={'version':json.loads((PACKAGE/'manifest.json').read_text())['version'],'source_sha256':initial,'pytest':counts,'splash':'Mono/Xvfb; versão, fabricante e animação','launcher':'C# compilado com e sem WEBVIEW2','platform':'Linux, Python '+sys.version.split()[0],'windows_native_executed':False,'profile':'amplo' if broad else 'curto_por_risco','elapsed_s':round(time.perf_counter()-started,2)}
    (EVIDENCE/'resultado.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(f"Validação aprovada: {counts['tests']} testes; splash e compilação C# aprovados.")
    if not args.gerar:return
    spec=importlib.util.spec_from_file_location('rs_updater',SYSTEM/'atualizador.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    dest=ROOT.parent/'atualizacoes';dest.mkdir(exist_ok=True)
    output=dest/f'RodoviaStudio_{metadata["version"].replace(".","_")}_atualizacao.zip'
    if output.exists():raise RuntimeError('O pacote final já existe; preserve-o antes de gerar outra entrega.')
    with tempfile.TemporaryDirectory(prefix='rs_package_') as tmp:
        stage=Path(tmp)/'pacote';shutil.copytree(PACKAGE,stage,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','*.pyc','tests'))
        docs=stage/'suporte/documentacao';docs.mkdir(parents=True,exist_ok=True)
        for f in stage.glob('*.md'):
            if metadata['version'].replace('.','_') in f.name:f.replace(docs/f.name)
            elif f.name.startswith(('ATUALIZACAO_','AUDITORIA_')):f.unlink()
            else:f.replace(docs/f.name)
        evidence=stage/('suporte/documentacao/validacao_'+metadata['version'].replace('.','_'));evidence.mkdir(parents=True)
        for name in ['268_zebrado_dxf.png','268_zebrado_sentidos.png','267_zebrado_ui.png','267_zebrado_render.png','266_artistico_sem_contornos.png','266_contornos_opcionais.png','266_realista.png','266_ultra_realista.png','266_videos.json','266_ui_perfis.png','266_3d.png','266_frente_dxf.png','266_frente_sem_avanco.png','266_obra_concluida.png','pytest-resultados.xml','resultado.json','validacao.log','splash_142_1_a.png','splash_142_1_b.png']:
            shutil.copy2(EVIDENCE/name,evidence/name)
        for name in ['origem.json','retomada.json','evidencias_reutilizadas.json','pytest-reexecutados.xml','perfil.json']:
            if (EVIDENCE/name).is_file():shutil.copy2(EVIDENCE/name,evidence/name)
        if state:
            for name,target in [('origem.json','origem-anterior.json'),('pytest-resultados.xml','pytest-origem.xml')]:shutil.copy2(Path(args.retomar)/name,evidence/target)
        manifest=json.loads((stage/'manifest.json').read_text())
        manifest['files']={f.relative_to(stage).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(stage.rglob('*')) if f.is_file() and f!=stage/'manifest.json'}
        (stage/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        up.validate_package(stage)
        temp=output.with_suffix('.zip.tmp')
        try:
            with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
                for f in sorted(stage.rglob('*')):
                    if f.is_file():z.write(f,'pacote/'+f.relative_to(stage).as_posix())
            with zipfile.ZipFile(temp) as z:
                if z.testzip():raise RuntimeError('O ZIP não passou na verificação de integridade.')
            temp.replace(output)
        finally:temp.unlink(missing_ok=True)
    sha=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256.txt').write_text(f'{sha}  {output.name}\n')
    (dest/'canal_estavel.json').write_text(json.dumps({'app':'Rodovia Studio','version':metadata['version'],'filename':output.name,'sha256':sha},ensure_ascii=False,indent=2)+'\n')
    print(f'Pacote gerado: {output}\nSHA-256: {sha}')


if __name__=='__main__':main()
