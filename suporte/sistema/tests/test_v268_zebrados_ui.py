import pytest
from test_v1425_live_3d import live as old_live,gl_page
from test_v268_zebrados_dxf import add_zebra
from visual_harness import screenshot

@pytest.fixture(scope='module')
def live(tmp_path_factory):
    gen=old_live.__wrapped__(tmp_path_factory);value=next(gen)
    try:
        from app.models import Settings
        from app.scene3d import build
        d=value[2]/value[1];add_zebra(d);s=Settings.model_validate_json((d/'config.json').read_text());s.lanes_per_direction=1;(d/'config.json').write_text(s.model_dump_json());build(d,s);yield value
    finally:next(gen,None)


def test_dxf_sources_directions_override_and_selected_contour(gl_page,live):
    p=gl_page;p.evaluate('RodoviaZebrados.sources()');hub=p.locator('#rsZebraSources');assert hub.get_by_text('ZEBRADO AMARELO',exact=True).is_visible()
    hub.locator('[data-config]').first.click();d=p.locator('#rsZebraDialog');d.locator('summary').click();d.locator('[data-z=directionA]').fill('0');d.locator('[data-z=directionB]').fill('180');d.locator('[data-color-flow]').click();assert d.locator('[data-z=color]').input_value()=='yellow';d.locator('[data-flow="-45"]').click();assert float(d.locator('[data-z=angle]').input_value())==-45
    d.locator('[data-z=width]').fill('.5');d.locator('[data-z=gap]').fill('1.5');screenshot(p,'268_zebrado_sentidos');d.locator('[data-save]').click();p.wait_for_function('!document.getElementById("rsZebraDialog")');p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=60000)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['hatch_areas'];assert len(saved)==1 and saved[0]['source_id'].startswith('dxf-zebra-') and saved[0]['holes'] and len(saved[0]['flow_guides'])==2 and saved[0]['angle_deg']==-45
    p.evaluate('RodoviaZebrados.sources()');hub.locator('[data-config]').first.click();d.locator('[data-z=enabled]').uncheck();d.locator('[data-save]').click();p.wait_for_function('!document.getElementById("rsZebraDialog")');p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=60000)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['hatch_areas'];assert len(saved)==1 and saved[0]['enabled'] is False
    p.evaluate('async()=>{await pickDxfArea({x:500120,y:7800012});RodoviaZebrados.selectedContour()}');assert d.is_visible();assert d.locator('[data-z=detach]').count()==0;d.locator('[data-close]').first.click();p.wait_for_function('!document.getElementById("rsZebraDialog")')
    p.evaluate("RodoviaZebrados.open({points:[{x:500280,y:7799998},{x:500300,y:7799998},{x:500300,y:7800002},{x:500280,y:7800002}]})")
    d.locator('summary').click();d.locator('[data-z=directionA]').fill('0');d.locator('[data-z=directionB]').fill('180');d.locator('[data-save]').click();p.wait_for_function('!document.getElementById("rsZebraDialog")');p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=60000)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['hatch_areas'][-1]
    assert saved['flow_guides'][0]['heading_deg']==0 and saved['flow_guides'][1]['heading_deg']==180
    assert saved['flow_guides'][0]['point']['y']<7800000<saved['flow_guides'][1]['point']['y']
    assert p.locator('#rsZebraDxf').count()==1
