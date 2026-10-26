"""Autentica snapshots IPC criados pelo próprio processo; chave fora do disco."""
import hashlib,hmac,json,secrets
from pathlib import Path
LIMIT=256*1024*1024

def file_hash(p):
    if p.is_symlink():raise ValueError('Snapshot por link recusado.')
    h=hashlib.sha256()
    with p.open('rb') as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()

def sign(folder,names):
    folder=Path(folder)
    if folder.is_symlink():raise ValueError('Pasta de snapshot inválida.')
    key=secrets.token_bytes(32);rows={n:file_hash(folder/n) for n in names};raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    (folder/'autenticacao.json').write_text(json.dumps({'files':rows,'mac':hmac.new(key,raw,'sha256').hexdigest()}));return key.hex()

def verify(folder,key,allowed):
    if not isinstance(key,str) or len(key)!=64:raise ValueError('Snapshot sem chave da sessão atual; gere novamente.')
    folder=Path(folder);manifest=folder/'autenticacao.json'
    if folder.is_symlink() or manifest.is_symlink() or manifest.stat().st_size>10000:raise ValueError('Manifesto de snapshot inválido.')
    data=json.loads(manifest.read_text());rows=data['files']
    if not isinstance(rows,dict) or 'scene.pkl' not in rows or not set(rows)<=set(allowed):raise ValueError('Arquivos de snapshot inválidos.')
    raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    if not hmac.compare_digest(hmac.new(bytes.fromhex(key),raw,'sha256').hexdigest(),data['mac']):raise ValueError('Snapshot alterado; autenticação recusada.')
    payload=folder/'scene.pkl'
    if payload.is_symlink() or payload.stat().st_size>LIMIT:raise ValueError('Snapshot excede o limite de 256 MiB.')
    content=payload.read_bytes()
    if hashlib.sha256(content).hexdigest()!=rows['scene.pkl']:raise ValueError('Snapshot alterado; conteúdo recusado.')
    for name,sha in rows.items():
        if name!='scene.pkl' and file_hash(folder/name)!=sha:raise ValueError('Matriz de snapshot alterada; conteúdo recusado.')
    return content
