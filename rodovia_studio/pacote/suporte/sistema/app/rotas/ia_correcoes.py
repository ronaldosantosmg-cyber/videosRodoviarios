"""2.56: correções tipadas propostas por regras/IA (ver app/ia_correcoes.py)."""
from fastapi import APIRouter,HTTPException
from pydantic import Field,ValidationError
from .. import store,ia_correcoes as C
from ..assistance import Strict
from ..project_state import Conflict
from .comum import dispatch_lock,idle

router=APIRouter()
class Aplicar(Strict):
    revisao:str=Field(pattern='^[a-f0-9]{64}$')
    ids:list[str]=Field(min_length=1,max_length=30)
class Texto(Strict):texto:str=Field(min_length=2,max_length=20000)
class Desfazer(Strict):lote:str=Field(min_length=10,max_length=40)

def _d(pid):
    try:return store.directory(pid)
    except (ValueError,FileNotFoundError) as e:raise HTTPException(404,str(e))
def _err(e):
    if isinstance(e,Conflict):return HTTPException(409,str(e))
    if isinstance(e,ValidationError):return HTTPException(422,'Correção fora do contrato do aplicativo; nada foi aplicado.')
    return HTTPException(422,str(e)[:500])

@router.get('/api/projects/{pid}/ia/correcoes')
def listar(pid,fase:str|None=None):
    if fase is not None and fase not in C.FASES:raise HTTPException(422,'Fase inválida.')
    try:return C.coletar(_d(pid),fase)
    except (ValueError,OSError) as e:raise _err(e)

@router.get('/api/projects/{pid}/ia/correcoes/prompt')
def prompt(pid,fase:str):
    if fase not in C.FASES:raise HTTPException(422,'Fase inválida.')
    return C.montar_prompt(_d(pid),fase)

@router.post('/api/projects/{pid}/ia/correcoes/interpretar')
def interpretar(pid,body:Texto):
    try:return C.interpretar_resposta(_d(pid),body.texto)
    except (ValueError,KeyError,TypeError,OSError) as e:raise _err(e)

@router.post('/api/projects/{pid}/ia/correcoes/aplicar')
def aplicar(pid,body:Aplicar):
    with dispatch_lock:
        idle(pid)
        try:
            d=_d(pid);atuais={c['id']:c for c in C.coletar(d)['correcoes']}
            falta=[i for i in body.ids if i not in atuais]
            if falta:raise ValueError('Correção(ões) fora da lista atual: '+', '.join(falta[:5]))
            return C.aplicar(d,[atuais[i] for i in body.ids],body.revisao)
        except (ValueError,KeyError,TypeError,OSError,ValidationError,Conflict) as e:raise _err(e)

@router.get('/api/projects/{pid}/ia/correcoes/lotes')
def lotes(pid):return {'lotes':C.lotes(_d(pid))}

@router.post('/api/projects/{pid}/ia/correcoes/desfazer')
def desfazer(pid,body:Desfazer):
    with dispatch_lock:
        idle(pid)
        try:return C.desfazer(_d(pid),body.lote)
        except (ValueError,KeyError,TypeError,OSError,ValidationError,Conflict) as e:raise _err(e)

class Consulta(Strict):fase:str

@router.post('/api/projects/{pid}/ia/correcoes/consultar-local')
def consultar_local(pid,body:Consulta):
    if body.fase not in C.FASES:raise HTTPException(422,'Fase inválida.')
    try:return C.consultar_local(_d(pid),body.fase)
    except InterruptedError as e:raise HTTPException(409,str(e))
    except (ValueError,KeyError,TypeError,OSError,ValidationError,Conflict,TimeoutError) as e:raise _err(e)
