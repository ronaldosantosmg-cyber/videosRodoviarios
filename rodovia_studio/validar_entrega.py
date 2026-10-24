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
EVIDENCE=ROOT/'evidencias'
TESTS=[
 'tests/test_v142_update.py','tests/test_v142_runtime.py','tests/test_v142_diagnostics.py',
 'tests/test_v142_visual.py','tests/test_v142_live_ui.py','tests/test_v141_technical.py',
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
    parser=argparse.ArgumentParser();parser.add_argument('--gerar',action='store_true');args=parser.parse_args()
    EVIDENCE.mkdir(exist_ok=True)
    env=dict(os.environ,PYTHONPYCACHEPREFIX=str(ROOT.parent.parent/'.cache/pycache'),XDG_CACHE_HOME=str(ROOT.parent.parent/'.cache'),VISUAL_ARTIFACTS=str(EVIDENCE),RODOVIA_DATA=str(Path(tempfile.gettempdir())/'rodovia_gate_data'))
    initial=digest();report=EVIDENCE/'pytest-resultados.xml';report.unlink(missing_ok=True)
    with (EVIDENCE/'validacao.log').open('w',encoding='utf-8') as log:
        run([sys.executable,'-m','pip','check'],env,log)
        run([sys.executable,'-m','compileall','-q','app','tests','atualizador.py','run.py'],env,log)
        node=shutil.which('node')
        if not node:raise RuntimeError('Node é necessário para validar JavaScript.')
        for f in sorted((SYSTEM/'app/js').glob('*.js')):run([node,'--check',f],env,log)
        run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*TESTS,f'--junitxml={report}'],env,log)
        suites=ET.parse(report).getroot().findall('.//testsuite')
        counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
        if not counts['tests'] or any(counts[k] for k in ['failures','errors','skipped']):raise RuntimeError('Há falhas, erros, testes ausentes ou ignorados. Pacote bloqueado.')
        native_checks(env,log)
    if digest()!=initial:raise RuntimeError('Os fontes mudaram durante a validação. Execute novamente.')
    metadata={'version':json.loads((PACKAGE/'manifest.json').read_text())['version'],'source_sha256':initial,'pytest':counts,'splash':'Mono/Xvfb; versão, fabricante e animação','launcher':'C# compilado com e sem WEBVIEW2','platform':'Linux, Python '+sys.version.split()[0],'windows_native_executed':False}
    (EVIDENCE/'resultado.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(f"Validação aprovada: {counts['tests']} testes; splash e compilação C# aprovados.")
    if not args.gerar:return
    spec=importlib.util.spec_from_file_location('rs_updater',SYSTEM/'atualizador.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    dest=ROOT.parent/'atualizacoes';dest.mkdir(exist_ok=True)
    output=dest/f'RodoviaStudio_{metadata["version"].replace(".","_")}_atualizacao.zip'
    if output.exists():raise RuntimeError('O pacote final já existe; preserve-o antes de gerar outra entrega.')
    with tempfile.TemporaryDirectory(prefix='rs_package_') as tmp:
        stage=Path(tmp)/'pacote';shutil.copytree(PACKAGE,stage,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','*.pyc'))
        evidence=stage/'suporte/documentacao/validacao_1_42_1';evidence.mkdir(parents=True)
        for name in ['pytest-resultados.xml','resultado.json','validacao.log','142_03_modelar_cascata.png','142_11_motor_editor_real.png','142_12_motor_editor_fluxo_problema.png','splash_142_1_a.png','splash_142_1_b.png']:
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
    print(f'Pacote gerado: {output}\nSHA-256: {sha}')


if __name__=='__main__':main()
