import json
from types import SimpleNamespace

from app import fleet_policy, runtime_identity, execlog


def identity(tmp_path, function=fleet_policy.require_export):
    source = tmp_path/'fleet_policy.py'
    source.write_text('original source', encoding='utf-8')
    (tmp_path/'VERSAO.json').write_text(json.dumps({'version':'3.22'}), encoding='utf-8')
    module = SimpleNamespace(__file__=str(source), __cached__=str(source)+'.pyc', require_export=function)
    return runtime_identity.RuntimeIdentity(tmp_path, module), source


def test_disk_changes_do_not_rewrite_loaded_identity(tmp_path):
    runtime, source = identity(tmp_path)
    before = runtime.report()
    source.write_text('changed source', encoding='utf-8')
    (tmp_path/'VERSAO.json').write_text(json.dumps({'version':'9.99'}), encoding='utf-8')
    after = runtime.report()
    assert after['version_at_import'] == '3.22'
    assert after['disk']['version_now'] == '9.99'
    assert after['version_changed_since_import']
    assert after['source_changed_since_import']
    assert after['policy'] == before['policy']
    assert after['source_fingerprint_now'] != after['source_fingerprint_at_start']


def test_live_old_function_detected_even_with_new_source(tmp_path):
    def old(sim, settings):
        raise ValueError('antigo bloqueio por comboio')
    runtime, _ = identity(tmp_path, old)
    result = runtime.report()
    assert result['version_at_import'] == '3.22'
    assert result['policy']['probe']['convoy'] == 'rejected'
    assert not result['policy']['probe']['ok']
    assert result['policy']['loaded_code_filename'] == __file__


def test_actual_loaded_policy_preserves_physical_guards():
    probe = runtime_identity.policy_probe(fleet_policy.require_export)
    assert probe == {'convoy':'accepted','collision':'rejected','incomplete':'rejected','ok':True}
    assert runtime_identity.report()['policy']['probe'] == probe


def test_log_version_is_frozen_and_identity_is_in_initial_event(tmp_path, monkeypatch):
    runtime, _ = identity(tmp_path)
    monkeypatch.setattr(execlog, 'IDENTITY', runtime)
    monkeypatch.setattr(execlog, 'runtime_report', runtime.report)
    (tmp_path/'VERSAO.json').write_text(json.dumps({'version':'9.99'}), encoding='utf-8')
    execlog.JobLog(tmp_path, 'job1', 'prepare')
    event = execlog.read(tmp_path, 'execucao')[0]
    assert event['versao'] == '3.22'
    assert event['runtime']['disk']['version_now'] == '9.99'


def test_report_cannot_mutate_snapshot():
    report = runtime_identity.report()
    report['policy']['probe']['ok'] = False
    assert runtime_identity.report()['policy']['probe']['ok']


def test_missing_source_is_not_reported_as_unchanged(tmp_path):
    runtime,source=identity(tmp_path);source.unlink();report=runtime.report()
    assert report['disk']['policy_source_sha256_now'] is None
    assert report['disk_changed'] is not False
    assert report['policy']['source_sha256_observed_at_import'] is not None
