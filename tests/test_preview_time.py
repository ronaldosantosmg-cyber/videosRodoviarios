from app.models import Settings


def test_instante_nao_ultrapassa_duracao_nem_arredonda_fracoes():
    assert Settings(duration_s=3).preview_time_s == 3
    assert Settings(duration_s=20, preview_time_s=1.25).preview_time_s == 1.25
