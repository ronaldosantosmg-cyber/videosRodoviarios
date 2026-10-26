import json
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_edit_during_save_remains_dirty_then_queued_save_wins(gl_page,live):
    p=gl_page;routes=[];url=live[0]+'/api/projects/'+live[1]+'/config'
    p.route(url,lambda r:routes.append(r))
    p.evaluate("()=>{$('name').value='Primeira gravação';projectSession.epoch++;savePending=true;window.firstSave=save();}")
    p.wait_for_timeout(150);assert len(routes)==1
    response=routes[0].fetch();assert response.ok
    p.evaluate("()=>{$('origin').value='Edição enquanto grava';projectSession.epoch++;savePending=true;window.secondSave=save();}")
    routes[0].fulfill(response=response);p.wait_for_timeout(150)
    assert p.evaluate('savePending')
    assert len(routes)==2
    second=routes[1].fetch();assert second.ok;routes[1].fulfill(response=second)
    p.evaluate('()=>Promise.all([firstSave,secondSave])')
    assert not p.evaluate('savePending')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['origin']=='Edição enquanto grava'
    screenshot(p,'1427_01_gravacao_serializada')


def test_conflict_keeps_local_edits_and_undo_history(gl_page,live):
    p=gl_page;url=live[0]+'/api/projects/'+live[1];current=p.request.get(url).json();remote={**current['config'],'name':'Outra janela'}
    assert p.request.put(url+'/config',data=remote,headers={'If-Match':current['config_revision']}).ok
    result=p.evaluate("async()=>{checkpoint();const before=undoStack.length;$('name').value='Nome local concorrente';cfg.destination='Destino local preservado';projectSession.epoch++;savePending=true;try{await save();return null}catch(e){return {message:e.message,dirty:savePending,undo:undoStack.length===before,destination:cfg.destination}}}")
    assert 'outra janela' in result['message'] and result['dirty'] and result['undo']
    assert result['destination']=='Destino local preservado'
    screenshot(p,'1427_02_conflito_preserva_edicao')
    # A nova janela de teste começa com a configuração atual, sem o estado local deliberadamente conflitante.
    p.evaluate('savePending=false')


def test_background_results_preserve_draft_selection_undo_and_pending_edit(gl_page,live):
    p=gl_page
    before=p.evaluate("()=>{checkpoint();M.pois.push({id:'local',title:'Intervenção pendente',kind:'obra',x:100,y:0});sel={key:'pois',i:M.pois.length-1};draft={type:'flowadd',pts:[{x:1,y:2}]};savePending=true;return {marks:JSON.stringify(M),undo:JSON.stringify(undoStack),selection:JSON.stringify(sel),draft:JSON.stringify(draft)}}")
    p.evaluate('(id)=>load(id,{resultsOnly:true})',live[1])
    after=p.evaluate('()=>({marks:JSON.stringify(M),undo:JSON.stringify(undoStack),selection:JSON.stringify(sel),draft:JSON.stringify(draft)})')
    assert before==after and p.evaluate('savePending')
    screenshot(p,'1427_03_resultados_preservam_historico')
    p.evaluate('savePending=false')


def test_out_of_order_open_does_not_replace_the_latest_project(gl_page,live):
    p=gl_page;data=p.request.get(live[0]+'/api/projects/'+live[1]).json();routes={};a='a'*32;b='b'*32
    def payload(key):return {**data,'id':key,'config':{**data['config'],'name':key},'analysis':None,'preview':None,'editor_ready':False}
    def intercept(r):
        key=r.request.url.rsplit('/',1)[-1]
        if key in routes:r.fulfill(json=payload(key))
        else:routes[key]=r
    for key in (a,b):p.route('**/api/projects/'+key,intercept)
    p.evaluate('(id)=>{window.openFirst=load(id)}',a);p.wait_for_timeout(100)
    p.evaluate('(id)=>{window.openSecond=load(id)}',b);p.wait_for_timeout(100)
    def payload(key):return {**data,'id':key,'config':{**data['config'],'name':key},'analysis':None,'preview':None,'editor_ready':False}
    routes[b].fulfill(json=payload(b));p.evaluate('()=>openSecond')
    routes[a].fulfill(json=payload(a));p.evaluate('()=>openFirst')
    assert p.evaluate('pid')==b and p.evaluate('cfg.name')==b
    screenshot(p,'1427_04_abertura_fora_de_ordem')


def test_finished_job_for_another_project_does_not_switch_project(gl_page):
    p=gl_page;before=p.evaluate('pid')
    p.route('**/api/jobs/finished-other',lambda r:r.fulfill(json={'project':'a'*32,'kind':'analyze','state':'done','message':'Concluído','progress':1}))
    p.evaluate("()=>poll('finished-other')")
    assert p.evaluate('pid')==before


def test_history_dialog_restores_an_explicit_revision(gl_page,live):
    p=gl_page;before=p.request.get(live[0]+'/api/projects/'+live[1]).json()
    p.evaluate("async()=>{$('name').value='Gravação a recuperar';await save();await openProjectHistory()}")
    p.locator('#rsHistoryRevision').select_option(before['config_revision'])
    screenshot(p,'1427_05_historico_recuperacao')
    p.locator('#rsHistoryRestore').click();p.wait_for_function('!document.querySelector("#rsProjectHistory").open')
    p.wait_for_function('(name)=>cfg.name===name',arg=before['config']['name'])
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']==before['config']['name']



def test_edit_while_background_response_waits_preserves_the_latest_history(gl_page,live):
    p=gl_page;held=[];url=live[0]+'/api/projects/'+live[1]
    p.route(url,lambda r:held.append(r))
    p.evaluate('(id)=>{window.backgroundLoad=load(id,{resultsOnly:true})}',live[1]);p.wait_for_timeout(100)
    assert held
    response=held[0].fetch()
    before=p.evaluate("()=>{checkpoint();M.pois.push({id:'during',title:'Durante o processamento',kind:'obra',x:250,y:0});checkpoint();savePending=true;return {marks:JSON.stringify(M),undo:JSON.stringify(undoStack)}}")
    p.unroute(url);held[0].fulfill(response=response);p.evaluate('()=>backgroundLoad')
    assert p.evaluate('()=>({marks:JSON.stringify(M),undo:JSON.stringify(undoStack)})')==before
    assert p.evaluate('savePending');p.evaluate('savePending=false')



def test_open_does_not_discard_edits_made_while_waiting_for_the_project(gl_page,live):
    p=gl_page;data=p.request.get(live[0]+'/api/projects/'+live[1]).json();held=[];other='c'*32
    p.route('**/api/projects/'+other,lambda r:held.append(r))
    p.evaluate('(id)=>{window.pendingOpen=load(id).catch(e=>e.message)}',other);p.wait_for_timeout(100)
    p.evaluate("()=>{$('destination').value='Editado durante abertura';checkpoint();savePending=true}")
    held[0].fulfill(json={**data,'id':other})
    message=p.evaluate('()=>pendingOpen')
    assert 'novas alterações' in message
    assert p.evaluate('pid')==live[1] and p.evaluate('savePending')
    assert p.locator('#destination').input_value()=='Editado durante abertura'
    assert p.evaluate('undoStack.length')>0
    p.evaluate('savePending=false')



def test_video_finished_for_an_older_revision_is_labelled_as_previous(gl_page,live):
    p=gl_page;url=live[0]+'/api/projects/'+live[1];data=p.request.get(url).json()
    data['artifacts']['video']={'state':'stale','revision':'previous'}
    data['render_info']={'encoder':'H.264','total_seconds':1}
    p.route(url,lambda r:r.fulfill(json=data))
    p.route('**/api/jobs/previous-video',lambda r:r.fulfill(json={'project':live[1],'kind':'render','state':'done','message':'Concluído','progress':1}))
    p.evaluate("()=>poll('previous-video')")
    assert 'configuração anterior' in p.locator('#message').inner_text()
    assert p.locator('#message').is_visible()
    screenshot(p,'1427_06_video_de_revisao_anterior')
