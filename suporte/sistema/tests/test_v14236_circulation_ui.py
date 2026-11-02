import json
from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def test_native_direction_reversal_persists_stable_key_not_list_position(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    p.get_by_role('tab',name='Tráfego',exact=True).click();p.get_by_role('button',name='Sentidos e nós',exact=True).click()
    p.locator('#rsDirections [data-native="0"]').select_option('forward')
    p.locator('#rsDirections [data-reverse-native="0"]').click();assert p.locator('#rsDirections [data-native="0"]').input_value()=='reverse'
    p.locator('#rsDirections [data-save]').click();p.locator('#rsDirections').wait_for(state='detached',timeout=30000)
    config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert any(k.startswith('axis:') and v=='reverse' for k,v in config['route_directions'].items())
    assert not any(k.isdigit() and v!='auto' for k,v in config['route_directions'].items())
    screenshot(p,'14236_sentido_estavel')


def test_manual_route_reversal_swaps_nodes_and_preserves_points(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    p.evaluate("async()=>{M.route_alignments.push({id:'reverse-route',name:'Via com nós',type:'unico',enabled:false,flow_direction:'crescente',flow_start:'entrada',flow_end:'saida',points:[{x:500100,y:7800000},{x:500400,y:7800000}]});projectSession.epoch++;await save()}")
    before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['route_alignments'][0]
    p.evaluate('RodoviaCirculation.directions()');p.locator('#rsDirections [data-reverse-route="0"]').click()
    assert p.locator('#rsDirections [data-start="0"]').input_value()=='saida'
    p.locator('#rsDirections [data-save]').click();p.locator('#rsDirections').wait_for(state='detached',timeout=30000)
    after=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['route_alignments'][0]
    assert after['points']==before['points'] and not after['enabled']
    assert after['flow_direction']=='decrescente' and after['flow_start']=='saida' and after['flow_end']=='entrada'
    for name in ['Inserir nó de ligação','Editar nó','Mover nó de ligação','Apagar nó','Nó de entrada, saída ou fim']:
        p.get_by_role('tab',name='Tráfego',exact=True).click();assert p.get_by_role('button',name=name,exact=True).is_visible()


def test_short_check_has_preview_and_rejects_stale_report_without_overwriting_config(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    # Fixture compartilhada pode ter eixo revertido, mas mantém fonte cadastrada.
    p.evaluate('RodoviaCirculation.check()');p.locator('#rsCirculationCheck').wait_for(state='visible',timeout=60000)
    report=p.request.get(live[0]+'/api/projects/'+live[1]+'/traffic-check').json()
    assert report['itineraries']>0 and report['fleet']['paths'] and report['duration_s']<=10
    assert p.request.get(live[0]+'/api/projects/'+live[1]+'/traffic-check.png').status==200
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    screenshot(p,'14236_conferencia_circulacao')
    assert p.locator('#rsCirculationCheck footer [data-close]').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight')
    p.locator('#rsCirculationCheck [data-close]').last.click()
    p.evaluate("async()=>{$('traffic_density').value='2';projectSession.epoch++;await save()}")
    assert p.request.get(live[0]+'/api/projects/'+live[1]+'/traffic-check').status==409


def test_poll_connection_loss_offers_resume_without_duplicate_calculation(gl_page,live):
    p=gl_page
    result=p.evaluate('''async()=>{const previous=api;let reads=0;api=async(url,opt)=>{if(url==='/api/jobs/test-tracking'){reads++;throw Error('Conexão perdida no ensaio')}return previous(url,opt)};try{await poll('test-tracking')}catch{}finally{api=previous}return {reads,task,visible:!$('rsResumeTracking').hidden}}''')
    assert result==dict(reads=1,task='test-tracking',visible=True)
    result=p.evaluate('''async()=>{const previous=api;let posts=0;api=async(url,opt)=>{if(opt?.method==='POST')posts++;if(url==='/api/jobs/test-tracking')return {id:'test-tracking',state:'done',project:'outro',kind:'analyze',message:'Concluído'};return previous(url,opt)};try{await poll('test-tracking');return {posts,task}}finally{api=previous}}''')
    assert result==dict(posts=0,task='')


def test_alignment_result_is_discarded_after_context_changes(gl_page):
    p=gl_page
    result=p.evaluate('''async()=>{const previous=api,oldContext=projectSession.context;let release;const wait=new Promise(r=>release=r);api=(url,opt)=>url==='/api/alignment/fit'?wait:previous(url,opt);alignResult=null;try{const work=fitAlign(false);projectSession.context++;release({mode:'translation',tx:99,ty:88,rms_m:0,pairs_used:1});const result=await work;return {discarded:result===false,alignment:alignResult}}finally{api=previous;projectSession.context=oldContext}}''')
    assert result==dict(discarded=True,alignment=None)
