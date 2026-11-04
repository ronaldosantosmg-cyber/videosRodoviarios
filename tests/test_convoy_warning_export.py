"""Comboio permanece no diagnóstico e não interrompe a publicação do MP4."""
import json
from types import SimpleNamespace
import pytest
from app import fleet_policy
from app.models import Settings
from app.render import render
from test_traffic_pipeline import project


def occurrence():
    return {'vehicle':1,'leader_vehicle':2,'path':1,'station_m':135.37,
            'time_s':202.,'reason':'lider','gap_m':8.088,'remaining_to_exit_m':432.1}


@pytest.mark.parametrize('complete',[False,True])
def test_reported_case_no_longer_blocks_completed_export_or_checkpoint(complete):
    row=occurrence();sim=SimpleNamespace(s=Settings(),simulation_complete=complete,
        collisions=0,side_collisions=0,fleet_audit={'violations':[row]})
    fleet_policy.require_export(sim,sim.s,allow_partial=not complete)
    assert sim.fleet_audit['violations']==[row]


@pytest.mark.parametrize('collision',['collisions','side_collisions'])
def test_real_collisions_still_block_even_with_convoy_warning(collision):
    sim=SimpleNamespace(s=Settings(),simulation_complete=True,
        collisions=0,side_collisions=0,fleet_audit={'violations':[occurrence()]})
    setattr(sim,collision,1)
    with pytest.raises(ValueError,match='Conflito veicular'):fleet_policy.require_export(sim,sim.s)


def test_unfinished_simulation_still_cannot_be_published():
    sim=SimpleNamespace(s=Settings(),simulation_complete=False,
        collisions=0,side_collisions=0,fleet_audit={'violations':[occurrence()]})
    with pytest.raises(ValueError,match='simulação ainda não terminou'):fleet_policy.require_export(sim,sim.s)


def test_mp4_is_published_with_original_warning_preserved(tmp_path,monkeypatch):
    cfg=project(tmp_path).model_copy(update={'duration_s':3.,'render_workers':1})
    original=fleet_policy.inspect
    def inject_report(sim,*args,**kwargs):
        original(sim,*args,**kwargs)
        if not sim.fleet_audit['violations']:sim.fleet_audit['violations'].append(occurrence())
    monkeypatch.setattr(fleet_policy,'inspect',inject_report)
    output=render(tmp_path,cfg)
    result=json.loads((tmp_path/'video.json').read_text())
    assert output.is_file() and result['validation']['ok']
    assert result['validation']['frames_decoded']==72
    assert not (tmp_path/'video.partial.mp4').exists()
    # A injeção é somente do diagnóstico: nenhuma posição física é manipulada.
    assert occurrence() in result['motion_audit']['gold_rule']['violations']
