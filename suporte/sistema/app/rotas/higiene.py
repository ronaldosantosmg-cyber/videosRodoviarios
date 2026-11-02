"""2.56: prévia da faxina e verificação de pastas/arquivos ausentes. A execução da limpeza exige o aplicativo FECHADO (LIMPAR E VERIFICAR.cmd)."""
from fastapi import APIRouter,HTTPException
from .. import higiene as H,store

router=APIRouter()

def _raiz():
    if store.INSTALL is None:raise HTTPException(409,'Modo de desenvolvimento: não há pasta de instalação para verificar.')
    return store.INSTALL

@router.get('/api/higiene/verificar')
def verificar():return H.verificar(_raiz())

@router.get('/api/higiene/inventario')
def inventario(manter_backups:int=3):
    return H.limpar(_raiz(),False,manter_backups=max(1,min(20,manter_backups)))|{'notice':'Prévia: nada foi alterado. Para limpar, feche o aplicativo e use "LIMPAR E VERIFICAR.cmd"; o que sai vai para sistema\\_quarentena e pode ser restaurado.'}
