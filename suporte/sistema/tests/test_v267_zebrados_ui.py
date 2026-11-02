from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot

def test_zebra_confirm_cancel_flow_and_saved_metric_geometry(gl_page,live):
    p=gl_page;p.wait_for_function('!!window.RodoviaZebrados')
    p.evaluate("async()=>{window.zebraCount=M.hatch_areas.length;runCommand('ZEBRADOAMARELO');for(const w of [{x:500180,y:7800001},{x:500200,y:7800001},{x:500200,y:7800006},{x:500180,y:7800006}])feedPoint(w);await finishDraft()}")
    d=p.locator('#rsZebraDialog');d.locator('[data-z=width]').fill('.6');d.locator('[data-z=gap]').fill('1.4');d.locator('[data-z=angle]').fill('-45');screenshot(p,'267_zebrado_ui');d.locator('[data-save]').click();p.wait_for_function('!document.getElementById("rsZebraDialog")');p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=60000)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['hatch_areas'][-1]
    assert saved['color']=='yellow' and saved['angle_deg']==-45 and saved['stripe_width_m']==.6 and saved['spacing_m']==2 and saved['world_aligned']
    assert p.evaluate('M.hatch_areas.length===zebraCount+1')
    p.evaluate('RodoviaZebrados.open({index:M.hatch_areas.length-1})');d.locator('[data-z=width]').fill('0');d.locator('[data-save]').click();assert d.is_visible();assert 'largura' in d.locator('[data-error]').inner_text()
    d.locator('[data-z=width]').fill('.8');d.locator('[data-close]').first.click();p.locator('[data-draft-choice=discard]').click();p.wait_for_function('!document.getElementById("rsZebraDialog")');assert p.evaluate('M.hatch_areas.at(-1).stripe_width_m')==.6
    data=p.evaluate("()=>{const backup=editor;try{editor={segments:[{points:[[0,0],[100,0]],forward:true}]};const points=[{x:10,y:1},{x:20,y:1},{x:20,y:5},{x:10,y:5}];return {angle:RodoviaZebrados.reference(points),bars:RodoviaZebrados.segments({points,angle_deg:45,spacing_m:2,stripe_width_m:.6,world_aligned:true}).length}}finally{editor=backup}}")
    assert data['angle']==0 and data['bars']>3
    assert p.locator('#rsZebra-white').count()==1 and p.locator('#rsZebra-yellow').count()==1
