"""1.42.40: textura sobre a hachura — OAE nova/existente/alargada, corte vermelho e aterro verde com grama, chamadas como na referência."""
import json
import numpy as np,ezdxf,pytest,cv2
from fastapi.testclient import TestClient
from test_workflow import settings
from app.models import Settings


def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})


def dxf_oae(tmp_path):
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAV','OAE_A','OAE_B','OAE_C','CORTE']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500400,7800000)],dxfattribs={'layer':'EIXO'})
    def hatch(layer,x0,x1,y0=7799991,y1=7800009,color=8):
        h=m.add_hatch(color=color,dxfattribs={'layer':layer});h.paths.add_polyline_path([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],is_closed=True)
    hatch('PAV',500000,500100);hatch('OAE_A',500100,500160);hatch('OAE_B',500160,500220);hatch('OAE_C',500220,500280);hatch('CORTE',500280,500340,7800009,7800030,color=1)
    d.saveas(tmp_path/'input.dxf');return tmp_path


def test_modelo_aceita_oae_kind_e_novas_superficies():
    from app.models import HatchRole
    assert HatchRole(role='oae',oae_kind='alargada').oae_kind=='alargada' and HatchRole(role='oae').oae_kind=='auto'
    with pytest.raises(Exception):HatchRole(role='oae',oae_kind='x')
    for k in ('oae_nova','oae_existente','oae_alargada'):S(texture_params={k:{'grao':1.2}})
    assert Settings.model_validate({'km_start_m':0,'km_end_m':100}).earthwork_look=='textura' and Settings(earthwork_look='hatch').earthwork_look=='hatch'


def test_previa_de_textura_das_novas_superficies():
    from app.server import app
    c=TestClient(app)
    for k in ('oae_nova','oae_existente','oae_alargada','talude_corte','talude_aterro'):
        r=c.get('/api/texture_preview.png',params={'surface':k});assert r.status_code==200 and r.content[:4]==b'\x89PNG',k


def test_estilos_de_talude_textura_corte_vermelho_aterro_verde():
    from app.earthworks import earthwork_style
    m=np.full((40,40),255,np.uint8);l=np.zeros_like(m)
    c,_=earthwork_style(m,l,'cut',.2,look='textura');f,_=earthwork_style(m,l,'fill',.2,look='textura')
    assert c[20,20,0]>c[20,20,1]+50 and f[20,20,1]>f[20,20,0]+30             # vermelho / verde
    n,_=earthwork_style(m,l,'cut',.2,look='natural');assert tuple(n[20,20])!=tuple(c[20,20])          # 'natural' não mudou


def test_grama_no_corte_so_na_textura():
    from app import visual
    im=np.full((120,160,3),(170,86,66),np.uint8);surf=np.full((120,160),6,np.uint8);A=np.array([[.05,0,700000.],[0,-.05,7800000.]]);v=np.ones((120,160),bool)
    a=im.copy();visual.shade_realistic(a,surf,A,.05,v);b=im.copy();visual.shade_realistic(b,surf,A,.05,v,earth_grass=True)
    assert b[:,:,1].mean()>a[:,:,1].mean()+1.5


def test_oae_por_tipo_vira_superficie_e_cor_distintas(tmp_path):
    from app.geometry import analyze
    from app.render import Scene
    from app import visual
    d=dxf_oae(tmp_path);lay={'axis':['EIXO']}
    rep=analyze(d,S(layers=lay,hatch_auto=False))[4]['hatches'];sig={h['layer']:h['sig'] for h in rep}
    roles={sig['PAV']:{'role':'pavement'},sig['OAE_A']:{'role':'oae','oae_kind':'nova'},sig['OAE_B']:{'role':'oae','oae_kind':'existente'},sig['OAE_C']:{'role':'oae','oae_kind':'alargada'},sig['CORTE']:{'role':'cut'}}
    items=analyze(d,S(layers=lay,hatch_auto=False,hatch_roles=roles))[0]
    assert {e['oae_kind'] for e in items if e['role']=='oae'}=={'nova','existente','alargada'}
    sc=Scene(d,S(layers=lay,hatch_auto=False,hatch_roles=roles,imagery='neutral',width=1280))
    def code(x,y):
        px=np.rint(sc.worldpx(np.array([[x,y]],float))).astype(int)[0];return int(sc.surface[px[1],px[0]]),sc.overlay[px[1],px[0],:3].tolist()
    got={k:code(x,7800000) for k,x in {'pav':500050,'nova':500130,'exist':500190,'alarg':500250}.items()}
    assert got['pav'][0]==visual.SURF['pavement']
    assert [got[k][0] for k in ('nova','exist','alarg')]==[9,10,11]
    assert len({tuple(got[k][1]) for k in ('nova','exist','alarg')})==3
    assert code(500310,7800020)[0]==6                       # corte: textura (look 'textura') sobre a hachura


def test_chamada_estilo_referencia():
    from app import visual
    from app.render import font
    im=np.full((500,900,3),(60,90,60),np.uint8);card=visual.callout_card('k','Início do TH57','Nova Era • km 325+850','',(236,218,168),font,1.0,'referencia')
    visual.draw_callout(im,(655,380),card,(236,218,168),1.0,0,500,[],(300,90),'referencia',1.)
    assert (np.abs(im[380,655].astype(int)-visual.REF_RED).sum()<40)                    # ponto vermelho na âncora
    near=im[240:290,480:560].reshape(-1,3).astype(int);assert (np.abs(near-visual.REF_CREAM).sum(1)<60).any()    # linha creme
    box=im[60:130,189:411].reshape(-1,3).astype(int);assert (box.sum(1)<90).sum()>.4*len(box)      # fundo azul-marinho
