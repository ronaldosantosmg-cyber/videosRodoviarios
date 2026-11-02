"""2.41: geometria REAL do projeto TH53 (EIXO_LESTE/EIXO_OESTE e eixo principal, simplificados) com as escolhas salvas pelo usuário
(Leste = Decrescente, Oeste = Crescente). Com “inverter eixo” ligado ou desligado, a seção cadastrada sobre cada eixo tem de circular no sentido do KM."""
import json,numpy as np
from pathlib import Path
from test_v14265_uniformidade_sentido import S
from app import routes
from app.models import RouteAlignment
from app.native_axes import axis_fingerprint
FX=json.loads((Path(__file__).parent/'fixtures'/'th53_eixos_reais.json').read_text(encoding='utf-8'))
def secao(layer,pts,mode):
    fp=axis_fingerprint([tuple(p) for p in pts],layer,0);L=float(np.sum(np.linalg.norm(np.diff(np.asarray(pts),axis=0),axis=1)))
    sec={'id':'s'+fp[:6],'name':'S','start_m':0,'end_m':L,'type':'simples','median_m':0,'left':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'right':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'left_dir':'mesmo' if mode=='meio' else 'contrario','right_dir':'mesmo'}
    return RouteAlignment.model_validate({'id':'r'+fp[:8],'name':'Seção '+layer,'points':[{'x':x,'y':y} for x,y in pts],'enabled':True,'type':'simples','lanes':1,'lane_width_m':3.6,'source':'eixo_dxf','source_axis_fingerprint':fp,'source_axis_layer':layer,'sections_only':True,'section_surface':True,'cross_sections':[sec]}),fp
def sentidos(chave_eixo,mode):
    axis=np.asarray(FX[chave_eixo],float);ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(axis,axis=0),axis=1))]
    chain=routes.make_chain(axis,ds,FX['km_dir_'+('rev' if chave_eixo.endswith('rev') else 'norm')])
    rs=[(secao(l,a['points'],mode),a['direction']) for l,a in FX['axes'].items()]
    st=S({'axis:'+fp:d for (r,fp),d in rs},[r for (r,_),_ in rs])
    out={}
    with routes.km_context(chain):
        for p in routes.raw_paths(st):
            pts=np.asarray(p['points'] if 'points' in p else p['p'],float)
            for (r,fp),d in rs:
                if p.get('route')==r.id or p.get('id')==r.id:out.setdefault(r.name,set()).add(np.sign(chain(pts[-1])-chain(pts[0])))
    return out
def test_th53_secoes_seguem_o_km_com_inverter_eixo_ligado_e_desligado():
    for eixo in ('main_axis_rev','main_axis_norm'):
        for mode in ('meio','dois'):
            o=sentidos(eixo,mode)
            assert o['Seção EIXO_LESTE']=={-1.0},(eixo,mode,o)      # Leste = Decrescente (km)
            assert o['Seção EIXO_OESTE']=={1.0},(eixo,mode,o)       # Oeste = Crescente (km)
