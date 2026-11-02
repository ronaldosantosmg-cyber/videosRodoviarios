"""2.48: o desenho novo dos veículos é SÓ aparência — mesma pegada L×B, mesma posição e mesmo rumo do cálculo; falha no sprite nunca derruba o vídeo."""
import math
import numpy as np
from app import visual,sprites_veiculos as SV
from app.visual import TYPES,vehicle_color,FROTA_BR
from app.vehicle_motion import PROFILES
TODOS=['car','pickup','van','moto','truck','bus','carreta']+[x[0] for x in FROTA_BR]
FUNDO=np.array([90,90,90],np.uint8)

def _desenha(k,ang=0.,S=40.,flip=False,centro=(300.,200.),tam=(600,400),cor=None):
    im=np.full((tam[1],tam[0],3),FUNDO,np.uint8);t=np.array([math.cos(ang),math.sin(ang)]);pt=np.array([2.0,-1.0])
    def screen(P):
        P=np.asarray(P,float);Q=(P-pt)*S*np.array([1.,-1. if flip else 1.])+np.array(centro);return Q
    visual.draw_vehicle(im,pt,t,k,(cor or vehicle_color((1,2,0),k)),screen,1/S,shadow_layer=np.zeros(im.shape[:2],np.uint8))
    return im,screen,pt,t
def _pixels(im):return np.argwhere((im!=FUNDO).any(2))

def test_pegada_cabe_em_LxB_para_todas_as_classes():
    for k in TODOS:
        L,B=TYPES[k]['L'],TYPES[k]['B'];sp,b=SV.obter(k,TYPES[k].get('style',k),vehicle_color((1,2,0),k),L,B,40.)
        assert sp is not None,k
        ys,xs=np.nonzero(sp[...,3]>40);w=(xs.max()-xs.min()+1)/b;h=(ys.max()-ys.min()+1)/b
        assert w<=L+.06 and h<=B+.06,(k,w,h,L,B)          # nunca maior que a pegada real
        assert w>=L*.93 and h>=B*.80,(k,w,h,L,B)          # e preenche quase toda ela
def test_posicao_e_rumo_corretos_inclusive_com_tela_espelhada():
    for flip in (False,True):
        for ang in (0.,.6,1.9,-2.4):
            for k in ('sedan','toco','carreta'):
                im,screen,pt,t=_desenha(k,ang,S=22.,flip=flip,centro=(600.,400.),tam=(1200,800));px=_pixels(im);assert len(px)>200
                P=px[:,::-1].astype(float);esp=screen(pt[None])[0];alvo=screen((pt+t)[None])[0]-esp;S_=np.linalg.norm(alvo);alvo/=S_;lat=np.array([-alvo[1],alvo[0]])
                for eixo_,tam in ((alvo,TYPES[k]['L']),(lat,TYPES[k]['B'])):
                    pr=(P-esp)@eixo_;meio=(pr.max()+pr.min())/2;assert abs(meio)<1.2,(k,ang,flip,meio)      # a pegada está centrada no ponto do veículo
                cen=P.mean(0)
                c=np.cov((px[:,::-1]-cen).T);w,v=np.linalg.eigh(c);eixo=v[:,1];alvo=screen((pt+t)[None])[0]-esp;alvo/=np.linalg.norm(alvo)
                assert abs(float(eixo@alvo))>.985,(k,ang,flip,eixo,alvo)                        # eixo principal alinhado ao rumo
def test_frente_e_traseira_nao_trocadas():
    im,screen,pt,t=_desenha('sedan',0.,cor=(40,70,200));esp=screen(pt[None])[0];px=_pixels(im)[:,::-1]
    luz=px[(im[px[:,1],px[:,0]].astype(int)[:,0]>225)&(im[px[:,1],px[:,0]].astype(int)[:,2]>225)]
    ver=px[(im[px[:,1],px[:,0]].astype(int)[:,0]>150)&(im[px[:,1],px[:,0]].astype(int)[:,1]<60)]
    assert len(luz) and luz[:,0].mean()>esp[0] and len(ver) and ver[:,0].mean()<esp[0]      # faróis à frente (+x), lanternas atrás
def test_mesma_pegada_em_escalas_diferentes():
    for S in (8.,16.,40.,90.):
        im,screen,pt,t=_desenha('onibus13',0.,S=S,tam=(1600,500),centro=(800,250));px=_pixels(im);ext=(px[:,1].max()-px[:,1].min()+1)/S
        assert abs(ext-TYPES['onibus13']['L'])<max(.35,2/S),(S,ext)
def test_dimensoes_dos_calculos_intactas():
    for k,(L,B,wb,_) in PROFILES.items():
        if k in TYPES:assert abs(TYPES[k]['L']-L)<1e-9 and abs(TYPES[k]['B']-B)<1e-9,k
def test_falha_no_sprite_cai_no_desenho_simples(monkeypatch):
    monkeypatch.setattr(SV,'_desenha',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('x')))
    SV._CACHE.clear();im,_,_,_=_desenha('hatch',0.);assert len(_pixels(im))>200
    SV._CACHE.clear()
def test_cache_reutiliza_e_cores_diferentes_geram_sprites_diferentes():
    SV._CACHE.clear();a,_=SV.obter('sedan','car',(200,30,30),4.6,1.8,40.);b,_=SV.obter('sedan','car',(200,30,30),4.6,1.8,40.);c,_=SV.obter('sedan','car',(30,30,200),4.6,1.8,40.)
    assert a is b and a is not c and len(SV._CACHE)==2
def test_desenho_muito_pequeno_usa_o_simples():
    im=np.full((60,60,3),FUNDO,np.uint8);assert SV.blit(im,np.array([0,0.]),np.array([1,0.]),'hatch','car',(200,30,30),lambda P:np.asarray(P)*1.+30,1.0,3.95,1.68) is False
