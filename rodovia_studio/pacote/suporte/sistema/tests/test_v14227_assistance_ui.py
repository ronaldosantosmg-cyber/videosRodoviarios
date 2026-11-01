"""Diagnósticos clicáveis, modo Projeto e configuração de vídeo reais no navegador."""
import json
import pytest
from app.calculation_guidance import guidance
from app import assistance,execlog
from test_v142_visual import page
from test_v1422_layout import seed
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_project_mode_uses_public_workspace_contract_and_returns_with_f11(page):
    page.get_by_role('menuitem',name='Exibir',exact=True).click()
    page.get_by_role('menuitem',name='Área de trabalho',exact=True).hover()
    page.get_by_role('menuitem',name='Modo Projeto',exact=True).click()
    assert page.evaluate("document.body.classList.contains('dwProjectFocus')")
    page.keyboard.press('F11');assert not page.evaluate("document.body.classList.contains('dwProjectFocus')")
    page.evaluate('RodoviaDesktopWorkspace.toggleCommand()')
    assert page.locator('#dwCommandDrawer').is_visible()
    page.evaluate('RodoviaDesktopWorkspace.toggleCommand()');assert page.locator('#dwCommandDrawer').is_hidden()


def diagnostic(page):
    seed(page)
    page.evaluate("""()=>{pid='a'.repeat(32);editor.engine_revision='ensaio-atual';editor.segments[0]={...editor.segments[0],mid:[0,0],technical_status:'problem',technical_message:'Curva brusca no eixo. Conferir vértices.',technical_points:[{point:[0,0],reason:'mudanca_brusca'}],technical_assistant:{title:'Corrigir geometria',steps:[{instruction:'Confira os vértices antes e depois do ponto.'}]}};draw()}""")
    page.locator('.rsFlowProblemPoint').wait_for()


def test_yellow_problem_marker_is_pulsing_clickable_and_not_in_canvas_pixels(page):
    diagnostic(page)
    p=page.locator('.rsFlowProblemPoint');assert p.count()==1
    assert p.evaluate("e=>getComputedStyle(e).backgroundColor")=='rgb(255, 221, 37)'
    assert p.evaluate("e=>getComputedStyle(e).animationName")=='rsProblemPulse'
    before=page.evaluate('canvas.toDataURL()');page.wait_for_timeout(250)
    assert before==page.evaluate('canvas.toDataURL()')
    p.click();d=page.get_by_role('dialog',name='Como corrigir este fluxo')
    assert d.get_by_text('Ponto informado pelo motor.',exact=True).is_visible()
    assert d.get_by_text('Confira os vértices antes e depois do ponto.',exact=True).is_visible()
    screenshot(page,'14227_ponto_amarelo_orientacao')
    d.get_by_role('button',name='Localizar no desenho').click();page.wait_for_timeout(100)
    r=page.locator('#canvas').bounding_box();b=p.bounding_box()
    assert abs(b['x']+b['width']/2-(r['x']+r['width']/2))<3


def test_markers_track_zoom_hide_for_valid_or_disabled_and_respect_reduced_motion(page):
    diagnostic(page)
    page.emulate_media(reduced_motion='reduce')
    assert page.locator('.rsFlowProblemPoint').evaluate('e=>getComputedStyle(e).animationName')=='none'
    page.evaluate("editor.segments[0].technical_status='ok';draw()")
    page.wait_for_timeout(100);assert page.locator('.rsFlowProblemPoint').count()==0
    page.evaluate("editor.segments[0].technical_status='problem';editor.segments[0].disabled=true;draw()")
    page.wait_for_timeout(100);assert page.locator('.rsFlowProblemPoint').count()==0
    page.evaluate("editor.segments[0].disabled=false;editor.segments[0].technical_points=[{point:[NaN,0]}];editor.segments[0].mid=[NaN,0];draw()")
    page.wait_for_timeout(100);assert page.locator('.rsFlowProblemPoint').count()==0


def test_markers_do_not_use_endless_redraw_and_are_bounded(page):
    diagnostic(page)
    page.evaluate("""()=>{editor.segments[0].technical_points=Array.from({length:350},(_,i)=>({point:[i*.1,0]}));draw()}""")
    page.wait_for_timeout(100);assert page.locator('.rsFlowProblemPoint').count()==200
    page.evaluate("""()=>{window.drawCount=0;window.drawBefore=draw;draw=function(...args){drawCount++;return drawBefore(...args)}}""")
    page.wait_for_timeout(250);assert page.evaluate('drawCount')==0


@pytest.mark.parametrize('size',[(1366,768),(760,720)])
def test_video_configuration_has_clear_groups_and_keeps_same_controls(page,size):
    page.set_viewport_size({'width':size[0],'height':size[1]})
    before=page.evaluate("[...document.querySelectorAll('.rsVideoSettings input,.rsVideoSettings select')].map(e=>[e.id,e.value,e.checked])")
    page.evaluate("psOpenHub('video')")
    d=page.locator('#rsPanelPopup');assert d.is_visible()
    pane=d.get_by_role('tabpanel',name='Exportação',exact=True)
    assert pane.locator('#width').is_visible() and pane.locator('#fps').is_visible()
    assert d.locator('#traffic_density').is_hidden()
    d.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    assert d.locator('#traffic_density').is_visible()
    for name in ('Câmera','Aparência','Avançado','Exportação'):
        d.get_by_role('tab',name=name,exact=True).click()
        assert d.get_by_role('tabpanel',name=name,exact=True).is_visible()
    assert before==page.evaluate("[...document.querySelectorAll('.rsVideoSettings input,.rsVideoSettings select')].map(e=>[e.id,e.value,e.checked])")
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    screenshot(page,'14227_video_organizado_'+str(size[0]))
    d.locator('#rsPanelCancel').click();assert d.is_hidden()


def test_more_menu_has_keyboard_cascades_and_fits_small_viewport(page):
    page.set_viewport_size({'width':760,'height':720})
    page.locator('[data-psmore]').click()
    menu=page.get_by_role('menu',name='Outros painéis por função',exact=True)
    assert menu.get_by_role('menuitem').count()==3
    menu.get_by_role('menuitem',name='Manutenção e assistência',exact=True).focus()
    page.keyboard.press('ArrowRight')
    action=page.get_by_role('menuitem',name='Diagnóstico do aplicativo / IA',exact=True)
    assert action.is_visible()
    for box in page.locator('.rsCascade').all():
        r=box.bounding_box();assert r['x']>=0 and r['y']>=0 and r['x']+r['width']<=761 and r['y']+r['height']<=721
    screenshot(page,'14227_mais_cascatas')
    page.keyboard.press('Escape');page.keyboard.press('Escape');assert page.locator('.rsCascade').count()==0


@pytest.mark.parametrize('message,expected',[
 ('RodoviaDesktopWorkspace is not defined','Comando da interface'),
 ('config.json corrompido','integridade'),('409 revisão obsoleta','outra revisão'),
 ('Fluxo atravessa barreira e sinal vermelho','Impedimento físico'),
 ('seção com acostamento fora da pista','seção operacional'),('OAE com hachura inválida','material'),
 ('WebGL context lost','visualização gráfica'),('ENOSPC no space left','Espaço insuficiente')])
def test_expert_guidance_covers_application_phases_without_arbitrary_execution(message,expected):
    r=guidance('tela',message)
    assert expected in ' '.join(r['causes']) and r['steps']
    assert all(a['id'] in {'protection','flow','sections','materials','video','maintenance','logs'} for a in r['actions'])


def test_logs_expose_review_actions_and_ia_opens_video_settings(gl_page,live):
    d=live[2]/live[1];execlog.write(d,'erros','erro_tela',mensagem='FFmpeg: erro ao gerar vídeo MP4')
    data=assistance.diagnostics(d)
    assert any(a['id']=='video' for issue in data['issues'] for a in issue['actions'])
    gl_page.evaluate("RodoviaIA.open('logs')")
    action=gl_page.locator('[data-ia-action=video]').first;action.wait_for(state='attached')
    action.locator('..').locator('summary').click();action.click()
    assert gl_page.locator('#rsPanelPopup').is_visible()
    assert gl_page.locator('#rsPanelPopup .rsVideoTabs').is_visible()


def test_video_density_save_and_discard_reach_actual_motor(gl_page,live):
    from app.project_state import read_config
    p=gl_page;d=live[2]/live[1];before=read_config(d)['traffic_density']
    p.evaluate("psOpenHub('video')")
    p.locator('#rsPanelPopup').get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    p.locator('#traffic_density').fill('3.4');p.locator('#rsPanelSave').click()
    p.wait_for_function("!RodoviaPanels.opened",timeout=15000)
    assert read_config(d)['traffic_density']==3.4
    p.evaluate("psOpenHub('video')")
    p.locator('#rsPanelPopup').get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    p.locator('#traffic_density').fill('5.2');p.locator('#rsPanelCancel').click()
    p.get_by_role('button',name='Descartar alterações',exact=True).click();p.wait_for_function('!RodoviaPanels.opened')
    assert read_config(d)['traffic_density']==3.4


def test_more_menu_second_click_retracts_and_escape_restores_focus(page):
    button=page.locator('[data-psmore]');button.click()
    assert button.get_attribute('aria-expanded')=='true'
    button.click();assert page.locator('.rsMoreCascade').count()==0
    assert button.get_attribute('aria-expanded')=='false'
    button.click();page.keyboard.press('Escape')
    assert button.evaluate('(e)=>document.activeElement===e')


def test_length_limit_is_intentional_exclusion_and_has_no_problem_marker(page):
    from types import SimpleNamespace
    from app.flow_diagnostics import flow_diagnostics
    n=SimpleNamespace(min_route=50,raw_info=[{'base':0,'points':[[0.,0.],[30.,0.]]}],edges=[],paths=[],short_ignored=set())
    result=flow_diagnostics(n)[0]
    assert result['technical_exclusion']=='length_limit' and result['technical_status']=='adjustment'
    diagnostic(page)
    page.evaluate("editor.segments[0].technical_exclusion='length_limit';draw()")
    page.wait_for_timeout(100);assert page.locator('.rsFlowProblemPoint').count()==0
