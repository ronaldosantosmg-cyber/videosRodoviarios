from pathlib import Path
import json
BASE=Path(__file__).resolve().parents[1]

def read(rel): return (BASE/rel).read_text(encoding='utf-8')

def test_version_1403():
    v=json.loads(read('VERSAO.json'))
    assert tuple(map(int,v['version'].split('.'))) >= (1,40,3)
    assert v['schema_version']>=33

def test_visual_order_controls_are_explicit():
    s=read('app/js/08_camadas_imagem_local.js')
    assert 'data-imgtop' in s and 'data-imgbottom' in s
    assert '1 = topo' in s
    assert '/imagery/order' in s

def test_viewport_preservation_module():
    s=read('app/js/52_interacao_camadas.js')
    assert 'RodoviaViewport' in s
    assert 'capture' in s and 'restore' in s
    assert 'Alt+clique' in s
    assert "e.key!=='Tab'" in s

def test_layout_changes_do_not_force_fit_view():
    s=read('app/js/07_tarefas_intervencoes.js')
    line=[x for x in s.splitlines() if "$('toggleSide').onclick" in x][0]
    full=[x for x in s.splitlines() if "fullscreenchange" in x][0]
    assert 'fitView()' not in line
    assert 'fitView()' not in full
    assert 'RodoviaViewport' in line and 'RodoviaViewport' in full

def test_selection_cleanup_is_policy_driven():
    s=read('app/js/27_comandos_limpos.js')
    assert 'RodoviaSelectionPolicy' in s
