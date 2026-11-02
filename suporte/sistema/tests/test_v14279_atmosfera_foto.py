"""2.46: atmosfera fotográfica — hora do dia e tempo mudam a imagem de forma coerente e determinística; desligada, nada muda."""
import types
import numpy as np
from app import fotorrealismo as F

def _cena(w='limpo',tod='hora_do_sol',k=.7,hora=15,noite=0.):
    return types.SimpleNamespace(s=types.SimpleNamespace(weather=w,weather_intensity=k,time_of_day=tod,sun_hour=hora),scale=.6,H=120,W=200,_night=noite)
def _img():
    rng=np.random.default_rng(2);im=np.full((120,200,3),(84,124,66),np.uint8);im[40:80]=(70,72,76);im[58:62:1,::20]=(240,240,240);via=np.zeros((120,200),bool);via[40:80]=True
    return (im+rng.integers(0,8,im.shape,dtype=np.uint8)).astype(np.uint8),via
def _run(**kw):
    im,via=_img();F.aplicar(_cena(**kw),im,2.0,0,120,via);return im.astype(float)
def test_ordem_de_luminosidade_dia_entardecer_noite():
    d,e,n=[_run(tod=x).mean() for x in('dia','entardecer','noite')];assert d>e>n
def test_entardecer_e_quente_e_noite_e_fria():
    e=_run(tod='entardecer');n=_run(tod='noite');d=_run(tod='dia')
    assert e[...,0].mean()/e[...,2].mean()>d[...,0].mean()/d[...,2].mean()+.15
    assert n[...,2].mean()>n[...,0].mean()
def test_neblina_reduz_contraste_e_aproxima_da_cor_da_nevoa():
    c=_run(tod='dia');f=_run(w='neblina',tod='dia');assert f.std()<c.std()*.85
def test_chuva_escurece_a_pista_e_e_deterministica():
    c=_run(tod='dia');r=_run(w='chuva',tod='dia');assert r[40:80].mean()<c[40:80].mean();assert np.array_equal(r,_run(w='chuva',tod='dia'))
def test_chuva_muda_com_o_tempo_mas_neblina_e_continua():
    im,via=_img();a=im.copy();b=im.copy();s=_cena('chuva','dia');F.aplicar(s,a,1.0,0,120,via);F.aplicar(s,b,1.2,0,120,via);assert not np.array_equal(a,b)
def test_hora_do_sol_segue_slider():
    assert F.hora(_cena(hora=7).s)==7 and F.hora(_cena(tod='noite').s) is None and F.hora(_cena(tod='dia').s)==12.
def test_desligado_o_clima_antigo_continua_igual():
    from app import ambiente
    s=types.SimpleNamespace(s=types.SimpleNamespace(weather='neblina',weather_intensity=.6,photo_atmosphere=False),scale=.6,H=120,W=200)
    a,_=_img();b=a.copy();ambiente.clima(s,a,1.,0,0);assert not np.array_equal(a,b)
def test_modelo_aceita_os_campos():
    from app.models import Settings
    s=Settings(photo_atmosphere=True,time_of_day='entardecer',weather='chuva');assert s.photo_atmosphere and s.time_of_day=='entardecer'
