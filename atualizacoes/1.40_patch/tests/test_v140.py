from pathlib import Path
import json
BASE=Path(__file__).resolve().parents[1]

def test_v140_desktop_workspace_files():
    js=(BASE/'app/js/50_desktop_workspace.js').read_text(encoding='utf-8')
    css=(BASE/'app/estilo.css').read_text(encoding='utf-8')
    assert 'Desktop Workspace' in js
    assert 'dwCommandDrawer' in js
    assert 'dwProjectFocus' in js
    assert 'Ctrl+Espaço' in js
    assert '.dwCommandDrawer' in css
    assert '.dwProjectFocus' in css

def test_v140_version():
    v=json.loads((BASE/'VERSAO.json').read_text(encoding='utf-8'))
    assert v['version']=='1.40.0'
    assert v['schema_version']>=31
    assert '1.40' in v['phases']
