from ui_release_helpers import ribbon_control
import json
from test_v1425_live_3d import live,gl_page
from test_v1426_transport_visual import click_world
from visual_harness import screenshot
from test_v142_visual import page


def test_cut_icon_removes_the_interval_from_circulation_and_keeps_the_dxf(gl_page,live):
    import hashlib
    p=gl_page;d=live[2]/live[1];before=hashlib.sha256((d/'input.dxf').read_bytes()).hexdigest()
    p.evaluate("start('analyze')");p.wait_for_function('!task && !taskRequestPending && !!editor',timeout=60000)
    ribbon_control(p,'flowcut','tool').click()
    click_world(p,500200,7800000);p.wait_for_function("draft?.type==='flowcut'")
    click_world(p,500260,7800000)
    p.wait_for_function('M.flow_cuts.length===1 && !task && !taskRequestPending && editor?.segments.length===2',timeout=60000)
    assert hashlib.sha256((d/'input.dxf').read_bytes()).hexdigest()==before
    report=json.loads((d/'traffic_network.json').read_text())
    assert report['explicit_flow_cuts'][0]['status']=='applied' and report['itineraries']>0
    screenshot(p,'14210_07_corte_de_intervalo_por_icone')
    p.evaluate('undo()');assert not p.evaluate('M.flow_cuts.length')


def test_join_icon_creates_one_valid_flow_and_preserves_undo(gl_page,live):
    p=gl_page;url=live[0]+'/api/projects/'+live[1]
    cfg=p.request.get(url).json()['config'];cfg.update(flow_cuts=[],flow_recoveries=[],flow_overrides=[],route_alignments=[],derive_traffic_paths=False,route_directions={'0':'off'},traffic_paths=[dict(id='a',name='Primeiro',points=[dict(x=500050,y=7800000),dict(x=500195,y=7800000)],kind='main',direction='growing'),dict(id='b',name='Segundo',points=[dict(x=500205,y=7800000),dict(x=500450,y=7800000)],kind='main',direction='growing')])
    assert p.request.put(url+'/config',data=cfg).ok
    p.evaluate('(id)=>load(id)',live[1]);p.evaluate("start('analyze')")
    p.wait_for_function('!task && !taskRequestPending && editor?.segments.length===2',timeout=60000)
    ribbon_control(p,'flowjoin','tool').click()
    click_world(p,500100,7800000);p.wait_for_function("draft?.type==='flowjoin'")
    click_world(p,500350,7800000)
    p.wait_for_function('M.route_alignments.length===1 && !task && !taskRequestPending',timeout=60000)
    report=json.loads((live[2]/live[1]/'traffic_network.json').read_text())
    assert report['itineraries']==1
    assert p.evaluate("M.flow_overrides.filter(o=>o.action==='disable').length")==2
    assert p.evaluate('M.route_alignments[0].type')=='unico'
    screenshot(p,'14210_08_juncao_validada_por_icone')
    p.evaluate('undo()');assert p.evaluate('M.route_alignments.length')==0
    assert p.evaluate('M.traffic_paths.length')==2


def test_flow_arrows_reverse_correctly_and_show_both_directions(gl_page):
    p=gl_page
    directions=p.evaluate("""()=>{const calls=[],before=arrowHead;arrowHead=(a,b)=>calls.push(Math.sign(b.x-a.x));try{arrowsAlong([{x:500050,y:7800000},{x:500450,y:7800000}],false,false,'#fff');const reverse=calls.slice();calls.length=0;arrowsAlong([{x:500050,y:7800000},{x:500450,y:7800000}],true,true,'#fff');return {reverse,both:calls}}finally{arrowHead=before}}""")
    assert directions['reverse'] and set(directions['reverse'])=={-1}
    assert set(directions['both'])=={-1,1}


def test_railway_can_be_created_by_selecting_a_route_then_choosing_model(gl_page):
    p=gl_page;p.evaluate("start('analyze')");p.wait_for_function('!task && !taskRequestPending && !!editor',timeout=60000)
    ribbon_control(p,'railway','tool').click()
    p.locator('#rsRailMode').select_option('fluxo')
    click_world(p,500250,7800000);p.wait_for_selector('#rsTransportDialog')
    assert p.locator('[data-transport-field=model]').is_visible()
    p.locator('[data-transport-field=model]').select_option('passageiros')
    p.locator('#rsTransportDialog button[type=submit]').click();p.wait_for_selector('#rsTransportDialog',state='detached')
    assert p.evaluate('M.railways[0].model')=='passageiros'
    screenshot(p,'14210_09_ferrovia_por_rota_selecionada')


def test_join_cannot_bypass_a_movement_explicitly_forbidden_in_the_project(gl_page,live):
    p=gl_page;url=live[0]+'/api/projects/'+live[1]
    cfg=p.request.get(url).json()['config'];cfg.update(flow_cuts=[],flow_recoveries=[],flow_overrides=[],route_alignments=[],railways=[],traffic_signals=[],signal_links=[],derive_traffic_paths=False,route_directions={'0':'off'},traffic_paths=[dict(id='a',name='A',points=[dict(x=500050,y=7800000),dict(x=500195,y=7800000)],kind='main',direction='growing'),dict(id='b',name='B',points=[dict(x=500205,y=7800000),dict(x=500450,y=7800000)],kind='main',direction='growing')],connection_rules=[dict(a=dict(x=500195,y=7800000),b=dict(x=500205,y=7800000),action='deny')])
    assert p.request.put(url+'/config',data=cfg).ok
    p.evaluate('(id)=>load(id)',live[1]);p.evaluate("start('analyze')");p.wait_for_function('!task && !taskRequestPending && editor?.segments.length===2',timeout=60000)
    stale=p.request.post(url+'/flow-tools/join',data={'first':0,'second':1,'revision':'0'*64})
    assert stale.status==409
    result=p.request.post(url+'/flow-tools/join',data={'first':0,'second':1})
    assert result.status==422 and 'proibida' in result.json()['detail']
    assert p.evaluate('M.route_alignments.length')==0


def test_a_protected_legacy_disable_with_empty_id_is_found_by_its_exact_reference(gl_page):
    p=gl_page
    index=p.evaluate("""()=>{const saved=M.flow_overrides;try{M.flow_overrides=[{id:'',x:500,y:0,action:'disable',enabled:true},{id:'',x:150,y:0,action:'disable',enabled:true}];return segOverride({points:[[0,0],[100,0]],disabled:true,override_ids:[''],protected_overrides:[{id:'',x:150,y:0,target_key:''}]},'disable')}finally{M.flow_overrides=saved}}""")
    assert index==1


def test_escape_cancels_a_join_before_the_delayed_validation_can_commit(page):
    from test_v1422_layout import seed
    seed(page)
    page.evaluate("""async()=>{window.beforeJoin=JSON.stringify(M);window.oldJoinApi=api;window.oldNearest=nearestSegment;let n=0;nearestSegment=()=>({...editor.segments[0],id:n++,mid:[100,0]});api=()=>new Promise(resolve=>window.finishPendingJoin=resolve);setTool('flowjoin');await FERRAMENTAS.flowjoin.clique({x:20,y:0});void FERRAMENTAS.flowjoin.clique({x:100,y:0})}""")
    page.wait_for_function('!!window.finishPendingJoin')
    page.keyboard.press('Escape');page.wait_for_function("tool==='pan' && draft===null")
    page.evaluate("finishPendingJoin({ok:true,points:[[0,0],[200,0]],level:0})")
    page.wait_for_timeout(100)
    assert page.evaluate('JSON.stringify(M)===beforeJoin')
    page.evaluate('()=>{api=oldJoinApi;nearestSegment=oldNearest}')
