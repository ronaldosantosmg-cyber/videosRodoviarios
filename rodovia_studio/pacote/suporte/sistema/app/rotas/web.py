"""Imagem web: ladrilhos Esri, Wayback, fonte do projeto e catálogo QuickMapServices."""
import asyncio,json,os,sys,uuid,shutil,subprocess,threading,time,zipfile,re
from xml.etree.ElementTree import ParseError as ET_ERRORS
from pathlib import Path
from typing import List
from fastapi import APIRouter,UploadFile,File,Form,HTTPException,Request
from fastapi.responses import HTMLResponse,FileResponse,JSONResponse,Response
from pydantic import BaseModel as _BM,ConfigDict,Field
from .. import store
from ..models import Settings
from ..render import ASSETS
from .comum import *
from .comum import _config,_save_config,_receive,_files_meta,_files_info,_img_type,_project_wgs84
router=APIRouter()

# ---------------- 1.9: editor sobre imagem web ----------------
@router.get('/tiles/esri/{z}/{y}/{x}')
def esri_tile(z:int,y:int,x:int):
    from ..webmap import tile
    try:data=tile(store.ROOT/'_ladrilhos',z,y,x)
    except ValueError as e:raise HTTPException(422,str(e))
    except Exception:raise HTTPException(404,'Ladrilho indisponível (sem internet e sem cache).')
    return Response(data,media_type='image/jpeg',headers={'Cache-Control':'public, max-age=604800'})

@router.get('/api/wayback/releases')
def wayback_list():
    from ..webmap import wayback_releases
    try:return {'releases':wayback_releases(store.ROOT/'_ladrilhos')}
    except Exception as e:raise HTTPException(503,'Não foi possível obter a lista de datas da Esri Wayback (sem internet?). '+str(e)[:150])

@router.get('/api/projects/{pid}/web_tiles/{z}/{y}/{x}')
def project_web_tile(pid,z:int,y:int,x:int):
    """Ladrilho da fonte web escolhida no projeto (Esri atual, Wayback, XYZ ou WMS), com cache em disco."""
    from ..webmap import tile,web_source
    d,s=_config(pid)
    try:src=web_source(s);data=tile(store.ROOT/'_ladrilhos',z,y,x,source=src)
    except ValueError as e:raise HTTPException(422,str(e))
    except Exception:raise HTTPException(404,'Ladrilho indisponível (sem internet e sem cache).')
    return Response(data,media_type=_img_type(data),headers={'Cache-Control':'public, max-age=604800'})

@router.get('/api/projects/{pid}/qms/buscar')
def qms_search(pid,q:str='',tipo:str='todos',cobre:bool=True,funcionando:bool=True,so_imagem:bool=True,offset:int=0):
    from .. import qms
    if tipo not in ('todos','tms','wms'):raise HTTPException(422,'Tipo deve ser todos, tms ou wms.')
    if len(q)>80:raise HTTPException(422,'Texto de busca muito longo (máx. 80).')
    area=_project_wgs84(pid)[0] if cobre else None
    try:return qms.search(store.ROOT/'_ladrilhos',q,tipo,area,funcionando,so_imagem,40,max(0,offset))
    except RuntimeError as e:raise HTTPException(502,str(e))

@router.get('/api/qms/{sid}')
def qms_detail(sid:int):
    from .. import qms
    try:return qms.summary(qms.detail(store.ROOT/'_ladrilhos',sid))
    except ValueError as e:raise HTTPException(404,str(e))
    except RuntimeError as e:raise HTTPException(502,str(e))

@router.get('/api/projects/{pid}/qms/{sid}/teste')
def qms_test(pid,sid:int):
    """Baixa uma amostra no centro do trecho e mede nitidez e falhas (para comparar serviços)."""
    from .. import qms
    _,(lon,lat)=_project_wgs84(pid)
    try:d=qms.summary(qms.detail(store.ROOT/'_ladrilhos',sid))
    except ValueError as e:raise HTTPException(404,str(e))
    except RuntimeError as e:raise HTTPException(502,str(e))
    if not d['usable']:return {'id':sid,'usable':False,'reason':d['reason']}
    r=qms.sample(store.ROOT/'_ladrilhos',d['web_imagery'],lon,lat)
    return {'id':sid,'usable':True,'restricted':d['restricted'],'name':d['name'],'z_max':d['z_max'],**r}

class QmsUse(_BM):
    model_config=ConfigDict(extra='forbid')
    aceito_termos: bool = False

@router.post('/api/projects/{pid}/qms/{sid}/usar')
def qms_use(pid,sid:int,body:QmsUse):
    from .. import qms
    from ..models import WebImagery
    try:d=qms.summary(qms.detail(store.ROOT/'_ladrilhos',sid))
    except ValueError as e:raise HTTPException(404,str(e))
    except RuntimeError as e:raise HTTPException(502,str(e))
    if not d['usable']:raise HTTPException(422,d['reason'])
    if d['restricted'] and not body.aceito_termos:
        raise HTTPException(409,'Este provedor costuma proibir, nos termos de uso, baixar os ladrilhos para uso fora dos aplicativos dele. Confirme que a concessionária tem autorização para usar.')
    dd,s=_config(pid);s.web_imagery=WebImagery.model_validate(d['web_imagery']);_save_config(pid,s)
    return {'web_imagery':s.web_imagery.model_dump(),'service':d}
