"""1.36: clima (nublado, chuva, neblina), sombras pela hora do sol, antes/depois e câmera por pontos-chave.
Tudo desligado por padrão: vídeo idêntico ao anterior."""
import numpy as np,pytest
from test_v116 import S  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_sol():
    from app.ambiente import sol,vetor_sombra
    az,el=sol(12);assert az==0 and abs(el-70)<1e-9
    assert sol(6)[0]==90 and sol(18)[0]==270 and sol(7)[1]<25
    v7,v12,v17=vetor_sombra(7),vetor_sombra(12),vetor_sombra(17)
    assert v7[0]<-1 and v17[0]>1 and abs(v12[0])<1e-9 and v12[1]<0 and np.linalg.norm(v7)>5*np.linalg.norm(v12)   # manhã: sombra longa a oeste; meio-dia: curta, ao sul

def test_padrao_identico(junction):
    from app.render import Scene
    from app.models import Settings
    s=Settings();assert (s.weather,s.sun_shadows,s.before_after,s.camera_mode)==('limpo',False,False,'obras')
    v=((500200,7800000),120);a=Scene(junction,S(traffic=True)).frame(3,view=v)[0];b=Scene(junction,S(traffic=True,weather='limpo',sun_hour=7)).frame(3,view=v)[0]
    assert np.array_equal(a,b)                       # hora do sol sem “sombras pelo sol” não muda nada

def test_clima(junction):
    from app.render import Scene
    v=((500200,7800000),120);base=Scene(junction,S()).frame(3,view=v)[0].astype(float)
    nub=Scene(junction,S(weather='nublado')).frame(3,view=v)[0].astype(float)
    sat=lambda a:float((a.max(2)-a.min(2))[200:500].mean())
    assert sat(nub)<sat(base) and nub[200:500].mean()<base[200:500].mean()
    nev=Scene(junction,S(weather='neblina',weather_intensity=1)).frame(3,view=v)[0].astype(float);assert nev[200:500].std()<base[200:500].std()*.8
    sc=Scene(junction,S(weather='chuva',weather_intensity=1));c1=sc.frame(3,view=v)[0];c2=sc.frame(3.5,view=v)[0];c1b=sc.frame(3,view=v)[0]
    assert np.array_equal(c1,c1b) and not np.array_equal(c1,c2)   # gotas determinísticas por quadro e animadas
    # Cabeçalho e rodapé não são afetados.
    h=int(157*sc.scale);assert np.array_equal(c1[:h],Scene(junction,S()).frame(3,view=v)[0][:h])

def test_sombras_pelo_sol(junction):
    from app.render import Scene
    sc=Scene(junction,S(sun_shadows=True,sun_hour=7));assert sc.sombra_veiculo[0]<-1
    assert np.allclose(Scene(junction,S()).sombra_veiculo,[.25,-.38])

def test_antes_depois(junction):
    from app.render import Scene
    from app.ambiente import antes_depois
    sc=Scene(junction,S(before_after=True,before_after_s=6,duration_s=30))
    assert antes_depois(sc,20) is None and antes_depois(sc,24)==0 and antes_depois(sc,30)==1 and 0<antes_depois(sc,26)<1
    a=sc.frame(26)[0];b=Scene(junction,S(duration_s=30)).frame(26)[0];assert not np.array_equal(a,b)
    assert (a[sc.H//2,:]>245).all(1).any()               # divisória branca na tela

def test_camera_pontos(junction):
    from app.render import Scene
    K=[{'x':500050,'y':7800000,'width_m':80,'hold_s':2,'title':'Início'},{'x':500350,'y':7800000,'width_m':160,'hold_s':2,'title':'Saída'}]
    sc=Scene(junction,S(camera_mode='pontos',camera_keys=K,duration_s=20))
    c0,w0,p0,_,n0=sc.pose(0);c1,w1,_,_,_=sc.pose(20);cm,wm,_,_,_=sc.pose(10)
    assert n0=='chave' and p0==1 and np.allclose(c0,[500050,7800000]) and w0==80 and np.allclose(c1,[500350,7800000]) and w1==160
    assert 500050<cm[0]<500350 and wm>80                 # no meio do voo, afastado (zoom de voo)
    sc.frame(0);assert sc._key_title=='Início'
    # Com um ponto só, o voo normal continua.
    assert Scene(junction,S(camera_mode='pontos',camera_keys=K[:1],duration_s=20)).pose(5)[4]!='chave'
