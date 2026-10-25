from test_v142_visual import page
from test_v1425_live_3d import live,gl_page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_active_sidebar_follows_each_panel_and_second_click_closes(page):
    for key in ('props','project','layers','video','props'):
        page.locator(f'[data-pshub={key}]').click();page.wait_for_timeout(100)
        assert page.locator('#atividades .psHub.on').count()==1
        assert page.locator(f'[data-pshub={key}]').get_attribute('aria-pressed')=='true'
        page.locator(f'[data-pshub={key}]').click();page.wait_for_timeout(100)
        assert page.locator('#atividades .psHub.on').count()==0
    screenshot(page,'1428_01_barra_lateral')


def test_flow_selection_opens_properties_after_other_object_selection(page):
    seed(page)
    page.evaluate("sel={key:'pavement_areas',i:0};selSet=[sel];showProps();recolherDock(true)")
    page.locator('#rsToolPanel0 [data-rs-command=EDITARFLUXOS]').click()
    assert page.evaluate('sel===null && selSet.length===0 && RodoviaFlowStudy.isEditing()')
    point=page.evaluate('W2C({x:0,y:0})');box=page.locator('#canvas').bounding_box()
    page.mouse.click(box['x']+point[0],box['y']+point[1]);page.wait_for_timeout(150)
    assert page.evaluate('selSeg?.id')==0
    assert page.locator('#propPanel').is_visible()
    assert page.locator('#propPanel [data-seg=reverse]').is_visible()
    assert page.locator('[data-pshub=props]').get_attribute('aria-pressed')=='true'
    screenshot(page,'1428_02_fluxo_selecionado')


def test_more_button_toggles_and_moves_the_highlight(page):
    page.locator('[data-pshub=project]').click();page.locator('[data-psmore]').click()
    assert page.locator('[data-psmore]').get_attribute('aria-pressed')=='true'
    assert page.locator('#atividades .psHub.on').count()==1
    page.locator('[data-psmore]').click();assert page.locator('#psMore').is_hidden()
    assert page.locator('[data-pshub=project]').get_attribute('aria-pressed')=='true'



def test_groups_keep_related_commands_together_and_distinguish_icons(page):
    groups=page.evaluate("()=>Object.fromEntries([...document.querySelectorAll('#rsToolPanel0 [data-rs-group]')].map(g=>[g.dataset.rsGroup,[...g.querySelectorAll('button')].map(b=>b.dataset.rsCommand||b.dataset.rsTool||b.dataset.rs3d)]))")
    assert {'MOVER','GIRAR','COPIAR','move','insertcontrol'}<=set(groups['Edição'])
    assert {'DIST','CALCULARFLUXOS','inspect'}<=set(groups['Cálculos'])
    assert {'EDITARFLUXOS','flowadd','flowoff','route'}<=set(groups['Fluxos de tráfego'])
    assert 'view3d' in groups['Navegação']
    for left,right in [('tool:move','cmd:MOVER'),('tool:chain','tool:align'),('tool:oae','tool:gantry'),('tool:access','tool:route'),('cmd:EDITARFLUXOS','tool:flowadd'),('cmd:DIST','tool:chain')]:
        def icon(key):
            kind,name=key.split(':');attribute='rs-tool' if kind=='tool' else 'rs-command'
            return page.locator(f'#rsToolPanel0 [data-{attribute}="{name}"] svg').inner_html()
        assert icon(left)!=icon(right),(left,right)
    duplicates=page.evaluate("()=>{const seen=new Map(),duplicates=[];for(const b of document.querySelectorAll('#rsToolPanel0 button')){const key=b.dataset.rsTool||b.dataset.rsCommand||b.dataset.rs3d,shape=b.querySelector('svg')?.innerHTML;if(!shape)continue;if(seen.has(shape))duplicates.push([seen.get(shape),key]);seen.set(shape,key)}return duplicates}")
    assert not duplicates,duplicates
    screenshot(page,'1428_03_grupos_e_icones')
    page.get_by_role('tab',name='Ferrovia e semáforos',exact=True).click()
    page.locator('[role=tabpanel]:visible [data-rs-tool=railway]').click()
    assert page.evaluate('tool')=='railway'
    page.get_by_role('tab',name='Cálculos',exact=True).click()
    page.locator('[role=tabpanel]:visible [data-rs-command=DIST]').click()
    assert page.evaluate('!!cadCmd')
    screenshot(page,'1428_04_calculos_medicao')



def test_calculation_button_runs_the_real_analysis_without_generating_video(gl_page,live):
    p=gl_page;previous=p.evaluate('lastPolled');p.get_by_role('tab',name='Cálculos',exact=True).click()
    p.locator('[role=tabpanel]:visible [data-rs-command=CALCULARFLUXOS]').click()
    p.wait_for_function('(previous)=>!!lastPolled&&lastPolled!==previous',arg=previous,timeout=10000);p.wait_for_function('!task && !!editor && editor.segments.length>0',timeout=60000)
    job=p.request.get(live[0]+'/api/jobs/'+p.evaluate('lastPolled')).json()
    assert job['kind']=='analyze' and job['state']=='done'
    assert p.evaluate('!!editor && editor.segments.length>0')
    assert not (live[2]/live[1]/'video.mp4').exists()
