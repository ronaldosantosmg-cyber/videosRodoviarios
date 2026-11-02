"""2.59: a água em blocos dá o mesmo resultado que o cálculo em um retângulo só, com memória limitada."""
import importlib.util,sys,numpy as np,cv2
from app import relevo

def _ref():
    spec=importlib.util.spec_from_file_location('relevo_ref',__file__.replace('test_v14288_agua_blocos.py','_relevo_agua_ref.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def _cena(n=900):
    rng=np.random.default_rng(3);img=rng.integers(40,200,(n,n,3),dtype=np.uint8);m=np.zeros((n,n),np.uint8)
    cv2.fillPoly(m,[np.array([[60,100],[820,220],[700,500],[300,420],[90,760],[40,300]],np.int32)],255)
    cv2.circle(m,(700,760),90,255,-1);cv2.circle(m,(700,760),30,0,-1)                           # ilha
    return img,m
WP=lambda p:np.asarray(p,float)*np.array([1.,-1.])*0+np.stack([np.asarray(p,float)[:,0]/2.,np.asarray(p,float)[:,1]/2.],1) if False else (lambda q:np.stack([q[:,0]/2.,q[:,1]/2.],1))(np.asarray(p,float))

def test_blocos_iguais_ao_calculo_unico():
    img,m=_cena();a=img.copy();b=img.copy()
    relevo.agua(a,m,WP,2.0,.65,bloco=200)                                                       # muitos blocos
    _ref().agua(b,m,WP,2.0,.65)
    dif=np.abs(a.astype(int)-b.astype(int))
    assert dif.max()<=1,dif.max()
    assert (a!=img).any()

def test_bloco_unico_tambem_igual():
    img,m=_cena(300);a=img.copy();b=img.copy();relevo.agua(a,m,WP,.5,.65,bloco=4096);_ref().agua(b,m,WP,.5,.65)
    assert np.abs(a.astype(int)-b.astype(int)).max()<=1

def test_memoria_limitada():
    import tracemalloc
    img,m=_cena(1500);tracemalloc.start();relevo.agua(img,m,WP,1.0,.65,bloco=256);pico=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
    assert pico<260*1024**2,pico/1e6                                                           # imagem 1500² cabe folgado; o antigo passava de 1,2 GB
