import re
import pytest
import zipfile
from pathlib import Path
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot,rect,open_activity


def test_all_original_139_tools_are_accessible_from_compact_bar(page):
    root=Path(__file__).resolve().parents[5]
    with zipfile.ZipFile(root/'atualizacoes/RodoviaStudio_1_39_atualizacao.zip') as z:
        name=next(n for n in z.namelist() if n.endswith('/app/js/04_ferramentas.js'))
        text=z.read(name).decode();text=text[text.index('const TOOLS='):text.index('const ICON_PATHS=')]
        expected=set(re.findall(r"\['([a-z_][a-z_0-9]*)','",text))
    actual=set(page.evaluate('TOOLS.filter(Array.isArray).map(t=>t[0])'))
    assert expected<=actual
    page.get_by_role('menuitem',name='Editar',exact=True).click()
    assert page.locator('.rsCascade').first.get_by_role('menuitem').count()>=6
    screenshot(page,'1423_01_ferramentas_139_restauradas')


def test_zoom_redraw_and_pan_quick_buttons_work(page):
    seed(page)
    page.evaluate('view.s=1.;view.ox=20;view.oy=30;draw()')
    page.evaluate("canvas.dispatchEvent(new WheelEvent('wheel',{clientX:300,clientY:400,deltaY:-100,cancelable:true}))");assert page.evaluate('view.s')>1.
    page.evaluate("canvas.dispatchEvent(new WheelEvent('wheel',{clientX:300,clientY:400,deltaY:100,cancelable:true}))");assert abs(page.evaluate('view.s')-1)<1e-6
    before=page.evaluate('({...view})');page.evaluate("runCommand('REDRAW')");page.wait_for_timeout(150)
    assert page.evaluate('({...view})')==pytest.approx(before,rel=0,abs=1e-9)
    page.locator('#rsQuickNavigation [data-rs-tool="pan"]').click();assert page.evaluate('tool')=='pan'
    screenshot(page,'1423_02_pan_zoom_redesenhar')


def test_modify_menu_keeps_transform_actions(page):
    open_activity(page,'Editar')
    names=page.locator('#rsToolPanel1 [data-rs-command]').all_text_contents()
    for label in ['Mover','Girar','Copiar','Escala','Espelhar','Paralela']:assert any(label in n for n in names)
    screenshot(page,'1423_03_modificar')


def test_insert_control_vertex_and_undo_without_corrupting_route(page):
    seed(page)
    page.evaluate("M.route_alignments=[{id:'r',name:'Rota',points:[{x:0,y:0},{x:100,y:0}],enabled:true,type:'simples',lanes:1,median_m:0,lane_width_m:3.5,taper_m:40,sections:[],lane_change_sections:[]}];sel={key:'route_alignments',i:0};showProps()")
    open_activity(page,'Editar').locator('[data-rs-tool=insertcontrol]').click()
    page.evaluate('click({x:50,y:0},{})')
    assert page.evaluate('M.route_alignments[0].points.length')==3
    assert page.evaluate('M.route_alignments[0].points[1]')==dict(x=50,y=0)
    page.evaluate('undo()');assert page.evaluate('M.route_alignments[0].points.length')==2
    screenshot(page,'1423_04_inserir_controle_desfazer')


def test_point_and_calibration_actions_are_not_hidden(page):
    open_activity(page,'Projeto').locator('[data-rs-tool=pair]').click()
    assert page.evaluate('tool')=='pair'
    open_activity(page,'Editar').locator('[data-rs-tool=move]').first.click()
    assert page.evaluate('tool')=='move'
    assert rect(page,'#rsToolRibbon')['height']<180
    screenshot(page,'1423_05_controle_calibracao')
