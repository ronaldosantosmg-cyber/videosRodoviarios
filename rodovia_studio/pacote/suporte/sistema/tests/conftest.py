"""Impede que a coleta de testes abra um banco de projeto dentro do pacote."""
import os
import tempfile

if not os.environ.get('RODOVIA_DATA'):
    os.environ['RODOVIA_DATA']=tempfile.mkdtemp(prefix='rodovia_pytest_')
