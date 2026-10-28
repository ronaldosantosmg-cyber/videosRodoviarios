from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def test_shared_decision_is_single_and_escape_preserves_draft(gl_page):
    p=gl_page;p.evaluate("()=>{window.ownerDraft=document.createElement('dialog');ownerDraft.innerHTML='<input value=Rascunho>';document.body.append(ownerDraft);ownerDraft.showModal();window.resultDraft=null;const a=RodoviaDialogDecision.ask(ownerDraft);const b=RodoviaDialogDecision.ask(ownerDraft);window.sameDraft=a===b;a.then(v=>resultDraft=v)}")
    assert p.locator('.rsDraftDecision').count()==1 and p.evaluate('sameDraft')
    p.keyboard.press('Escape');assert p.evaluate('resultDraft')=='continue'
    assert p.evaluate('ownerDraft.querySelector("input").value')=='Rascunho'
    p.evaluate('()=>{ownerDraft.close();ownerDraft.remove()}')


def test_failed_save_keeps_question_and_retry_finishes_once(gl_page):
    p=gl_page;p.evaluate("()=>{window.ownerDraft=document.createElement('dialog');document.body.append(ownerDraft);ownerDraft.showModal();window.attemptDraft=0;window.resultDraft=null;RodoviaDialogDecision.ask(ownerDraft,{save:async()=>{if(++attemptDraft===1)throw Error('Falha controlada');return true}}).then(v=>resultDraft=v)}")
    q=p.locator('.rsDraftDecision');q.get_by_role('button',name='Salvar e fechar',exact=True).click()
    assert q.get_by_role('alert').inner_text()=='Falha controlada'
    assert q.get_by_role('button',name='Salvar e fechar').is_enabled()
    q.get_by_role('button',name='Salvar e fechar').click();assert p.evaluate('resultDraft')=='save' and p.evaluate('attemptDraft')==2
    p.evaluate('()=>{ownerDraft.close();ownerDraft.remove()}')


def test_catalog_close_saves_profile_without_applying_to_project(gl_page,live):
    p=gl_page;before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    writes=[];p.on('request',lambda r:writes.append(r.url) if r.method=='POST' and (r.url.endswith('/refresh') or r.url.endswith('/scene3d')) else None)
    p.evaluate("RodoviaUpdatePolicy.setMode('automatic')")
    p.evaluate('RodoviaAssetCatalog.open()');d=p.locator('#rsAssetCatalog');d.wait_for()
    p.locator('#rsAssetProfile').fill('Perfil de fechamento do catálogo');p.locator('#rsAssetPattern').fill('*EDIFICACAO_TESTE*')
    d.get_by_role('button',name='Fechar',exact=True).click();p.get_by_role('button',name='Continuar editando',exact=True).click()
    assert p.locator('#rsAssetPattern').input_value()=='*EDIFICACAO_TESTE*'
    d.get_by_role('button',name='Fechar',exact=True).click();p.get_by_role('button',name='Salvar perfil e fechar',exact=True).click();d.wait_for(state='detached')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    assert any(r['name']=='Perfil de fechamento do catálogo' for r in p.request.get(live[0]+'/api/layer_profiles').json()['profiles'])
    p.wait_for_timeout(500);assert not writes
    assert not p.evaluate('RodoviaUpdatePolicy.snapshot().waiting')
    p.evaluate("RodoviaUpdatePolicy.setMode('manual')")


def test_ai_profile_has_save_discard_continue_and_no_implicit_application(gl_page,live):
    p=gl_page;before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];p.evaluate("RodoviaIA.open('layers')")
    d=p.locator('#rsIAStudio');d.locator('#rsIAStatus').filter(has_text='Análise local pronta').wait_for()
    d.get_by_text('Perfis reutilizáveis',exact=True).click();d.locator('#rsIAProfileName').fill('Perfil do assistente ao fechar')
    d.locator('footer [data-close]').click();p.get_by_role('button',name='Continuar editando',exact=True).click()
    assert d.locator('#rsIAProfileName').input_value()=='Perfil do assistente ao fechar'
    d.locator('footer [data-close]').click();p.get_by_role('button',name='Salvar perfil e fechar',exact=True).click();d.wait_for(state='detached')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    assert any(r['name']=='Perfil do assistente ao fechar' for r in p.request.get(live[0]+'/api/assistencia/perfis').json()['profiles'])


def test_online_connection_discard_does_not_send_key(gl_page):
    p=gl_page;writes=[];p.on('request',lambda r:writes.append(r.url) if r.method=='POST' and r.url.endswith('/assistencia/conexao') else None)
    p.evaluate('RodoviaSmallAI.connect()');d=p.get_by_role('dialog',name='Conectar API online',exact=True)
    d.get_by_label('Chave da API',exact=True).fill('sk-test-SOMENTE-RASCUNHO-123456')
    d.get_by_role('button',name='Fechar',exact=True).click();p.get_by_role('button',name='Continuar editando',exact=True).click()
    assert d.get_by_label('Chave da API',exact=True).input_value().startswith('sk-test-')
    d.get_by_role('button',name='Fechar',exact=True).click();p.get_by_role('button',name='Descartar',exact=True).click();d.wait_for(state='detached')
    assert not writes


def test_decision_actions_fit_small_window(gl_page):
    p=gl_page;p.set_viewport_size(dict(width=760,height=480));p.evaluate("()=>{window.ownerDraft=document.createElement('dialog');document.body.append(ownerDraft);ownerDraft.showModal();RodoviaDialogDecision.ask(ownerDraft,{message:'Um rascunho permanece aberto até salvar ou descartar.',save:async()=>true})}")
    q=p.locator('.rsDraftDecision');assert q.get_by_role('button',name='Salvar e fechar').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight')
    screenshot(p,'formularios_decisao_compacta');q.get_by_role('button',name='Descartar',exact=True).click();p.evaluate('()=>{ownerDraft.close();ownerDraft.remove()}')
