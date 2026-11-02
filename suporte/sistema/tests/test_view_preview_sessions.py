from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def open_view(p):
    p.evaluate("openSection('Vista, prévia e sessões')");p.locator('#rsPanelPopup').wait_for(state='visible')


def test_view_groups_keep_original_controls_and_open_without_calculations(gl_page):
    p=gl_page;p.set_viewport_size(dict(width=760,height=620));writes=[]
    p.on('request',lambda r:writes.append(r.url) if r.method=='POST' and r.url.endswith(('/preview','/refresh','/analyze','/scene3d')) else None)
    open_view(p);d=p.locator('#rsPanelPopup')
    for name in ['Navegação e enquadramento','Prévia e instante','Fundo e camadas da edição','Sessões de trabalho']:assert d.get_by_role('group',name=name,exact=True).is_visible()
    for identity in ['preview','preview_mode','fitView','tileAlpha','vecAlpha','sessList','sessSave','sessLoad','sessDel']:assert d.locator('#'+identity).count()==1 and d.locator('#'+identity).is_visible()
    assert d.locator('#regenPreview').is_hidden() and d.locator('#updFlows').is_hidden()
    d.get_by_text('Avançado: regeneração e fluxos',exact=True).click()
    assert d.locator('#regenPreview').is_visible() and d.locator('#updFlows').is_visible()
    d.get_by_text('Avançado: regeneração e fluxos',exact=True).click()
    assert p.locator('#bottomBar').bounding_box()['height']<=32
    assert not writes
    screenshot(p,'vista_previa_sessoes_760');p.locator('#rsPanelCancel').click();assert d.is_hidden()


def test_discard_restores_background_opacity_and_stored_preferences(gl_page,live):
    p=gl_page;before=p.evaluate('()=>({mode:baseMode,image:tileAlpha,vector:vecAlpha})');config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];open_view(p)
    p.locator('#baseMode').select_option('none')
    p.locator('#tileAlpha').evaluate("e=>{e.value='0.35';e.dispatchEvent(new Event('input',{bubbles:true}))}")
    p.locator('#vecAlpha').evaluate("e=>{e.value='0.4';e.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert p.evaluate('RodoviaPanels.pending')
    p.locator('#rsPanelDiscard').click();assert p.locator('#rsPanelPopup').is_hidden()
    assert p.evaluate('()=>({mode:baseMode,image:tileAlpha,vector:vecAlpha})')==before
    persisted=p.evaluate("JSON.parse(localStorage.getItem('rodovia_base'))")
    assert persisted['mode']==before['mode'] and persisted['ta']==before['image'] and persisted['va']==before['vector']
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==config


def test_sessions_save_restore_and_child_escape_do_not_dirty_project(gl_page,live):
    p=gl_page;config=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    p.evaluate("saveSession('Sessão base')");open_view(p);p.locator('#sessList').select_option('Sessão base');assert not p.evaluate('RodoviaPanels.pending')
    p.locator('#sessSave').click();p.locator('#inputValue').fill('Vista do rio');p.locator('#inputOk').click()
    p.wait_for_function("$('sessList').value==='Vista do rio'")
    assert not p.evaluate('RodoviaPanels.pending')
    p.locator('#sessSave').click();p.locator('#inputDlg').wait_for(state='visible');p.keyboard.press('Escape')
    assert p.locator('#inputDlg').is_hidden() and p.locator('#rsPanelPopup').is_visible()
    p.locator('#sessLoad').click();p.wait_for_function("$('message').textContent.includes('restaurada')")
    assert p.locator('#rsPanelPopup').is_hidden()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==config


def test_switching_classic_layout_preserves_control_identity(gl_page):
    p=gl_page;p.evaluate("()=>{window.previewBeforeVista=$('preview');window.handlerBeforeVista=$('preview').onclick;pnColunaClassica(true)}")
    assert p.locator('#preview').count()==1 and p.evaluate("$('preview')===previewBeforeVista&&$('preview').isConnected")
    p.evaluate('pnColunaClassica(false)');open_view(p)
    assert p.locator('#rsVistaPreview').count()==1 and p.evaluate("$('preview')===previewBeforeVista&&$('preview').onclick===handlerBeforeVista")
    screenshot(p,'vista_previa_sessoes_restaurada');p.locator('#rsPanelCancel').click()


def test_old_session_listing_is_discarded_after_context_changes(gl_page):
    p=gl_page;result=p.evaluate("""async()=>{const previous=api,context=projectSession.context,before=$('sessList').innerHTML;let release;api=(url,...args)=>url.endsWith('/sessoes')?new Promise(resolve=>release=resolve):previous(url,...args);try{const work=sessionsUi();projectSession.context++;release({sessions:[{name:'Sessão de outro contexto',state:{},saved:'agora'}]});await work;return {same:$('sessList').innerHTML===before,oldVisible:$('sessList').textContent.includes('outro contexto')}}finally{api=previous;projectSession.context=context}}""")
    assert result==dict(same=True,oldVisible=False)
