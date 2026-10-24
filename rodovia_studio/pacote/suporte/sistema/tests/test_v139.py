"""1.39: bordas sem dados começam só no branco 255 / preto 0 ligados à beira da imagem."""
import numpy as np,cv2
from test_workflow import settings
from test_v117 import ortho,write_geotiff,X0,Y1,PX,W,H
from app.models import Settings,LocalImagery

def montar(tmp_path,a,nodata):
    from app.local_tiles import LocalMosaic
    d=tmp_path;(d/'imagem_local').mkdir(exist_ok=True)
    write_geotiff(d/'imagem_local'/'a.tif',a)
    s=Settings(**{**settings().model_dump(),'local_imagery':LocalImagery(name='a',image='a.tif',nodata=nodata).model_dump()})
    return LocalMosaic(d,s)

def amostra(m,col,row,n=40,r=1.0):
    x=X0+col*PX;y=Y1-row*PX
    return m.sample_box([x-r,y-r,x+r,y+r],n,n)

def imagem():
    a=ortho()
    a[:,:300]=255                          # colar branco puro à esquerda (sem dados)
    a[:,300:340]=254                       # faixa 254 colada ao colar: já é imagem
    a[:150,:]=0                            # colar preto puro no topo
    a[600:700,1500:1700]=255               # telhado branco puro no meio da imagem
    a[800:820,900:1600]=(253,253,253)      # pintura quase branca no meio
    return a

def test_borda_so_255_ligado_a_beira(tmp_path):
    m=montar(tmp_path,imagem(),'borda')
    assert amostra(m,150,600)[:,:,3].max()==0            # colar branco: transparente
    assert amostra(m,1200,70)[:,:,3].max()==0            # colar preto: transparente
    assert amostra(m,1600,650)[:,:,3].min()==255         # telhado 255 no meio: imagem
    assert amostra(m,1250,810,r=.4)[:,:,3].min()==255    # 253 no meio: imagem
    f=amostra(m,320,600,n=40,r=.5)                       # faixa 254 junto do colar: imagem
    assert f[:,:,3].min()==255 and f[:,:,:3].min()>=250

def test_anterior_e_manter(tmp_path):
    a=imagem()
    m=montar(tmp_path,a,'auto')
    assert amostra(m,1600,650)[:,:,3].max()==0           # anterior furava o telhado
    assert amostra(m,1250,810,r=.4)[:,:,3].max()==0
    m2=montar(tmp_path/'x' if (tmp_path/'x').mkdir() is None else tmp_path,a,'none')
    assert amostra(m2,150,600)[:,:,3].min()==255

def test_nd_exact_16_bits_e_migracao():
    from app.local_tiles import nd_exact
    from app.migration import migrate
    a=np.zeros((2,2,3),np.uint16);a[0,0]=65535;a[0,1]=65534;a[1,0]=(0,0,1)
    assert nd_exact(a).tolist()==[[True,False],[False,True]]
    d=migrate({'schema_version':29,'local_imagery':{'image':'a.tif','nodata':'auto','others':[{'image':'b.tif','nodata':'none'},{'image':'c.tif'}]}})
    li=d['local_imagery'];assert li['nodata']=='borda' and li['others'][0]['nodata']=='none' and li['others'][1]['nodata']=='borda'

def zig_net(m):
    from shapely.geometry import box
    from app.traffic import TrafficNetwork
    axis=np.array([[0.,0.],[400.,0.]]);ds=np.array([0.,400.])
    A=np.array([[0.,0.],[180.,0.]]);Z=np.array([[183.,0.],[193.,6.],[203.,0.]]);B=np.array([[206.,0.],[400.,0.]])
    s=Settings(derive_traffic_paths=False,hydrography=False,min_route_segment_m=m,median_crossing='free',route_directions={'0':'forward','1':'forward','2':'forward'})
    return TrafficNetwork([box(0,-9,400,11)],[],[{'points':A},{'points':Z},{'points':B}],axis,ds,s)

def desvio(n):
    return max(float(np.ptp(p['p'][:,1])) for p in n.paths)   # oscilação lateral do veículo (m)

def test_trecho_curto_nao_faz_ziguezague():
    antes=zig_net(0)
    assert not antes.paths or desvio(antes)<.05  # auditoria cinemática também protege com o filtro de 50 m desligado
    n=zig_net(50)
    assert not n.paths or desvio(n)<.05  # nenhuma rota insegura pode receber veículos
    assert n.rejected_connectors or n.rejected_paths
    assert n.short_ignored and any('curto' in w for w in n.warnings)
    assert all(not set(p['edges'])&n.short_ignored for p in n.paths)
    # as ligações e a pintura da rede não mudam (o atalho é só da rota)
    assert set(n.connectors)==set(antes.connectors)
