from ui_release_helpers import presentation_options
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot

def test_limit_selector_options_persist_and_recalculate_automatically(page):
    seed(page);presentation_options(page)
    field=page.locator('#min_route_segment_m')
    assert field.is_visible()
    assert set(field.locator('option').evaluate_all('(items)=>items.map(o=>Number(o.value))'))==set(range(20,201,20))|{50}
    page.evaluate("pid='limite-teste';window.recalculations=0;$('updFlows').onclick=()=>{window.recalculations++};void 0")
    field.select_option('120');page.wait_for_timeout(800)
    assert page.evaluate('collect().min_route_segment_m')==120
    assert page.evaluate('window.recalculations')==1
    screenshot(page,'1424_05_limite_fluxos')

def test_short_geometry_is_kept_and_project_limit_is_reversible(page):
    seed(page);presentation_options(page)
    page.locator('#min_route_segment_m').select_option('120')
    page.evaluate("concluirRota({pts:[{x:0,y:0},{x:90,y:0}],src:'cliques'})")
    assert page.evaluate('M.route_alignments.length')==1
    assert page.evaluate('M.route_alignments[0].enabled')
    assert 'sem veículos' in page.locator('#message').inner_text()
    page.locator('#min_route_segment_m').select_option('40')
    assert page.evaluate('minFlowLength()')==40 and page.evaluate('M.route_alignments[0].enabled')

def test_missing_and_legacy_values_are_not_silently_zeroed(page):
    page.evaluate('fill({})');assert page.evaluate('minFlowLength()')==50
    page.evaluate('fill({min_route_segment_m:75})');assert page.evaluate('collect().min_route_segment_m')==75
    assert page.locator('#min_route_segment_m option[data-legacy]').text_content()=='75 m (valor do projeto anterior)'
