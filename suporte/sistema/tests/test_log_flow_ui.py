import pytest
from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


@pytest.mark.parametrize('destination',[False,True])
def test_brush_ignores_area_response_after_escape_or_context_change(gl_page,destination):
    p=gl_page
    result=p.evaluate('''async destination=>{
      startBrush();brushHit=()=>null;hitObject=()=>null;
      if(destination)brush.src={mode:'pav',kind:'pavement',material:'auto',texture:null};
      const before=JSON.stringify(M),oldApi=api;let release;
      api=async()=>await new Promise(r=>release=r);
      const pending=brushClick({x:500100,y:7800000},{});
      if(destination)projectSession.context++;else setTool('pan');
      release({layer:'PAVIMENTO',role:'pavement',points:[[0,0],[1,0],[1,1]]});
      try{await pending;return {unchanged:JSON.stringify(M)===before,source:brush?.src||null}}
      finally{api=oldApi}
    }''',destination)
    assert result['unchanged']
    if not destination:assert result['source'] is None


def test_vehicle_help_exposes_direction_review_without_releasing_routes(gl_page):
    p=gl_page;p.evaluate('RodoviaTrafficHelp.open()')
    d=p.get_by_role('dialog',name='Diagnosticar veículos',exact=True)
    assert d.get_by_role('button',name='Conferir sentidos e nós',exact=True).is_visible()
    assert d.get_by_role('button',name='Revisar modo de ensaio e proteções',exact=True).is_visible()
    screenshot(p,'diagnostico_veiculos_sentidos');d.get_by_role('button',name='Fechar',exact=True).click()
