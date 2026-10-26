import numpy as np
from test_v142_visual import page
from test_v1422_layout import seed
from test_v14213_continuity import network,AXIS
from app.flow_diagnostics import flow_diagnostics
from visual_harness import screenshot,open_activity


def present(page,n):
    diagnostics=flow_diagnostics(n);segments=[]
    for i,(raw,diag) in enumerate(zip(n.raw_info,diagnostics)):
        points=raw['points'];segments.append(dict(id=i,base=raw['base'],points=points.tolist(),
            mid=points[len(points)//2].tolist(),source=raw['source'],origin_key=raw['origin_key'],
            forward=raw['forward'],both=raw['both'],disabled=raw['disabled'],**diag))
    seed(page)
    page.evaluate('''segments=>{
      meta.camera=[300,0];editor={segments,connections:[],denied:[]};
      M.pavement_areas=[{id:'p',name:'Pista',kind:'pista_nova',points:[{x:-10,y:-15},{x:610,y:-15},{x:610,y:15},{x:-10,y:15}]}];
      fitView();RodoviaFlowStudy.stale=false;draw();
    }''',segments)
    open_activity(page,'Tráfego').locator('[data-rs-command=EDITARFLUXOS]').click()
    return segments


def test_native_contact_piece_is_green_selectable_and_has_continuity_explanation(page):
    n=network([dict(points=AXIS),dict(points=np.array([[250.,0.],[250.,150.]])),dict(points=np.array([[275.,0.],[275.,150.]]))])
    segments=present(page,n)
    selected=next(s for s in segments if 'Subtrecho integrado' in s['technical_message'])
    point=page.evaluate('(p)=>W2C({x:p[0],y:p[1]})',selected['mid']);box=page.locator('#canvas').bounding_box()
    page.mouse.click(box['x']+point[0],box['y']+point[1])
    assert page.evaluate('selSeg?.id')==selected['id']
    assert page.evaluate('flowStudyColor(segById(selSeg.id))')=='#22c55e'
    assert 'Subtrecho integrado' in page.locator('#propPanel').inner_text()
    screenshot(page,'14213_01_eixo_continuo_encontro')


def test_real_block_shows_reason_location_and_manual_surface_correction(page):
    from shapely.geometry import box
    n=network([dict(points=AXIS)],obstacles=[box(295,-20,305,220)])
    segments=present(page,n);assert not n.paths
    target=next(s for s in segments if 'corpo_fora_da_pista' in s['technical_reasons'])
    page.evaluate('(id)=>{selSeg={id};showSegProps();draw()}',target['id'])
    text=page.locator('#propPanel').inner_text()
    assert 'corpo do veículo fora do pavimento reconhecido' in text
    assert 'Linhas de bordo não são barreiras' in text
    assert target['technical_points']
    screenshot(page,'14213_02_bloqueio_localizado')
