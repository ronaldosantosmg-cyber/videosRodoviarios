from types import SimpleNamespace as S
import numpy as np
from app import visual
from app.models import Settings
from app.presentation import palette


def test_artistic_does_not_apply_realistic_cracks_or_repairs(monkeypatch):
    def forbidden(*a,**kw):raise AssertionError('Desgaste realista aplicado ao artístico')
    monkeypatch.setattr(visual,'shade_realistic',forbidden)
    monkeypatch.setattr(visual,'cracks',forbidden)
    im=np.full((100,120,3),86,np.uint8);surf=np.full(im.shape[:2],2,np.uint8)
    visual.shade_style(im,surf,np.array([[.02,0,730000.],[0,-.02,7830000.]]),.02,np.ones(surf.shape,bool),Settings())
    assert im.std()>0 and np.isfinite(im).all()


def test_realistic_is_a_separate_path_and_keeps_weathering(monkeypatch):
    calls=[]
    monkeypatch.setattr(visual,'shade_realistic',lambda *a,**kw:calls.append('realistic'))
    monkeypatch.setattr(visual,'shade_artistic',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Estilos misturados')))
    im=np.full((8,8,3),86,np.uint8);surf=np.full((8,8),2,np.uint8)
    visual.shade_style(im,surf,np.array([[.02,0,0],[0,-.02,0]]),.02,np.ones((8,8),bool),Settings(texture_style='realistic'))
    assert calls==['realistic']
    assert palette(Settings())['existing_pavement']!=palette(Settings(texture_style='realistic'))['existing_pavement']


def test_artistic_grassy_cut_and_fill_preserve_colors_and_holes():
    im=np.full((90,120,3),17,np.uint8);surf=np.zeros((90,120),np.uint8)
    surf[5:85,5:55]=6;surf[5:85,65:115]=7;surf[35:55,20:40]=0
    im[surf==6]=[183,105,84];im[surf==7]=[156,189,117];before=im.copy()
    visual.shade_style(im,surf,np.array([[.03,0,730000],[0,-.03,7830000]]),.03,surf>0,Settings())
    np.testing.assert_array_equal(im[surf==0],before[surf==0])
    cut=im[surf==6].mean(0);fill=im[surf==7].mean(0)
    assert cut[0]>cut[1]>cut[2] and fill[1]>fill[0]>fill[2]
    assert im[surf==6].std(0).max()>0 and im[surf==7].std(0).max()>0


def test_artistic_signage_stays_clean_and_realistic_relief_is_optional():
    from app.render import Scene
    assert not Scene._tinta_on(S(s=Settings()))
    assert Scene._tinta_on(S(s=Settings(texture_style='realistic')))


def test_artistic_earthwork_keeps_outline_and_holes_without_dxf_offset_strokes():
    from app.earthworks import earthwork_style
    mask=np.zeros((40,50),np.uint8);mask[3:37,3:47]=255;mask[15:25,20:30]=0
    lines=np.zeros_like(mask);lines[10,:]=255;lines[:,12]=255
    color,alpha=earthwork_style(mask,lines,'cut',.1,look='natural',artistic=True)
    assert np.all(alpha[mask==0]==0)
    np.testing.assert_array_equal(color[10,30],color[11,30])
    assert alpha[10,30]==255


def test_switching_style_uses_distinct_surface_and_detail_caches(tmp_path):
    from app.render import Scene
    from test_traffic_pipeline import project
    cfg=project(tmp_path).model_copy(update={'imagery_pixels':2048,'traffic':False,'natural_materials_only':False})
    art=Scene(tmp_path,cfg)
    art_key=art.geometry_signature;detail_key=art.detail.key
    assert art.color('existing_pavement')=='#565b60'
    real=Scene(tmp_path,cfg.model_copy(update={'texture_style':'realistic'}))
    assert real.geometry_signature!=art_key and real.detail.key!=detail_key
    assert real.color('existing_pavement')=='#858279'
    restored=Scene(tmp_path,cfg)
    assert restored.geometry_signature==art_key and restored.geometry_cache_hit
