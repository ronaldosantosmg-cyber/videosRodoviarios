import json,os,time,shutil
from pathlib import Path
import pytest
from app import higiene as H

def _mk(p,txt='x',old=None):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt,encoding='utf-8')
    if old:
        os.utime(p,(old,old))
        if p.parent.name.startswith(('antes_','legado_')):os.utime(p.parent,(old,old))
    return p

@pytest.fixture
def inst(tmp_path):
    r=tmp_path/'Rodovia_Studio';P=r/'sistema/programa'
    _mk(P/'app/server.py','from . import util\nfrom .util import x\n');_mk(P/'app/__init__.py','');_mk(P/'app/util.py','x=1\n')
    _mk(P/'app/index.html','<script src="js/a.js"></script><link href="css/s.css">');_mk(P/'app/js/a.js','1');_mk(P/'app/css/s.css','1')
    for n in ('run.py','iniciar.ps1','preparar.py','requirements.txt','atualizador.py'):_mk(P/n,'#')
    _mk(P/'VERSAO.json',json.dumps({'version':'9.9'}));_mk(P/'assets/a.png','p');_mk(P/'rodovia.ico','i');_mk(P/'app/georas_logo.png','p');_mk(P/'app/icone.png','p');_mk(P/'runtime/python.exe','p')
    for d in ('projetos','videos','atualizacoes'):(r/d).mkdir()
    _mk(r/'ABRIR RODOVIA STUDIO.cmd','@echo off')
    import shutil;shutil.copytree(Path(__file__).resolve().parent.parent/'assets'/'texturas',P/'assets'/'texturas')
    return r

def test_instalacao_integra_passa(inst):
    v=H.verificar(inst);assert v['ok'] and v['versao']=='9.9',v

def test_ausentes_sao_detectados_um_a_um(inst):
    P=inst/'sistema/programa'
    for rel,tipo in [('app/server.py','ausente'),('app/js','ausente'),('assets','ausente'),('VERSAO.json','ausente'),('run.py','ausente'),('app/util.py','modulo_ausente'),('app/js/a.js','recurso_ausente'),('app/css/s.css','recurso_ausente')]:
        alvo=P/rel;bak=inst.parent/'bak'/rel.replace('/','_')
        bak.parent.mkdir(parents=True,exist_ok=True)
        if rel=='app/server.py':  # sem server.py a pasta deixa de ser um programa
            continue
        shutil.move(str(alvo),str(bak))
        try:
            v=H.verificar(inst);assert not v['ok'] and any(p['tipo']==tipo or tipo=='ausente' and p['tipo'] in ('ausente','vazio') for p in v['problemas']),(rel,v)
        finally:shutil.move(str(bak),str(alvo))
        assert H.verificar(inst)['ok'],rel

def test_sintaxe_e_versao_invalidas(inst):
    P=inst/'sistema/programa';_mk(P/'app/quebrado.py','def f(:\n');assert any(p['tipo']=='invalido' for p in H.verificar(inst)['problemas']);(P/'app/quebrado.py').unlink()
    _mk(P/'VERSAO.json','{nao json');assert any('VERSAO' in p['caminho'] for p in H.verificar(inst)['problemas'])

def test_previa_nao_altera_e_limpeza_vai_para_quarentena(inst,monkeypatch):
    import atualizador;monkeypatch.setattr(atualizador,'app_running',lambda *a,**k:None)
    velho=time.time()-90*86400;S=inst/'sistema'
    for i in range(6):_mk(S/f'backups/antes_v2_0{i}_x/rollback.json','{}',velho+i*3600)
    _mk(S/'backups/legado_1/a.txt','a',velho);_mk(S/'backups/legado_2/a.txt','a',velho-1)
    for i in range(5):_mk(inst/f'atualizacoes/aplicadas/RodoviaStudio_2_{i}_atualizacao.zip','z',velho+i*3600)
    _mk(inst/'atualizacoes/RodoviaStudio_2_99_atualizacao.zip','pendente');_mk(inst/'projetos/p1/config.json','{}');_mk(inst/'videos/v.mp4','v')
    _mk(inst/'sistema/programa/app/__pycache__/m.pyc','c');_mk(S/'logs/servidor.log','L'*(6*1024*1024))
    _mk(inst/'suporte/sistema/app/server.py','dup');_mk(inst/'pacote/suporte/x','x');_mk(inst/'manifest.json','{}')
    snapshot=sorted(str(p.relative_to(inst)) for p in inst.rglob('*'))
    pre=H.limpar(inst);assert not pre['executado'] and pre['liberado_bytes']>6*1024*1024
    cats={i['categoria'] for i in pre['itens']};assert {'backups_atualizacao','zips_aplicados','caches_python','logs_grandes','programa_duplicado','entrega_extraida','backups_legado'}<=cats,cats
    assert sorted(str(p.relative_to(inst)) for p in inst.rglob('*'))==snapshot          # prévia não mexe em nada
    r=H.limpar(inst,executar=True);assert not r['erros'],r['erros']
    resto=sorted(p.name for p in (S/'backups').glob('antes_*'));assert len(resto)==3 and resto[-1].startswith('antes_v2_05')   # as 3 mais recentes ficam
    assert len(list((inst/'atualizacoes/aplicadas').glob('*.zip')))==2
    assert (inst/'atualizacoes/RodoviaStudio_2_99_atualizacao.zip').exists() and (inst/'projetos/p1/config.json').exists() and (inst/'videos/v.mp4').exists()
    assert H.verificar(inst)['ok'] and (S/'logs/servidor.log').read_text()==''
    assert not (inst/'suporte').exists() and not (inst/'pacote').exists() and (inst/'sistema/programa/app/server.py').exists()
    st=Path(r['quarentena']).name;assert (Path(r['quarentena'])/'quarentena.json').exists()
    # restaurar devolve o que saiu
    back=H.restaurar(inst,st);assert back['restaurados']>=5 and (inst/'suporte/sistema/app/server.py').exists()
    assert len(list((S/'backups').glob('antes_*')))==6

def test_nao_executa_com_app_aberto_e_nao_apaga_nada_fora_da_quarentena(inst,monkeypatch):
    import atualizador;monkeypatch.setattr(atualizador,'app_running',lambda *a,**k:8765)
    _mk(inst/'suporte/x','x')
    with pytest.raises(RuntimeError):H.limpar(inst,executar=True)
    assert (inst/'suporte/x').exists()

def test_protegidos_e_links(inst,monkeypatch):
    import atualizador;monkeypatch.setattr(atualizador,'app_running',lambda *a,**k:None)
    assert H._seguro(inst,'projetos/p1') is None and H._seguro(inst,'videos/v.mp4') is None and H._seguro(inst,'dados/x') is None
    assert H._seguro(inst,'atualizacoes/RodoviaStudio_2_99_atualizacao.zip') is None and H._seguro(inst,'sistema/programa') is None and H._seguro(inst,'../fora') is None

def test_esvaziar_quarentena_so_antiga(inst):
    q=inst/'sistema/_quarentena';_mk(q/'20200101_000000/x.txt','x',time.time()-60*86400);os.utime(q/'20200101_000000',(time.time()-60*86400,)*2);_mk(q/'novo/y.txt','y')
    p=H.esvaziar_quarentena(inst,30,False);assert p['removidas']==['20200101_000000'] and (q/'20200101_000000').exists()
    H.esvaziar_quarentena(inst,30,True);assert not (q/'20200101_000000').exists() and (q/'novo').exists()

def test_rotas_higiene_registradas(inst,monkeypatch,tmp_path):
    monkeypatch.setenv('RODOVIA_DATA',str(tmp_path/'d'))
    from fastapi.testclient import TestClient
    from app.server import app
    from app import store
    c=TestClient(app,base_url='http://127.0.0.1')
    assert c.get('/api/higiene/verificar').status_code==409           # sem pasta de instalação (modo desenvolvimento)
    monkeypatch.setattr(store,'INSTALL',inst)
    r=c.get('/api/higiene/verificar');assert r.status_code==200 and r.json()['ok']
    r=c.get('/api/higiene/inventario');assert r.status_code==200 and not r.json()['executado']
