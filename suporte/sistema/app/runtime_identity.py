"""Identidade por processo: distingue código carregado de arquivos no disco."""
import copy
import hashlib
import json
import marshal
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from . import fleet_policy


def _file_hash(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except (OSError, TypeError):
        return None


def _version(root):
    try:
        return json.loads((Path(root)/'VERSAO.json').read_text(encoding='utf-8')).get('version')
    except (OSError, ValueError, TypeError):
        return None


def policy_probe(function):
    """Exercita a função viva sem usar ou alterar veículos do projeto."""
    result = {}
    for case in ('convoy', 'collision', 'incomplete'):
        settings = SimpleNamespace(traffic=True, traffic_prevent_collisions=True,
                                   traffic_respect_signals=True, traffic_export_scope='strict')
        sim = SimpleNamespace(s=settings, simulation_complete=case!='incomplete',
                              collisions=int(case=='collision'), side_collisions=0,
                              fleet_audit={'violations':[{'vehicle':1,'path':0}]})
        try:
            function(sim, settings)
        except ValueError:
            result[case] = 'rejected'
        except Exception as exc:
            result[case] = 'error:'+type(exc).__name__
        else:
            result[case] = 'accepted'
    result['ok'] = result == {'convoy':'accepted','collision':'rejected','incomplete':'rejected'}
    return result


class RuntimeIdentity:
    """Captura uma vez; SHA do fonte observado não comprova o bytecode carregado."""
    def __init__(self, root, module=fleet_policy):
        self.root = Path(root).resolve()
        self.source = Path(module.__file__).resolve()
        function = module.require_export
        code = getattr(function, '__code__', None)
        self.snapshot = {
            'version_at_import':_version(self.root), 'pid':os.getpid(),
            'executable':str(Path(sys.executable).resolve()), 'root':str(self.root),
            'policy':{
                'module_path':str(self.source), 'cached_path':getattr(module,'__cached__',None),
                'source_sha256_observed_at_import':_file_hash(self.source),
                'loaded_code_sha256':hashlib.sha256(marshal.dumps(code)).hexdigest() if code else None,
                'loaded_code_filename':getattr(code,'co_filename',None),
                'probe':policy_probe(function),
            },
        }

    def report(self):
        result = copy.deepcopy(self.snapshot)
        current = _file_hash(self.source)
        result['disk'] = {'version_now':_version(self.root), 'policy_source_sha256_now':current}
        previous = result['policy']['source_sha256_observed_at_import']
        result['source_changed_since_import'] = current != previous if current and previous else None
        result['version_changed_since_import'] = result['disk']['version_now'] != result['version_at_import']
        result.update(program_root=result['root'], version_at_start=result['version_at_import'],
                      source_fingerprint_at_start=previous, source_fingerprint_now=current,
                      disk_changed=result['source_changed_since_import'],
                      export_policy_probe_ok=result['policy']['probe']['ok'])
        return result


IDENTITY = RuntimeIdentity(Path(__file__).resolve().parents[1])


def report():
    return IDENTITY.report()
