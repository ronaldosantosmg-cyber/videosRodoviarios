"""2.48: texturas com relevo iluminado — ancoradas no mundo (sem costura entre ladrilhos), determinísticas, só onde há máscara, sem estourar cores."""
import numpy as np
from app import relevo
COR={'pavement':(74,76,80),'existing_pavement':(111,130,145),'shoulder':(150,140,118),'median':(86,124,64),'terrain':(86,124,64),'fill':(84,128,62),'cut':(168,96,70),'oae':(182,183,178)}
def _a(role,x0,w,px=.2,h=100):return relevo.acabar(np.full((h,w,3),COR[role],np.uint8),role,x0,50.,px,seed=11)
def test_sem_costura_entre_ladrilhos_vizinhos():
    for role in COR:
        for px in (.2,.05):
            big=_a(role,100.,200,px);a=_a(role,100.,100,px);b=_a(role,100.+100*px,100,px)
            assert np.array_equal(big[:,:100],a) and np.array_equal(big[:,100:],b),(role,px)
def test_deterministico_e_cores_validas():
    for role in COR:
        a=_a(role,10.,64);assert a.dtype==np.uint8 and np.array_equal(a,_a(role,10.,64))
def test_tem_textura_e_mantem_a_cor_media():
    for role,c in COR.items():
        a=_a(role,10.,128,.1).astype(float);assert a.std(axis=(0,1)).mean()>1.5,role                  # não é cor chapada
        assert np.all(np.abs(a.mean(axis=(0,1))-np.array(c))<28),(role,a.mean(axis=(0,1)))              # e não muda a cor do material
def test_ancorada_no_mundo_deslocar_o_ladrilho_desloca_a_textura():
    a=_a('pavement',0.,200);b=_a('pavement',.2*20,180);assert np.array_equal(a[:,20:],b)
def test_papel_desconhecido_nao_muda():
    c=np.full((8,8,3),123,np.uint8);assert np.array_equal(relevo.acabar(c,'ignore',0.,0.,.2),c)
def test_blocos_igual_a_passo_unico_e_respeita_mascara():
    n=300;c=np.full((n,n,3),COR['pavement'],np.uint8);m=np.zeros((n,n),bool);m[40:200,30:260]=True
    ref=relevo.acabar(c,'pavement',500.,900.,.2,seed=11);o=relevo.acabar_blocos(c,m,'pavement',500.,900.,.2,seed=11)
    assert np.array_equal(o[m],ref[m])                       # dentro da máscara é idêntico ao passo único
    assert np.array_equal(o[256:,:],c[256:,:])             # bloco sem nenhum pixel de máscara fica intacto

def test_modelo_tem_o_campo():
    from app.models import Settings
    assert Settings().texture_relief is True and Settings(texture_relief=False).texture_relief is False

# ---- 2.49: pavimento rígido × flexível, novo × existente ----
def _p(role,rig,px=.1,n=200,x0=300.):
    cor={'pavement':{False:(48,50,54),True:(190,190,184)},'existing_pavement':{False:(111,130,145),True:(170,170,164)}}[role][rig]
    return relevo.acabar(np.full((n,n,3),cor,np.uint8),role,x0,900.,px,seed=11,rigido=rig).astype(float)
def test_quatro_tipos_de_pavimento_tem_texturas_distintas():
    t={(r,g):_p(r,g) for r in('pavement','existing_pavement') for g in(False,True)}
    ks=list(t)
    for i in range(4):
        for j in range(i+1,4):
            a,b=t[ks[i]],t[ks[j]];assert np.abs((a-a.mean((0,1)))-(b-b.mean((0,1)))).mean()>1.0,(ks[i],ks[j])
def test_existente_e_mais_irregular_que_novo():
    for rig in(False,True):
        assert _p('existing_pavement',rig,.1,300).std(axis=(0,1)).mean()>_p('pavement',rig,.1,300).std(axis=(0,1)).mean()*1.1,rig
def test_rigido_sem_costura_e_deterministico():
    for role in('pavement','existing_pavement'):
        big=relevo.acabar(np.full((100,200,3),(170,170,164),np.uint8),role,100.,50.,.2,seed=11,rigido=True)
        a=relevo.acabar(np.full((100,100,3),(170,170,164),np.uint8),role,100.,50.,.2,seed=11,rigido=True);b=relevo.acabar(np.full((100,100,3),(170,170,164),np.uint8),role,120.,50.,.2,seed=11,rigido=True)
        assert np.array_equal(big[:,:100],a) and np.array_equal(big[:,100:],b)
def test_misto_aplica_cada_material_na_sua_regiao():
    n=256;c=np.full((n,n,3),(120,120,118),np.uint8);m=np.ones((n,n),np.uint8)*255;r=np.zeros((n,n),np.uint8);r[:,128:]=255
    o=relevo.acabar_misto(c,m>0,r,'existing_pavement',300.,900.,.1);f=relevo.acabar(c,'existing_pavement',300.,900.,.1,seed=11);g=relevo.acabar(c,'existing_pavement',300.,900.,.1,seed=11,rigido=True)
    assert np.array_equal(o[:,:128],f[:,:128]) and np.array_equal(o[:,128:],g[:,128:])
def test_misto_sem_rigido_igual_a_flexivel():
    c=np.full((64,64,3),(60,60,60),np.uint8);o=relevo.acabar_misto(c,np.ones((64,64),bool),None,'pavement',300.,900.,.2)
    assert np.array_equal(o,relevo.acabar(c,'pavement',300.,900.,.2,seed=11))
def test_barreira_e_acostamento_rigido_tem_relevo():
    assert 'barrier' in relevo.MATERIAIS and 'shoulder' in relevo.RIGIDOS

# ---- 2.50: OAE, água e vegetação ----
def test_oae_tres_tipos_distintos_e_sem_costura():
    c={'nova':(156,158,154),'existente':(128,130,126),'alargada':(146,143,132)};t={}
    for k,cor in c.items():
        big=relevo.acabar_oae(np.full((120,240,3),cor,np.uint8),np.ones((120,240),bool),k,100.,50.,.1)
        a=relevo.acabar_oae(np.full((120,120,3),cor,np.uint8),np.ones((120,120),bool),k,100.,50.,.1);b=relevo.acabar_oae(np.full((120,120,3),cor,np.uint8),np.ones((120,120),bool),k,112.,50.,.1)
        assert np.array_equal(big[:,:120],a) and np.array_equal(big[:,120:],b),k;t[k]=big.astype(float)
    assert t['existente'].std()>t['nova'].std()
    assert np.abs(t['nova']-t['existente']).mean()>1.5 and np.abs(t['alargada']-t['existente']).mean()>1.5
def _wp(x0=500000.,y1=7800000.,R=.25):return (lambda p:np.column_stack([(np.asarray(p)[:,0]-x0)/R,(y1-np.asarray(p)[:,1])/R]))
def test_agua_sem_costura_entre_ladrilhos_e_so_na_mascara():
    R=.25;n=200;wpB=_wp(R=R);wpL=_wp(500000.,7800000.,R);wpR=_wp(500000.+100*R,7800000.,R)
    big=np.full((n,2*100,3),(86,120,66),np.uint8);mb=np.zeros((n,200),np.uint8);mb[40:160,:]=255;relevo.agua(big,mb,wpB,R,.9)
    L=np.full((n,100,3),(86,120,66),np.uint8);ml=np.zeros((n,100),np.uint8);ml[40:160,:]=255
    # origem do ladrilho direito deslocada 100 px: a textura deve coincidir com o mosaico inteiro longe da borda de máscara
    Rr=np.full((n,100,3),(86,120,66),np.uint8);relevo.agua(Rr,ml,wpR,R,.9)
    assert np.abs(big[90:110,110:190].astype(int)-Rr[90:110,10:90].astype(int)).max()<=3
    assert (big[:30]==(86,120,66)).all()                       # fora da máscara nada muda
def test_agua_azulada_e_mais_escura_no_fundo():
    R=.25;img=np.full((300,300,3),(86,120,66),np.uint8);m=np.zeros((300,300),np.uint8);m[20:280,20:280]=255;relevo.agua(img,m,_wp(R=R),R,1.0)
    assert img[150,150,2]>img[150,150,0] and img[150,150].sum()<img[25,150].sum()+40
def test_copa_determinismo_cache_e_limites():
    relevo._COPAS.clear();a=relevo.copa_cache(20,20,(58,104,48),(34,66,30),(104,150,74),.3,.7);b=relevo.copa_cache(20,20,(58,104,48),(34,66,30),(104,150,74),.3,.7)
    assert a is b and len(relevo._COPAS)==1 and a.shape[2]==4
    h,w=a.shape[:2];ys,xs=np.nonzero(a[...,3]>40);assert (xs.max()-xs.min()+1)<=w and (xs.max()-xs.min()+1)>=w*.7 and (ys.max()-ys.min()+1)>=h*.7
    assert a[...,3].max()==255 and a[0,0,3]==0                              # cantos transparentes
    c=relevo.copa(20,20,(58,104,48),(34,66,30),(104,150,74),.3,.7);assert np.array_equal(c,relevo.copa(20,20,(58,104,48),(34,66,30),(104,150,74),.3,.7))
def test_copa_lado_do_sol_mais_claro():
    for ang,sinal in ((0.,1),(np.pi,-1)):
        s=relevo.copa(24,24,(58,104,48),(34,66,30),(104,150,74),.4,ang);m=s[...,3]>200;lum=s[...,:3].mean(2);W=s.shape[1];xs=np.nonzero(m)[1]
        d=lum[m][xs>W/2].mean()-lum[m][xs<=W/2].mean();assert d*sinal>0,(ang,d)
def test_blit_copa_nas_bordas_nao_quebra():
    im=np.full((50,50,3),90,np.uint8);sp=relevo.copa(20,20,(58,104,48),(34,66,30),(104,150,74),.4,.5)
    for c in ((0,0),(49,49),(-30,-30),(80,10),(25,25)):relevo.blit_copa(im,c[0],c[1],sp)
