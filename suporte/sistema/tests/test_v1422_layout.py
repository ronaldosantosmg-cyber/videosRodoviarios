"""1.42.2: barra rápida útil, informações no rodapé e rotas em primeiro plano."""
import pytest
from test_v142_visual import page
from visual_harness import rect,overlap,screenshot


def test_information_is_below_canvas_and_quick_buttons_below_menu(page):
    menu=rect(page,'#menuBar');quick=rect(page,'#rsToolRibbon');canvas=rect(page,'.canvasWrap')
    footer=rect(page,'#rsStudyFooter');legend=rect(page,'#rsFlowLegend')
    assert menu['y']+menu['height']<=quick['y']+1
    assert quick['y']+quick['height']<=canvas['y']+1
    assert footer['y']>=canvas['y']+canvas['height']-1
    assert legend['y']>=footer['y']
    assert legend['y']+legend['height']<=page.viewport_size['height']-20
    assert page.locator('#rsStudyFooter .dwCursor').count()==1
    assert page.locator('#rsStudyFooter #rsActiveTool').count()==1
    assert page.locator('#rsQuickTools').count()==0
    assert page.locator('#rsCommandBindings #undo,#rsCommandBindings #redo').count()==2
    screenshot(page,'1422_01_acesso_rapido_rodape')


def test_quick_actions_execute_and_properties_toggle(page):
    page.locator('#rsToolPanel0 [data-rs-tool="route"]').click()
    assert page.evaluate('tool')=='route'
    page.locator('#rsToolPanel0 [data-rs-tool="pan"]').click()
    assert page.evaluate('tool')=='pan'
    page.locator('[data-pshub="props"]').click()
    assert not page.evaluate('dockState.recolhida')
    page.locator('[data-pshub="props"]').click()
    page.wait_for_timeout(200)
    assert page.evaluate('dockState.recolhida')
    page.locator('#rsToolPanel0 [data-rs-command="EDITARFLUXOS"]').click()
    assert page.locator('#rsToolPanel0 [data-rs-command="EDITARFLUXOS"]').get_attribute('aria-pressed')=='true'
    page.locator('#rsToolPanel0 [data-rs-command="EDITARFLUXOS"]').click()
    assert page.locator('#rsToolPanel0 [data-rs-command="EDITARFLUXOS"]').get_attribute('aria-pressed')=='false'
    screenshot(page,'1422_02_botoes_funcionais')


def seed(page):
    page.evaluate("""()=>{
      meta={width_m:1000,screen_width:1000,screen_height:1000,camera:[0,0],right:[1,0],up:[0,1]};
      baseImage=document.createElement('canvas');baseImage.width=1000;baseImage.height=1000;baseMode='preview';
      view={s:1,ox:0,oy:0};cfg={km_start_m:0};M.chainage.mode='off';
      editor={segments:[{id:0,base:0,points:[[-120,0],[120,0]],forward:true,both:false,technical_status:'ok',technical_message:'Fluxo válido'}],connections:[],denied:[]};
      M.pavement_areas=[{id:'p',name:'Superfície sobre a rota',kind:'pista_nova',points:[{x:-150,y:-30},{x:150,y:-30},{x:150,y:30},{x:-150,y:30}]}];
      vecOn.flows=true;RodoviaFlowStudy.stale=false;
      // Enquadra a imagem de teste na área real, sem presumir 1000 px de altura.
      fitView();draw();
    }""")


def test_all_flows_are_drawn_above_surfaces_with_contrast(page):
    seed(page)
    page.locator('#rsToolPanel0 [data-rs-command="EDITARFLUXOS"]').click()
    colors=page.evaluate("""()=>{
      const original=ctx.stroke;const strokes=[];ctx.stroke=function(...a){strokes.push(this.strokeStyle);return original.apply(this,a)};
      try{draw()}finally{ctx.stroke=original}
      const [x,y]=W2C({x:0,y:0});return {strokes,pixel:[...ctx.getImageData(Math.round(x),Math.round(y),1,1).data]};
    }""")
    assert colors['strokes'][-2:]==['#081623','#22c55e']
    # Frações de pixel e antialiasing podem variar até dois níveis por canal.
    # A cor e a opacidade continuam estritas o suficiente para rejeitar sobreposição.
    assert max(abs(actual-expected) for actual,expected in zip(colors['pixel'][:3],[34,197,94]))<=2
    assert colors['pixel'][3]==255
    screenshot(page,'1422_03_fluxos_sobre_superficies')


def test_route_object_points_are_visible_in_foreground(page):
    seed(page)
    page.evaluate("M.route_alignments=[{id:'r',name:'Rota explícita',enabled:true,type:'simples',points:[{x:-100,y:40},{x:100,y:40}],sections:[]}];setTool('route');draw()")
    assert page.evaluate("RodoviaFlowStudy.isEditing()")
    screenshot(page,'1422_04_rotas_explicitas_destaque')


def test_flow_click_has_priority_over_surface(page):
    seed(page)
    page.locator('#rsToolPanel0 [data-rs-command="EDITARFLUXOS"]').click()
    point=page.evaluate("()=>{const [x,y]=W2C({x:0,y:0});const r=canvas.getBoundingClientRect();return {x:r.left+x*r.width/canvas.width,y:r.top+y*r.height/canvas.height}}")
    page.mouse.click(point['x'],point['y']);page.wait_for_timeout(150)
    assert page.evaluate('selSeg?.id')==0
    assert page.evaluate('sel') is None
    screenshot(page,'1422_05_selecao_fluxo_prioritaria')


@pytest.mark.parametrize('width',[1024,1366,1920])
def test_responsive_bars_keep_canvas_clear(page,width):
    page.set_viewport_size({'width':width,'height':900});page.evaluate("setTool('sign');dwCommandOpen()")
    page.wait_for_timeout(200)
    c=rect(page,'.canvasWrap');footer=rect(page,'#rsStudyFooter');top=rect(page,'#rsCommandRail')
    assert overlap(c,footer)<1 and overlap(c,top)<1
    assert c['height']>300
    legend=rect(page,'#rsFlowLegend');assert legend['y']+legend['height']<=900-20
    assert page.locator('#rsQuickTools').count()==0
    assert page.get_by_role('menuitem',name='Vídeo',exact=True).is_visible()
    assert page.locator('#rsStudyFooter #dwCommandDrawer').count()==1
    screenshot(page,f'1422_06_layout_{width}')
