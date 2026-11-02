from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def test_expansion_preserves_shortcuts_icons_and_fits_viewport(gl_page):
    p=gl_page;p.set_viewport_size(dict(width=1024,height=720));p.get_by_role('tab',name='Projeto',exact=True).click()
    panel=p.locator('[data-activity="Projeto"]');panel.get_by_text('Parâmetros de apresentação',exact=True).click();p.wait_for_timeout(150)
    assert panel.get_by_role('button',name='Arquivos do projeto',exact=True).is_visible()
    assert panel.locator('details[open]').bounding_box()['width']>panel.bounding_box()['width']*.9
    assert abs(panel.get_by_role('button',name='Proteção de dados',exact=True).bounding_box()['y']-panel.get_by_role('button',name='Arquivos do projeto',exact=True).bounding_box()['y'])<3
    for identity in ['rsRepairFlows','rsCalculationGuide','rsPresentationImages']:
        b=p.locator('#'+identity);assert b.is_visible() and b.locator('svg').is_visible()
        assert b.evaluate('e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth}')
    screenshot(p,'expansao_parametros_1024')
    p.get_by_role('tab',name='Tráfego',exact=True).click();panel=p.locator('[data-activity="Tráfego"]');panel.get_by_text('Mais ferramentas',exact=True).click();p.wait_for_timeout(100)
    assert panel.get_by_role('button',name='Corrigir problemas',exact=True).is_visible()
    assert panel.locator('[data-rs-tool=flowcut] svg').is_visible()
    assert panel.locator('details[open]').bounding_box()['width']>panel.bounding_box()['width']*.9
    assert p.locator('#logs').evaluate('e=>{const r=e.getBoundingClientRect();return r.right<=innerWidth&&r.bottom<=innerHeight}')
    screenshot(p,'expansao_trafego_1024')


def test_legend_uses_same_colors_as_render_and_marks_previous_results(gl_page):
    p=gl_page;result=p.evaluate("""()=>{window.editorBeforeLegend=editor;editor={...editor,segments:[{technical_status:'ok'},{technical_status:'problem'},{technical_status:'adjustment'},{disabled:true},{technical_exclusion:'length_limit'}]};RodoviaFlowStudy.stale=false;vecOn.flows=true;RodoviaContextualUI.sync();return [...document.querySelectorAll('[data-flow-status]')].map(e=>({status:e.dataset.flowStatus,text:e.textContent,color:e.querySelector('span').style.color}))}""")
    assert [r['status'] for r in result]==['ok','problem','adjustment','off']
    assert [r['color'] for r in result]==['rgb(34, 197, 94)','rgb(239, 68, 68)','rgb(234, 179, 8)','rgb(148, 163, 184)']
    assert result[-1]['text'].endswith('2')
    p.evaluate('RodoviaFlowStudy.stale=true;RodoviaContextualUI.sync()');assert 'Resultado anterior' in p.locator('#rsFlowLegend').inner_text()
    assert 'Trajeto válido 0' in p.locator('#rsFlowLegend').inner_text()
    p.evaluate('editor=editorBeforeLegend;RodoviaFlowStudy.stale=false;RodoviaContextualUI.sync()')


def test_progress_unknown_stage_is_indeterminate_and_time_is_labeled(gl_page):
    p=gl_page;p.evaluate("window.dispatchEvent(new CustomEvent('rodovia:job',{detail:{id:'progress-test',kind:'convert_imagery',progress:.87,message:'Gerando visões reduzidas · percentual indisponível nesta etapa',state:'running'}}))")
    assert p.locator('#progress').get_attribute('value') is None
    assert p.locator('#pcPct').inner_text()==''
    assert p.locator('#pcTempo').inner_text().startswith('Decorrido ')
    screenshot(p,'progresso_indeterminado')
    p.evaluate("window.dispatchEvent(new CustomEvent('rodovia:job',{detail:{id:'progress-test',kind:'convert_imagery',progress:1,message:'Conferindo arquivo',state:'running'}}))")
    assert p.locator('#pcPct').inner_text()=='99%'
    p.evaluate("window.dispatchEvent(new CustomEvent('rodovia:job',{detail:{id:'progress-test',kind:'convert_imagery',progress:1,message:'Concluído',state:'done'}}))")
    assert p.locator('#pcPct').inner_text()=='Concluído'


def test_stale_artifact_cannot_show_green_even_if_local_flag_is_false(gl_page):
    p=gl_page;result=p.evaluate("""()=>{const prior=projectSession.artifacts.editor,stale=RodoviaFlowStudy.stale;try{RodoviaFlowStudy.stale=false;projectSession.artifacts.editor={state:'stale'};RodoviaContextualUI.sync();return {status:flowStudyStatus({technical_status:'ok'}),off:flowStudyStatus({disabled:true}),note:$('rsFlowLegend').textContent}}finally{projectSession.artifacts.editor=prior;RodoviaFlowStudy.stale=stale;RodoviaContextualUI.sync()}}""")
    assert result['status']=='adjustment' and result['off']=='off' and 'Resultado anterior' in result['note']


def test_progress_remains_single_line_without_reducing_graphical_area(gl_page):
    p=gl_page
    for width in [1440,1024,760]:
        p.set_viewport_size(dict(width=width,height=720));p.wait_for_timeout(150)
        height=p.locator('#canvas').bounding_box()['height']
        p.evaluate("window.dispatchEvent(new CustomEvent('rodovia:job',{detail:{id:'single-row',kind:'convert_imagery',progress:.87,message:'Gerando visões reduzidas · percentual indisponível nesta etapa',state:'running'}}))")
        p.wait_for_timeout(100)
        assert p.locator('#bottomBar').bounding_box()['height']<=32
        assert abs(p.locator('#canvas').bounding_box()['height']-height)<2
        assert abs(p.locator('#pcCancel').bounding_box()['y']-p.locator('#rsUpdateProject').bounding_box()['y'])<4
        assert p.locator('#pcCancel').evaluate('e=>e.getBoundingClientRect().right<=innerWidth')
        p.evaluate("window.dispatchEvent(new CustomEvent('rodovia:job',{detail:{id:'single-row',kind:'convert_imagery',progress:1,message:'Concluído',state:'done'}}))")
    screenshot(p,'rodape_linha_unica_760')
