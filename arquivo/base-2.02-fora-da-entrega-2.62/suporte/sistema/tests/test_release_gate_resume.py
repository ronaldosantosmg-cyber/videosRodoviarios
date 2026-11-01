import sys,json,xml.etree.ElementTree as E
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
import validacao_incremental as V


def tree(tmp_path):
    package=tmp_path/'pacote';system=package/'suporte/sistema';tests=system/'tests';tests.mkdir(parents=True)
    (system/'programa.py').write_text('valor=1\n')
    (tests/'test_a.py').write_text('from helper import fixture\ndef test_ok():pass\n')
    (tests/'helper.py').write_text('fixture=1\n')
    (tests/'test_b.py').write_text('def test_bad():pass\n')
    origin=tmp_path/'original';origin.mkdir()
    (origin/'origem.json').write_text(json.dumps(dict(product_sha256=V.product_digest(package),tests=V.test_hashes(system))))
    root=E.Element('testsuites');s=E.SubElement(root,'testsuite')
    E.SubElement(s,'testcase',classname='tests.test_a',name='test_ok')
    c=E.SubElement(s,'testcase',classname='tests.test_b',name='test_bad');E.SubElement(c,'failure',message='falha')
    E.ElementTree(root).write(origin/'pytest-resultados.xml')
    return package,system,tests,origin


def test_dependency_change_repeats_all_importers(tmp_path):
    package,system,tests,origin=tree(tmp_path);before=V.test_hashes(system)
    (tests/'helper.py').write_text('fixture=2\n')
    assert V.affected(system,before)=={'helper.py','test_a.py'}


def test_same_product_reuses_only_passed_unchanged_cases(tmp_path,monkeypatch):
    package,system,tests,origin=tree(tmp_path)
    monkeypatch.setattr(V,'collect',lambda *a:{('test_a.py','test_ok'),('test_b.py','test_bad')})
    with (tmp_path/'log').open('w') as log:state=V.plan(package,system,['tests/test_a.py','tests/test_b.py'],origin,{},log)
    assert state['arguments']==['tests/test_b.py'] and set(state['keep'])=={('test_a.py','test_ok')}
    root=E.Element('testsuites');s=E.SubElement(root,'testsuite');E.SubElement(s,'testcase',classname='tests.test_b',name='test_bad')
    fresh=tmp_path/'novo.xml';E.ElementTree(root).write(fresh)
    result=V.merge(state,fresh,tmp_path/'merged.xml');assert result['total']==2 and result['executed_tests']==1 and result['reused_tests']==1


def test_product_change_blocks_reuse(tmp_path,monkeypatch):
    package,system,tests,origin=tree(tmp_path);(system/'programa.py').write_text('valor=2\n')
    with (tmp_path/'log').open('w') as log:
        with pytest.raises(RuntimeError,match='Produto alterado'):V.plan(package,system,[],origin,{},log)


def test_changed_test_and_its_dependencies_are_not_reused(tmp_path,monkeypatch):
    package,system,tests,origin=tree(tmp_path);(tests/'helper.py').write_text('fixture=3\n')
    monkeypatch.setattr(V,'collect',lambda *a:{('test_a.py','test_ok'),('test_b.py','test_bad')})
    with (tmp_path/'log').open('w') as log:state=V.plan(package,system,['tests/test_a.py','tests/test_b.py'],origin,{},log)
    assert not state['keep'] and set(state['arguments'])=={'tests/test_a.py','tests/test_b.py'}


def test_failure_or_skip_still_blocks_delivery(tmp_path,monkeypatch):
    package,system,tests,origin=tree(tmp_path)
    monkeypatch.setattr(V,'collect',lambda *a:{('test_a.py','test_ok'),('test_b.py','test_bad')})
    with (tmp_path/'log').open('w') as log:state=V.plan(package,system,['tests/test_a.py','tests/test_b.py'],origin,{},log)
    with pytest.raises(RuntimeError,match='pacote bloqueado'):V.merge(state,origin/'pytest-resultados.xml',tmp_path/'merged.xml')


def test_incomplete_coverage_blocks_delivery(tmp_path):
    state=dict(keep={},wanted={('test_a.py','test_ok')},filenames={'test_a.py'})
    with pytest.raises(RuntimeError,match='Cobertura divergente'):V.merge(state,None,tmp_path/'merged.xml')
