import numpy as np
import ezdxf
from app.models import Settings
from app.geometry import analyze
from app.render import Scene
from app.pavement import paint_rigid,JointField
from app import visual


def project(directory,overrides=None):
    doc=ezdxf.new();m=doc.modelspace()
    for layer in ('EIXO','PAVIMENTO','CORTE ROCHA','CORTE SOLO'):doc.layers.new(layer)
    m.add_lwpolyline([(0,0),(200,0)],dxfattribs={'layer':'EIXO'})
    for layer,points in [('PAVIMENTO',[(0,-5),(200,-5),(200,5),(0,5)]),('CORTE ROCHA',[(20,10),(100,10),(100,35),(20,35)]),('CORTE SOLO',[(110,10),(180,10),(180,35),(110,35)])]:
        h=m.add_hatch(dxfattribs={'layer':layer});h.paths.add_polyline_path(points,is_closed=True)
        if layer=='CORTE ROCHA':h.paths.add_polyline_path([(40,15),(50,15),(50,20),(40,20)],is_closed=True,flags=0)
    doc.saveas(directory/'input.dxf')
    return Settings(layers={'axis':['EIXO'],'pavement':['PAVIMENTO'],'cut':['CORTE ROCHA','CORTE SOLO']},layer_materials=overrides or {},
        texture_style='artistico',imagery='neutral',imagery_pixels=2048,hydrography=False,traffic=False,pavement_material='rigido',earthwork_look='natural',coordinates_confirmed=True,duration_s=3)


def test_only_explicit_rock_names_or_overrides_are_used(tmp_path):
    from app.asset_catalog import material_for
    assert material_for('cut','CORTE SOLO')=='cut_soil'
    assert material_for('cut','CORTE ROCHA')=='rock'
    cfg=project(tmp_path);items,*_=analyze(tmp_path,cfg)
    rocks=[e for e in items if e.get('asset_material')=='rock']
    assert rocks and all(e['layer']=='CORTE ROCHA' and e['role']=='cut' for e in rocks)
    changed=cfg.model_copy(update={'layer_materials':{'CORTE ROCHA':'cut_soil','CORTE SOLO':'rock'}})
    items,*_=analyze(tmp_path,changed)
    assert all(e['layer']=='CORTE SOLO' for e in items if e.get('asset_material')=='rock')


def test_rock_reaches_scene_and_detail_without_filling_holes(tmp_path):
    scene=Scene(tmp_path,project(tmp_path))
    for point,expected in [((30,22),visual.ROCK_SURF),((130,22),6),((45,17),0)]:
        x,y=np.rint(scene.worldpx(np.array([point]))[0]).astype(int)
        assert scene.surface[y,x]==expected
    detail=scene.detail;i=int((30-detail.x0)/(detail.R*1024));j=int((detail.y1-22)/(detail.R*1024))
    _,surface=detail.overlay_tile(i,j);x,y=np.rint(detail.worldpx(i,j)(np.array([[30,22]]))[0]).astype(int)
    assert surface[y,x]==visual.ROCK_SURF


def test_rock_shading_is_anchored_and_does_not_change_other_surfaces():
    im=np.full((80,100,3),138,np.uint8);surf=np.zeros((80,100),np.uint8);surf[10:70,10:90]=visual.ROCK_SURF;surf[30:40,30:40]=0
    before=im.copy();A=np.array([[.05,0,730000.],[0,-.05,7830000.]])
    visual.shade_rock(im,surf,A,.05,surf>0)
    np.testing.assert_array_equal(im[surf==0],before[surf==0])
    other=before.copy();visual.shade_rock(other,surf,A,.05,surf>0)
    np.testing.assert_array_equal(other,im)
    assert im[surf>0].std()>5


def test_clean_concrete_is_light_with_joints_inside_mask():
    mask=np.zeros((60,100),bool);mask[5:55,5:95]=True
    field=JointField([np.array([[0.,0.],[40.,0.]])])
    base=np.full((60,100,3),25,np.uint8)
    clean=paint_rigid(base,mask,'pavement',0,5,.1,field,5.,artistic=True)
    real=paint_rigid(base,mask,'pavement',0,5,.1,field,5.)
    np.testing.assert_array_equal(clean[~mask],base[~mask])
    assert clean[mask].mean()>real[mask].mean()+10
    assert clean[mask].max()-clean[mask].min()>10


def test_rock_and_concrete_are_distinct_in_3d_and_vectors(tmp_path):
    from app.scene3d import build
    from app.webmap import vectors
    cfg=project(tmp_path);(tmp_path/'config.json').write_text(cfg.model_dump_json());data=build(tmp_path,cfg)
    rock=next(m for m in data['meshes'] if m.get('asset_material')=='rock')
    soil=next(m for m in data['meshes'] if m.get('layer')=='CORTE SOLO')
    concrete=next(m for m in data['meshes'] if m.get('role')=='pavement')
    assert rock['color']=='#8a8781' and soil['color']!='#8a8781'
    assert concrete['asset_material']=='concrete' and concrete['color']=='#c2c2bb'
    items,axis,*_=analyze(tmp_path,cfg)
    records=vectors(items,axis,[])['layers']['cut']
    assert any(r.get('asset_material')=='rock' for r in records)


def test_concrete_and_rock_export_is_fully_decodable(tmp_path):
    import json
    from app.render import render
    cfg=project(tmp_path).model_copy(update={'width':1280,'fps':24,'encoder':'cpu','render_workers':1})
    output=render(tmp_path,cfg)
    report=json.loads((tmp_path/'video.json').read_text())
    assert output.is_file() and report['validation']['frames_decoded']==72
    assert report['validation']['ok']
