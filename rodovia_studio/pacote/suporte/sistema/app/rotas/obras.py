"""1.35: obras do PER — ler planilha/cronograma (prévia, sem gravar), modelo do Excel, exportar e tipos."""
from fastapi import APIRouter,UploadFile,File,HTTPException
from fastapi.responses import Response
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
    _config(pid);data=await file.read();await file.close()
    if len(data)>30*1024*1024:raise HTTPException(413,'Arquivo maior que 30 MB.')
    try:rows,warn=read_any(data,file.filename or '')
    except (ValueError,KeyError) as e:raise HTTPException(422,str(e)[:400])
    return {'obras':[r for r in rows if not r.get('sem_km')],'sem_km':[r for r in rows if r.get('sem_km')],'avisos':warn,'arquivo':file.filename}

@router.get('/api/projects/{pid}/obras.xlsx')
def exportar(pid):
    from ..obras import export_xlsx
    d,s=_config(pid)
    return Response(export_xlsx([w.model_dump() for w in s.works]),media_type=XLSX,headers={'Content-Disposition':'attachment; filename="obras_PER.xlsx"'})
