from test_v142_visual import page


def test_layers_are_available_before_analysis_and_keep_named_mapping(page):
    page.evaluate("""()=>{analysis=null;cfg.layers={axis:['EIXO']};sourceLayerCatalog={source:'input.dxf',layers:[{name:'0',count:2},{name:'EIXO',count:4},{name:'PAVIMENTO',count:8}],warnings:[]};showLayers()}""")
    assert page.evaluate("lmLayers().map(l=>l.name)")==['0','EIXO','PAVIMENTO']
    page.evaluate("pid='layer-test';openLayerManager()");page.wait_for_selector('#layerDlg[open]')
    assert page.locator('#lmRows select[data-lmrole]').count()==3
    assert page.locator('#lmRows [data-lmn="EIXO"] select[data-lmrole]').input_value()=='axis'
    page.locator('#lmRows [data-lmn="PAVIMENTO"] select[data-lmrole]').select_option('pavement')
    assert page.evaluate("collect().layers.pavement") == ['PAVIMENTO']
