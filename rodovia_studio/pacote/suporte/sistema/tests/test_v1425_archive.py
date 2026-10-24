import hashlib,json,zipfile
from pathlib import Path
import atualizador as U
from test_v142_update import install,package,put,unchanged_data


def test_only_verified_previous_tests_are_archived_and_rollback_restores_them(install,package,tmp_path):
    original=b'# teste do pacote anterior\n';modified=b'# personalizado pelo usuario\n'
    previous={'suporte/sistema/tests/test_antigo.py':hashlib.sha256(original).hexdigest(),
              'suporte/sistema/tests/test_modificado.py':hashlib.sha256(original).hexdigest()}
    old=install/'atualizacoes/aplicadas/anterior.zip';old.parent.mkdir(parents=True)
    with zipfile.ZipFile(old,'w') as z:z.writestr('pacote/manifest.json',json.dumps({'version':'1.42','files':previous}))
    a=put(install,'sistema/programa/tests/test_antigo.py',original.decode())
    b=put(install,'sistema/programa/tests/test_modificado.py',modified.decode())
    c=put(install,'sistema/programa/tests/test_desconhecido.py','# desconhecido\n')
    result=U.apply(package,install,check_running=False)
    assert result['archived_residuals']==1 and not a.exists()
    assert b.read_bytes()==modified and c.exists()
    backup=Path(result['backup']);assert (backup/'residuos/sistema/programa/tests/test_antigo.py').read_bytes()==original
    moved=tmp_path/'Instalação movida';install.rename(moved);U.restore_previous(moved,check_running=False)
    assert (moved/'sistema/programa/tests/test_antigo.py').read_bytes()==original
    assert (moved/'sistema/programa/tests/test_modificado.py').read_bytes()==modified
    unchanged_data(moved)


def test_without_previous_manifest_unknown_tests_remain(install,package):
    f=put(install,'sistema/programa/tests/arquivo.py','# nao apagar\n')
    result=U.apply(package,install,check_running=False)
    assert result['archived_residuals']==0 and f.exists()
