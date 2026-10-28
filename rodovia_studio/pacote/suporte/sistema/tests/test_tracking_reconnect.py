"""Reconexão de leitura: não reenviar cálculos nem falhar por espera de dois minutos."""
from test_v142_visual import page
from test_v1425_live_3d import live,gl_page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_transient_outage_recovers_automatically_without_posts_or_error_storm(page):
    result=page.evaluate('''async()=>{
      const previous=api;let reads=0,posts=0,lost=0,resumed=0;
      const onLost=()=>lost++,onResumed=()=>resumed++;
      addEventListener('rodovia:tracking-lost',onLost);addEventListener('rodovia:tracking-resumed',onResumed);
      api=async(url,opt)=>{if(opt?.method==='POST')posts++;if(url==='/api/jobs/reconnect'){reads++;if(reads===1)throw Error('Rede indisponível');return {id:'reconnect',state:'done',project:'other',kind:'analyze',message:'Concluído'}};return previous(url,opt)};
      try{const result=await poll('reconnect');return {reads,posts,lost,resumed,state:result.state,task,stored:localStorage.getItem('rodovia_job'),visible:!$('rsResumeTracking').hidden}}
      finally{api=previous;removeEventListener('rodovia:tracking-lost',onLost);removeEventListener('rodovia:tracking-resumed',onResumed)}
    }''')
    assert result==dict(reads=2,posts=0,lost=1,resumed=1,state='done',task='',stored=None,visible=False)


def test_manual_resume_shares_the_existing_poll_and_only_one_get_is_in_flight(page):
    result=page.evaluate('''async()=>{
      const previous=api;let reads=0,finish;
      api=async(url,opt)=>{if(url==='/api/jobs/single-poll'){reads++;return await new Promise(r=>finish=r)}return previous(url,opt)};
      try{const a=poll('single-poll'),b=poll('single-poll');const same=a===b;finish({id:'single-poll',state:'done',project:'other',kind:'analyze',message:'Concluído'});await Promise.all([a,b]);return {reads,task}}
      finally{api=previous}
    }''')
    assert result==dict(reads=1,task='')


def test_waiting_over_two_minutes_does_not_fail_or_submit_and_can_clear_queue(page):
    seed(page)
    result=page.evaluate('''async()=>{
      const previous=Date.now,oldApi=api;let offset=0,status='waiting',posts=0;
      Date.now=()=>previous()+offset;api=async(url,opt)=>{if(opt?.method==='POST')posts++;return oldApi(url,opt)};
      try{pid='long-running';task='server-job';const request=start('analyze').then(v=>{status=v===false?'cleared':'submitted';return v},e=>{status=e.message;return 'failed'});offset=300000;await new Promise(r=>setTimeout(r,400));const during=status;RodoviaUpdates.clearQueue();const value=await request;return {during,status,value,posts,task,queue:RodoviaUpdates.snapshot().requests}}
      finally{Date.now=previous;api=oldApi;task=''}
    }''')
    assert result==dict(during='waiting',status='cleared',value=False,posts=0,task='server-job',queue=0)


def test_start_repeated_during_outage_shares_original_calculation(page):
    seed(page)
    result=page.evaluate('''async()=>{
      const before={api,save};let posts=0,reads=0;pid='same-request';save=async()=>{};
      const lost=new Promise(r=>addEventListener('rodovia:tracking-lost',r,{once:true}));
      api=async(url,opt)=>{if(url==='/api/projects/same-request/analyze'){posts++;return {id:'same-job'}}if(url==='/api/jobs/same-job'){reads++;if(reads===1)throw Error('Perda de conexão');return {id:'same-job',state:'done',project:'other',kind:'analyze',message:'Concluído'}}return before.api(url,opt)};
      try{const a=start('analyze'),b=start('analyze');await lost;const c=start('analyze');poll('same-job');const all=await Promise.all([a,b,c]);return {same:a===b&&b===c,posts,reads,states:all.map(r=>r.state),task,queued:RodoviaUpdates.snapshot().requests}}
      finally{api=before.api;save=before.save}
    }''')
    assert result==dict(same=True,posts=1,reads=2,states=['done']*3,task='',queued=0)


def test_cancel_during_outage_is_observed_without_resubmitting_calculation(page):
    result=page.evaluate('''async()=>{
      const previous=api;let cancelled=false,posts=[];
      const lost=new Promise(r=>addEventListener('rodovia:tracking-lost',r,{once:true}));
      api=async(url,opt)=>{if(opt?.method==='POST'){posts.push(url);cancelled=true;return {ok:true}}if(url==='/api/jobs/cancel-reconnect'){if(!cancelled)throw Error('Rede indisponível');return {id:'cancel-reconnect',state:'cancelled',project:'other',kind:'analyze',message:'Cancelado'}}return previous(url,opt)};
      try{const work=poll('cancel-reconnect');await lost;await $('cancel').onclick();poll('cancel-reconnect');const result=await work;return {posts,state:result.state,task,disabled:$('cancel').disabled}}
      finally{api=previous}
    }''')
    assert result==dict(posts=['/api/jobs/cancel-reconnect/cancel'],state='cancelled',task='',disabled=True)


def test_completed_job_never_loads_a_project_switched_during_outage(page):
    result=page.evaluate('''async()=>{
      const before={api,load,pid,context:projectSession.context};let reads=0,loads=0;
      const lost=new Promise(r=>addEventListener('rodovia:tracking-lost',r,{once:true}));
      load=async()=>loads++;pid='original';api=async(url,opt)=>{if(url==='/api/jobs/other-context'){reads++;if(reads===1)throw Error('Rede indisponível');return {id:'other-context',state:'done',project:'original',kind:'analyze',message:'Concluído'}}return before.api(url,opt)};
      try{const work=poll('other-context');await lost;pid='new-project';projectSession.context++;poll('other-context');await work;return {loads,pid,task}}
      finally{api=before.api;load=before.load;pid=before.pid;projectSession.context=before.context}
    }''')
    assert result==dict(loads=0,pid='new-project',task='')


def test_permission_error_preserves_lock_and_can_resume_after_access_is_restored(page):
    result=page.evaluate('''async()=>{
      const previous=api;let allowed=false,message='';
      api=async(url,opt)=>{if(url==='/api/jobs/permission'){if(!allowed){const e=Error('Acesso negado');e.status=403;throw e}return {id:'permission',state:'done',project:'other',kind:'analyze',message:'Concluído'}}return previous(url,opt)};
      try{try{await poll('permission')}catch(e){message=e.message}const locked=task==='permission'&&!$('rsResumeTracking').hidden;allowed=true;await poll('permission');return {locked,task,message}}
      finally{api=previous}
    }''')
    assert result['locked'] and result['task']=='' and '(403)' in result['message']


def test_reconnect_notice_keeps_one_footer_and_existing_view(page):
    seed(page)
    page.evaluate('''()=>{
      window.trackingPreviousApi=api;window.trackingLost=new Promise(r=>addEventListener('rodovia:tracking-lost',r,{once:true}));
      api=async(url,opt)=>{if(url==='/api/jobs/notice')throw Error('Rede indisponível');return trackingPreviousApi(url,opt)};
      window.trackingNoticeWork=poll('notice');
    }''')
    page.evaluate('trackingLost')
    assert page.locator('#rsResumeTracking').is_visible()
    assert page.evaluate("!!baseImage&&task==='notice'")
    assert 'Reconectando' in page.locator('#message').text_content()
    screenshot(page,'acompanhamento_reconectando')
    page.evaluate("api=async(url,opt)=>url==='/api/jobs/notice'?{id:'notice',state:'done',project:'other',kind:'analyze',message:'Concluído'}:trackingPreviousApi(url,opt)")
    page.get_by_role('button',name='Retomar acompanhamento',exact=True).click()
    page.evaluate('async()=>{await trackingNoticeWork;api=trackingPreviousApi}')


def test_real_server_calculation_survives_status_connection_drop(gl_page,live):
    p=gl_page;posts=[];drops=[]
    p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    def status_route(route):
        if route.request.method=='GET' and not drops:
            drops.append(route.request.url);route.abort('connectionreset')
        else:route.continue_()
    p.route('**/api/jobs/*',status_route)
    p.on('request',lambda r:posts.append(r.url) if r.method=='POST' and r.url.endswith('/analyze') else None)
    result=p.evaluate("async()=>{const a=start('analyze'),b=start('analyze');const [x,y]=await Promise.all([a,b]);return {same:a===b,first:x.id,second:y.id,state:x.state,task,project:pid,segments:editor.segments.length}}")
    assert result['same'] and result['first']==result['second'] and result['state']=='done'
    assert result['task']=='' and result['project']==live[1] and result['segments']>0
    assert len(posts)==1 and len(drops)==1
    screenshot(p,'acompanhamento_servidor_recuperado')


def test_queue_waits_until_recovered_results_have_finished_loading(page):
    seed(page)
    result=page.evaluate('''async()=>{
      const before={api,load};let release,posts=0,started;pid='loading-result';savePending=false;
      const loading=new Promise(r=>started=r);load=async()=>{started();await new Promise(r=>release=r)};
      api=async(url,opt)=>{if(opt?.method==='POST'){posts++;throw Error('Não deve iniciar durante a aplicação do resultado')}return {id:'loading-job',state:'done',project:pid,kind:'analyze',message:'Concluído'}};
      try{const work=poll('loading-job');await loading;const request=start('analyze');await new Promise(r=>setTimeout(r,250));const during=posts;RodoviaUpdates.clearQueue();release();await work;const value=await request;return {during,posts,value,task}}
      finally{api=before.api;load=before.load}
    }''')
    assert result==dict(during=0,posts=0,value=False,task='')
