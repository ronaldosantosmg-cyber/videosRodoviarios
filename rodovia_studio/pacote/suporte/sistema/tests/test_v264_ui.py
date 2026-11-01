"""Aceitação real da escolha de detalhe: salvar/descartar, motor e WebGL."""
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot


def settled(p):p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=45000)


def test_quality_reaches_saved_config_discard_preserves_it_and_webgl_uses_it(gl_page,live):
    p=gl_page;settled(p)
    p.evaluate('RodoviaMaterialsHub.open()')
    p.locator('#realism_profile').select_option('realista');p.locator('#presentation_guides').check();p.locator('#dxf_lead_m').fill('45')
    screenshot(p,'266_ui_perfis')
    p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened');settled(p)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert saved['realism_profile']=='realista' and saved['presentation_guides'] is True and saved['dxf_lead_m']==45
    p.evaluate('RodoviaMaterialsHub.open()');p.locator('#realism_profile').select_option('ultra_realista');p.locator('#dxf_lead_m').fill('5');p.locator('#rsPanelDiscard').click();p.wait_for_function('!RodoviaPanels.opened');settled(p)
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['realism_profile']=='realista'
    assert p.locator('#realism_profile').input_value()=='realista' and p.locator('#dxf_lead_m').input_value()=='45'
    open3d(p)
    assert p.evaluate('Rodovia3D.stats().ready&&Rodovia3D.stats().vehicles>0')
    scene=p.request.get(live[0]+'/api/projects/'+live[1]+'/scene3d.json').json()
    assert scene['realism_profile']=='realista'
    screenshot(p,'266_3d')
