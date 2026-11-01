"""O gate deve falhar rápido, encerrar filhos e elevar o risco quando necessário."""
import io,os,sys,time
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import validar_entrega as gate
import gate_profiles


def test_core_or_unknown_change_promotes_broad_and_appearance_is_currently_scoped():
    report=gate_profiles.assess(gate.ROOT.parent,gate.SYSTEM)
    assert report['baseline']=='3ff694c' and not report.get('requires_broad'),report
    # Um contrato existente não pode desaparecer ao retirar os campos de aparência.
    assert gate_profiles.model_contract('class Settings:\n x:int=1')!=gate_profiles.model_contract('class Settings:\n x:int=2',True)


def test_deadline_stops_test_children_instead_of_leaving_a_late_write(tmp_path):
    flag=tmp_path/'nao_deve_existir'
    child=f"import time;from pathlib import Path;time.sleep(.6);Path({str(flag)!r}).write_text('atrasado')"
    command='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(child)+']);time.sleep(5)'
    with (tmp_path/'gate.log').open('w') as log:
        with pytest.raises(RuntimeError,match='pacote bloqueado'):gate.test_process([sys.executable,'-c',command],dict(os.environ),log,.15)
    time.sleep(.7)
    assert not flag.exists()


def test_gate_external_tests_and_helpers_participate_in_reuse_hash():
    from validacao_incremental import test_hashes
    hashes=test_hashes(gate.SYSTEM)
    assert all(name in hashes for name in ('test_gate_curto.py','gate_profiles.py','validar_entrega.py','validacao_incremental.py'))


def test_reviewed_reader_is_bound_to_exact_source_not_a_blanket_exception():
    for name in ('app/models.py','app/geometry.py','app/traffic.py','app/webmap.py','app/rotas/editor.py'):
        data=(gate.SYSTEM/name).read_bytes()
        assert gate_profiles.reviewed(name,data)
        assert not gate_profiles.reviewed(name,data+b'\n# outra alteracao')
