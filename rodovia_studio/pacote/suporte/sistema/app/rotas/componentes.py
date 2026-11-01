"""2.57: estado das texturas do pacote e da IA local."""
from fastapi import APIRouter
from .. import texturas_pacote,small_ai

router=APIRouter()
@router.get('/api/componentes/status')
def status():
    from .. import store
    try:
        from ..componentes import estado_instalado
        inst=estado_instalado(store.INSTALL) if store.INSTALL else {}
    except Exception:inst={}
    return {'texturas':texturas_pacote.status(),'ia':{k:v for k,v in small_ai.status().items() if k in ('installed','message','candidate','folder')},'componentes_instalados':inst,
            'como_atualizar':'Coloque RodoviaStudio_componentes_*.zip em atualizacoes/componentes e execute ATUALIZAR TEXTURAS E IA.cmd com o aplicativo fechado.'}
