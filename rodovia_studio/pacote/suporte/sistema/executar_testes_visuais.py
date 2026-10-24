from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;ART=ROOT/'resultados_testes_visuais';ART.mkdir(exist_ok=True)
env=os.environ.copy();env['PYTHONPATH']=str(ROOT);env['VISUAL_ARTIFACTS']=str(ART)
if not env.get('CHROMIUM'):
    for p in ('/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome'):
        if Path(p).exists():env['CHROMIUM']=p;break
cmd=[sys.executable,'-m','pytest','-q','tests/test_v1409_visual.py']
print('Rodovia Studio — testes visuais ampliados 1.40.9');print('Artefatos:',ART)
rc=subprocess.call(cmd,cwd=ROOT,env=env);print('\nResultado:','APROVADO' if rc==0 else 'FALHOU');print('Screenshots:',ART);raise SystemExit(rc)
