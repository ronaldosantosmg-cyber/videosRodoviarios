from test_v142_visual import page


def test_layers_are_available_before_analysis_and_keep_named_mapping(page):
    page.evaluate("""()=>{analysis=null;cfg.layers={axis:['EIXO']};sourceLayerCatalog={layers:[{name:'0',count:2},{name:'EIXO',count:4},{name:'PAVIMENTO',count:8}],warnings:[]};showLayers()}""")
    assert page.evaluate("lmLayers().map(l=>l.name)")==['0','EIXO','PAVIMENTO']
    assert page.locator('#layers select').count()==3
    assert page.locator('#layers select[data-layer="EIXO"]').input_value()=='axis'
    page.evaluate("()=>{const el=document.querySelector('#layers select[data-layer=\"PAVIMENTO\"]');el.value='pavement';el.dispatchEvent(new Event('change',{bubbles:true}))}")
    assert page.evaluate("collect().layers.pavement") == ['PAVIMENTO']
