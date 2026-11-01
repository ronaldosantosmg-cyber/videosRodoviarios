import pytest
from app.calculation_guidance import guidance
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


@pytest.mark.parametrize('kind,message',[('analyze','corpo_fora da pista e fluxo inválido'),('render','ffmpeg falhou'),('convert_imagery','GeoTIFF inválido'),('alignment','alinhamento com resíduos'),('scene3d','memória excessiva'),('outro','causa ainda desconhecida')])
def test_all_calculation_failures_have_local_actionable_guidance(kind,message):
    report=guidance(kind,message,[15,25]);assert report['method']=='sistema_especialista_local'
    assert report['causes'] and len(report['steps'])>=2 and report['point']==[15,25]
    assert 'local' in report['limitations']


def test_invalid_location_is_never_offered_and_message_is_inert():
    r=guidance('analyze','<script>executar()</script>',[float('nan'),1]);assert r['point'] is None
    assert r['message']=='<script>executar()</script>'


@pytest.mark.parametrize('width',[768,1024,1366])
def test_new_project_has_padding_and_all_tools_stay_inside_viewport(page,width):
    page.set_viewport_size({'width':width,'height':900});page.evaluate('RodoviaNewProject.open()')
    r=page.locator('#rsNewProject').bounding_box();field=page.locator('#rsNewName').bounding_box()
    assert field['x']-r['x']>=14 and r['x']+r['width']-(field['x']+field['width'])>=14
    screenshot(page,'14217_novo_projeto_'+str(width));page.locator('#rsNewCancel').click()
    result=page.evaluate("()=>{const p=$('rsToolPanel0'),r=p.getBoundingClientRect();return {width:p.scrollWidth,client:p.clientWidth,edge:r.right,viewport:innerWidth}}")
    assert result['width']<=result['client']+1 and result['edge']<=result['viewport']
    page.locator('#rsToolPanel0 [data-rs-tool=flowcut]').scroll_into_view_if_needed()
    assert page.locator('#rsToolPanel0 [data-rs-tool=flowcut]').is_visible()
    screenshot(page,'14217_faixa_grupos_'+str(width))


def test_guidance_does_not_open_a_modal_during_processing_and_escapes_messages(page):
    seed(page);page.evaluate("()=>{pid='p';window._guideApi=api}")
    # A resposta da API é substituída na camada HTTP offline; interface real preservada.
    page.evaluate("()=>{window.fetch=async()=>({ok:true,status:200,json:async()=>({title:'Como corrigir este cálculo',causes:['Conferir entrada'],steps:['Corrigir o campo','Recalcular'],point:[30,0],message:'<img src=x onerror=alert(1)>',project:'p'}),headers:new Headers()})}")
    page.evaluate("RodoviaCalculationGuide.advise('analyze','erro',[30,0])")
    assert page.locator('dialog[open]').count()==0
    page.locator('#rsCalculationGuide').click()
    assert 'Conferir entrada' in page.get_by_role('dialog').inner_text()
    assert page.get_by_role('dialog').locator('img').count()==0
    page.get_by_role('button',name='Localizar ponto problemático',exact=True).click()
    assert page.evaluate('Math.abs(C2W(canvas.width/2,canvas.height/2).x-30)<1e-6')

from test_v1425_live_3d import live,gl_page


def test_missing_record_removal_preserves_existing_files_and_archives_catalogue(gl_page,live):
    from app import store
    p=gl_page;pid='a'*32;folder=live[2]/pid;folder.mkdir();(folder/'original.dxf').write_bytes(b'preservar')
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,'Registro residual'))
    p.evaluate('openProjectDialog()');p.locator('[data-op="'+pid+'"]').click()
    assert p.locator('#opDel').inner_text()=='Remover registro…'
    screenshot(p,'14217_registro_residual')
    p.locator('#opDel').click();p.locator('#confirmYes').click()
    p.wait_for_function('(id)=>!opRows.some(r=>r.id===id)',arg=pid,timeout=10000)
    assert (folder/'original.dxf').read_bytes()==b'preservar'
    assert list((live[2]/'_registros_removidos').glob(pid+'*.json'))
    assert not any(r['id']==pid for r in p.request.get(live[0]+'/api/projects_info').json())
    assert p.request.delete(live[0]+'/api/project-records/'+live[1]).status==409
    assert p.request.delete(live[0]+'/api/project-records/invalid').status==422


def test_missing_record_with_running_job_cannot_be_removed(gl_page,live):
    from app import store
    pid='b'*32
    with store.connect() as c:
        c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,'Em execução'))
        c.execute('INSERT INTO jobs(id,project,kind,state) VALUES(?,?,?,?)',('busy',pid,'analyze','running'))
    assert gl_page.request.delete(live[0]+'/api/project-records/'+pid).status==409
    with store.connect() as c:
        assert c.execute('SELECT 1 FROM projects WHERE id=?',(pid,)).fetchone()
        c.execute("UPDATE jobs SET state='failed' WHERE id='busy'")


def test_real_api_calculation_error_produces_guidance_without_blocking_motor(gl_page):
    p=gl_page
    p.evaluate("async()=>{try{await api('/api/alignment/fit',json('POST',{mode:'inexistente',pairs:[]}))}catch{}}")
    p.wait_for_function("$('rsCalculationGuide').textContent.includes('corrigir')",timeout=10000)
    assert p.locator('dialog[open]').count()==0
    p.locator('#rsCalculationGuide').click()
    assert 'Possíveis causas' in p.get_by_role('dialog').inner_text()
    screenshot(p,'14217_orientacao_calculo_real')
    p.get_by_role('button',name='Fechar',exact=True).click()


def test_calculation_guide_is_visible_next_to_flow_repair(page):
    page.set_viewport_size({'width':1024,'height':900})
    assert page.evaluate("$('rsRepairFlows').nextElementSibling.id==='rsCalculationGuide'")
    r=page.locator('#rsCalculationGuide').bounding_box()
    assert r['x']>=0 and r['x']+r['width']<=1024
