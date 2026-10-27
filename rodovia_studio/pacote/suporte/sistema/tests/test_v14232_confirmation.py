import json
import pytest
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def visible_actions(p,root,ids):
    for identity in ids:
        b=p.locator('#'+identity);assert b.is_visible()
        assert b.evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth}')
        assert b.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}')


@pytest.mark.parametrize('size',[(1366,620),(760,480)])
def test_video_smoke_and_density_have_visible_commit_and_direct_discard(gl_page,live,size):
    p=gl_page;p.set_viewport_size(dict(width=size[0],height=size[1]));p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    p.evaluate("psOpenHub('video')");p.get_by_role('tab',name='Veículos e fluxo',exact=True).click()
    p.locator('#traffic_density').fill('3.2');p.locator('#traffic_density').dispatch_event('change')
    # Fumaça está dentro das opções de apresentação dos agentes; localiza sua aba real.
    p.evaluate("()=>{const e=$('rail_smoke');const pane=e.closest('.rsVideoPane');if(pane)document.querySelector('[aria-controls='+pane.id+']').click();for(let a=e.parentElement;a&&a.id!=='rsPanelBody';a=a.parentElement)if(a.tagName==='DETAILS')a.open=true}")
    p.locator('#rail_smoke').set_checked(not before['rail_smoke'])
    p.locator('#rsPanelBody').evaluate('e=>e.scrollTop=e.scrollHeight')
    visible_actions(p,'rsPanelPopup',['rsPanelCancel','rsPanelDiscard','rsPanelSave'])
    screenshot(p,'14232_confirmacao_video_'+str(size[0]))
    p.locator('#rsPanelDiscard').click();assert p.locator('#rsPanelPopup').is_hidden()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    assert p.evaluate('cfg.rail_smoke')==before['rail_smoke']


def open_layers(p):
    p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    p.evaluate('openLayerManager()');p.locator('#layerDlg').wait_for(state='visible')


def test_layer_changes_are_draft_then_saved_or_discarded_without_losing_previous_data(gl_page,live):
    p=gl_page;p.set_viewport_size(dict(width=760,height=480))
    before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];open_layers(p)
    row=p.locator('#lmRows tr[data-lmn]').first;name=row.get_attribute('data-lmn')
    visible=row.locator('[data-lmv]');original=visible.is_checked();visible.set_checked(not original)
    p.wait_for_timeout(1100)
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    visible_actions(p,'layerDlg',['lmClose','lmDiscard','lmSave']);screenshot(p,'14232_confirmacao_camadas')
    p.locator('#lmDiscard').click();assert p.locator('#layerDlg').is_hidden()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    assert p.evaluate('cfg.hidden_layers')==before['hidden_layers']
    open_layers(p);p.locator('#lmRows tr').filter(has=p.locator('[data-lmv]')).first.locator('[data-lmv]').set_checked(not original)
    p.locator('#lmSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=30000)
    after=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert (name in after['hidden_layers'])==original
    assert p.locator('#layerDlg').is_hidden() and not p.locator('#lmSave').is_disabled()
    # Restaura a camada do próprio ensaio antes de recarregar a fixture compartilhada.
    open_layers(p);p.locator('#lmRows [data-lmv]').first.set_checked(original);p.locator('#lmSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=30000)


def test_layer_filters_do_not_create_pending_edits_and_escape_confirms_real_edits(gl_page):
    p=gl_page;open_layers(p)
    p.locator('#lmSearch').fill('EIXO');assert not p.evaluate('RodoviaPanels.pending')
    p.locator('#lmClose').click();assert p.locator('#layerDlg').is_hidden() and p.locator('#rsPanelDecision').count()==0
    open_layers(p);p.locator('#lmSearch').fill('');p.locator('#lmRows [data-lmf]').first.check()
    p.keyboard.press('Escape');p.locator('#rsPanelDecision').wait_for(state='visible')
    p.locator('[data-choice=continue]').click();assert p.locator('#layerDlg').is_visible()
    assert p.locator('#layerDlg .dlgX').count()==0
    p.locator('#layerDlg .rsCommitHeader button').click();p.locator('#rsPanelDecision').wait_for(state='visible')
    p.locator('[data-choice=discard]').click();assert p.locator('#layerDlg').is_hidden()


def test_layer_failed_save_keeps_draft_buttons_and_server_configuration(gl_page,live):
    p=gl_page;before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];open_layers(p)
    p.locator('#lmRows [data-lmf]').first.check()
    pattern='**/api/projects/'+live[1]+'/config'
    p.route(pattern,lambda r:r.fulfill(status=503,json={'detail':'Falha de gravação simulada no ensaio'}))
    p.locator('#lmSave').click()
    p.wait_for_function("document.querySelector('#layerDlg [data-rs-edit-status]').textContent.includes('Não foi salvo')")
    assert p.locator('#layerDlg').is_visible() and not p.locator('#lmSave').is_disabled()
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']==before
    p.unroute(pattern);p.locator('#lmDiscard').click();assert p.locator('#layerDlg').is_hidden()


def test_confirmation_footer_is_available_in_project_materials_and_configuration(gl_page):
    p=gl_page;p.set_viewport_size(dict(width=1024,height=540));p.wait_for_function('!task&&!taskRequestPending',timeout=90000)
    for expression in ["psOpenHub('project')","openSection('Configuração')","RodoviaMaterialsHub.open()"]:
        p.evaluate(expression);p.locator('#rsPanelPopup').wait_for(state='visible')
        p.locator('#rsPanelBody').evaluate('e=>e.scrollTop=e.scrollHeight')
        visible_actions(p,'rsPanelPopup',['rsPanelCancel','rsPanelDiscard','rsPanelSave'])
        p.locator('#rsPanelDiscard').click();assert p.locator('#rsPanelPopup').is_hidden()
