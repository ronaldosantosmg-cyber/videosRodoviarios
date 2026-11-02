import hashlib
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def test_previa_subpixel_dispensa_simulacao():
    from app.traffic_presentation import visible

    def simular(_):
        raise AssertionError("A prévia geral não deve simular veículos invisíveis")

    scene = SimpleNamespace(s=SimpleNamespace(traffic=True), W=1280, preview_fast=True, traffic_iter=simular)
    items, stats = visible(scene, 30, (0, 0), 20000, 1)
    assert not items
    assert stats["simulacao_dispensada"]


def test_pacote_atualizacao_valido_sem_projetos(tmp_path):
    from empacotar_studio import empacotar

    path = empacotar(tmp_path / "studio.zip")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert not any("projetos/" in n or n.endswith(".sqlite3") or "legado/" in n for n in names)
        manifest = json.loads(archive.read("pacote/manifest.json"))
        assert manifest["version"] == "3.5.1"
        assert len(names) == len(manifest["files"]) + 1
        for name, digest in manifest["files"].items():
            assert hashlib.sha256(archive.read("pacote/" + name)).hexdigest() == digest


def test_editor_obsoleto_nao_e_anunciado_como_pronto(tmp_path, monkeypatch):
    from app.rotas.projetos import get_project
    from app import store, project_state
    from app.models import Settings

    (tmp_path / "editor.json").write_text("{}")
    monkeypatch.setattr(store, "directory", lambda _: tmp_path)
    monkeypatch.setattr(project_state, "state", lambda _: {
        "config": Settings().model_dump(),
        "artifacts": {"preview": {"state": "missing"}, "editor": {"state": "stale"}}})
    assert not get_project("a" * 32)["editor_ready"]


def test_atualizacao_continua_bloqueada_por_tarefa_ativa():
    import pytest
    from fastapi import HTTPException
    from app import store
    from app.rotas.sistema import update_ready

    with store.connect() as c:
        c.execute("INSERT INTO jobs(id,project,kind,state) VALUES (?,?,?,?)", ("ocupado", "p", "refresh", "running"))
    try:
        with pytest.raises(HTTPException) as error:
            update_ready()
        assert error.value.status_code == 409
    finally:
        with store.connect() as c:
            c.execute("DELETE FROM jobs WHERE id='ocupado'")
    assert update_ready()["pronto"]


def test_semeadura_consulta_cancelamento_antes_de_trabalhar():
    import numpy as np
    import pytest
    from app.simulation import TrafficSim

    sim = TrafficSim.__new__(TrafficSim)
    sim.paths = [{"length": 100}]
    sim.rate = [1]

    def cancelar(*_):
        raise InterruptedError("Cancelado")

    with pytest.raises(InterruptedError):
        sim.semear_percurso([], 0, -90, np.random.default_rng(1), cancelar)
