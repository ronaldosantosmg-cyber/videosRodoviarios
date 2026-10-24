"""Interações reais em Chromium: painéis, cascatas, comandos e estudo de fluxos."""
import pytest
from playwright.sync_api import sync_playwright
from visual_harness import chromium_path,load_offline,screenshot,rect,overlap


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_path(),args=['--no-sandbox','--disable-gpu'])
        page=browser.new_page(viewport={'width':1440,'height':900})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        load_offline(page)
        yield page
        assert not errors,errors
        browser.close()


def test_properties_opens_and_collapses_second_click(page):
    b=page.locator('[data-pshub="props"]')
    b.click();page.wait_for_timeout(150)
    assert not page.evaluate('dockState.recolhida')
    b.click();page.wait_for_timeout(350)
    assert page.evaluate('dockState.recolhida')
    assert b.get_attribute('aria-expanded')=='false'
    screenshot(page,'142_01_propriedades_recolhidas')


def test_properties_stays_closed_after_selection_resize(page):
    page.evaluate("M.route_alignments=[{id:'r1',name:'Rota',points:[{x:0,y:0},{x:100,y:0}],enabled:true,sections:[],lane_change_sections:[]}];sel={key:'route_alignments',i:0};showProps()")
    page.wait_for_timeout(120)
    page.locator('[data-pshub="props"]').click();page.wait_for_timeout(100)
    # clicking the same active properties button closes the selected-object panel.
    if not page.evaluate('dockState.recolhida'):page.locator('[data-pshub="props"]').click()
    page.evaluate('resizeCanvas();showProps()');page.wait_for_timeout(400)
    assert page.evaluate('dockState.recolhida')
    screenshot(page,'142_02_propriedades_selecao_fechada')


def test_model_menu_cascades_and_selects_tool(page):
    page.get_by_role('menuitem',name='Modelar',exact=True).click()
    assert page.locator('.rsCascade').count()==1
    root=page.locator('.rsCascade').first
    assert root.get_by_role('menuitem').count()<=6
    root.get_by_role('menuitem',name='Tráfego e ligações',exact=True).hover()
    assert page.locator('.rsCascade').count()==2
    submenu=page.locator('.rsCascade').nth(1)
    a=root.bounding_box();b=submenu.bounding_box()
    assert b['x']>=a['x']+a['width']-4
    screenshot(page,'142_03_modelar_cascata')
    submenu.get_by_role('menuitem',name='Inverter fluxo',exact=True).click()
    assert page.evaluate('tool')=='flowrev'
    assert page.locator('.rsCascade').count()==0


def test_menu_keyboard_and_escape(page):
    b=page.get_by_role('menuitem',name='Modelar',exact=True)
    b.focus();page.keyboard.press('ArrowDown');page.keyboard.press('ArrowRight')
    assert page.locator('.rsCascade').count()==2
    page.keyboard.press('ArrowLeft');assert page.locator('.rsCascade').count()==1
    page.keyboard.press('Escape');assert page.locator('.rsCascade').count()==0
    assert b.evaluate('(b)=>document.activeElement===b')


def test_commands_below_menu_do_not_cover_canvas(page):
    page.evaluate("setTool('sign');dwCommandOpen()")
    page.wait_for_timeout(200)
    rail=rect(page,'#rsCommandRail');drawing=rect(page,'.canvasWrap')
    assert rail['y']+rail['height']<=drawing['y']+1
    assert overlap(rail,drawing)<1
    assert page.locator('.canvasWrap #toolOptions,.canvasWrap #selBar').count()==0
    assert page.locator('#rsCommandRail #toolOptions').count()==1
    screenshot(page,'142_04_comandos_abaixo_menu')


def test_context_follows_current_command_and_cancel(page):
    page.evaluate("draft={type:'flowadd',pts:[{x:0,y:0},{x:20,y:0}]};openCanvasMenu(500,300,{x:0,y:0})")
    root=page.locator('.rsCascade')
    assert root.get_by_role('menuitem',name='Concluir',exact=True).is_visible()
    assert root.get_by_role('menuitem',name='Cancelar',exact=True).is_visible()
    assert not root.get_by_role('menuitem',name='Modelar',exact=True).count()
    screenshot(page,'142_05_contexto_comando')
    page.keyboard.press('Escape');assert page.locator('.rsCascade').count()==0


def test_context_canvas_modeling_cascades(page):
    page.evaluate('openCanvasMenu(600,300,{x:0,y:0})')
    page.locator('.rsCascade').get_by_role('menuitem',name='Modelar',exact=True).hover()
    page.locator('.rsCascade').nth(1).get_by_role('menuitem',name='Tráfego e ligações',exact=True).hover()
    assert page.locator('.rsCascade').count()==3
    screenshot(page,'142_06_contexto_tres_niveis')


def test_flow_states_green_red_yellow_and_recalculation_pending(page):
    status=page.evaluate("""()=>{
      const a=flowStudyColor({technical_status:'ok'}),b=flowStudyColor({disabled:true}),c=flowStudyColor({technical_status:'adjustment'});
      RodoviaFlowStudy.stale=true;
      const pending=flowStudyColor({technical_status:'ok'});RodoviaFlowStudy.stale=false;
      return {a,b,c,pending};
    }""")
    assert status==dict(a='#22c55e',b='#ef4444',c='#eab308',pending='#eab308')
    assert 'não aparece no vídeo' in page.inner_text('#rsFlowLegend')
    screenshot(page,'142_07_legenda_fluxos')


def test_update_dialog_portuguese_and_exe_button(page):
    page.evaluate("api=async()=>({instalada:'1.42',modo:'exe',encontradas:[{arquivo:'RodoviaStudio_1_42_1_atualizacao.zip',versao:'1.42.1',pasta:'atualizacoes',mais_nova:true}],pasta_atualizacoes:'atualizacoes',rollback:{previous:'1.41'}});openUpdate()")
    assert page.locator('#updGo').is_visible()
    assert page.locator('#updRestore').is_visible()
    assert 'Downloads' not in page.inner_text('#updDlg')
    screenshot(page,'142_08_dialogo_atualizacao')


def test_failed_save_and_unfinished_command_block_update(page):
    assert page.evaluate("async()=>{pid='teste';draft=null;save=async()=>{throw Error('Falha de escrita')};return await rodoviaPrepararAtualizacao()}") is False
    assert page.evaluate("async()=>{draft={type:'flowadd',pts:[]};return await rodoviaPrepararAtualizacao()}") is False
    screenshot(page,'142_09_atualizacao_adiada')


@pytest.mark.parametrize('width',[1024,1920])
def test_workspace_responsive_and_panel_docked(page,width):
    page.set_viewport_size({'width':width,'height':900});page.locator('[data-pshub="props"]').click();page.wait_for_timeout(250)
    assert overlap(rect(page,'.editorSide'),rect(page,'.canvasWrap'))<1
    assert page.locator('#menuBar').bounding_box()['width']<=width
    screenshot(page,f'142_10_area_{width}')
