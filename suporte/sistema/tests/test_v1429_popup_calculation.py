from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_calculation_resolves_popup_and_sends_current_configuration(gl_page,live):
    p=gl_page
    p.evaluate("openSection('Configuração')")
    p.locator('#name').fill('Dados confirmados antes do cálculo')
    p.locator('#name').dispatch_event('change')
    p.evaluate("window.calculationFinished=false;window.calculationError=null;void start('analyze').then(()=>window.calculationFinished=true).catch(e=>window.calculationError=e.message)")
    p.locator('#rsPanelDecision').wait_for(state='visible')
    p.locator('[data-choice=save]').click()
    p.wait_for_function('calculationFinished||calculationError',timeout=60000)
    assert p.evaluate('calculationError') is None
    assert not p.evaluate('RodoviaPanels.opened')
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert saved['name']=='Dados confirmados antes do cálculo'
    job=p.request.get(live[0]+'/api/jobs/'+p.evaluate('lastPolled')).json()
    assert job['kind']=='analyze' and job['state']=='done',job
    screenshot(p,'1429_03_calculo_configuracao_confirmada')
    # Continuar editando cancela a solicitação de cálculo sem iniciar uma tarefa.
    previous=p.evaluate('lastPolled')
    p.evaluate("openSection('Configuração')")
    p.locator('#name').fill('Edição ainda não confirmada')
    p.evaluate("window.cancelledCalculation=null;void start('analyze').then(r=>window.cancelledCalculation=r)")
    p.locator('[data-choice=continue]').click()
    p.wait_for_function('cancelledCalculation===false')
    assert p.evaluate('lastPolled')==previous
    assert p.evaluate('!!RodoviaPanels.opened')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']==saved['name']


def test_toolbar_command_runs_once_after_popup_confirmation(gl_page,live):
    p=gl_page;p.evaluate("openSection('Configuração')")
    p.locator('#name').fill('Configuração enviada pelo botão técnico')
    p.evaluate("""()=>{window.toolbarRuns=0;const b=document.createElement('button');b.id='testCalculationCommand';b.textContent='Calcular verificação';b.style='position:fixed;left:400px;top:40px;z-index:999999';b.onclick=async()=>{window.toolbarRuns++;await start('analyze')};document.body.appendChild(b)}""")
    previous=p.evaluate('lastPolled')
    p.locator('#testCalculationCommand').click()
    p.locator('#rsPanelDecision').wait_for(state='visible')
    assert p.evaluate('toolbarRuns')==0
    p.locator('[data-choice=save]').click()
    p.wait_for_function('(previous)=>lastPolled!==previous',arg=previous,timeout=15000)
    p.wait_for_function('toolbarRuns===1 && !task',timeout=60000)
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['name']=='Configuração enviada pelo botão técnico'
    assert p.evaluate('toolbarRuns')==1
