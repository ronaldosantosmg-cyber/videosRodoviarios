"""Impede que a coleta de testes abra um banco de projeto dentro do pacote."""
import os
import tempfile

if not os.environ.get('RODOVIA_DATA'):
    os.environ['RODOVIA_DATA']=tempfile.mkdtemp(prefix='rodovia_pytest_')

# 2.28: testes que abrem navegador (Playwright) recebem o marcador "navegador".
# Gate rápido: pytest -m "not navegador"   |   só navegador: pytest -m navegador
_CACHE={}
def pytest_configure(config):
    config.addinivalue_line('markers','navegador: abre o navegador (Playwright); lento')
def pytest_collection_modifyitems(config,items):
    import pytest
    for item in items:
        path=str(item.fspath)
        if path not in _CACHE:
            try:text=open(path,encoding='utf-8').read()
            except OSError:text=''
            _CACHE[path]=any(k in text for k in ('playwright','chromium','gl_page','visual_harness','test_v14234_nodes_ui_video'))
        if _CACHE[path] or {'live','gl_page','page','browser'}&set(getattr(item,'fixturenames',())):item.add_marker(pytest.mark.navegador)
