"""A atualização de rotas conserva a vista sem exigir remontar o projeto."""
from test_v142_visual import page
from test_v1422_layout import seed
import pytest
from visual_harness import screenshot

@pytest.mark.parametrize('failed_preview',[False,True,'stale'])
def test_route_results_preserve_world_center_and_scale(page,failed_preview):
    seed(page)
    result=page.evaluate('''async failed=>{
      pid='retention';geoPid=pid;view={s:2.7,ox:-250,oy:125};
      const before=captureProjectView(),oldImage=baseImage,oldMeta=meta;
      const original={api,loadGeo,loadImage};
      api=async url=>url.endsWith('editor.json')?editor:{config:cfg,files:{},analysis:null,
        preview:failed==='stale'?null:{...meta,camera:[800,900],width_m:2000},editor_ready:true};
      loadGeo=async()=>{};
      loadImage=async()=>{if(failed)throw Error('falha de rede simulada');baseImage=document.createElement('canvas');baseImage.width=1000;baseImage.height=1000};
      try{await load(pid,{resultsOnly:true});return {before,after:captureProjectView(),ready:ready(),sameImage:baseImage===oldImage,sameMeta:meta===oldMeta}}
      finally{api=original.api;loadGeo=original.loadGeo;loadImage=original.loadImage}
    }''',failed_preview)
    assert result['ready']
    assert result['after']['center']['x']==pytest.approx(result['before']['center']['x'])
    assert result['after']['center']['y']==pytest.approx(result['before']['center']['y'])
    assert result['after']['scale']==pytest.approx(result['before']['scale'])
    if failed_preview:assert result['sameImage'] and result['sameMeta']


def test_invalid_view_is_rejected_without_overwriting_current_view(page):
    seed(page)
    assert page.evaluate('''()=>{const saved=JSON.stringify(view);return !restoreProjectView({center:{x:NaN,y:0},scale:1})&&JSON.stringify(view)===saved}''')


def test_layers_cache_keeps_identical_pixels_after_pan_and_undo_invalidation(page):
    seed(page)
    result=page.evaluate('''()=>{
      const pixel=()=>{const q=W2C({x:0,y:0});return [...ctx.getImageData(Math.round(q[0]),Math.round(q[1]),1,1).data]};
      RodoviaLayers.setEnabled(false);draw();const direct=pixel();
      RodoviaLayers.setEnabled(true);draw();const cached=pixel(),before=RodoviaLayers.stats();draw();
      const hit=RodoviaLayers.stats();view.ox+=20;draw();const pan=RodoviaLayers.stats();
      RodoviaLayers.invalidate();draw();const invalidated=RodoviaLayers.stats();
      return {direct,cached,before,hit,pan,invalidated}
    }''')
    assert result['direct']==result['cached']
    assert result['hit']['backgroundBuilds']==result['before']['backgroundBuilds']
    assert result['hit']['hits']>result['before']['hits']
    assert result['pan']['backgroundBuilds']>result['hit']['backgroundBuilds']
    assert result['invalidated']['backgroundBuilds']>result['pan']['backgroundBuilds']
    assert result['invalidated']['bytes']<=result['invalidated']['budgetBytes']


@pytest.mark.parametrize('width',[1024,1366,1920])
def test_compact_workspace_keeps_graphics_and_commands_accessible(page,width):
    page.set_viewport_size({'width':width,'height':900})
    seed(page)
    assert page.locator('#canvas').bounding_box()['height']>500
    assert page.locator('#rsTechnicalOptions').count()==1
    assert page.locator('#rsToolRibbon #rsTechnicalOptions').count()==1
    page.locator('#rsSidebarToggle').click()
    assert page.locator('#rsSidebarToggle').get_attribute('aria-expanded')=='false'
    assert page.evaluate('ready()')
    page.locator('#rsSidebarToggle').click()
    assert page.locator('#rsSidebarToggle').get_attribute('aria-expanded')=='true'
    screenshot(page,'14215_area_util_'+str(width))


def test_missing_geo_response_keeps_loaded_project_reference(page):
    seed(page)
    result=page.evaluate('''async()=>{
      pid='geo-retention';geoPid=pid;analysis={};cfg={};
      geo={mpp_crs:1,img_w:1000,img_h:1000};const saved=geo,original=api;
      api=async()=>{throw Error('rede indisponível')};
      try{await loadGeo();return geo===saved&&ready()}finally{api=original}
    }''')
    assert result


def test_cache_allocation_failure_falls_back_once_and_restores_context(page):
    seed(page)
    result=page.evaluate('''()=>{
      RodoviaLayers.invalidate();const original=document.createElement.bind(document),saved=ctx;let allocations=0,a=0,b=0;
      document.createElement=function(name,...args){const node=original(name,...args);if(name==='canvas'&&++allocations===2)node.getContext=()=>null;return node};
      try{RodoviaLayers.compose(()=>a++,()=>b++);return {a,b,context:ctx===saved,bytes:RodoviaLayers.stats().bytes}}
      finally{document.createElement=original}
    }''')
    assert result=={'a':1,'b':1,'context':True,'bytes':0}


def test_cache_budget_falls_back_without_allocating_extra_surfaces(page):
    seed(page)
    result=page.evaluate('''()=>{
      canvas.width=4096;canvas.height=2048;let paints=0;
      RodoviaLayers.compose(()=>paints++,()=>paints++);
      return {paints,...RodoviaLayers.stats()}
    }''')
    assert result['paints']==2 and result['bytes']==0 and result['surfaces']==1


def test_late_preview_failure_cannot_restore_another_projects_image(page):
    seed(page)
    result=page.evaluate('''async()=>{
      pid='old';geoPid=pid;const original={api,loadGeo,loadImage};let next;
      api=async url=>url.endsWith('editor.json')?editor:{config:cfg,files:{},analysis:null,preview:meta,editor_ready:true};
      loadGeo=async()=>{};loadImage=async()=>{pid='new';projectSession.context++;projectSession.loadIntent++;next=document.createElement('canvas');baseImage=next;meta=null;throw Error('requisição antiga falhou')};
      try{const loaded=await load('old',{resultsOnly:true});return loaded===false&&pid==='new'&&baseImage===next&&meta===null}
      finally{api=original.api;loadGeo=original.loadGeo;loadImage=original.loadImage}
    }''')
    assert result
