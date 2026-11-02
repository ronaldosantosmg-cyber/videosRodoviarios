from test_v1425_live_3d import live,gl_page
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_recovery_button_is_visible_in_selected_flow_properties(page):
    seed(page);page.evaluate('selSeg={id:0};showSegProps()')
    assert page.locator('[data-flow-recovery=recover]').is_visible()
    assert 'Não liga através das lacunas' in page.locator('[data-flow-recovery=recover]').get_attribute('title')
    screenshot(page,'14210_01_recuperar_fluxo_principal')


def test_recovery_action_is_saved_recalculated_and_can_be_undone(gl_page,live):
    p=gl_page;p.evaluate("()=>{selSeg={id:editor.segments[0].id};showSegProps()}")
    points_before=p.evaluate('JSON.stringify(editor.segments[0].points)')
    p.locator('[data-flow-recovery=recover]').click()
    p.locator('[data-choice=save]').click()
    p.wait_for_function('!task && (editor?.segments||[]).some(s=>s.technical_recovery?.enabled)',timeout=60000)
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert len(cfg['flow_recoveries'])==1
    assert p.evaluate('JSON.stringify(editor.segments[0].points)')==points_before
    p.evaluate('selSeg={id:editor.segments[0].id};showSegProps()')
    assert p.locator('[data-flow-recovery=remove]').is_visible()
    screenshot(p,'14210_02_fluxo_recuperado_recalculado')
    p.locator('#rsPanelClose').click()
    # O checkpoint da ação continua no histórico mesmo após o recálculo.
    p.evaluate('undo()')
    assert not p.evaluate("M.flow_recoveries.length>0")


def test_problem_axis_recovers_vehicle_tracks_without_changing_the_dxf(gl_page,live):
    import io,json,hashlib
    import ezdxf
    p=gl_page;url=live[0]+'/api/projects/'+live[1]
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO')
    model=doc.modelspace();model.add_lwpolyline([(500050,7800000),(500200,7800000),(500200,7800150)],dxfattribs={'layer':'EIXO'})
    hatch=model.add_hatch(dxfattribs={'layer':'PAVIMENTO'});hatch.paths.add_polyline_path([(500000,7799980),(500230,7799980),(500230,7800170),(500000,7800170)],is_closed=True)
    buffer=io.StringIO();doc.write(buffer);raw=buffer.getvalue().encode('utf-8')
    response=p.request.post(url+'/files',multipart={'file':{'name':'eixo_generico.dxf','mimeType':'application/octet-stream','buffer':raw}})
    assert response.ok,response.text()
    cfg=p.request.get(url).json()['config'];cfg.update(derive_traffic_paths=False,vehicle_paths='anterior',flow_recoveries=[],flow_overrides=[],min_route_segment_m=50)
    assert p.request.put(url+'/config',data=cfg).ok
    p.evaluate('(id)=>load(id)',live[1]);p.wait_for_function('!task',timeout=60000)
    p.evaluate("start('analyze')")
    p.wait_for_function('!task && !taskRequestPending && !!editor',timeout=60000)
    directory=live[2]/live[1]
    assert json.loads((directory/'traffic_network.json').read_text())['itineraries']==0
    before=hashlib.sha256((directory/'input.dxf').read_bytes()).hexdigest()
    p.evaluate('selSeg={id:editor.segments[0].id};showSegProps()')
    p.locator('[data-flow-recovery=recover]').click();p.locator('[data-choice=save]').click()
    p.wait_for_function('!task && editor?.segments.some(s=>s.technical_recovery?.excluded_m>0)',timeout=60000)
    assert json.loads((directory/'traffic_network.json').read_text())['itineraries']>0
    p.wait_for_function('!taskRequestPending && !RodoviaFlowStudy.stale',timeout=15000)
    p.evaluate("()=>{selSeg={id:editor.segments[0].id};showSegProps()}")
    assert 'excluídos' in p.locator('.rsFlowDiagnostic').inner_text()
    screenshot(p,'14210_03_eixo_com_falha_recuperado')
    p.locator('#rsPanelClose').click()
    p.evaluate("start('scene3d')")
    job=p.request.get(live[0]+'/api/jobs/'+p.evaluate('lastPolled')).json()
    assert job['state']=='done' and job['kind']=='scene3d',job
    scene=json.loads((directory/'scene3d.json').read_text())
    from app.scene3d import revision
    assert scene['revision']==revision(directory)
    assert scene['vehicles']
    assert hashlib.sha256((directory/'input.dxf').read_bytes()).hexdigest()==before


def test_two_simultaneous_requests_start_only_one_calculation(gl_page):
    p=gl_page
    p.wait_for_function('!task && !taskRequestPending',timeout=60000)
    results=p.evaluate("""async()=>{window.analysisRequests=0;const previous=api;api=async function(url,opt){if(url.endsWith('/analyze')&&opt?.method==='POST')analysisRequests++;return previous(url,opt)};try{return await Promise.all([start('analyze'),start('analyze')])}finally{api=previous}}""")
    assert False in results
    assert p.evaluate('analysisRequests')==1
    assert p.evaluate('!taskRequestPending && !task')
