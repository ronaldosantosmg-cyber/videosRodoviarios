from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def test_lost_response_after_commit_is_reconciled_once(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    result=p.evaluate('''async()=>{
      const previous=fetch;let puts=0;
      window.fetch=async(url,opt)=>{const response=await previous(url,opt);if(String(url).endsWith('/config')&&opt?.method==='PUT'){puts++;throw new TypeError('Resposta perdida após commit')}return response};
      try {$('name').value='Salvo com resposta perdida';projectSession.epoch++;savePending=true;await save();return {puts,pending:savePending,name:cfg.name}}
      finally {window.fetch=previous}
    }''')
    assert result==dict(puts=1,pending=False,name='Salvo com resposta perdida')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']==result['name']


def test_switch_project_clears_highlight_and_rejects_late_lane_preview(gl_page,live):
    p=gl_page
    new=p.request.post(live[0]+'/api/projects',data={'name':'Projeto vazio B','origin':'Origem B','destination':'Destino B'}).json()['id']
    p.evaluate('''()=>{
      window._previousFetch=fetch;window._laneGate=new Promise(resolve=>window._releaseLane=resolve);
      window.fetch=async(url,opt)=>String(url)==='/api/rotas_previa'?(_releaseReady=true,await _laneGate,new Response(JSON.stringify({lanes:[{points:[[1,2],[3,4]],dir:'f',enabled:true}]}),{headers:{'Content-Type':'application/json'}})):_previousFetch(url,opt);
      window._releaseReady=false;
      layerShow={name:'RESIDUO_A',p:[[[500000,7800000],[500500,7800000]]]};layerPrev={RESIDUO_A:{p:layerShow.p}};
      M.route_alignments=[{id:'late',name:'Eixo temporário',enabled:true,type:'unico',points:[{x:500000,y:7800000},{x:500500,y:7800000}]}];refreshRouteLanes(true);
    }''')
    p.wait_for_function('_releaseReady')
    p.evaluate('(id)=>load(id)',new)
    p.evaluate('''async()=>{_releaseLane();await new Promise(r=>setTimeout(r,50));window.fetch=_previousFetch}''')
    assert p.evaluate('layerShow===null&&layerPrev===null&&routeLanes.length===0&&editor===null&&geo===null')
    assert p.locator('#layers').inner_text()==''
    assert p.evaluate('cfg.name')=='Projeto vazio B'
    screenshot(p,'14235_projeto_novo_sem_residuos')


def test_old_layer_request_cannot_restore_highlight_in_new_context(gl_page,live):
    p=gl_page
    result=p.evaluate('''async()=>{
      const previous=fetch;let release;const wait=new Promise(r=>release=r);layerPrev=null;
      window.fetch=async(url,opt)=>String(url).endsWith('/layers_preview.json')?(await wait,new Response(JSON.stringify({ANTIGA:{p:[[[1,1],[2,2]]]}}))):previous(url,opt);
      const work=showLayer('ANTIGA');projectSession.context++;layerShow=null;layerPrev=null;
      release();await work;window.fetch=previous;return {highlight:layerShow,catalog:layerPrev}
    }''')
    assert result==dict(highlight=None,catalog=None)


def test_axis_suggestion_requires_explicit_designation(gl_page):
    p=gl_page
    result=p.evaluate('''()=>{const old=cfg.layers;cfg.layers={};showLayers();const choice=document.querySelector('#layers select[data-layer="EIXO"]');const value=choice?.value;cfg.layers=old;showLayers();return value}''')
    assert result==''
