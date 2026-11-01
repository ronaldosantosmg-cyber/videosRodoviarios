"""Seleciona regressão por risco; mudança em núcleo promove o perfil amplo."""
import ast,subprocess
from pathlib import Path
BASE='61eb954'  # entrega 2.63 preservada
VISUAL_FILES={
 'app/presentation.py','app/render.py','app/detail.py','app/earthworks.py','app/relevo.py',
 'app/scene3d.py','app/visual.py','app/dependencies.py','app/webgl/viewer.mjs',
 'app/signage.py','app/js/04_ferramentas.js','app/js/05_desenho.js','app/js/06_lista_marcacoes.js','app/js/97_zebrados.js',
 'app/index.html','app/js/01_estado_configuracao.js','app/js/75_operacao_consolidada.js',
}
NEW_FIELDS={'realism_profile','presentation_guides','dxf_lead_m'}

def model_contract(text,strip=False):
    tree=ast.parse(text)
    if strip:
        for node in tree.body:
            if isinstance(node,ast.ClassDef) and node.name=='Settings':
                node.body=[n for n in node.body if not(isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in NEW_FIELDS)]
    if strip:
        for node in tree.body:
            if isinstance(node,ast.ClassDef) and node.name=='HatchArea':
                node.body=[n for n in node.body if not (isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in {'stripe_width_m','world_aligned'}) and not (isinstance(n,ast.FunctionDef) and n.name=='zebra_dimensions')]
    return ast.dump(tree,include_attributes=False)

def assess(root,system):
    root=Path(root);system=Path(system);prefix=system.relative_to(root).as_posix()+'/'
    def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.DEVNULL,timeout=15)
    try:
        changed=set(git('diff','--name-only',BASE,'--',prefix).splitlines())|set(git('ls-files','--others','--exclude-standard','--',prefix).splitlines())
        changed={f[len(prefix):] for f in changed if f.startswith(prefix)}
        runtime={f for f in changed if not f.startswith('tests/') and f!='VERSAO.json' and not f.endswith('.md')}
        sensitive=runtime-VISUAL_FILES-{'app/models.py'}
        if 'app/models.py' in runtime:
            before=git('show',BASE+':'+prefix+'app/models.py')
            if model_contract(before)!=model_contract((system/'app/models.py').read_text(),True):sensitive.add('app/models.py (contrato além dos campos de aparência)')
        return {'baseline':BASE,'changed_runtime':sorted(runtime),'sensitive':sorted(sensitive),'requires_broad':bool(sensitive)}
    except (subprocess.SubprocessError,OSError,ValueError,SyntaxError) as error:
        return {'baseline':BASE,'requires_broad':True,'reason':'Não foi possível comprovar o escopo das mudanças: '+str(error)[:160]}
