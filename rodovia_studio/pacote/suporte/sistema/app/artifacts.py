"""Proveniência dos resultados: nenhuma tarefa antiga torna um resultado atual."""
import json,time
from pathlib import Path
from .project_state import locked,_state,_write
from .dependencies import FILES,revisions

OUTPUTS={'refresh':('analysis','editor','vectors','preview'),'analyze':('analysis','editor','vectors'),'preview':('analysis','editor','vectors','preview'),'scene3d':('analysis','editor','vectors','scene3d'),'render':('analysis','editor','vectors','video')}

def _read(d):
    p=_state(d)/'resultados.json'
    if not p.exists():return {}
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (ValueError,OSError):return {}

def stamps(d,kind):
    rows=[]
    for name in FILES[kind]:
        p=Path(d)/name
        if not p.is_file() or p.is_symlink():return None
        st=p.stat();rows.append([name,st.st_size,st.st_mtime_ns])
    return rows

def begin(d,jid,kind,settings):
    with locked(d):
        keys=revisions(d,settings);rows=_read(d)
        for name in OUTPUTS.get(kind,()):rows[name]={'job':jid,'revision':keys[name],'state':'processing','time':time.time()}
        _write(_state(d)/'resultados.json',rows)
        return {'job':jid,'kind':kind,'keys':keys}

def finish(d,ticket,success=True):
    if ticket is None:return
    with locked(d):
        rows=_read(d)
        for name in OUTPUTS.get(ticket['kind'],()):
            row=rows.get(name,{})
            if row.get('job')!=ticket['job']:continue
            files=stamps(d,name)
            row.update(state='ready' if success and files else 'failed',files=files,time=time.time())
        _write(_state(d)/'resultados.json',rows)

def status(d,keys=None):
    with locked(d):
        keys=keys or revisions(d);rows=_read(d);out={}
        for name in FILES:
            row=rows.get(name);files=stamps(d,name)
            if not files:state='missing'
            elif row:
                state=row['state']
                if state=='ready' and (row.get('revision')!=keys[name] or row.get('files')!=files):state='stale'
            elif name in ('editor','scene3d'):
                try:
                    doc=json.loads((Path(d)/FILES[name][0]).read_text(encoding='utf-8'))
                    state='ready' if doc.get('engine_revision' if name=='editor' else 'revision')==keys[name] else 'stale'
                except (ValueError,OSError):state='stale'
            else:state='unverified'
            out[name]={'state':state,'revision':row.get('revision') if row else None}
        return out


def require_current(d,kind):
    from fastapi import HTTPException
    row=status(d)[kind]
    if row['state'] in ('stale','processing','failed'):
        raise HTTPException(409,'Resultado desatualizado ou em processamento. Atualize o projeto antes de usar esta visualização.')
