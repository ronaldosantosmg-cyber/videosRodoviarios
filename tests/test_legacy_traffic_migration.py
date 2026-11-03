"""Projetos anteriores podem exportar com o motor atual sem desligar a regra de ouro."""
import json
import pytest
from app.models import Settings
from app.fleet_policy import validate_mode
from app.render import render
from test_traffic_pipeline import project


@pytest.mark.parametrize('legacy',[{'traffic_classic':True},{'traffic_model':'anterior'},
    {'traffic_classic':True,'traffic_model':'anterior','traffic_prevent_collisions':False,'traffic_respect_signals':False}])
def test_old_modes_migrate_to_protected_simulation_preserving_routes(legacy):
    original={'route_directions':{'layer:EIXO':'forward'},'traffic_density':2.4,'traffic_seed':7,**legacy}
    settings=Settings.model_validate(original)
    assert settings.traffic_model=='simulado' and not settings.traffic_classic
    assert settings.traffic_prevent_collisions and settings.traffic_respect_signals
    assert settings.traffic_legacy_migrated and settings.route_directions==original['route_directions']
    assert settings.traffic_density==2.4 and settings.traffic_seed==7
    validate_mode(settings)


def test_normal_mode_explicit_unsafe_controls_still_blocked():
    settings=Settings(traffic_prevent_collisions=False)
    with pytest.raises(ValueError,match='Ative'):validate_mode(settings)


def test_export_old_model_uses_validated_simulation_and_records_migration(tmp_path):
    settings=project(tmp_path).model_copy(update={'duration_s':3.,'traffic_model':'anterior','traffic_classic':True})
    output=render(tmp_path,settings)
    assert output.is_file()
    metadata=json.loads((tmp_path/'video.json').read_text(encoding='utf-8'))
    assert metadata['traffic_processing']['legacy_mode_migrated']
    assert metadata['motion_audit']['model']=='microssimulacao'
    assert metadata['motion_audit']['signals_respected'] and metadata['motion_audit']['collision_prevention']
    assert not metadata['motion_audit']['gold_rule']['violations']
    assert metadata['validation']['frames_decoded']==72


def test_disabled_old_traffic_stays_disabled_but_is_ready_for_safe_enable():
    settings=Settings(traffic=False,traffic_classic=True,traffic_prevent_collisions=False)
    assert not settings.traffic and not settings.traffic_classic
    assert settings.traffic_prevent_collisions and settings.traffic_model=='simulado'
