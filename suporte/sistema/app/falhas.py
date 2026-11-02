"""2.28: registro de falhas tratadas (antes engolidas por `except ...: pass`).

Não altera o comportamento: a exceção continua sendo ignorada, mas fica guardada (últimas 200) e vai ao log
`rodovia.falhas` em nível DEBUG, para diagnóstico. `resumo()` alimenta relatórios e testes.
"""
import logging,threading,time
_LOG=logging.getLogger('rodovia.falhas');_LOCK=threading.Lock();_ULTIMAS=[]
def registrar(origem,exc):
    try:
        item={'t':time.time(),'origem':str(origem),'tipo':type(exc).__name__,'msg':str(exc)[:300]}
        with _LOCK:
            _ULTIMAS.append(item)
            if len(_ULTIMAS)>200:del _ULTIMAS[0]
        _LOG.debug('%s: %s: %s',item['origem'],item['tipo'],item['msg'])
    except Exception:
        pass
def resumo():
    with _LOCK:
        por={}
        for i in _ULTIMAS:por[i['origem']]=por.get(i['origem'],0)+1
        return {'total':len(_ULTIMAS),'por_modulo':por,'ultimas':list(_ULTIMAS[-10:])}
