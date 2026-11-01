"""1.42.38: purga de imagens e reinício das análises não ficam presos por tarefa pendente."""
import numpy as np,cv2
from pathlib import Path
from fastapi.testclient import TestClient


def _projeto_com_imagem(c):
    from app import store
    from app.models import Settings
    pid=c.post('/api/projects',json=Settings(name='Purga').model_dump()).json()['id']
    png=cv2.imencode('.png',np.zeros((8,8,3),np.uint8))[1].tobytes()
    r=c.post(f'/api/projects/{pid}/imagery',files=[('files',('foto.png',png,'image/png')),('files',('foto.pgw',b'1\n0\n0\n-1\n0\n8\n','text/plain'))],data={'crs':'EPSG:31983'})
    assert r.status_code in (200,201),r.text
    return pid,store.ROOT/pid


def _job(pid,estado):
    import uuid
    from app import store
    jid=uuid.uuid4().hex
    with store.connect() as k:k.execute("INSERT INTO jobs(id,project,kind,state,message,created) VALUES(?,?,?,?,?,datetime('now'))",(jid,pid,'analyze',estado,'x'))
    return jid


def test_remover_imagem_so_do_mosaico_ou_com_arquivo():
    from app.server import app
    c=TestClient(app);pid,d=_projeto_com_imagem(c)
    pasta=d/'imagem_local';antes=sorted(p.name for p in pasta.iterdir())
    assert any(n.endswith('.png') for n in antes)
    r=c.delete(f'/api/projects/{pid}/imagery/0');assert r.status_code==200 and r.json()['arquivos_apagados']==[]
    assert sorted(p.name for p in pasta.iterdir())==antes          # padrão: arquivo preservado
    pid,d=_projeto_com_imagem(c);pasta=d/'imagem_local'
    r=c.delete(f'/api/projects/{pid}/imagery/0?arquivo=true');assert r.status_code==200
    assert r.json()['arquivos_apagados'] and not [p for p in pasta.iterdir() if p.suffix in ('.png','.pgw')]


def test_limpeza_reinicia_analises_sem_tocar_em_entradas():
    from app.server import app
    from app import maintenance
    c=TestClient(app);pid,d=_projeto_com_imagem(c)
    for n in ('analysis.json','editor.json','vectors.json','preview.png','preview.json','video.mp4'):(d/n).write_bytes(b'{}')
    (d/'config.json').exists() or (d/'config.json').write_text('{}')
    cfg=(d/'config.json').read_bytes()
    r=c.post('/api/limpeza',json={'categorias':['analises']});assert r.status_code==200,r.text
    for n in ('analysis.json','editor.json','vectors.json','preview.png','preview.json'):assert not (d/n).exists()
    assert (d/'video.mp4').exists() and (d/'config.json').read_bytes()==cfg and any((d/'imagem_local').iterdir())
    assert 'analises' in maintenance.CATEGORIAS and maintenance.CATEGORIAS['analises'][2] is False   # nunca marcada por padrão


def test_tarefa_na_fila_bloqueia_mas_pode_ser_cancelada():
    from app.server import app
    from app import store
    from app.server import maintenance_pending
    c=TestClient(app);pid,d=_projeto_com_imagem(c)
    maintenance_pending.set()                                    # impede o despachante de iniciar a tarefa durante o teste
    try:_teste_fila(c,pid,store)
    finally:maintenance_pending.clear()


def _teste_fila(c,pid,store):
    jid=_job(pid,'queued')
    r=c.post('/api/limpeza',json={'categorias':['caches']});assert r.status_code==409 and 'cancelar tarefas pendentes' in r.text
    r=c.post('/api/limpeza',json={'categorias':['caches'],'cancelar_pendentes':True});assert r.status_code==200,r.text
    with store.connect() as k:assert k.execute("SELECT state FROM jobs WHERE id=?",(jid,)).fetchone()[0]=='cancelled'
