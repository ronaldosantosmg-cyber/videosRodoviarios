from types import SimpleNamespace

import pytest

from app.fleet_policy import validate_mode


def settings(**overrides):
    base = dict(
        traffic=True,
        traffic_model='simulado',
        traffic_classic=False,
        traffic_prevent_collisions=True,
        traffic_respect_signals=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_simulado_prevalece_sobre_flag_classica_residual():
    s = settings(traffic_model='simulado', traffic_classic=True)

    validate_mode(s)

    assert s.traffic_classic is False


def test_modelo_anterior_continua_bloqueado_pela_regra_de_ouro():
    s = settings(traffic_model='anterior', traffic_classic=False)

    with pytest.raises(ValueError, match='modelo de tráfego simulado'):
        validate_mode(s)

    assert s.traffic_classic is True


def test_seguranca_continua_obrigatoria_no_modelo_simulado():
    s = settings(traffic_prevent_collisions=False)

    with pytest.raises(ValueError, match='prevenção de colisões'):
        validate_mode(s)
