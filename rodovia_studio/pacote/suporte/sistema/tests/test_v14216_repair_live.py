from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_visible_repair_action_reaches_real_motor_and_preserves_dxf(gl_page,live):
    import hashlib,json
    p=gl_page;url=live[0]+'/api/projects/'+live[1];directory=live[2]/live[1]
    # O ensaio exige um defeito real; um eixo reto já aprovado não deve ser recuperado.
    import ezdxf
    from app import project_state as P
    from app.native_axes import axis_fingerprint
    doc=ezdxf.readfile(directory/'input.dxf');m=doc.modelspace()
    for entity in list(m):m.delete_entity(entity)
    points=[(500050,7800000),(500200,7800000),(500200,7800150)]
    m.add_lwpolyline(points,dxfattribs={'layer':'EIXO'})
    hatch=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});hatch.paths.add_polyline_path([(500000,7799980),(500500,7799980),(500500,7800200),(500000,7800200)],is_closed=True);doc.saveas(directory/'input.dxf')
    config=P.read_config(directory);config['route_directions']={'axis:'+axis_fingerprint(points,'EIXO',0):'forward'};P.save_config(directory,config)
    p.evaluate('async id=>{await load(id,{resultsOnly:true,syncConfig:true});await start("analyze")}',live[1])
    before=hashlib.sha256((directory/'input.dxf').read_bytes()).hexdigest()
    p.get_by_role('tab',name='Tráfego',exact=True).click();p.get_by_role('button',name='Corrigir problemas',exact=True).click();p.get_by_role('button',name='Recortar, juntar e recuperar',exact=True).click()
    p.locator('.rsFlowRepairAdvanced').first.locator('summary').click()
    p.locator('[data-repair-action=recover]').first.click()
    p.wait_for_function('!task && !taskRequestPending && !!editor?.segments.some(s=>s.technical_recovery?.enabled)',timeout=60000)
    config=p.request.get(url).json()['config']
    assert len(config['flow_recoveries'])==1
    assert json.loads((directory/'traffic_network.json').read_text())['itineraries']>0
    assert hashlib.sha256((directory/'input.dxf').read_bytes()).hexdigest()==before
    assert not p.evaluate('!!document.querySelector("dialog[open]")')
    p.get_by_role('tab',name='Tráfego',exact=True).click();p.get_by_role('button',name='Corrigir problemas',exact=True).click();p.get_by_role('button',name='Recortar, juntar e recuperar',exact=True).click()
    screenshot(p,'14216_recuperacao_motor_real')
