"""Seleciona regressão por risco; mudança em núcleo promove o perfil amplo."""
import ast,subprocess,hashlib
from pathlib import Path
BASE='b3dcd3e'  # entrega 2.67 publicada e validada
VISUAL_FILES={
 'app/presentation.py','app/render.py','app/detail.py','app/earthworks.py','app/relevo.py',
 'app/scene3d.py','app/visual.py','app/dependencies.py','app/webgl/viewer.mjs',
 'app/zebrados.py','app/js/14_cad_edicao.js',
 'app/signage.py','app/js/04_ferramentas.js','app/js/05_desenho.js','app/js/06_lista_marcacoes.js','app/js/97_zebrados.js',
 'app/index.html','app/js/01_estado_configuracao.js','app/js/75_operacao_consolidada.js',
}
# Contratos/leitor revisados nesta entrega: qualquer diferença adicional exige regressão ampla.
REVIEWED={'app/models.py': '9bdc7fc13e8563fc0e10dc4dbf9a5d1de9250e8ea956b0bd159288a3cc4de1c3', 'app/geometry.py': 'c04f8f862ac36cd24fb50550e182aa15f4a49ddb42ada1c13b0d09e2986ef628'}

def reviewed(name,data):return name in REVIEWED and hashlib.sha256(data).hexdigest()==REVIEWED[name]

def model_contract(text,strip=False):return ast.dump(ast.parse(text),include_attributes=False)

def assess(root,system):
    root=Path(root);system=Path(system);prefix=system.relative_to(root).as_posix()+'/'
    def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.DEVNULL,timeout=15)
    try:
        changed=set(git('diff','--name-only',BASE,'--',prefix).splitlines())|set(git('ls-files','--others','--exclude-standard','--',prefix).splitlines())
        changed={f[len(prefix):] for f in changed if f.startswith(prefix)}
        runtime={f for f in changed if not f.startswith('tests/') and f!='VERSAO.json' and not f.endswith('.md')}
        sensitive=runtime-VISUAL_FILES
        for name in runtime & REVIEWED.keys():
            if reviewed(name,(system/name).read_bytes()):sensitive.discard(name)
        return {'baseline':BASE,'changed_runtime':sorted(runtime),'sensitive':sorted(sensitive),'requires_broad':bool(sensitive)}
    except (subprocess.SubprocessError,OSError,ValueError,SyntaxError) as error:
        return {'baseline':BASE,'requires_broad':True,'reason':'Não foi possível comprovar o escopo das mudanças: '+str(error)[:160]}
