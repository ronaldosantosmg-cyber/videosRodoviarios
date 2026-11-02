"""Smoke real: inicia o servidor em dados temporários e verifica API e interface."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verificar():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="studio-smoke-") as tmp:
        env = {**os.environ, "RODOVIA_DATA": str(Path(tmp) / "dados"),
               "RODOVIA_VIDEOS": str(Path(tmp) / "videos"),
               "RODOVIA_NO_BROWSER": "1", "RODOVIA_PORT": str(port)}
        log = Path(tmp) / "servidor.log"
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.Popen([sys.executable, str(ROOT / "suporte/sistema/run.py")],
                                       cwd=ROOT / "suporte/sistema", env=env, stdout=stream, stderr=stream)
            try:
                base = f"http://127.0.0.1:{port}"
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Servidor encerrou: " + log.read_text(encoding="utf-8"))
                    try:
                        with urllib.request.urlopen(base + "/api/health", timeout=2) as response:
                            assert json.load(response)["status"] == "ok"
                        break
                    except OSError:
                        time.sleep(.2)
                else:
                    raise RuntimeError("Servidor não ficou pronto: " + log.read_text(encoding="utf-8"))
                for route in ("/", "/js/01_estado_configuracao.js", "/js/36_videos_limpeza_atualizar.js"):
                    with urllib.request.urlopen(base + route, timeout=5) as response:
                        assert response.status == 200
                        assert response.read()
                print("Servidor Studio: API, página e JavaScript acessíveis")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    verificar()
