"""Gera uma atualização do código versionado, sem copiar projetos ou caches."""
import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "suporte/sistema"))
from atualizador import validate_package


def empacotar(output):
    origem = json.loads((ROOT / "proveniencia/studio-3.5.json").read_text(encoding="utf-8"))
    versao = json.loads((ROOT / "suporte/sistema/VERSAO.json").read_text(encoding="utf-8"))["version"]
    nomes = sorted(set(origem["files"]) | {"CORRECOES_3_5.md", "ATUALIZACAO_3_6.md", "ATUALIZACAO_3_7.md", "VALIDACAO_3_7.md", "ATUALIZACAO_3_8.md", "VALIDACAO_3_8.md", "ATUALIZACAO_3_9.md", "VALIDACAO_3_9.md", "ATUALIZACAO_3_10.md", "VALIDACAO_3_10.md", "ATUALIZACAO_3_11.md", "VALIDACAO_3_11.md", "ATUALIZACAO_3_12.md", "VALIDACAO_3_12.md", "ATUALIZACAO_3_13.md", "VALIDACAO_3_13.md", "ATUALIZACAO_3_14.md", "VALIDACAO_3_14.md", "ATUALIZACAO_3_15.md", "VALIDACAO_3_15.md", "ATUALIZACAO_3_16.md", "VALIDACAO_3_16.md", "ATUALIZACAO_3_17.md", "VALIDACAO_3_17.md", "ATUALIZACAO_3_18.md", "VALIDACAO_3_18.md", "suporte/sistema/app/dimension_audit.py", "suporte/sistema/app/quarantine.py", "suporte/sistema/app/marking_policy.py", "suporte/sistema/app/traffic_cache.py", "suporte/sistema/app/traffic_history.py", "suporte/sistema/app/traffic_pipeline.py", "suporte/sistema/app/fleet_policy.py", "suporte/sistema/app/js/99_frota_iluminacao.js"})
    with tempfile.TemporaryDirectory(prefix="studio-pacote-") as tmp:
        pacote = Path(tmp) / "pacote"
        hashes = {}
        for nome in nomes:
            rel = nome if nome.startswith("suporte/") or nome.startswith(("ATUALIZACAO_", "CORRECOES_", "VALIDACAO_")) else "raiz/" + nome
            data = (ROOT / nome).read_bytes()
            target = pacote / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            hashes[rel] = hashlib.sha256(data).hexdigest()
        manifest = {"app": "Rodovia Studio", "version": versao,
                    "description": "Studio 3.18: espaçamento preventivo, auditoria antes do vídeo, materiais, ancoragens e quarentena. Requer Python 3.12.",
                    "files": hashes}
        (pacote / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        validate_package(pacote)
        output = Path(output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for arquivo in sorted(pacote.rglob("*")):
                if arquivo.is_file():
                    info = zipfile.ZipInfo("pacote/" + arquivo.relative_to(pacote).as_posix(), (2026, 11, 2, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, arquivo.read_bytes())
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        output.with_suffix(".sha256.txt").write_text(f"{digest}  {output.name}\n", encoding="ascii")
        print(f"Pacote {versao}: {len(hashes)} arquivos; SHA-256 {digest}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist/RodoviaStudio_3_18_atualizacao.zip")
    empacotar(parser.parse_args().output)
