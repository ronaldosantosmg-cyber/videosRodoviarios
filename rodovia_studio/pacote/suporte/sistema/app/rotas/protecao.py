from fastapi import APIRouter
from pydantic import Field
from .. import store,project_integrity as I,assisted_execution as E
from ..assistance import Strict
from .comum import dispatch_lock,idle,enqueue
router=APIRouter()
class Recovery(Strict):
    revision:str=Field(pattern='^[a-f0-9]{64}$')
    report_id:str=Field(pattern='^[a-f0-9]{64}$')
class Proposal(Strict):
    segment:int=Field(ge=0)
    action:str=Field(default='auto',pattern='^(auto|recover|reconstruct)$')
    signature:str=Field(pattern='^[a-f0-9]{64}$')
@router.get('/api/projects/{pid}/integridade')
def inspect(pid):return I.inspect(store.directory(pid))
@router.post('/api/projects/{pid}/integridade/recuperar')
def recover(pid,body:Recovery):
    with dispatch_lock:
        idle(pid);return I.recover(store.directory(pid),body.revision,body.report_id)
@router.get('/api/projects/{pid}/assistencia/execucao')
def execution(pid):
    from ..artifacts import require_current
    import json
    d=store.directory(pid);require_current(d,'editor');data=json.loads((d/'editor.json').read_text())
    return {'signature':E.signature(d),'segments':data['segments']}
@router.post('/api/projects/{pid}/assisted_plan',status_code=202)
def propose(pid,body:Proposal):
    with dispatch_lock:
        idle(pid);d=store.directory(pid)
        if body.signature!=E.signature(d):
            from ..project_state import Conflict
            raise Conflict('Diagnóstico desatualizado.')
        store.write_json(E.folder(d)/'pedido.json',body.model_dump());return enqueue(pid,'assisted_plan')
@router.get('/api/projects/{pid}/assistencia/execucao/proposta')
def latest(pid):
    import json
    d=store.directory(pid);key=json.loads((E.folder(d)/'ultima.json').read_text())['id'];return E.load(d,key)
@router.post('/api/projects/{pid}/assistencia/execucao/{key}/aplicar')
def apply(pid,key):
    with dispatch_lock:
        idle(pid);return E.apply(store.directory(pid),key)
@router.post('/api/projects/{pid}/assistencia/execucao/{key}/desfazer')
def undo(pid,key):
    with dispatch_lock:
        idle(pid);return E.undo(store.directory(pid),key)
@router.get('/api/projects/{pid}/assistencia/execucao/{key}/resultado')
def outcome(pid,key):return E.outcome(store.directory(pid),key)
