"""Recalcular uma vez cada derivação no contexto de uma tarefa completa."""
from contextvars import ContextVar
from contextlib import contextmanager

_current=ContextVar('rodovia_full_update',default=None)

@contextmanager
def complete_update(enabled=True):
    token=_current.set(set() if enabled else None)
    try:yield
    finally:_current.reset(token)

def required(kind,key):
    current=_current.get()
    return current is not None and (kind,str(key)) not in current

def rebuilt(kind,key):
    current=_current.get()
    if current is not None:current.add((kind,str(key)))
