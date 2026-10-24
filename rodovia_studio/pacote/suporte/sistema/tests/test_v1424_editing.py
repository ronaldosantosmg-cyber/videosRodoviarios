import pytest
from test_v142_visual import page
from test_v1422_layout import seed
from visual_harness import screenshot

@pytest.mark.parametrize('dpi',[1,2])
def test_zoom_keeps_mouse_anchor_normalizes_wheel_and_allows_close_detail(page,dpi):
    seed(page)
    result=page.evaluate('''dpi=>{
      Object.defineProperty(window,'devicePixelRatio',{configurable:true,value:dpi});resizeCanvas();view={s:1,ox:10,oy:20};
      const r=canvas.getBoundingClientRect(),cx=Math.floor(r.left+r.width*.4),cy=Math.floor(r.top+r.height*.6);
      const [x,y]=evtCanvas({clientX:cx,clientY:cy}),before=C2W(x,y);
      canvas.dispatchEvent(new WheelEvent('wheel',{clientX:cx,clientY:cy,deltaY:-3,deltaMode:1,cancelable:true}));
      const after=C2W(x,y),lineScale=view.s;
      view={s:1,ox:10,oy:20};canvas.dispatchEvent(new WheelEvent('wheel',{clientX:cx,clientY:cy,deltaY:-48,deltaMode:0,cancelable:true}));
      const pixelScale=view.s;
      for(let i=0;i<12;i++)canvas.dispatchEvent(new WheelEvent('wheel',{clientX:cx,clientY:cy,deltaY:-10000,cancelable:true}));
      return {before,after,lineScale,pixelScale,view:{...view},maximum:maxViewScale()};
    }''',dpi)
    assert result['before']==pytest.approx(result['after'],rel=0,abs=1e-8)
    assert result['lineScale']==pytest.approx(result['pixelScale'])
    assert 60<result['view']['s']<=result['maximum']
    screenshot(page,f'1424_06_zoom_dpi_{dpi}')

def test_invalid_wheel_and_degenerate_fit_do_not_corrupt_view(page):
    seed(page)
    assert page.evaluate('''()=>{
      const before=JSON.stringify(view);const e=new Event('wheel',{cancelable:true});Object.defineProperty(e,'deltaY',{value:NaN});canvas.dispatchEvent(e);
      const kept=JSON.stringify(view)===before;analysis={bounds:[[1,1],[1,1]]};baseImage.width=0;fitView();
      return kept&&Object.values(view).every(Number.isFinite);
    }''')

def test_undo_redo_clear_stale_geometry_and_skip_noop_snapshots(page):
    seed(page)
    result=page.evaluate('''()=>{
      undoStack=[];redoStack=[];M.custom_axis={enabled:true,points:[{x:0,y:0},{x:100,y:0}]};checkpoint();
      M.custom_axis.points[1].x=120;checkpoint();checkpoint();axisCache={stale:true};snapIndex={stale:true};exactSnap={stale:true};drag={type:'grip'};
      const before={...view};undo();const undone=M.custom_axis.points[1].x;const cleared=axisCache===null&&exactSnap===null&&drag===null;
      redo();return {undone,redone:M.custom_axis.points[1].x,cleared,before,after:{...view}};
    }''')
    assert result['undone']==100 and result['redone']==120 and result['cleared']
    assert result['before']==pytest.approx(result['after'],rel=0,abs=1e-9)

def test_undo_restores_multiple_operations_and_new_edit_drops_redo(page):
    seed(page)
    result=page.evaluate('''()=>{
      M.cities=[];undoStack=[];redoStack=[];checkpoint();M.cities.push({id:'a',name:'A',point:{x:0,y:0},show:true});
      checkpoint();M.cities[0].point.x=.001;undo();const p=M.cities[0].point.x;undo();const empty=M.cities.length===0;redo();const one=M.cities.length===1;
      checkpoint();M.cities[0].name='Nova';return {p,empty,one,redo:redoStack.length};
    }''')
    assert result==dict(p=0,empty=True,one=True,redo=0)
