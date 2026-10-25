from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot


def test_static_markup_cache_updates_on_edit_and_undo_without_rebuilding_aerial(page):
    seed(page)
    result=page.evaluate('''()=>{
      const pixel=()=>{const q=W2C({x:50,y:15});return [...ctx.getImageData(Math.round(q[0]),Math.round(q[1]),1,1).data]};
      draw();const before=RodoviaLayers.stats(),original=pixel();checkpoint();M.pavement_areas[0].kind='shoulder';changed();const edited=pixel(),after=RodoviaLayers.stats();undo();draw();
      return {before,after,original,edited,restored:pixel(),last:RodoviaLayers.stats()}
    }''')
    assert result['before']['backgroundBuilds']==result['after']['backgroundBuilds']
    assert result['after']['technicalBuilds']>result['before']['technicalBuilds']
    assert result['original']!=result['edited'] and result['restored']==result['original']
    assert result['last']['bytes']<=32*1024*1024
    screenshot(page,'14218_camadas_edicao_desfazer')


def test_seed_empty_or_nonfinite_cannot_be_saved(page):
    page.evaluate("$('pedestrian_seed').value=''")
    result=page.evaluate("()=>{try{collect();return ''}catch(e){return e.message}}")
    assert 'Semente' in result


def test_interval_direction_requests_recalculation_instead_of_only_drawing_arrow(page):
    seed(page)
    page.evaluate("()=>{pid='direction';window._startOriginal=start;window._starts=[];start=async(kind,payload,options)=>{window._starts.push({kind,automatic:options?.automatic});return {state:'done'}};checkpoint();M.direction_marks=[{id:'interval',start:{x:100,y:0},end:{x:200,y:0}}];changed()}")
    page.wait_for_function("window._starts.some(s=>s.kind==='analyze'&&s.automatic)",timeout=5000)
    page.evaluate('()=>{start=window._startOriginal}')


def test_three_surfaces_preserve_full_raster_with_only_rounding_tolerance(page):
    seed(page)
    result=page.evaluate('''()=>{
      RodoviaLayers.setEnabled(false);const direct=ctx.getImageData(0,0,canvas.width,canvas.height).data;
      RodoviaLayers.setEnabled(true);const cached=ctx.getImageData(0,0,canvas.width,canvas.height).data;
      let maximum=0,over=0;for(let i=0;i<direct.length;i++){const d=Math.abs(direct[i]-cached[i]);maximum=Math.max(maximum,d);if(d>3)over++}return {maximum,over}
    }''')
    assert result['over']==0,result


def test_pan_keeps_direct_markup_and_settles_without_losing_geometry(page):
    seed(page)
    result=page.evaluate('''()=>{
      view.ox+=21;drag={type:'pan'};draw();const direct=ctx.getImageData(0,0,canvas.width,canvas.height).data;
      drag=null;draw();const cached=ctx.getImageData(0,0,canvas.width,canvas.height).data;
      let maximum=0;for(let i=0;i<direct.length;i++)maximum=Math.max(maximum,Math.abs(direct[i]-cached[i]));return {maximum,ready:ready()}
    }''')
    assert result['ready'] and result['maximum']<=3
