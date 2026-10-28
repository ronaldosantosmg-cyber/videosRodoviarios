"""Reutiliza testes somente do mesmo produto, repetindo módulos alterados e dependentes."""
import ast,copy,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path


def product_digest(package):
    package=Path(package);h=hashlib.sha256()
    for f in sorted(package.rglob('*')):
        rel=f.relative_to(package)
        if f.is_file() and not any(p in rel.parts for p in ('tests','__pycache__','.pytest_cache')):
            h.update(rel.as_posix().encode());h.update(f.read_bytes())
    return h.hexdigest()


def test_hashes(system):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(system)/'tests').glob('*.py')}


def affected(system,previous):
    files={p.name:p for p in (Path(system)/'tests').glob('*.py')}
    names={Path(n).stem:n for n in files};changed={n for n,p in files.items() if previous.get(n)!=hashlib.sha256(p.read_bytes()).hexdigest()}
    if 'conftest.py' in changed:return set(files)
    dependencies={};unknown=set()
    for n,p in files.items():
        deps=set()
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
            if isinstance(node,ast.ImportFrom) and node.module:
                if node.module.split('.')[-1] in names:deps.add(names[node.module.split('.')[-1]])
            elif isinstance(node,ast.Import):
                for item in node.names:
                    if item.name.split('.')[-1] in names:deps.add(names[item.name.split('.')[-1]])
            elif isinstance(node,ast.Call) and (isinstance(node.func,ast.Name) and node.func.id=='__import__' or isinstance(node.func,ast.Attribute) and node.func.attr=='import_module'):
                if node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
                    name=node.args[0].value.split('.')[-1]
                    if name in names:deps.add(names[name])
                else:unknown.add(n)
        dependencies[n]=deps
    if changed:changed|=unknown
    while True:
        more={n for n,deps in dependencies.items() if deps&changed}-changed
        if not more:return changed
        changed|=more


def key(case,filenames):
    parts=(case.get('classname') or '').split('.')
    for i,part in enumerate(parts):
        if part+'.py' in filenames:
            return part+'.py','::'.join(parts[i+1:]+[case.get('name','')])
    raise RuntimeError('Caso de teste sem módulo reconhecido: '+str(case.attrib))


def failed(case):return any(case.find(t) is not None for t in ('failure','error','skipped'))


def collect(system,selected,env,log):
    result=subprocess.run([sys.executable,'-m','pytest','--collect-only','-q',*selected],cwd=system,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log.write(result.stdout);log.flush()
    if result.returncode:raise RuntimeError('A coleta dos testes obrigatórios falhou.')
    cases=set()
    for line in result.stdout.splitlines():
        if '::' not in line or not line.split('::',1)[0].endswith('.py'):continue
        file,name=line.split('::',1);cases.add((Path(file).name,name))
    if not cases:raise RuntimeError('Nenhum caso obrigatório coletado.')
    return cases


def plan(package,system,selected,origin_dir,env,log):
    origin_dir=Path(origin_dir);origin=json.loads((origin_dir/'origem.json').read_text(encoding='utf-8'))
    if origin['product_sha256']!=product_digest(package):raise RuntimeError('Produto alterado: a retomada foi recusada; execute a suíte completa.')
    wanted=collect(system,selected,env,log);filenames={n for n,_ in wanted}
    baseline={key(c,filenames):c for c in ET.parse(origin_dir/'pytest-resultados.xml').iter('testcase')}
    changed=affected(system,origin['tests'])
    retry=changed|{n for n,name in wanted if (n,name) not in baseline or failed(baseline[(n,name)])}
    arguments=[value for value in selected if Path(value.split('::')[0]).name in retry]
    keep={k:copy.deepcopy(v) for k,v in baseline.items() if k in wanted and k[0] not in retry and not failed(v)}
    return dict(wanted=wanted,arguments=arguments,keep=keep,filenames=filenames,product_sha256=origin['product_sha256'],origin=str(origin_dir),changed=sorted(changed))


def merge(state,fresh_report,output):
    result=dict(state['keep']);executed=0
    if fresh_report is not None:
        for case in ET.parse(fresh_report).iter('testcase'):
            k=key(case,state['filenames']);result[k]=copy.deepcopy(case);executed+=1
    if set(result)!=state['wanted']:raise RuntimeError('Cobertura divergente dos testes obrigatórios; pacote bloqueado.')
    bad=[k for k,c in result.items() if failed(c)]
    suites=ET.Element('testsuites');suite=ET.SubElement(suites,'testsuite',name='Regressoes completas do mesmo produto',tests=str(len(result)),failures=str(sum(c.find('failure') is not None for c in result.values())),errors=str(sum(c.find('error') is not None for c in result.values())),skipped=str(sum(c.find('skipped') is not None for c in result.values())))
    for k in sorted(result):suite.append(result[k])
    ET.ElementTree(suites).write(output,encoding='utf-8',xml_declaration=True)
    summary=dict(reused_tests=len(state['keep']),executed_tests=executed,total=len(result),product_sha256=state['product_sha256'],origin=state['origin'],changed_test_modules=state['changed'])
    Path(output).with_name('retomada.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if bad:raise RuntimeError(f'{len(bad)} casos ainda falharam ou foram ignorados; pacote bloqueado.')
    return summary
