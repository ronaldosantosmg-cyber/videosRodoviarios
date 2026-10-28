import json
import numpy as np
import ezdxf
from app.models import Settings
from app.render import Scene
from app.scene3d import build
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page,open3d
from test_v142_visual import page
from visual_harness import screenshot


def test_native_asset_layers_have_2d_textures_and_real_3d_geometry(tmp_path):
    d,s=project(tmp_path,traffic=False);doc=ezdxf.readfile(d/'input.dxf');model=doc.modelspace()
    for name in ['GASMIG','ARVORES','EDIFICACAO','POSTES','REDE ELETRICA','FIBRA OPTICA','RADAR','TORRE','EROSAO','CORTINA ATIRANTADA','OFFSET','FERROVIA']:doc.layers.new(name)
    for name,y in [('GASMIG',12),('REDE ELETRICA',40),('FIBRA OPTICA',-30),('FERROVIA',-45)]:model.add_lwpolyline([(500030,7800000+y),(500470,7800000+y)],dxfattribs={'layer':name})
    for name,x in [('POSTES',80),('RADAR',200),('TORRE',390)]:model.add_point((500000+x,7800030),dxfattribs={'layer':name})
    for name,x in [('ARVORES',30),('EDIFICACAO',130),('EROSAO',270),('CORTINA ATIRANTADA',330),('OFFSET',400)]:
        h=model.add_hatch(dxfattribs={'layer':name});h.paths.add_polyline_path([(500000+x,7800045),(500030+x,7800045),(500030+x,7800070),(500000+x,7800070)],is_closed=True)
    doc.saveas(d/'input.dxf')
    from app.geometry import guess
    for name in ['GASMIG','ARVORES','EDIFICACAO','POSTES','REDE ELETRICA','FIBRA OPTICA','RADAR','TORRE','EROSAO','CORTINA ATIRANTADA','OFFSET','FERROVIA']:
        s.layers.setdefault(guess(name),[]).append(name)
    scene=Scene(d,s);im,_=scene.frame(1,overview=True)
    q=scene.screen(np.array([[500040.,7800012.]]),scene.center,scene.overview)[0].astype(int)
    patch=im[max(0,q[1]-5):q[1]+6,max(0,q[0]-5):q[0]+6].astype(int)
    assert np.any((patch[:,:,0]>150)&(patch[:,:,1]>80)&(patch[:,:,2]<130))
    (d/'config.json').write_text(s.model_dump_json(),encoding='utf-8')
    data=build(d,s)
    roles={m['role'] for m in data['meshes']}
    assert {'gas','vegetation','building','pole','electric','fiber','radar','tower','erosion','anchored_wall','earthwork','railway'}<=roles
    assert all(np.isfinite(m['positions']).all() for m in data['meshes'])
    import os
    from pathlib import Path
    from PIL import Image
    if os.environ.get('VISUAL_ARTIFACTS'):Image.fromarray(im).save(Path(os.environ['VISUAL_ARTIFACTS'])/'14210_04_texturas_interferencias.png')


def test_catalog_saves_a_reusable_name_and_material_profile(gl_page,live):
    p=gl_page;p.evaluate('RodoviaAssetCatalog.open()');p.wait_for_selector('#rsAssetCatalog')
    assert p.locator('#rsAssetGallery [data-material]').count()>=32
    p.locator('#rsAssetGallery [data-material=gas]').click()
    p.locator('#rsAssetPattern').fill('*MEU_NOME_GAS*');p.locator('#rsAssetProfile').fill('Padrão profissional de teste')
    p.locator('#rsAssetAdd').click();p.locator('#rsAssetSave').click()
    p.wait_for_function("profiles.some(p=>p.name==='Padrão profissional de teste')")
    profile=next(row for row in p.request.get(live[0]+'/api/layer_profiles').json()['profiles'] if row['name']=='Padrão profissional de teste')
    assert profile['rules'][0]=={'pattern':'*MEU_NOME_GAS*','role':'gas','material':'gas'}
    screenshot(p,'14210_05_catalogo_nomes_materiais')
    p.locator('#rsAssetCatalog footer [data-close]').click();assert p.locator('#rsAssetCatalog').count()==0


def test_signal_clock_in_plan_matches_the_backend_with_a_link(page):
    from app.transport import Transport
    s=Settings(traffic_signals=[dict(id='a',point=dict(x=0,y=0),phases=3,offset_s=4),dict(id='b',point=dict(x=150,y=0),phases=3)],signal_links=[dict(id='link',source='a',target='b',speed_kmh=40)])
    controller=Transport(s);page.evaluate('(cfg)=>{M.traffic_signals=cfg.traffic_signals;M.signal_links=cfg.signal_links}',s.model_dump())
    for t in [0,5,15,30,50,80,120]:
        for signal in s.traffic_signals:
            expected=controller.signal_state(signal,t)
            for axis in [0,1]:assert page.evaluate('([id,t,axis])=>RodoviaTransport.signalPhase(M.traffic_signals.find(s=>s.id===id),t,axis)',[signal.id,t,axis])==expected[axis]


def test_train_night_headlights_and_signal_arms_are_present_in_webgl(gl_page,live):
    from test_v1426_transport_visual import controls
    p=gl_page;d=live[2]/live[1];s=controls(Settings.model_validate_json((d/'config.json').read_text()),duration=3)
    # Disponibiliza a composição na prévia curta.
    for rail in s.railways:rail.start_s=0
    (d/'config.json').write_text(s.model_dump_json());build(d,s)
    p.evaluate('(id)=>load(id)',live[1]);open3d(p);p.evaluate('Rodovia3D.setTime(2.9)');p.locator('[data-rs3d=light3d]').click();p.locator('[data-rs3d=light3d]').click()
    stats=p.evaluate('Rodovia3D.stats()')
    assert stats['light']=='noite' and stats['trainHeadlightsActive']>0 and stats['signalArms']>0
    screenshot(p,'14210_06_semaforo_braco_farol_noturno_3d')
    p.locator('[data-rs3d=light3d]').click();assert p.evaluate('Rodovia3D.stats().trainHeadlightsActive')==0


def test_catalog_footer_stays_visible_and_close_offers_save_or_discard(gl_page):
    p=gl_page;p.set_viewport_size({'width':1024,'height':720});p.evaluate('RodoviaAssetCatalog.open()')
    p.wait_for_selector('#rsAssetCatalog');p.locator('#rsAssetProfile').fill('Ainda não salvo')
    footer=p.locator('#rsAssetCatalog footer').bounding_box()
    assert footer['y']>=0 and footer['y']+footer['height']<=720
    p.locator('#rsAssetCatalog footer [data-close]').click()
    p.get_by_role('button',name='Continuar editando',exact=True).click();assert p.locator('#rsAssetCatalog').is_visible()
    p.locator('#rsAssetCatalog footer [data-close]').click();p.get_by_role('button',name='Descartar',exact=True).click()
    assert p.locator('#rsAssetCatalog').count()==0
