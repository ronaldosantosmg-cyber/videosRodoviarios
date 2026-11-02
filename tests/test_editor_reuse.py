import ezdxf

from app import store
from app.models import Settings
from app.render import Scene


def test_editor_reutiliza_camera_e_invalida_alteracao_de_sentido(tmp_path, monkeypatch):
    document = ezdxf.new()
    model = document.modelspace()
    document.layers.new('EIXO')
    document.layers.new('PAVIMENTO')
    model.add_lwpolyline([(500000, 7800000), (500400, 7800000)], dxfattribs={'layer': 'EIXO'})
    hatch = model.add_hatch(dxfattribs={'layer': 'PAVIMENTO'})
    hatch.paths.add_polyline_path([(500000, 7799993), (500400, 7799993), (500400, 7800007), (500000, 7800007)], is_closed=True)
    document.saveas(tmp_path / 'input.dxf')
    settings = Settings(imagery='neutral', hydrography=False, route_directions={'layer:EIXO': 'forward'})
    scene = Scene.light(tmp_path, settings)
    data = scene.editor_data()
    store.write_json(tmp_path / 'editor.json', data)
    same = Scene.light(tmp_path, settings.model_copy(update={'preview_time_s': 12}))
    import app.flow_diagnostics as diagnostic
    original = diagnostic.flow_diagnostics
    calls = []

    def observe(network):
        calls.append(network)
        return original(network)

    monkeypatch.setattr(diagnostic, 'flow_diagnostics', observe)
    assert same.editor_data()['engine_revision'] == data['engine_revision']
    assert same.report['editor_cache_hit']
    assert not calls
    changed = Scene.light(tmp_path, settings.model_copy(update={'route_directions': {'layer:EIXO': 'reverse'}}))
    assert changed.editor_data()['engine_revision'] != data['engine_revision']
    assert not changed.report['editor_cache_hit']
    assert calls


def test_json_compacto_preserva_valores_e_gravacao_atomica(tmp_path):
    import json

    path = tmp_path / 'editor.json'
    data = {'engine_revision': 'r1', 'points': [[1.25, 2.5]] * 1000}
    store.write_json(path, data)
    assert json.loads(path.read_text()) == data
    assert len(path.read_bytes()) < len(json.dumps(data, indent=2).encode()) / 2
