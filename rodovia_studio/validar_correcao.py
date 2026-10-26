#!/usr/bin/env python3
"""Diagnóstico direcionado. Nunca gera nem aprova pacote de entrega."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SYSTEM = ROOT / 'pacote/suporte/sistema'
AREAS = {
    'atualizacao': ['tests/test_v14223_update_policy.py','tests/test_v1425_capture3d.py'],
    'confiabilidade': ['tests/test_v14222_reliability.py','tests/test_v14216_flow_repair.py','tests/test_v1423_toolbar.py','tests/test_v1424_ribbon.py'],
    'operacao': ['tests/test_v14221_simplification.py', 'tests/test_v1429_popup_calculation.py', 'tests/test_v1427_state.py'],
    'secoes': ['tests/test_v14220_sections_materials.py','tests/test_v14212_modelagem.py','tests/test_v14212_ui.py'],
    'regressoes': ['tests/test_v14219_usage_log.py','tests/test_v14219_reconstruction_curves_semantics.py'],
    'agentes': ['tests/test_v14218_agents.py','tests/test_v14218_axis_policy.py','tests/test_v14218_scene_agents.py','tests/test_v14218_live_agents.py','tests/test_v14218_layers_ui.py'],
    'popup': [
        'tests/test_v14214_panels_ui.py',
        'tests/test_v14212_ui.py::test_automatic_job_does_not_close_a_panel_opened_while_save_is_pending',
        'tests/test_v1426_import_capacity_ui.py::test_saves_3500_capacity_and_higher_demand_through_real_api',
        'tests/test_v1428_panels.py::test_popup_save_reaches_the_real_api_and_restores_enabled_controls',
        'tests/test_v1428_panels.py::test_popup_discard_restores_form_and_preserves_previous_pending_edits',
    ],
    'fluxo': ['tests/test_v14218_axis_policy.py','tests/test_v14216_flow_repair.py','tests/test_v14216_repair_live.py','tests/test_v14214_assistant.py','tests/test_v14213_continuity.py','tests/test_v14212_traffic_safety.py',
              'tests/test_v14212_modelagem.py::test_requested_vehicle_widths_and_lateral_reservation'],
    'imagem': ['tests/test_v14212_modelagem.py', 'tests/test_v14212_ui.py',
               'tests/test_v14212_presentation.py'],
    'interface': ['tests/test_v14217_usability.py','tests/test_v14215_view_retention.py', 'tests/test_v1428_menu_flow.py', 'tests/test_v1423_toolbar.py'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--area', action='append', required=True, choices=sorted(AREAS))
    parser.add_argument('--listar', action='store_true', help='Mostrar os testes sem executar.')
    args = parser.parse_args()
    selected = list(dict.fromkeys(test for area in args.area for test in AREAS[area]))
    if args.listar:
        print('\n'.join(selected))
        print('Diagnóstico: não aprova entrega. Pacote exige validar_entrega.py --gerar.')
        return 0
    version = json.loads((ROOT / 'pacote/manifest.json').read_text())['version']
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence = ROOT / 'evidencias' / version / 'diagnosticos' / stamp
    evidence.mkdir(parents=True)
    report = evidence / 'pytest.xml'
    initial = fingerprint()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='rodovia_correcao_') as data:
        env = dict(os.environ, RODOVIA_DATA=data, VISUAL_ARTIFACTS=str(evidence),
                   PYTHONPYCACHEPREFIX=str(ROOT.parent.parent / '.cache/pycache'),
                   XDG_CACHE_HOME=str(ROOT.parent.parent / '.cache'))
        cmd = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               '--durations=10', *selected, f'--junitxml={report}']
        with (evidence / 'validacao.log').open('w') as log:
            process = subprocess.Popen(cmd, cwd=SYSTEM, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            code = process.wait()
    suites = ET.parse(report).getroot().findall('.//testsuite') if report.exists() else []
    counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
              for key in ('tests', 'failures', 'errors', 'skipped')}
    approved = (code == 0 and counts['tests'] > 0 and
                not any(counts[k] for k in ('failures', 'errors', 'skipped')) and
                initial == fingerprint())
    result = dict(mode='diagnostico_direcionado', areas=args.area, selected=selected,
                  diagnostic_approved=approved, release_approved=False, pytest=counts,
                  elapsed_s=round(time.monotonic()-started, 2), source_sha256=initial)
    (evidence / 'resultado.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(f'Evidências: {evidence}')
    print('Diagnóstico aprovado.' if approved else 'Diagnóstico reprovado.')
    print('Pacote continua exigindo validar_entrega.py --gerar; nenhum ZIP foi gerado.')
    return 0 if approved else 1


def fingerprint():
    digest = hashlib.sha256()
    for path in sorted((ROOT / 'pacote').rglob('*')):
        if path.is_file() and not any(p in path.parts for p in ('__pycache__', '.pytest_cache')):
            digest.update(path.relative_to(ROOT / 'pacote').as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


if __name__ == '__main__':
    raise SystemExit(main())
