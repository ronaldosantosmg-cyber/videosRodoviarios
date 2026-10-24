"""1.16: texturas realistas (agregado, remendos, fissuras, trilhas de roda), taludes com aparência de
terreno, cor da imagem detalhada casada com o mosaico e detalhe a 0,1 m; modo anterior igual à 1.15."""
import numpy as np,cv2,ezdxf,pytest
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,'traffic':False,**kw})

@pytest.fixture
def mixed(tmp_path):
    """Pista existente (larga) ao lado da projetada, com talude de corte e de aterro."""
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO','PAVIMENTO_EXISTENTE','CORTE','ATERRO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
    def hatch(layer,pts):h=m.add_hatch(dxfattribs={'layer':layer});h.paths.add_polyline_path(pts,is_closed=True)
    hatch('PAVIMENTO',[(500000,7799996),(500300,7799996),(500300,7800004),(500000,7800004)])
    hatch('PAVIMENTO_EXISTENTE',[(500000,7800006),(500300,7800006),(500300,7800014),(500000,7800014)])
    hatch('CORTE',[(500000,7800016),(500300,7800016),(500300,7800030),(500000,7800030)])
    hatch('ATERRO',[(500000,7799970),(500300,7799970),(500300,7799994),(500000,7799994)])
    d.saveas(tmp_path/'input.dxf');return tmp_path

def region(sc,v,p0,p1):
    a=sc.screen(np.array([p0,p1]),np.array(v[0]),v[1]).astype(int);x0,x1=sorted(a[:,0]);y0,y1=sorted(a[:,1])
    return slice(y0,y1),slice(x0,x1)

def hf(a):return float(np.abs(cv2.Laplacian(cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(np.float32),cv2.CV_32F)).mean())

def test_realistic_textures_only_on_surfaces(mixed):
    from app.render import Scene
    v=((500150,7800005),40)
    a=Scene(mixed,S(texture_style='anterior')).frame(0,view=v)[0];b=Scene(mixed,S()).frame(0,view=v)[0]
    sc=Scene(mixed,S());ex=region(sc,v,(500140,7800007),(500160,7800013))
    assert hf(b[ex])>hf(a[ex])*1.15            # pista existente: agregado, remendos e fissuras
    v2=((500298,7800005),40);a2=Scene(mixed,S(texture_style='anterior')).frame(0,view=v2)[0];b2=Scene(mixed,S()).frame(0,view=v2)[0]
    gr=region(sc,v2,(500303,7799999),(500312,7800011))
    assert np.array_equal(a2[gr],b2[gr])        # fora das superfícies: nada muda
    assert abs(float(b[ex].mean())-float(a[ex].mean()))<12   # sem mudar o tom geral

def test_wheel_paths_on_existing_pavement_detail(mixed):
    from app.render import Scene
    sc=Scene(mixed,S(traffic=True));det=sc.detail
    i=int((500150-det.x0)//(1024*det.R));j=int((det.y1-7800010)//(1024*det.R))
    ov,surf=det.overlay_tile(i,j)
    assert (surf==8).any() and (surf==2).any()
    wp=det.worldpx(i,j);ys,xs=np.nonzero(surf==8);w=np.column_stack([det.x0+i*1024*det.R+xs*det.R,det.y1-j*1024*det.R-ys*det.R])
    assert (w[:,1]>7800005.9).all() and (w[:,1]<7800014.1).all()   # só na pista existente
    anterior=Scene(mixed,S(traffic=True,texture_style='anterior')).detail.overlay_tile(i,j)[1];assert not (anterior==8).any()

def test_natural_earthworks(mixed):
    from app.render import Scene
    from app.earthworks import earthwork_style
    mask=np.zeros((60,60),np.uint8);mask[10:50,10:50]=255;lines=np.zeros_like(mask)
    c,a=earthwork_style(mask,lines,'cut',.2,look='natural');inner=a[15:45,15:45]
    assert inner.min()==inner.max()>0                                  # sem listras
    assert c[30,30,0]>c[30,30,2] and abs(int(c[30,30,0])-int(c[30,30,1]))<60  # solo
    c2,_=earthwork_style(mask,lines,'fill',.2,look='natural');assert c2[30,30,1]>c2[30,30,0]
    h,_=earthwork_style(mask,lines,'cut',.2);assert h[30,30,0]==224          # hachura padrão inalterada
    v=((500150,7800020),70);sc=Scene(mixed,S(earthwork_look='natural'));im=sc.frame(0,view=v)[0]
    hatch=Scene(mixed,S()).frame(0,view=v)[0]
    r=region(sc,v,(500140,7800018),(500160,7800028))
    red=lambda x:float(((x[:,:,0].astype(int)-x[:,:,1])>70).mean())
    assert red(hatch[r])>.1 and red(im[r])<.05

def test_detail_color_matches_base_mosaic(junction):
    from app.render import Scene
    sc=Scene(junction,S(imagery='neutral'))
    sc.s=sc.s.model_copy(update={'imagery':'esri'})  # simula mosaico de imagem real
    sc.map=np.full_like(np.asarray(sc.map),(90,120,80))
    det=sc.detail;img=np.full((1024,1024,3),(150,150,150),np.uint8)
    out=det.match_base(img,0,0);m=out.reshape(-1,3).mean(0)
    assert np.allclose(m,(90*1,120,80),atol=12) or np.allclose(m,(105,105,105),atol=60)
    assert np.abs(m-np.array([90,120,80])).max()<np.abs(np.array([150,150,150])-np.array([90,120,80])).max()
    # Fundo neutro: sem ajuste.
    sc2=Scene(junction,S(imagery='neutral'));assert np.array_equal(sc2.detail.match_base(img,0,0),img)

def test_detail_resolution_01(junction):
    from app.render import Scene
    a=Scene(junction,S());b=Scene(junction,S(detail_resolution_m=0.1))
    assert b.detail.R==.1 and a.detail.key!=b.detail.key
    x0,y0,x1,y1=b.detail.tile_box(0,0);assert abs((x1-x0)-102.4)<1e-6
    v=((500150,7800009),30);im=b.frame(0,view=v)[0];assert im.shape==(b.H,b.W,3)
    def blur_px(sc):
        al=sc.detail.compose(np.array(v[0]),v[1],False,True)[2][:,:,3].astype(int)
        col=al[:,sc.W//2];return int(((col>40)&(col<215)).sum())
    assert blur_px(b)<blur_px(a)   # borda do pavimento mais nítida a 0,1 m

def test_schema_v15():
    s=Settings.model_validate({'schema_version':14,'km_start_m':0,'km_end_m':100})
    assert s.schema_version>=15 and s.texture_style=='realistic' and s.earthwork_look=='hatch' and s.detail_resolution_m==.2
