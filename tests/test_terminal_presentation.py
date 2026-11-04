from types import SimpleNamespace
import pytest
from app.models import Settings
from app.fleet_policy import terminal_alpha


def test_final_25m_are_empty_without_changing_physical_path():
    sim=SimpleNamespace(s=Settings(),paths=[{'length':200.,'terminal_offsets_m':[0.,0.]}],info={1:(0,'car')})
    original=sim.paths[0].copy()
    # Frente do carro: ainda antes, durante a dissolução e na faixa vazia.
    assert terminal_alpha(sim,1,0,150)==1
    values=[terminal_alpha(sim,1,0,s) for s in (165,168,170,173,175,199)]
    assert values==sorted(values,reverse=True)
    assert 0<values[1]<1
    assert values[-1]==values[-2]==0
    assert sim.paths[0]==original


def test_trimmed_terminal_uses_original_end_and_zero_disables_mask():
    sim=SimpleNamespace(s=Settings(),paths=[{'length':180.,'terminal_offsets_m':[0.,20.]}],info={1:(0,'car')})
    assert terminal_alpha(sim,1,0,150)==1
    assert terminal_alpha(sim,1,0,175)==0
    sim.s.traffic_exit_hidden_m=0
    assert terminal_alpha(sim,1,0,180)==1


def test_setting_is_persistent_and_bounded():
    assert Settings.model_validate_json(Settings().model_dump_json()).traffic_exit_hidden_m==25
    with pytest.raises(ValueError):Settings(traffic_exit_hidden_m=-1)
