"""Impede que a coleta de testes abra um banco de projeto dentro do pacote."""
import os
import tempfile

if not os.environ.get('RODOVIA_DATA'):
    os.environ['RODOVIA_DATA']=tempfile.mkdtemp(prefix='rodovia_pytest_')

# Cada processo de teste simula uma instalação diferente. Inicializar um servidor
# não pode marcar tarefas de outro worker como interrompidas no mesmo banco.
worker=os.environ.get('PYTEST_XDIST_WORKER','')
if worker.startswith('gw') and worker[2:].isdigit():
    from pathlib import Path
    os.environ['RODOVIA_DATA']=str(Path(os.environ['RODOVIA_DATA'])/worker)
