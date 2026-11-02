"""Interface real: duas seções, edição pendente e localização de obras da planilha."""
import json
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def settled(page):
    page.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=180000)


def open_route(page,whole):
    settled(page)
    page.evaluate('''(whole)=>{
      M.route_alignments=[{id:'duas-secoes',name:'Eixo em dois trechos',points:[{x:500050,y:7800000},{x:500450,y:7800000}],enabled:true,type:'simples',lanes:1,lane_width_m:3.5,median_m:0,taper_m:40,sections_only:true,section_surface:false,cross_sections:whole?[{id:'S',name:'Trecho original',start_m:0,end_m:400,type:'simples',median_m:0,left:[{kind:'pista',width_m:3.5,traffic_enabled:true}],right:[{kind:'pista',width_m:3.5,traffic_enabled:true}]}]:[]}];
      RodoviaSections.open(0);
    }''',whole)
    page.locator('#rsRoadSections').wait_for(state='visible')


def test_split_axis_preserves_first_section_and_saves_modified_second(gl_page,live):
    p=gl_page;open_route(p,True);d=p.locator('#rsRoadSections')
    d.locator('[name=splitAt]').fill('200');d.locator('[data-split-section]').click()
    assert d.locator('[data-sections] li').count()==2
    assert d.locator('[name=start]').input_value()=='200'
    d.locator('[name=template]').select_option('dupla')
    screenshot(p,'263_duas_secoes')
    d.locator('[data-save]').click();d.wait_for(state='detached',timeout=45000)
    sections=p.evaluate('M.route_alignments[0].cross_sections')
    assert len(sections)==2 and sections[0]['type']=='simples' and sections[1]['type']=='dupla'
    assert [(s['start_m'],s['end_m']) for s in sections]==[(0,200),(200,400)]
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert cfg['route_alignments'][0]['cross_sections']==sections


def test_save_and_close_includes_next_section_without_extra_add_click(gl_page,live):
    p=gl_page;open_route(p,False);d=p.locator('#rsRoadSections')
    d.locator('[name=end]').fill('150');d.locator('[data-add-section]').click()
    assert float(d.locator('[name=start]').input_value())==150
    d.locator('[name=template]').select_option('dupla');d.locator('[name=sectionName]').fill('Duplicação do segundo trecho')
    d.locator('[data-save]').click();d.wait_for(state='detached',timeout=45000)
    sections=p.evaluate('M.route_alignments[0].cross_sections')
    assert len(sections)==2 and sections[1]['name']=='Duplicação do segundo trecho'
    assert [(s['start_m'],s['end_m']) for s in sections]==[(0,150),(150,400)]


def test_csv_import_previews_positions_and_outside_work_cannot_be_located(gl_page,live):
    p=gl_page;settled(p)
    p.evaluate("async()=>{M.chainage={...M.chainage,mode:'auto'};M.works=[];await save();abrirImportarObras()}")
    d=p.locator('#obImpDlg');d.locator('#obArq').set_input_files({'name':'obras.csv','mimeType':'text/csv','buffer':'Obra;Km inicial;Km final\nPonte teste;0+050;0+100\nFora do eixo;9+000;9+100\n'.encode()})
    p.wait_for_function("document.querySelector('#obImpInfo').textContent.includes('Posicionamento automático')",timeout=45000)
    assert 'Fora do eixo' in d.locator('#obImpRows').inner_text()
    assert 'Localizada' in d.locator('#obImpRows').inner_text()
    screenshot(p,'263_per_importacao')
    d.locator('#obImpOk').click();p.evaluate('save()');settled(p)
    p.evaluate('conferirPosicionamentoObras()');report=p.locator('#rsPERLocation');report.wait_for(state='visible',timeout=45000)
    rows=report.locator('tbody tr');assert rows.count()==2
    assert rows.nth(0).get_by_role('button',name='Localizar',exact=True).count()==1
    assert rows.nth(1).get_by_role('button',name='Localizar',exact=True).count()==0
    screenshot(p,'263_per_localizacao')
    report.get_by_role('button',name='Localizar',exact=True).click();assert report.count()==0
