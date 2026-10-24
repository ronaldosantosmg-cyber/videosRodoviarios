import pytest
pw=pytest.importorskip("playwright.sync_api")
from visual_harness import chromium_path,load_offline,screenshot

def run_page(fn):
    exe=chromium_path()
    if not exe: pytest.skip("Chromium não encontrado.")
    with pw.sync_playwright() as p:
        b=p.chromium.launch(executable_path=exe,args=["--disable-gpu","--no-sandbox"])
        page=b.new_page(viewport={"width":1366,"height":768});errors=[]
        page.on("pageerror",lambda e: errors.append(str(e)))
        load_offline(page);fn(page);assert not errors, errors;b.close()

def select_route(page,length=500):
    return page.evaluate("""(L)=>{M.route_alignments=[{id:'r1',name:'Rota 01',points:[{x:0,y:0},{x:L,y:0}],enabled:true,type:'dupla',lanes:2,median_m:6,lane_width_m:3.5,taper_m:40,level:0,outside_pavement:false,sections:[],lane_change:'marked',lane_change_sections:[]}];sel={key:'route_alignments',i:0};selSet=[];showProps();return true}""",length)

def test_route_menu_is_portuguese_and_operable():
    def f(page):
        select_route(page)
        txt=page.locator("#propPanel").inner_text()
        assert "Ultrapassagem e mudança de faixa" in txt and "Somente em trechos permitidos" in txt
        assert "lane_change" not in txt and "marked" not in txt
        page.select_option("#propPanel [data-lcmode]","off")
        assert page.evaluate("M.route_alignments[0].lane_change")=="off"
        page.select_option("#propPanel [data-lcmode]","safe")
        assert page.evaluate("M.route_alignments[0].lane_change")=="safe"
        screenshot(page,"1410_01_menu_rotas_portugues")
    run_page(f)

def test_short_route_is_visually_disabled_and_safe():
    def f(page):
        select_route(page,40)
        txt=page.locator("#propPanel").inner_text()
        assert "Rota não habilitada para veículos" in txt and "50 m" in txt
        assert page.evaluate("M.route_alignments[0].enabled") is False
        screenshot(page,"1410_02_rota_curta_bloqueada")
    run_page(f)

def test_route_rule_add_edit_delete_menu():
    def f(page):
        select_route(page,600)
        page.locator("#propPanel [data-lcadd='allow']").click()
        assert page.locator("#propPanel [data-lcdel]").count()==1
        page.locator("#propPanel [data-lc='0:start_m']").fill("100");page.locator("#propPanel [data-lc='0:start_m']").press("Enter")
        page.locator("#propPanel [data-lc='0:end_m']").fill("300");page.locator("#propPanel [data-lc='0:end_m']").press("Enter")
        z=page.evaluate("M.route_alignments[0].lane_change_sections[0]")
        assert z["start_m"]==100 and z["end_m"]==300
        page.locator("#propPanel [data-lcdel='0']").click()
        assert page.evaluate("M.route_alignments[0].lane_change_sections.length")==0
        screenshot(page,"1410_03_regra_rota_crud")
    run_page(f)
