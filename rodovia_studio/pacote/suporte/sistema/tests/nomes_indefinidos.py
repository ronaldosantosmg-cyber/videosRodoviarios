"""Verificador simples de nomes indefinidos em módulos Python (substitui o pyflakes, que não está no runtime).

Uso: python tests/nomes_indefinidos.py arquivo.py [...]  -> imprime 'arquivo:linha: nome' para cada nome lido que não
foi definido no módulo, na função (parâmetros, atribuições, imports, for, with, except, compreensões) nem é builtin.
Imports com * são resolvidos importando o módulo de origem.
"""
import ast,builtins,importlib,sys
from pathlib import Path

def module_names(tree,pkg):
    names=set()
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            for a in node.names:
                if a.name=='*':
                    mod=importlib.import_module(('.'*node.level+(node.module or '')),pkg) if node.level else importlib.import_module(node.module)
                    names|={k for k in vars(mod) if not k.startswith('__')}
                else:names.add((a.asname or a.name).split('.')[0])
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):names.add(node.name)
        for t in ast.walk(node):
            if isinstance(t,ast.Name) and isinstance(t.ctx,ast.Store):names.add(t.id)
            if isinstance(t,ast.Global):names|=set(t.names)
    return names

def local_names(fn):
    out=set()
    a=fn.args
    for x in a.args+a.kwonlyargs+a.posonlyargs+([a.vararg] if a.vararg else [])+([a.kwarg] if a.kwarg else []):out.add(x.arg)
    for t in ast.walk(fn):
        if isinstance(t,ast.Name) and isinstance(t.ctx,(ast.Store,ast.Del)):out.add(t.id)
        elif isinstance(t,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and t is not fn:out.add(t.name)
        elif isinstance(t,(ast.Import,ast.ImportFrom)):
            for x in t.names:out.add((x.asname or x.name).split('.')[0])
        elif isinstance(t,ast.ExceptHandler) and t.name:out.add(t.name)
        elif isinstance(t,ast.arg):out.add(t.arg)
        elif isinstance(t,ast.MatchAs) and t.name:out.add(t.name)
    return out

def check(path):
    p=Path(path);tree=ast.parse(p.read_text(encoding='utf-8'))
    pkg='app' if p.parent.name=='app' else ('app.'+p.parent.name if p.parent.parent.name=='app' else None)
    known=module_names(tree,pkg)|set(dir(builtins))|{'__file__','__name__'}
    bad=[]
    def visit(node,scope):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)):
            scope=scope|local_names(node) if not isinstance(node,ast.Lambda) else scope|{a.arg for a in node.args.args}
        if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load) and node.id not in scope:bad.append((node.lineno,node.id))
        for ch in ast.iter_child_nodes(node):visit(ch,scope)
    visit(tree,known)
    return [f'{p}:{l}: {n}' for l,n in bad]

if __name__=='__main__':
    out=[x for f in sys.argv[1:] for x in check(f)]
    print('\n'.join(out) or 'ok');sys.exit(1 if out else 0)
