from test_v14234_nodes_ui_video import live, gl_page
from visual_harness import screenshot


def test_large_node_catalog_is_indexed_cached_and_invalidated(gl_page):
    result=gl_page.evaluate('''()=>{
      const original=editor,marks=M,epoch=projectSession.epoch;
      try {
        let reads=0;const segments=Array.from({length:20000},(_,i)=>({id:i,origin_key:String(i)}));
        for(const s of segments){const id=s.id;Object.defineProperty(s,'id',{get(){reads++;return id}})}
        editor={engine_revision:'stress',segments,connections:Array.from({length:2000},(_,i)=>({from:i,to:i+1,a:[i,0],b:[i+1,0],p:[[i,0],[i+1,0]]}))};
        M={...M,connection_rules:[],route_alignments:[]};projectSession.epoch++;
        const first=RodoviaNodes.nodes(),initialReads=reads;
        for(let i=0;i<30;i++)if(RodoviaNodes.nodes()!==first)throw Error('Cache não reutilizado');
        const cachedReads=reads;
        projectSession.epoch++;const edited=RodoviaNodes.nodes();
        return {count:first.length,initialReads,cachedReads,invalidated:edited!==first};
      } finally {editor=original;M=marks;projectSession.epoch=epoch}
    }''')
    assert result['count']==500
    assert result['initialReads']==20000
    assert result['cachedReads']==result['initialReads'] and result['invalidated']


def test_failed_node_save_releases_form_and_retry_persists(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    p.evaluate('''()=>{M.connection_rules.push({id:'save-retry',name:'Nó teste',a:{x:500100,y:7800000},b:{x:500101,y:7800000},action:'force',enabled:true});projectSession.epoch++;RodoviaNodes.select({x:500100.5,y:7800000});return RodoviaNodes.edit().then(()=>true)}''')
    p.locator('#rsNodeEdit [data-name]').fill('Nó confirmado após falha')
    pattern='**/api/projects/'+live[1]+'/config'
    def fail(route):
        if route.request.method=='PUT':route.fulfill(status=503,json={'detail':'Falha temporária de gravação no teste'})
        else:route.continue_()
    p.route(pattern,fail)
    p.locator('#rsNodeEdit [data-save]').click()
    p.wait_for_function("document.querySelector('#rsNodeEdit [data-error]').textContent.includes('Falha temporária')")
    assert p.locator('#rsNodeEdit [data-save]').is_enabled()
    assert p.locator('#rsNodeEdit [data-name]').input_value()=='Nó confirmado após falha'
    screenshot(p,'14235_falha_salvar_no_recuperavel')
    p.unroute(pattern,fail)
    p.locator('#rsNodeEdit [data-save]').click();p.locator('#rsNodeEdit').wait_for(state='detached',timeout=30000)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert next(r for r in saved['connection_rules'] if r['id']=='save-retry')['name']=='Nó confirmado após falha'
