"""Projetos: criar, listar, abrir, renomear, salvar como, retirar, configuração, pacote e importação."""
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

@router.get('/api/projects')
def projects():
    with store.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM projects ORDER BY created DESC,rowid DESC')]
@router.post('/api/projects',status_code=201)
def create(s:Settings):
    pid=uuid.uuid4().hex;d=store.ROOT/pid;d.mkdir();store.write_json(d/'config.json',s.model_dump())
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,s.name))
    return {'id':pid,'config':s.model_dump()}
# ---------------- 1.19: limpar trabalho / retirar projeto ----------------
class ResetBody(_BM):
    groups:list[str]=['obras','sinalizacao']
    outputs:bool=False

@router.get('/api/reset_groups')
def reset_groups():
    from ..workreset import GROUPS,DEFAULT
    return {'groups':[{'id':k,'label':v[0],'keys':v[1],'default':k in DEFAULT} for k,v in GROUPS.items()]}

@router.post('/api/projects/{pid}/reset_work')
def reset_work(pid,body:ResetBody):
    """Limpa as marcações escolhidas e mantém as características do segmento (com cópia da configuração)."""
    from ..workreset import reset
    idle(pid);d,s=_config(pid)
    try:new,info=reset(d,s,body.groups,body.outputs)
    except ValueError as e:raise HTTPException(422,str(e))
    _save_config(pid,new);return {'config':new.model_dump(),**info}

@router.post('/api/projects/{pid}/reset_work/undo')
def reset_work_undo(pid):
    from ..workreset import undo
    idle(pid);d=store.directory(pid)
    try:s,name=undo(d)
    except ValueError as e:raise HTTPException(409,str(e))
    _save_config(pid,s);return {'config':s.model_dump(),'restored':name}

class SaveAsBody(_BM):
    name:str=Field(min_length=1,max_length=100)

@router.post('/api/projects/{pid}/save_as',status_code=201)
def project_save_as(pid,body:SaveAsBody):
    """1.22: “Salvar como”: cópia do projeto (configuração, DXF/KMZ, imagens locais, camadas e elevação), sem caches."""
    d,s=_config(pid);new=uuid.uuid4().hex;nd=store.ROOT/new;nd.mkdir()
    try:
        for item in d.iterdir():
            if item.name.startswith(('cache','config_antes','config_restaurado')) or item.suffix in ('.mp4','.tmp') or item.name in ('preview.png','video.json','encoder.json','ffmpeg.log'):continue
            if item.is_dir():
                if item.name in ('imagem_local','camadas','elevacao','hidrografia'):shutil.copytree(item,nd/item.name)
                continue
            shutil.copy2(item,nd/item.name)
        s.name=body.name;store.write_json(nd/'config.json',s.model_dump())
    except Exception:
        shutil.rmtree(nd,ignore_errors=True);raise
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(new,body.name))
    return {'id':new,'name':body.name}

@router.delete('/api/projects/{pid}')
def project_trash(pid):
    """Retira o projeto da lista: a pasta vai para _lixeira (pode ser recuperada manualmente)."""
    from ..workreset import trash
    idle(pid);store.directory(pid)
    dst=trash(store.ROOT,pid)
    with store.connect() as c:c.execute('DELETE FROM projects WHERE id=?',(pid,))
    return {'trash':dst.name}

# ---------------- 1.30: abrir projeto, renomear e modelos ----------------
@router.get('/api/projects_info')
def projects_info():
    """Lista para a janela “Abrir projeto”: nome, criação, última gravação, arquivos e se há prévia."""
    out=[]
    with store.connect() as c:rows=[dict(r) for r in c.execute('SELECT * FROM projects ORDER BY created DESC,rowid DESC')]
    for r in rows:
        d=store.ROOT/r['id'];cf=d/'config.json'
        if not cf.exists():r['missing']=True;out.append(r);continue
        r['modified']=time.strftime('%Y-%m-%d %H:%M',time.localtime(cf.stat().st_mtime))
        r['files']={'dxf':(d/'input.dxf').exists(),'kmz':(d/'input.kmz').exists()}
        meta=_files_meta(d);r['file_names']={k:v.get('name') for k,v in meta.items() if isinstance(v,dict)}
        r['preview']=(d/'preview.png').exists();r['video']=(d/'video.mp4').exists();r['analyzed']=(d/'analysis.json').exists()
        try:
            j=json.loads(cf.read_text(encoding='utf-8'));r['origin']=j.get('origin','');r['destination']=j.get('destination','')
            r['km']=[j.get('km_start_m'),j.get('km_end_m')]
        except Exception:pass
        out.append(r)
    return out

@router.get('/api/projects/{pid}/miniatura.jpg')
def project_thumb(pid):
    """Miniatura da prévia (320 px), guardada em miniatura.jpg e refeita quando a prévia muda."""
    import cv2,numpy as np
    d=store.directory(pid);src=d/'preview.png';dst=d/'miniatura.jpg'
    if not src.exists():raise HTTPException(404,'Projeto sem prévia.')
    if not dst.exists() or dst.stat().st_mtime<src.stat().st_mtime:
        im=cv2.imdecode(np.fromfile(str(src),np.uint8),cv2.IMREAD_COLOR)
        if im is None:raise HTTPException(404,'Prévia ilegível.')
        h,w=im.shape[:2];k=320/max(w,1);im=cv2.resize(im,(320,max(1,int(h*k))),interpolation=cv2.INTER_AREA)
        ok,buf=cv2.imencode('.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,82]);tmp=dst.with_suffix('.tmp');tmp.write_bytes(buf.tobytes());store.replace(tmp,dst)
    return FileResponse(dst,media_type='image/jpeg',headers={'Cache-Control':'no-store'})

class RenameBody(_BM):
    name:str=Field(min_length=1,max_length=100)

@router.post('/api/projects/{pid}/rename')
def project_rename(pid,body:RenameBody):
    from ..migration import clean_name
    n=clean_name(body.name,'')
    if not n:raise HTTPException(422,'Nome inválido: use pelo menos uma letra ou número.')
    d,s=_config(pid);s.name=n;store.write_json(d/'config.json',s.model_dump())
    with store.connect() as c:c.execute('UPDATE projects SET name=? WHERE id=?',(n,pid))
    return {'id':pid,'name':n}

@router.post('/api/example',status_code=201)
def example():
    s=Settings.model_validate(json.loads((ASSETS/'th57/config.json').read_text(encoding='utf-8')));r=create(s);d=store.directory(r['id']);shutil.copyfile(ASSETS/'th57/projeto.dxf',d/'input.dxf');return r
@router.get('/api/projects/{pid}')
def get_project(pid):
    d=store.directory(pid);r={'id':pid,'config':Settings.model_validate_json((d/'config.json').read_text(encoding='utf-8')).model_dump(),'files':{'dxf':(d/'input.dxf').exists(),'kmz':(d/'input.kmz').exists()},'files_info':_files_info(d)}
    if (d/'analysis.json').exists():r['analysis']=json.loads((d/'analysis.json').read_text(encoding='utf-8'))
    if (d/'video.json').exists():r['render_info']=json.loads((d/'video.json').read_text(encoding='utf-8'))
    if (d/'preview.json').exists():r['preview']=json.loads((d/'preview.json').read_text(encoding='utf-8'))
    r['editor_ready']=(d/'editor.json').exists()
    return r
@router.put('/api/projects/{pid}/config')
def config(pid,s:Settings):
    # 1.28: a configuração pode ser salva com uma tarefa em andamento (a tarefa já leu a configuração ao começar).
    # Antes a gravação era recusada e a edição feita durante a tarefa se perdia ao recarregar.
    d=store.directory(pid);store.write_json(d/'config.json',s.model_dump())
    with store.connect() as c:c.execute('UPDATE projects SET name=? WHERE id=?',(s.name,pid))
    return {'ok':True}
@router.get('/api/projects/{pid}/config.json')
def config_file(pid):return FileResponse(store.directory(pid)/'config.json',filename='configuracao_rodovia.json')

@router.get('/api/projects/{pid}/package.zip')
def package_zip(pid):
    from ..exporters import package
    d,s=_config(pid);data=package(d,VERSION)
    safe=re.sub(r'[^\w\-]+','_',s.name)[:60] or 'projeto'
    return Response(data,media_type='application/zip',headers={'Content-Disposition':f'attachment; filename="{safe}.rodovia.zip"'})

@router.post('/api/import_package',status_code=201)
async def import_package(file:UploadFile=File(...)):
    from ..exporters import unpack
    data=await file.read();await file.close()
    if len(data)>900*1024*1024:raise HTTPException(413,'Pacote acima de 900 MB.')
    pid=uuid.uuid4().hex;d=store.ROOT/pid;d.mkdir()
    try:
        unpack(data,d);s=Settings.model_validate(json.loads((d/'config.json').read_text(encoding='utf-8')))
        store.write_json(d/'config.json',s.model_dump())
    except Exception as e:
        shutil.rmtree(d,ignore_errors=True)
        raise HTTPException(422,'Pacote inválido: '+str(e)[:300])
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,s.name))
    return {'id':pid,'config':s.model_dump()}

@router.post('/api/projects/{pid}/import_markings')
async def import_markings(pid,file:UploadFile=File(...)):
    from ..exporters import read_any,apply_import
    from ..per import read_csv
    idle(pid);data=await file.read();await file.close();d,s=_config(pid)
    if Path(file.filename or '').suffix.lower()=='.csv':
        works=read_csv(data);s.works=works;_save_config(pid,s);return {'imported':{'works':len(works)}}
    try:feats=read_any(data,file.filename or '',s.crs)
    except Exception as e:raise HTTPException(422,"Arquivo não reconhecido: "+str(e)[:300])
    cfg,counts=apply_import(s.model_dump(),feats)
    if not counts:raise HTTPException(422,'Nenhuma marcação do Rodovia Studio encontrada no arquivo.')
    s=Settings.model_validate(cfg);_save_config(pid,s)
    return {'imported':counts}
