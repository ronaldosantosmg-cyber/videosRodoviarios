from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def test_menu_unique_and_nodes_group(gl_page):
    p=gl_page;p.get_by_role('menuitem',name='Editar',exact=True).click()
    assert p.get_by_role('menuitem',name='Mover',exact=True).count()==1
    assert p.get_by_role('menuitem',name='Seleção e propriedades',exact=True).is_visible()
    p.keyboard.press('Escape');p.get_by_role('menuitem',name='Tráfego',exact=True).click()
    for n in ['Sentidos e nós','Testar circulação','Central de correção dos fluxos','Nós e edição de trechos']:assert p.get_by_role('menuitem',name=n,exact=True).is_visible()
    p.get_by_role('menuitem',name='Nós e edição de trechos',exact=True).hover();assert p.get_by_role('menuitem',name='Apagar nó',exact=True).is_visible()
    p.keyboard.press('Escape');p.keyboard.press('Escape')


def test_central_disabled_flow_and_small_screen_close(gl_page):
    p=gl_page;p.set_viewport_size(dict(width=760,height=620))
    p.route('**/assistencia/execucao',lambda r:r.fulfill(json={'signature':'test','segments':[dict(id=0,source='Eixo teste',technical_status='problem',technical_message='Curva a conferir',disabled=True,technical_assistant={'title':'Conferir eixo','steps':[{'instruction':'Revisar vértices'}]})]}))
    p.evaluate('RodoviaFlowRepair.open()');d=p.locator('#rsFlowCenter');d.wait_for()
    assert d.get_by_text('Revisar vértices',exact=True).is_visible()
    assert d.get_by_role('button',name='Analisar e propor correção').is_disabled()
    assert d.locator('footer button').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight')
    screenshot(p,'14237_central_compacta');d.get_by_role('button',name='Fechar',exact=True).click();assert d.count()==0
    p.unroute('**/assistencia/execucao')


def test_failed_proposal_releases_button_without_changing_model(gl_page):
    p=gl_page;p.route('**/assistencia/execucao',lambda r:r.fulfill(json={'signature':'test','segments':[dict(id=0,source='Eixo',technical_status='problem',technical_message='Conferir geometria',disabled=False)]}))
    p.evaluate('RodoviaFlowRepair.open()');d=p.locator('#rsFlowCenter');d.wait_for()
    p.evaluate("()=>{window.before37=JSON.stringify(M);window.oldStart37=start;start=async()=>{throw Error('Falha controlada de proposta')}}")
    try:
        b=d.get_by_role('button',name='Analisar e propor correção');b.click();p.wait_for_function("!document.querySelector('#rsFlowCenter').dataset.pending")
        assert b.is_enabled() and d.is_visible() and p.evaluate('JSON.stringify(M)===before37')
        d.get_by_role('button',name='Fechar',exact=True).click()
    finally:p.evaluate('()=>{start=oldStart37}');p.unroute('**/assistencia/execucao')


def test_cancel_keeps_draft_until_explicit_discard(gl_page):
    p=gl_page;p.evaluate("RodoviaModelDialog.open({id:'confirm37',title:'Edição',html:'<input name=check value=Original>',save:async()=>true})")
    d=p.locator('#confirm37');d.locator('input').fill('Editado');d.get_by_role('button',name='Cancelar',exact=True).click()
    p.get_by_role('button',name='Continuar editando',exact=True).click();assert d.locator('input').input_value()=='Editado'
    d.get_by_role('button',name='Cancelar',exact=True).click();p.get_by_role('button',name='Descartar',exact=True).click();assert d.count()==0


def test_committed_plan_cannot_be_submitted_again_after_refresh_failure(gl_page):
    p=gl_page
    p.route('**/assistencia/execucao',lambda r:r.fulfill(json={'signature':'test','segments':[dict(id=0,source='Eixo',technical_status='problem',technical_message='Conferir',disabled=False)]}))
    p.route('**/assistencia/execucao/proposta',lambda r:r.fulfill(json=dict(id='test-plan',action='recover',before={'message':'Antes','geometry':[[0,0],[1,1]]},after=[{'message':'Depois'}],geometry=[[[0,0],[1,1]]],notice='Proposta de teste',can_apply=True)))
    p.route('**/assistencia/execucao/test-plan/aplicar',lambda r:r.fulfill(json={'ok':True}))
    p.evaluate('RodoviaExecution.open()')
    p.evaluate("()=>{window.start37=start;window.load37=load;start=async()=>({state:'done'});load=async()=>{throw Error('Falha de leitura após aplicação')}}")
    try:
        d=p.locator('#rsFlowCenter');d.get_by_role('button',name='Analisar e propor correção').click()
        b=d.get_by_role('button',name='Confirmar e aplicar correção');b.wait_for();b.click()
        p.wait_for_function("!document.querySelector('#rsFlowCenter').dataset.pending")
        assert b.is_disabled() and b.get_attribute('data-applied')=='true'
        d.get_by_role('button',name='Fechar',exact=True).click()
    finally:p.evaluate('()=>{start=start37;load=load37}')


def test_save_and_close_confirms_once_and_removes_dialog(gl_page):
    p=gl_page;p.evaluate("()=>{window.saved37=0;RodoviaModelDialog.open({id:'save37',title:'Confirmar edição',html:'<input value=Original>',save:async()=>{saved37++;return true}})}")
    d=p.locator('#save37');d.locator('input').fill('Confirmado');d.get_by_role('button',name='Salvar e fechar',exact=True).click()
    assert d.count()==0 and p.evaluate('saved37')==1


def test_receiving_results_preserves_selection_without_opening_properties(gl_page,live):
    p=gl_page
    p.evaluate("async id=>{await RodoviaPanels.close();selSeg={id:editor.segments[0].id};await load(id,{resultsOnly:true})}",live[1])
    p.set_viewport_size(dict(width=1200,height=700));p.wait_for_timeout(400)
    assert p.evaluate('selSeg!==null')
    assert not p.evaluate('!!RodoviaPanels.opened')
    assert not p.locator('#rsPanelPopup').is_visible()
