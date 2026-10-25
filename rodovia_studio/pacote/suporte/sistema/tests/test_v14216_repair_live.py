from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_visible_repair_action_reaches_real_motor_and_preserves_dxf(gl_page,live):
    import hashlib,json
    p=gl_page;url=live[0]+'/api/projects/'+live[1];directory=live[2]/live[1]
    before=hashlib.sha256((directory/'input.dxf').read_bytes()).hexdigest()
    p.locator('#rsRepairFlows').click()
    p.locator('[data-repair-action=recover]').first.click()
    p.wait_for_function('!task && !taskRequestPending && !!editor?.segments.some(s=>s.technical_recovery?.enabled)',timeout=60000)
    config=p.request.get(url).json()['config']
    assert len(config['flow_recoveries'])==1
    assert json.loads((directory/'traffic_network.json').read_text())['itineraries']>0
    assert hashlib.sha256((directory/'input.dxf').read_bytes()).hexdigest()==before
    assert not p.evaluate('!!document.querySelector("dialog[open]")')
    p.locator('#rsRepairFlows').click()
    screenshot(p,'14216_recuperacao_motor_real')
