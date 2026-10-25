import pytest
from test_v1425_live_3d import live,gl_page
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_saves_3500_capacity_and_higher_demand_through_real_api(gl_page):
    p=gl_page;p.locator('[data-pshub=video]').click();p.get_by_text('Tráfego: simulação, engarrafamento e canteiro',exact=True).click();p.locator('#traffic_capacity_vphpl').fill('3500');p.locator('#traffic_demand_vphpl').fill('5000');p.locator('#traffic_demand_vphpl').dispatch_event('input');p.locator('#rsPanelSave').click();p.wait_for_function('!RodoviaPanels.opened',timeout=15000);p.locator('[data-pshub=video]').click()
    assert p.evaluate('cfg.traffic_capacity_vphpl')==3500 and p.evaluate('cfg.traffic_demand_vphpl')==5000
    assert 'sobressaturação' in p.locator('#rsTrafficStudy').inner_text()
    screenshot(p,'1426_06_demanda_sobressaturacao')
    p.locator('#traffic_capacity_vphpl').fill('0')
    result=p.evaluate('()=>{try{collect();return ""}catch(e){return e.message}}');assert 'maior que zero' in result


def test_validation_errors_are_portuguese_and_zoom_tolerance_is_adaptive(page):
    text=page.evaluate("validationMessage([{type:'greater_than',loc:['body','traffic_capacity_vphpl'],ctx:{gt:0}}])")
    assert text=='Capacidade nominal por faixa: informe um número maior que 0.'
    seed(page);page.evaluate('RodoviaFlowStudy.stale=false;view.s=.1')
    assert page.evaluate('!!nearestSegment({x:0,y:12})')
    page.evaluate('view.s=10')
    assert not page.evaluate('!!nearestSegment({x:0,y:12})')
    screenshot(page,'1426_05_fluxos_zoom_diagnostico')


def test_rejected_upload_preserves_existing_kmz_and_loaded_analysis(gl_page,live):
    import io,zipfile,hashlib
    from test_v1426_import_capacity import KML
    p=gl_page;url=live[0]+'/api/projects/'+live[1]+'/files';content=io.BytesIO()
    with zipfile.ZipFile(content,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('doc.kml',KML)
    response=p.request.post(url,multipart={'file':{'name':'referencia.kmz','mimeType':'application/vnd.google-earth.kmz','buffer':content.getvalue()}});assert response.status==200
    path=live[2]/live[1]/'input.kmz';before=hashlib.sha256(path.read_bytes()).hexdigest()
    preserved=p.evaluate("async()=>{const previous=analysis;await sendFiles([new File(['arquivo corrompido'],'DUPLICAÇÃO TH53.kmz')]);return analysis===previous}")
    assert preserved and hashlib.sha256(path.read_bytes()).hexdigest()==before
    assert 'ZIP válido' in p.locator('#message').inner_text()
