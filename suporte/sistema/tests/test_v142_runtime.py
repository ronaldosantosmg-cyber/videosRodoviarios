"""Servidor iniciado fora da pasta raiz e encerrado pelo protocolo da sessão."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def test_real_server_graceful_shutdown_from_other_directory(tmp_path):
    base=Path(__file__).resolve().parents[1]
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    root=tmp_path/'Projetos ç';root.mkdir()
    (root/'original.kmz').write_bytes(b'KMZ manter')
    env=dict(os.environ,RODOVIA_DATA=str(root),RODOVIA_PORT=str(port),RODOVIA_NO_BROWSER='1',RODOVIA_CONTROL_TOKEN='sessao-teste-real')
    with (tmp_path/'servidor.log').open('w') as log:
        proc=subprocess.Popen([sys.executable,str(base/'run.py')],cwd=tmp_path,env=env,stdout=log,stderr=log)
        url=f'http://127.0.0.1:{port}'
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                assert proc.poll() is None,(tmp_path/'servidor.log').read_text()
                try:
                    with opener.open(url+'/api/health',timeout=1) as r:health=json.load(r)
                    break
                except OSError:time.sleep(.1)
            else:raise AssertionError('Servidor não iniciou.')
            assert health['version']==json.loads((base/'VERSAO.json').read_text())['version'] and health['ffmpeg']
            with opener.open(url+'/api/atualizacao',timeout=3) as r:
                assert json.load(r)['modo']=='desenvolvimento'
            req=urllib.request.Request(url+'/api/sessao/encerrar',data=b'',headers={'X-Rodovia-Control':'sessao-teste-real'},method='POST')
            with opener.open(req,timeout=3) as r:assert json.load(r)['encerrando']
            assert proc.wait(timeout=15)==0,(tmp_path/'servidor.log').read_text()
            assert (root/'original.kmz').read_bytes()==b'KMZ manter'
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
