"""2.41: ramo/laço/perpendicular ao eixo principal não tem sentido de km; Crescente/Decrescente valem pela ordem do desenho (mesmo no motor e na prévia).
Eixos paralelos continuam seguindo o km."""
import numpy as np
from test_v14265_uniformidade_sentido import S,dirs_por_rota
from test_v14269_projeto_real_th53 import FX,secao
from app import routes
from app.models import RouteAlignment
from app.native_axes import axis_fingerprint
DS=np.array([0.,1000.]);MAIN=np.array([[0.,0.],[1000.,0.]])
def sec_pts(layer,pts):return secao(layer,pts,'meio')
def dirs(pts,km_dir,d='forward'):
    r,fp=sec_pts('RAMO',pts);st=S({'axis:'+fp:d},[r])
    with routes.km_context(routes.make_chain(MAIN,DS,km_dir)):
        return dirs_por_rota(st,routes.raw_paths(st)).get(r.id)
def test_paralelo_segue_km():
    p=[(100.,20.),(500.,20.)]
    assert dirs(p,1)=={'f'} and dirs(p,-1)=={'r'}
def test_perpendicular_usa_ordem_do_desenho_em_qualquer_km():
    p=[(500.,20.),(500.,220.)]
    assert dirs(p,1)=={'f'} and dirs(p,-1)=={'f'}
    assert dirs(p,1,'reverse')=={'r'} and dirs(p,-1,'reverse')=={'r'}
def test_laco_usa_ordem_do_desenho():
    p=[(300.,20.),(340.,80.),(380.,20.),(300.,20.)]
    assert dirs(p,1)=={'f'} and dirs(p,-1)=={'f'}
def test_ramo_oblíquo_curto_ao_longo_do_eixo_ainda_segue_km():
    p=[(100.,20.),(200.,60.)]      # Δestaca 100 de 108 m
    assert dirs(p,-1)=={'r'}
def test_front_aplica_o_mesmo_limiar():
    from pathlib import Path
    t=(Path(__file__).resolve().parents[1]/'app'/'js'/'32_rotas.js').read_text(encoding='utf-8')
    assert '0.45*L' in t.split('function routeKmSigns')[1].split('\n')[0] and routes.KM_AMBIGUO==.45
def test_cadeia_do_km_e_serializavel_para_o_snapshot_do_video():
    import pickle
    ch=routes.make_chain(MAIN,DS,-1);c2=pickle.loads(pickle.dumps(ch,protocol=5))
    assert c2((300.,5.))==ch((300.,5.))==-300.
from test_v110 import junction  # noqa: F401
def test_snapshot_da_cena_com_trafego_grava_e_recarrega(junction,tmp_path):
    """2.41: o vídeo falhava em Scene.snapshot (pickle) por causa da cadeia de km em lambda (2.39). Cena com tráfego tem de gravar e recarregar."""
    from app.render import Scene
    from test_v110 import S as S110
    sc=Scene(junction,S110())
    key=sc.snapshot(tmp_path/'snap');b=Scene.load_snapshot(tmp_path/'snap',key=key)
    assert b.network._km_chain((10.,10.)) == sc.network._km_chain((10.,10.))
