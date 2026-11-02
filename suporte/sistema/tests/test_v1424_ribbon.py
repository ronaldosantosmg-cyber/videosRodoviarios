"""Ferramentas da 1.39 como botões visíveis, sem depender de menu."""
import re,zipfile
from pathlib import Path
import pytest
from test_v142_visual import page
from visual_harness import rect,overlap,screenshot,open_activity

def test_original_buttons_are_visible_in_their_groups(page):
    with zipfile.ZipFile(Path(__file__).resolve().parents[5]/'atualizacoes/RodoviaStudio_1_39_atualizacao.zip') as z:
        text=z.read(next(n for n in z.namelist() if n.endswith('/app/js/04_ferramentas.js'))).decode()
        expected=set(re.findall(r"\['([a-z_][a-z_0-9]*)','",text[text.index('const TOOLS='):text.index('const ICON_PATHS=')]))
    seen=set(page.locator('#rsQuickNavigation [data-rs-tool]').evaluate_all('(bs)=>bs.map(b=>b.dataset.rsTool)'))
    for tab in page.locator('#rsToolTabs [role=tab]').all():
        open_activity(page,tab.inner_text());assert tab.get_attribute('aria-selected')=='true'
        panels=page.locator('#rsToolRibbon [role=tabpanel]:visible');assert panels.count()==1
        for button in panels.locator('[data-rs-tool]').all():
            assert button.is_visible();seen.add(button.get_attribute('data-rs-tool'))
    assert expected<=seen
    screenshot(page,'1424_01_comandos_139_visiveis')

def test_commands_and_tool_options_execute(page):
    open_activity(page,'Editar')
    for name in ['MOVER','GIRAR','COPIAR','ESCALA','ESPELHAR','OFFSET','APAGAR']:
        assert page.locator(f'[role=tabpanel]:visible [data-rs-command="{name}"]').is_visible()
    open_activity(page,'Editar')
    page.locator('[role=tabpanel]:visible [data-rs-command="DIST"]').click();assert page.evaluate('!!cadCmd')
    page.keyboard.press('Escape');page.locator('#confirmYes').click();assert not page.evaluate('!!cadCmd')
    open_activity(page,'Editar')
    page.locator('[role=tabpanel]:visible [data-rs-tool="insertcontrol"]').click();assert page.evaluate('tool')=='insertcontrol'
    open_activity(page,'Tráfego')
    page.locator('[role=tabpanel]:visible [data-rs-tool="block"]').click();assert page.evaluate('tool')=='block'
    assert page.locator('#blkMode').is_visible()
    assert page.locator('[role=tabpanel]:visible [data-rs-tool="block"]').get_attribute('aria-pressed')=='true'
    screenshot(page,'1424_02_comando_e_opcoes')

def test_keyboard_tabs(page):
    tabs=page.locator('#rsToolTabs [role=tab]');tabs.first.focus()
    page.keyboard.press('ArrowRight');assert tabs.nth(1).get_attribute('aria-selected')=='true'
    page.keyboard.press('End');assert tabs.last.get_attribute('aria-selected')=='true'
    page.keyboard.press('Home');assert tabs.first.get_attribute('aria-selected')=='true'

@pytest.mark.parametrize('width',[1024,1366,1920])
def test_ribbon_above_drawing(page,width):
    page.set_viewport_size({'width':width,'height':900})
    open_activity(page,'Cena');page.wait_for_timeout(150)
    top=rect(page,'#rsCommandRail');canvas=rect(page,'.canvasWrap');footer=rect(page,'#rsStudyFooter')
    ribbon=rect(page,'#rsToolRibbon');quick=rect(page,'#rsQuickNavigation');menu=rect(page,'#menuBar')
    assert menu['y']+menu['height']<=ribbon['y'] and ribbon['y']-menu['y']-menu['height']<=10
    assert quick['y']>=ribbon['y'] and quick['y']+quick['height']<=ribbon['y']+ribbon['height']
    assert overlap(top,canvas)<1 and overlap(footer,canvas)<1 and canvas['height']>300
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    screenshot(page,f'1424_03_faixa_{width}')


def test_default_bar_shows_all_icons_with_hover_help_and_no_names_button(page):
    assert page.get_by_role('tab',name='Todas',exact=True).count()==0
    assert page.get_by_role('tab',name='Projeto',exact=True).get_attribute('aria-selected')=='true'
    open_activity(page,'Tráfego')
    panel=page.locator('#rsToolPanel2')
    assert page.locator('#rsToolRibbon [data-rs-tool]').count()>=35
    assert panel.locator('[data-rs-tool=flowoff]').is_visible()
    assert page.locator('#rsQuickNavigation [data-rs-tool=pan]').is_visible()
    assert page.locator('#rsToolNames').count()==0
    assert page.locator('#rsQuickNavigation [data-rs-tool=pan] span').is_hidden()
    button=panel.locator('[data-rs-tool="flowoff"]');button.hover()
    help=page.get_by_role('tooltip');assert help.is_visible()
    assert 'Desativar fluxo' in help.inner_text() and 'geometria' in help.inner_text()
    screenshot(page,'1424_04_barra_completa_139')
    page.mouse.move(5,5);assert help.is_hidden()
    button.focus();assert help.is_visible()
