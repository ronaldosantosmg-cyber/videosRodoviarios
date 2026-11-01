"""2.02: pacote com versão menor que a instalada é arquivado SEM aplicar e o aviso diz isso e como proceder."""
import zipfile
from test_v18 import old_install,package,U


def _zip(tmp_path,root,version,server):
    (root/'atualizacoes').mkdir(exist_ok=True);pk=package(tmp_path,version,server);z=root/'atualizacoes'/f'RodoviaStudio_{version.replace(".","_")}_atualizacao.zip'
    with zipfile.ZipFile(z,'w') as zf:
        for f in pk.rglob('*'):
            if f.is_file():zf.write(f,'pacote/'+f.relative_to(pk).as_posix())
    return z


def test_versao_menor_nao_e_aplicada_e_o_aviso_explica(tmp_path,monkeypatch):
    root=tmp_path/'R';old_install(root);monkeypatch.setattr(U.Path,'home',lambda:tmp_path/'home')
    _zip(tmp_path,root,'2.42.38','# alto');msgs=[]
    assert U.search_and_apply(root,say=msgs.append,check_running=False)['version']=='2.42.38'
    z=_zip(tmp_path,root,'2.0','# baixo')
    assert U.search_and_apply(root,say=msgs.append,check_running=False) is None
    assert (root/'sistema/programa/app/server.py').read_text()=='# alto'                  # nada foi aplicado
    assert 'SEM ser aplicado' in msgs[-1] and 'MENOR' in msgs[-1] and 'RESTAURAR VERSAO ANTERIOR' in msgs[-1]
    assert (root/'atualizacoes/aplicadas'/z.name).exists()
