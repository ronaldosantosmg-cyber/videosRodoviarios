"""2.57: texturas no pacote, atualização só de componentes e instalador da IA local."""
import json,zipfile,hashlib
from pathlib import Path
import numpy as np,pytest
from app import texturas_pacote as T,componentes as C,ia_instalar as I

def test_texturas_do_pacote_integras():
    st=T.status();assert st['ok'] and st['total']>=7,st
    X,Y=np.meshgrid(np.linspace(0,.2,64),np.linspace(0,.2,64));f=T.detalhe('asfalto_escuro',X,Y);assert f is not None and abs(f.mean()-1)<.25 and f.std()>.03

def test_relevo_usa_texturas_em_zoom_proximo_e_cai_para_procedural():
    from app import relevo
    c=np.full((64,64,3),70.);a=relevo.acabar(c,'pavement',10.,10.,.002,seed=3)
    T._cache['asfalto_escuro']=None;b=relevo.acabar(c,'pavement',10.,10.,.002,seed=3);T.limpar_cache()
    assert a.shape==b.shape and not np.array_equal(a,b)
    far=relevo.acabar(c,'pavement',10.,10.,.05,seed=3);T._cache['asfalto_escuro']=None;far2=relevo.acabar(c,'pavement',10.,10.,.05,seed=3);T.limpar_cache()
    assert np.array_equal(far,far2)                                  # longe: sem mudança

def _inst(tmp):
    r=tmp/'inst';(r/'sistema/programa/app').mkdir(parents=True);(r/'sistema/programa/app/server.py').write_text('#');(r/'sistema/programa/VERSAO.json').write_text('{"version":"2.56"}')
    (r/'sistema/programa/assets/texturas').mkdir(parents=True);(r/'sistema/programa/assets/texturas/a.jpg').write_bytes(b'velho')
    for n in ('projetos','videos','atualizacoes'):(r/n).mkdir()
    return r
def _zip(tmp,arquivos,nome='RodoviaStudio_componentes_t_2.zip'):
    o=tmp/'o';o.mkdir(exist_ok=True)
    for k,v in arquivos.items():(o/k).parent.mkdir(parents=True,exist_ok=True);(o/k).write_bytes(v)
    out=tmp/nome
    if 'texturas' in {k.split('/')[0] for k in arquivos}:C.empacotar(out,texturas=o/'texturas',versao_texturas='2')
    return out

def test_instala_so_componentes_com_backup_e_restaura(tmp_path):
    r=_inst(tmp_path);z=_zip(tmp_path,{'texturas/a.jpg':b'novo','texturas/b.jpg':b'extra'})
    C.instalar(r,z,check_running=False)
    t=r/'sistema/programa/assets/texturas';assert (t/'a.jpg').read_bytes()==b'novo' and (t/'b.jpg').exists()
    assert (r/'sistema/programa/VERSAO.json').read_text()=='{"version":"2.56"}'            # programa intacto
    assert C.estado_instalado(r)['texturas']['versao']=='2'
    C.restaurar(r,check_running=False);assert (t/'a.jpg').read_bytes()==b'velho'

def test_recusa_pacotes_perigosos(tmp_path):
    r=_inst(tmp_path)
    def mk(nome,man,arq):
        p=tmp_path/nome
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('componente.json',json.dumps(man))
            for k,v in arq.items():z.writestr(k,v)
        return p
    h=lambda b:hashlib.sha256(b).hexdigest()
    for nome,man,arq in [
        ('a.zip',{'tipo':'componentes','componentes':{'texturas':{'files':{'texturas/../x':h(b'1')}}}},{'texturas/../x':b'1'}),
        ('b.zip',{'tipo':'componentes','componentes':{'app':{'files':{'app/server.py':h(b'1')}}}},{'app/server.py':b'1'}),
        ('c.zip',{'tipo':'componentes','componentes':{'texturas':{'files':{'texturas/a.jpg':h(b'1')}}}},{'texturas/a.jpg':b'2'}),
        ('d.zip',{'tipo':'componentes','componentes':{'texturas':{'files':{'texturas/a.jpg':h(b'1')}}}},{'texturas/a.jpg':b'1','extra.py':b'x'}),
        ('e.zip',{'tipo':'outro','componentes':{}},{})]:
        with pytest.raises(C.ComponenteErro):C.instalar(r,mk(nome,man,arq),check_running=False)
    assert (r/'sistema/programa/assets/texturas/a.jpg').read_bytes()==b'velho'

def test_pendentes_vao_para_aplicadas_e_invalidos_para_rejeitadas(tmp_path):
    r=_inst(tmp_path);d=r/'atualizacoes/componentes';d.mkdir()
    z=_zip(tmp_path,{'texturas/a.jpg':b'n'});(d/z.name).write_bytes(z.read_bytes());(d/'RodoviaStudio_componentes_ruim.zip').write_bytes(b'nao e zip')
    C.instalar_pendentes(r,say=lambda *_:None,check_running=False)
    assert (r/'atualizacoes/aplicadas'/z.name).exists() and (r/'atualizacoes/rejeitadas/RodoviaStudio_componentes_ruim.zip').exists()

def test_full_update_ignora_zip_de_componentes():
    import atualizador;assert not atualizador.ZIP_RE.search('RodoviaStudio_componentes_texturas_ia_v1.zip')

def test_instalar_ia_local_gera_manifesto_aceito_pelo_small_ai(tmp_path):
    import os
    g=tmp_path/'m.gguf';g.write_bytes(b'GGUF'+b'0'*100);rt=tmp_path/'rt';rt.mkdir();(rt/('llama-server.exe' if os.name=='nt' else 'llama-server')).write_bytes(b'x')
    I.instalar_local(g,rt,tmp_path/'raiz',say=lambda *_:None)
    from app import small_ai;d=tmp_path/'raiz'/'modelos_ia'
    m=json.loads((d/'modelo.json').read_text());assert 'modelo.gguf' in m['files'] and m['quantization']=='Q4_K_M'
    small_ai.assets=lambda:d;small_ai._files()                                          # manifesto aceito
    with pytest.raises(ValueError):I._baixar('http://huggingface.co/x',tmp_path/'x',print)
    with pytest.raises(ValueError):I._baixar('https://exemplo.com/x',tmp_path/'x',print)

def test_rotas_registradas(monkeypatch,tmp_path):
    monkeypatch.setenv('RODOVIA_DATA',str(tmp_path/'d'))
    from fastapi.testclient import TestClient
    from app.server import app
    c=TestClient(app,base_url='http://127.0.0.1');r=c.get('/api/componentes/status');assert r.status_code==200 and r.json()['texturas']['ok']
    assert c.post('/api/projects/x/ia/correcoes/consultar-local',json={'fase':'xyz'}).status_code in (404,422)
