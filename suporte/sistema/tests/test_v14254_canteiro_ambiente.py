"""2.28: canteiro com relevo iluminado pelo sol e clima; asfalto novo (CBUQ) e OAE."""
import numpy as np
from app import visual

def _grama(sol,m=.02):
    im=np.full((96,96,3),(112,142,92),np.uint8);surf=np.full((96,96),5,np.uint8);v=np.ones((96,96),bool)
    A=np.array([[m,0,700000.],[0,-m,7800000.]]);visual.shade_surface(im,surf,A,m,v,True,sol=sol);return im.astype(float)

def test_sol_muda_o_relevo_e_a_cor_do_canteiro():
    meio=_grama({'az':180,'el':70,'weather':'limpo','k':.6,'sun':True})
    manha=_grama({'az':80,'el':12,'weather':'limpo','k':.6,'sun':True})
    assert np.abs(meio-manha).mean()>3                 # posição/altura do sol alteram a imagem
    assert manha[:,:,0].mean()/manha[:,:,2].mean()>meio[:,:,0].mean()/meio[:,:,2].mean()   # sol baixo: luz mais quente
    assert manha.mean()<meio.mean()                    # e mais escura

def test_clima_responde_no_canteiro():
    base=dict(az=250,el=50,k=.8,sun=True)
    limpo=_grama({**base,'weather':'limpo'});chuva=_grama({**base,'weather':'chuva'});nub=_grama({**base,'weather':'nublado'})
    assert chuva.mean()<limpo.mean()                    # grama molhada mais escura
    assert nub.std()<limpo.std()                        # nublado: luz difusa, menos contraste de relevo

def test_ancorado_no_terreno_e_sem_sol_continua_funcionando():
    a=_grama(None);assert a.shape==(96,96,3) and a.std()>1
    s={'az':200,'el':50,'weather':'limpo','k':.6,'sun':True}
    x=_grama(s);y=_grama(s);assert np.array_equal(x,y)   # determinístico

def test_cbuq_novo_tem_agregado_claro_sobre_ligante_escuro():
    im=np.full((120,120,3),(58,60,63),np.uint8);surf=np.ones((120,120),np.uint8);v=np.ones((120,120),bool)
    m=.02;A=np.array([[m,0,700000.],[0,-m,7800000.]]);visual.shade_surface(im,surf,A,m,v,True)
    g=im.astype(float).mean(2);assert g.max()-np.median(g)>12   # pontos minerais claros acima do fundo
    assert abs(g[:60].mean()-g[60:].mean())<6                  # tom uniforme (sem manchas grandes)
