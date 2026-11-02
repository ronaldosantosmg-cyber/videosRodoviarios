from test_v1425_live_3d import live,gl_page
from test_v14230_flow_ui import open_policy
from visual_harness import screenshot


def test_endpoint_controls_roundtrip_to_existing_engine_without_losing_section(gl_page,live):
    p=gl_page;p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    p.evaluate("""()=>{M.route_alignments=[{id:'nosP',name:'Principal por nós',points:[{x:500050,y:7800000},{x:500450,y:7800000}],enabled:true,type:'dupla',lanes:2,median_m:2,lane_width_m:3.5,sections:[],cross_sections:[]}]}""")
    p.set_viewport_size({'width':760,'height':820});d=open_policy(p)
    detail=d.locator('details').filter(has=p.locator('[data-node-field=flow_role]'));detail.locator('summary').click()
    d.locator('[data-node-field=flow_role]').select_option('principal')
    d.locator('[data-node-field=flow_start]').select_option('saida');d.locator('[data-node-field=flow_end]').select_option('entrada')
    screenshot(p,'14231_nos_sentido_secao')
    assert d.evaluate('e=>e.getBoundingClientRect().right<=innerWidth')
    d.locator('[data-calculate]').click();p.wait_for_function("!document.querySelector('#rsFlowPolicy')",timeout=30000)
    p.wait_for_function("""async()=>{const d=await(await fetch('/api/projects/'+pid)).json();return d.analysis?.traffic_simulation?.flow_balance?.conserved===true}""",timeout=120000)
    data=p.request.get(live[0]+'/api/projects/'+live[1]).json();r=data['config']['route_alignments'][0]
    assert r['flow_role']=='principal' and r['flow_start']=='saida' and r['flow_end']=='entrada'
    assert r['type']=='dupla' and r['lanes']==2 and r['median_m']==2
    p.reload();p.wait_for_function('!!window.RodoviaFlowPolicy',timeout=60000);p.evaluate('(v)=>load(v)',live[1]);p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    d=open_policy(p);assert d.locator('[data-node-field=flow_end]').input_value()=='entrada'
    d.get_by_role('button',name='Cancelar',exact=True).click()
