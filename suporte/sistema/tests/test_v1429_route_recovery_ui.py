from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_route_recovery_explains_automatic_and_manual_actions(page):
    seed(page)
    page.evaluate("""()=>{const s=editor.segments[0];s.technical_status='problem';s.technical_message='Trajetória recusada pela análise de continuidade.';s.technical_automatic='Excluir os movimentos inválidos da simulação; preservar o traçado original para revisão.';s.technical_manual='Editar os pontos, o sentido e as ligações; recalcular antes de circular.';selSeg={id:s.id};showSegProps()}""")
    assert page.locator('.rsFlowRecovery').is_visible()
    assert 'Tratamento automático' in page.locator('.rsFlowRecovery').inner_text()
    assert 'preservar o traçado original' in page.locator('.rsFlowRecovery').inner_text()
    assert 'Correção manual' in page.locator('.rsFlowRecovery').inner_text()
    assert page.locator('#propPanel [data-segx=edit]').is_visible()
    screenshot(page,'1429_tratamento_erros_rota')
