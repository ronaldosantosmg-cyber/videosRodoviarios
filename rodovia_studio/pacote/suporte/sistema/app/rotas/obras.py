"""1.35: obras do PER — ler planilha/cronograma (prévia, sem gravar), modelo do Excel, exportar e tipos."""
from fastapi import APIRouter,UploadFile,File,HTTPException
from fastapi.responses import Response
import asyncio
from ..models import Settings,PERWork
from pydantic import ValidationError
from .comum import _config
router=APIRouter()
XLSX='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

@router.get('/api/obras/tipos')
def tipos():
    from ..obras import WORK_STYLE
    return [{'id':k,'rotulo':v[0],'cor':v[1],'sigla':v[2]} for k,v in WORK_STYLE.items()]

@router.get('/api/obras/modelo.xlsx')
def modelo():
    from ..obras import template_xlsx
    return Response(template_xlsx(),media_type=XLSX,headers={'Content-Disposition':'attachment; filename="modelo_obras_PER.xlsx"'})

@router.post('/api/projects/{pid}/obras/ler')
async def ler(pid,file:UploadFile=File(...)):
    """Lê Excel (.xlsx), CSV ou cronograma do MS Project (.xml) e devolve as obras para conferência (nada é gravado)."""
    from ..obras import read_any
    d,s=_config(pid);data=await file.read();await file.close()
    if len(data)>30*1024*1024:raise HTTPException(413,'Arquivo maior que 30 MB.')
    try:rows,warn=read_any(data,file.filename or '')
    except (ValueError,KeyError) as e:raise HTTPException(422,str(e)[:400])
    valid=[r for r in rows if not r.get('sem_km')];location=None
    if valid and (d/'input.dxf').is_file():
        try:location=await asyncio.to_thread(_locate,d,s,valid)
        except (ValueError,OSError,ValidationError) as error:warn.append('Localização pendente: '+str(error)[:240])
    return {'obras':valid,'sem_km':[r for r in rows if r.get('sem_km')],'avisos':warn,'arquivo':file.filename,'localizacao':location}

@router.get('/api/projects/{pid}/obras.xlsx')
def exportar(pid):
    from ..obras import export_xlsx
    d,s=_config(pid)
    return Response(export_xlsx([w.model_dump() for w in s.works]),media_type=XLSX,headers={'Content-Disposition':'attachment; filename="obras_PER.xlsx"'})


def _locate(directory,settings,works=None):
    from ..geometry import analyze
    from ..per_positioning import locate_works
    _,axis,_,_,_=analyze(directory,settings)
    return locate_works(settings,axis,works)

@router.post('/api/projects/{pid}/obras/localizar')
async def localizar(pid,body:dict):
    """Prévia somente leitura; usa também a configuração ainda em edição, validada."""
    d,s=_config(pid)
    try:
        if set(body)-{'config','works'}:raise ValueError('Campos de localização não reconhecidos.')
        if body.get('config') is not None:s=Settings.model_validate(body['config'])
        works=body.get('works')
        if works is not None:
            if not isinstance(works,list) or len(works)>1000:raise ValueError('Informe até 1000 obras.')
            works=[PERWork.model_validate(w) for w in works]
        return await asyncio.to_thread(_locate,d,s,works)
    except (ValueError,OSError,ValidationError) as error:raise HTTPException(422,str(error)[:500])
