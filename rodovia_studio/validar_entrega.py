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

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT/'pacote'
SYSTEM=PACKAGE/'suporte/sistema'
EVIDENCE=ROOT/'evidencias'/json.loads((PACKAGE/'manifest.json').read_text())['version']
TESTS=[
 'tests/test_v14224_assistance.py','tests/test_v14224_workspace.py',
 'tests/test_v14223_update_policy.py',
 'tests/test_v14222_reliability.py',
 'tests/test_v14221_simplification.py','tests/test_v14220_sections_materials.py','tests/test_v14219_reconstruction_curves_semantics.py',
 'tests/test_v14218_agents.py','tests/test_v14218_axis_policy.py','tests/test_v14218_scene_agents.py','tests/test_v14218_live_agents.py','tests/test_v14218_layers_ui.py',
 'tests/test_v14217_usability.py',
 'tests/test_v14216_flow_repair.py','tests/test_v14216_repair_live.py',
 'tests/test_v14215_view_retention.py',
 'tests/test_v14214_assistant.py','tests/test_v14214_panels_ui.py',
 'tests/test_v14213_continuity.py','tests/test_v14213_continuity_ui.py',
 'tests/test_v14212_modelagem.py','tests/test_v14212_traffic_safety.py',
 'tests/test_v14212_ui.py','tests/test_v14212_presentation.py',
 'tests/test_v14211_infrarail_icons.py',
 'tests/test_v14210_flow_recovery.py','tests/test_v14210_recovery_ui.py',
 'tests/test_v14210_flow_tools.py','tests/test_v14210_flow_edit_ui.py',
 'tests/test_v14210_engineering_assets.py','tests/test_v14210_assets_visual.py',
 'tests/test_v1429_project_imagery.py','tests/test_v1429_mouse.py',
 'tests/test_v1429_popup_calculation.py',
 'tests/test_v1429_layer_reading.py','tests/test_v1429_layers_ui.py',
 'tests/test_v1429_route_recovery.py',
 'tests/test_v1429_route_recovery_ui.py',
 'tests/test_v1428_long_paths.py',
 'tests/test_v1428_panels.py',
 'tests/test_v1428_menu_flow.py',
 'tests/test_v1427_state.py','tests/test_v1427_state_ui.py',
 'tests/test_v1426_transport.py','tests/test_v1426_transport_visual.py',
 'tests/test_v1426_import_capacity.py','tests/test_v1426_import_capacity_ui.py',
 'tests/test_v1425_scene3d.py','tests/test_v1425_fan_pruning.py',
 'tests/test_v1425_archive.py','tests/test_v1425_capture3d.py','tests/test_v1425_live_3d.py',
 'tests/test_v1424_resilience.py','tests/test_v1424_editing.py',
 'tests/test_v132.py::test_cleanup_categories','tests/test_v126.py::test_api_images_lines_sessions_and_logs',
 'tests/test_v1424_flow_limit.py','tests/test_v1424_flow_limit_ui.py',
 'tests/test_v1424_ribbon.py',
 'tests/test_v1423_motion.py','tests/test_v1423_toolbar.py','tests/test_v1423_video.py',
 'tests/test_v139.py','tests/test_v1404_traffic_sim.py','tests/test_v127.py::test_curve_envelope',
 'tests/test_v142_update.py','tests/test_v142_runtime.py','tests/test_v142_diagnostics.py',
 'tests/test_v142_visual.py','tests/test_v1422_layout.py','tests/test_v142_live_ui.py','tests/test_v141_technical.py',
 'tests/test_v1410_final.py','tests/test_v1405_robust_traffic.py','tests/test_v1407_imagery_cache.py',
 'tests/test_v1408.py','tests/test_v1409_functionality.py','tests/test_v1407_visual.py',
 'tests/test_v1408_visual.py','tests/test_v1409_visual.py','tests/test_v1410_visual.py',
 'tests/test_workflow.py::test_video_encoder','tests/test_workflow.py::test_api_complete',
]


def run(args,env,log):
    result=subprocess.run([str(a) for a in args],cwd=SYSTEM,env=env,stdout=log,stderr=subprocess.STDOUT)
    log.flush()
    if result.returncode:raise RuntimeError(f'Verificação falhou: {args[0]}. Consulte {log.name}.')


def digest():
    h=hashlib.sha256()
    for f in sorted(PACKAGE.rglob('*')):
        if f.is_file() and not any(x in f.parts for x in ['__pycache__','.pytest_cache']):
            h.update(f.relative_to(PACKAGE).as_posix().encode());h.update(f.read_bytes())
    return h.hexdigest()


def native_checks(env,log):
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
        run(cmd+common+['-main:SplashValidation',f'-out:{tmp/"SplashValidation.exe"}','iniciador/RodoviaStudio.cs','tests/SplashValidation.cs'],env,log)
        from PIL import Image
        # A arte original é preservada; Mono exige um ICO BMP alinhado em 32 px.
        Image.open(SYSTEM/'rodovia.ico').convert('RGB').save(tmp/'logo.ico',format='ICO',sizes=[(32,32)],bitmap_format='bmp')
        run([mono,tmp/'SplashValidation.exe',tmp/'logo.ico',EVIDENCE],env,log)


def main():
    global EVIDENCE
    parser=argparse.ArgumentParser();parser.add_argument('--gerar',action='store_true');parser.add_argument('--rapido',action='store_true',help='Diagnóstico curto; não autoriza gerar pacote.');args=parser.parse_args()
    if args.rapido and args.gerar:parser.error('--rapido não pode gerar pacote; execute a validação completa.')
    selected=TESTS
    if args.rapido:
        EVIDENCE=EVIDENCE/'diagnostico_rapido'
        selected=['tests/test_v14210_flow_tools.py','tests/test_v14210_engineering_assets.py','tests/test_v14210_flow_recovery.py','tests/test_v1429_layer_reading.py','tests/test_v1429_layers_ui.py','tests/test_v1429_route_recovery.py','tests/test_v1429_mouse.py','tests/test_v1429_project_imagery.py']
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONPYCACHEPREFIX=str(ROOT.parent.parent/'.cache/pycache'),XDG_CACHE_HOME=str(ROOT.parent.parent/'.cache'),VISUAL_ARTIFACTS=str(EVIDENCE),RODOVIA_DATA=tempfile.mkdtemp(prefix='rodovia_gate_data_'))
    for name in ['projetos','videos','dados']:
        if (PACKAGE/name).exists():raise RuntimeError(f'Dados locais não devem integrar a entrega: {name}')
    initial=digest();report=EVIDENCE/'pytest-resultados.xml';report.unlink(missing_ok=True)
    with (EVIDENCE/'validacao.log').open('w',encoding='utf-8') as log:
        run([sys.executable,'-m','pip','check'],env,log)
        run([sys.executable,'-m','compileall','-q','app','tests','atualizador.py','run.py'],env,log)
        node=shutil.which('node')
        if not node:raise RuntimeError('Node é necessário para validar JavaScript.')
        for f in sorted((SYSTEM/'app/js').glob('*.js'))+sorted((SYSTEM/'app/webgl').glob('*.mjs'))+sorted((SYSTEM/'app/vendor/three').rglob('*.js')):run([node,'--check',f],env,log)
        # Coleta todas as regressões numa execução; qualquer falha continua bloqueando o ZIP.
        run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*selected,f'--junitxml={report}'],env,log)
        suites=ET.parse(report).getroot().findall('.//testsuite')
        counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
        if not counts['tests'] or any(counts[k] for k in ['failures','errors','skipped']):raise RuntimeError('Há falhas, erros, testes ausentes ou ignorados. Pacote bloqueado.')
        if not args.rapido:native_checks(env,log)
    if digest()!=initial:raise RuntimeError('Os fontes mudaram durante a validação. Execute novamente.')
    if args.rapido:
        (EVIDENCE/'resultado.json').write_text(json.dumps({'mode':'diagnostico_rapido','release_approved':False,'pytest':counts},ensure_ascii=False,indent=2)+'\n')
        print(f"Diagnóstico rápido aprovado: {counts['tests']} testes. Entrega exige validação completa.");return
    metadata={'version':json.loads((PACKAGE/'manifest.json').read_text())['version'],'source_sha256':initial,'pytest':counts,'splash':'Mono/Xvfb; versão, fabricante e animação','launcher':'C# compilado com e sem WEBVIEW2','platform':'Linux, Python '+sys.version.split()[0],'windows_native_executed':False}
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
        for name in ['14212_07_imagem_sem_dxf.png','14212_01_contornos_sugeridos_grupos.png','14212_02_contornos_persistentes.png','14212_03_secoes_assimetricas.png','14212_04_janela_salvar_descartar.png','14212_05_mascaras_texturas_2d.png','14212_06_edificacoes_3d_pisca_alerta.png','14211_01_icones_barra_tecnica.png','14211_02_pacote_32_simbolos.png','14211_03_catalogo_com_simbolos.png','14210_04_texturas_interferencias.png','14210_05_catalogo_nomes_materiais.png','14210_06_semaforo_braco_farol_noturno_3d.png','14210_07_corte_de_intervalo_por_icone.png','14210_08_juncao_validada_por_icone.png','14210_09_ferrovia_por_rota_selecionada.png','14210_01_recuperar_fluxo_principal.png','14210_02_fluxo_recuperado_recalculado.png','14210_03_eixo_com_falha_recuperado.png','1429_01_novo_projeto_reaberto.png','1429_02_imagem_convertida_mista.png','1429_03_calculo_configuracao_confirmada.png','1429_tratamento_erros_rota.png','1428_08_ortofoto_local_real.png','1428_05_marcacoes_popup_1024.png','1428_06_popup_descartar.png','1428_07_imagem_apresentacao.png','1428_03_grupos_e_icones.png','1428_04_calculos_medicao.png','1428_01_barra_lateral.png','1428_02_fluxo_selecionado.png','1427_06_video_de_revisao_anterior.png','1427_01_gravacao_serializada.png','1427_02_conflito_preserva_edicao.png','1427_03_resultados_preservam_historico.png','1427_04_abertura_fora_de_ordem.png','1427_05_historico_recuperacao.png','1426_07_link_onda_verde.png','1426_01_semaforo_tres_tempos.png','1426_02_ferrovia_propriedades.png','1426_03_ferrovia_semaforos_webgl.png','1426_04_cabine_controle.png','1426_05_fluxos_zoom_diagnostico.png','1426_06_demanda_sobressaturacao.png','1426_video_0.png','1426_video_1.5.png','1426_video_2.9.png','1426_video_metadados.json','1425_01_webgl_trafego_real.png','1425_02_captura_e_diagnostico.png','1425_03_contexto_recuperado.png','1425_04_novo_projeto_identificado.png','1425_05_video_3d_conferido.png','1424_06_zoom_dpi_1.png','1424_06_zoom_dpi_2.png','1424_05_limite_fluxos.png','1424_04_barra_completa_139.png','1424_01_comandos_139_visiveis.png','1424_02_comando_e_opcoes.png','1424_03_faixa_1024.png','1424_03_faixa_1366.png','1424_03_faixa_1920.png','1423_01_ferramentas_139_restauradas.png','1423_02_pan_zoom_redesenhar.png','1423_03_modificar.png','1423_04_inserir_controle_desfazer.png','1423_05_controle_calibracao.png','1423_video_quadro_0.png','1423_video_quadro_36.png','1423_video_quadro_71.png','1423_video_metadados.json','pytest-resultados.xml','resultado.json','validacao.log','142_03_modelar_cascata.png','1422_01_acesso_rapido_rodape.png','1422_03_fluxos_sobre_superficies.png','1422_05_selecao_fluxo_prioritaria.png','142_11_motor_editor_real.png','142_12_motor_editor_fluxo_problema.png','splash_142_1_a.png','splash_142_1_b.png']:
            shutil.copy2(EVIDENCE/name,evidence/name)
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
