import numpy as np
from app import relevo
from app.structures import draw_structure,bridge_geometry
from app.models import POI

def _scr(ppm=8):return lambda p:np.asarray(p,float)*ppm+[400,300]

def _passarela(acc='ramps',real=True,ppm=8):
    im=np.full((600,800,3),(70,72,70),np.uint8)
    p=POI(title='P',kind='passarela',x=0,y=0,bridge_access=acc).model_dump()
    a=draw_structure(im,p,np.array([1.,0.]),_scr(ppm),ppm,realista=real);return im,a

def test_anchor_igual_ao_desenho_simples():
    _,a=_passarela(real=True);_,b=_passarela(real=False)
    assert np.allclose(a,b)

def test_realista_deterministico_e_visivel():
    a,_=_passarela();b,_=_passarela()
    assert np.array_equal(a,b)
    base=np.full((600,800,3),(70,72,70),np.uint8)
    assert np.any(np.any(a!=base,axis=2)) and (a!=base).any(axis=2).sum()>5000

def test_deck_claro_e_texturizado():
    im,_=_passarela()
    g=bridge_geometry(np.array([0.,0.]),np.array([1.,0.]),POI(title='P',kind='passarela',x=0,y=0).model_dump())
    q=np.rint(_scr()(g['center'])).astype(int)
    patch=im[q[1]-6:q[1]+6,q[0]-6:q[0]+6].reshape(-1,3).astype(float)
    assert patch.mean()>130 and patch.std(axis=0).mean()>0.5   # concreto claro com variação

def test_escada_e_rampa_nao_quebram():
    for acc in('ramps','stairs','none'):
        im,a=_passarela(acc);assert np.isfinite(a).all() and im.dtype==np.uint8

def test_tinta_so_altera_onde_pintou():
    im=np.full((200,300,3),(60,60,60),np.uint8);pre=im.copy();im[90:100,:]=(240,240,240)
    A=np.array([[.1,0,0],[0,-.1,20.]]);out=relevo.tinta(im.copy(),pre,A,.1)
    assert np.array_equal(out[:80],pre[:80]) and np.array_equal(out[110:],pre[110:])
    assert out[90:100].mean()>150 and out[90:100].mean()<=240.5
    assert np.array_equal(out,relevo.tinta(im.copy(),pre,A,.1))

def test_tinta_sem_pintura_nao_muda():
    im=np.full((50,50,3),90,np.uint8);assert np.array_equal(relevo.tinta(im.copy(),im.copy(),np.array([[.1,0,0],[0,-.1,5.]]),.1),im)

def test_tinta_ancorada_no_mundo():
    # mesma região do mundo em duas janelas diferentes → mesmo padrão de desgaste
    def run(dx):
        im=np.full((60,200,3),50,np.uint8);pre=im.copy();im[:,:]=(230,230,230)
        A=np.array([[.05,0,dx*.05],[0,-.05,3.]]);return relevo.tinta(im,pre,A,.05)
    a=run(0);b=run(20)
    assert np.abs(a[:,20:200].astype(int)-b[:,:180].astype(int)).max()<=2

def test_tinta_mais_clara_que_asfalto():
    im=np.full((100,100,3),55,np.uint8);pre=im.copy();im[40:60,:]=(238,238,230)
    out=relevo.tinta(im,pre,np.array([[.2,0,0],[0,-.2,20.]]),.2)
    assert out[40:60].mean()>out[:30].mean()+100

def test_postes_opcionais_nas_rampas():
    from app.structures import poste_pontos
    g=bridge_geometry(np.array([0.,0.]),np.array([1.,0.]),POI(title='P',kind='passarela',x=0,y=0).model_dump())
    assert poste_pontos(g,'none')==[]
    L=poste_pontos(g,'landings');B=poste_pontos(g,'both')
    assert len(L)==8 and len(B)==12
    # nenhum poste dentro da laje da rampa (distância ao eixo do lance ≥ meia largura)
    for pt,_ in L:
        d=min(np.min(np.linalg.norm(np.linspace(a,b,200)-pt,axis=1)) for path in g['ramps'] for a,b in zip(path[:-1],path[1:]))
        assert d>=g['width']/2-1e-6
    a,_=_passarela(real=True);base=np.full((600,800,3),(70,72,70),np.uint8)
    p=POI(title='P',kind='passarela',x=0,y=0,bridge_poles='landings').model_dump()
    im=base.copy();draw_structure(im,p,np.array([1.,0.]),_scr(),8,realista=True)
    assert not np.array_equal(im,a)
    im2=base.copy();draw_structure(im2,p,np.array([1.,0.]),_scr(),8,realista=False);assert im2.any()

def test_modelo_aceita_bridge_poles():
    assert POI(title='P',kind='passarela',x=0,y=0).bridge_poles=='none'
    assert POI(title='P',kind='passarela',x=0,y=0,bridge_poles='both').bridge_poles=='both'

def test_graos_preservam_tom_medio_e_sao_deterministicos():
    c=np.full((200,200,3),70.,np.float64);m=.003
    X,Y=np.meshgrid((np.arange(200)+.5)*m,(np.arange(200)+.5)*m)
    a=relevo._graos(c,X,Y,m,5);b=relevo._graos(c,X,Y,m,5)
    assert np.array_equal(a,b) and a.std()>3                     # aparecem grãos
    assert abs(a.mean()/70-1)<.06                                # tom médio preservado
    far=relevo._graos(c,X,Y,.02,5);assert np.array_equal(far,c)  # longe: nada (sem cintilação)

def test_craquele_so_de_perto_e_nao_vaza_para_fora_da_tinta():
    m=.003;im=np.full((120,120,3),60,np.uint8);pre=im.copy();im[:,40:80]=(230,230,225)
    A=np.array([[m,0,0],[0,-m,.4]]);o=relevo.tinta(im.copy(),pre,A,m,.4)
    assert np.array_equal(o[:,:40],pre[:,:40]) and np.array_equal(o[:,80:],pre[:,80:])
    assert (o[:,40:80].astype(int).std()>8)                       # placas/furos visíveis
