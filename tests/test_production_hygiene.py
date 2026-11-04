"""Limpeza de produção retira apenas ferramentas conhecidas, de forma reversível."""
import json
import time
from pathlib import Path
import pytest
from app import higiene as H
import atualizador


@pytest.fixture
def install(tmp_path,monkeypatch):
    root=tmp_path/'studio';program=root/'sistema/programa'
    files={'app/server.py':'# server','app/index.html':'interface','assets/manter.txt':'asset','runtime/manter.txt':'runtime',
           'tests/test_x.py':'# teste','requirements-dev.txt':'pytest','executar_testes_visuais.py':'# teste',
           'portao.py':'# teste','TESTAR INTERFACE.cmd':'rem teste','desconhecido.py':'# preservar',
           'VERSAO.json':'{"version":"3.23.0"}'}
    for name,text in files.items():
        path=program/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    for name in ('projetos/meu.dxf','videos/meu.mp4','atualizacoes/pendente.zip'):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('preservar')
    monkeypatch.setattr(atualizador,'app_running',lambda:None)
    return root,program


def test_preview_execute_restore_and_retention(install):
    root,program=install
    preview=H.limpar(root,categorias=['desenvolvimento'])
    assert not preview['executado'] and len(preview['itens'])==5
    assert (program/'tests/test_x.py').exists()
    result=H.limpar(root,executar=True,categorias=['desenvolvimento'])
    assert not result['erros'] and len(result['itens'])==5
    assert not (program/'tests').exists()
    for name in ('app/server.py','app/index.html','assets/manter.txt','runtime/manter.txt','desconhecido.py'):
        assert (program/name).exists()
    for name in ('projetos/meu.dxf','videos/meu.mp4','atualizacoes/pendente.zip'):
        assert (root/name).exists()
    quarantine=Path(result['quarentena'])
    manifest=json.loads((quarantine/'quarentena.json').read_text())
    assert manifest['retention_days']==30
    assert H.esvaziar_quarentena(root,dias=0,agora=time.time()+29*H.DIA)['removidas']==[]
    assert H.restaurar(root,quarantine.name)['restaurados']==5
    assert (program/'tests/test_x.py').exists()


@pytest.mark.parametrize('force',[False,True])
def test_open_app_blocks_development_cleanup(install,monkeypatch,force):
    root,program=install
    monkeypatch.setattr(atualizador,'app_running',lambda:8765)
    with pytest.raises(RuntimeError,match='está aberto'):
        H.limpar(root,executar=True,categorias=['desenvolvimento'],force=force)
    assert (program/'tests/test_x.py').exists()


def test_symlinks_and_running_script_are_excluded(install,monkeypatch,tmp_path):
    root,program=install
    external=tmp_path/'external';external.write_text('não tocar')
    (program/'tests/link').symlink_to(external)
    script=program/'portao.py'
    monkeypatch.setattr(H.sys,'argv',[str(script)])
    preview=H.limpar(root,categorias=['desenvolvimento'])
    paths={Path(item['caminho']).name for item in preview['itens']}
    assert 'tests' not in paths and 'portao.py' not in paths
    assert H._seguro(root,'sistema/programa/tests') is None
    result=H.limpar(root,executar=True,categorias=['desenvolvimento'])
    assert len(result['itens'])==3
    assert external.read_text()=='não tocar' and script.exists()


def test_parent_with_running_cli_cannot_be_quarantined(install,monkeypatch):
    root,program=install
    monkeypatch.setattr(H.sys,'argv',[str(program/'tests/test_x.py')])
    preview=H.limpar(root,categorias=['desenvolvimento'])
    assert all(Path(item['caminho']).name!='tests' for item in preview['itens'])
