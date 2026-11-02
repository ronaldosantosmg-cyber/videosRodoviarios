"""2.38 (uniformidade): para 6 eixos com escolhas independentes (eixo, layer, auto), o sentido que o MOTOR usa (raw_paths),
o que a PRÉVIA mostra (preview) e o que a POLÍTICA declara (resolver_eixo) são o mesmo; mudar um eixo não muda os outros."""
import itertools,re
from pathlib import Path
from app.models import RouteAlignment
from app import routes
from app.native_axes import axis_fingerprint,direction_for
from app.direction_policy import resolver_eixo,ROTULO
JS=Path(__file__).resolve().parents[1]/'app'/'js'

class S:
    def __init__(s,rd,routes_):
        s.route_directions=rd;s.route_alignments=routes_;s.axis_types={};s.min_route_segment_m=50;s.flow_overrides=[];s.alternating_zones=[];s.direction_marks=[];s.reverse_axis=False
def eixos():
    out=[]
    for i in range(6):
        y=i*40.;pts=[(0.,y),(120.,y+5),(240.,y+30)];layer='EIXO_%d'%(i%3)   # 3 layers compartilhados por 6 eixos
        out.append(dict(points=pts,layer=layer,level=0,fp=axis_fingerprint(pts,layer,0)))
    return out
def rota(a,mode):
    sec={'id':'s%s'%a['fp'][:6],'name':'S','start_m':0,'end_m':240,'type':'simples','median_m':0,'left':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'right':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'left_dir':'mesmo' if mode=='meio' else 'contrario','right_dir':'mesmo'}
    return RouteAlignment.model_validate({'id':'r'+a['fp'][:8],'name':'Seção '+a['layer']+a['fp'][:4],'points':[{'x':x,'y':y} for x,y in a['points']],'enabled':True,'type':'simples','lanes':1,'lane_width_m':3.6,'source':'eixo_dxf','source_axis_fingerprint':a['fp'],'source_axis_layer':a['layer'],'sections_only':True,'section_surface':True,'cross_sections':[sec]})
def dirs_por_rota(st,fonte):
    d={}
    for p in fonte:
        rid=p.get('route') if 'route' in p and isinstance(p.get('route'),str) and 'route_dir' in p else p.get('id')
        d.setdefault(rid,set()).add(p.get('route_dir') or p.get('dir'))
    return d
def esperado(rd,a,mode):
    v=direction_for(rd,'axis:'+a['fp'],a['layer'])
    if v=='forward':return {'f'}
    if v=='reverse':return {'r'}
    return {'f'} if mode=='meio' else {'f','r'}
def test_motor_previa_e_politica_concordam_em_todas_as_combinacoes():
    A=eixos();checadas=0
    escolhas=['forward','reverse','auto']
    for mode in ('meio','dois'):
        rotas=[rota(a,mode) for a in A]
        for combo in itertools.product(escolhas,repeat=3):          # 27 combos por layer
            rd={'layer:EIXO_%d'%k:v for k,v in enumerate(combo) if v!='auto'}
            rd['axis:'+A[3]['fp']]='reverse' if combo[0]!='reverse' else 'forward'   # um eixo com escolha própria que vence a do layer
            st=S(rd,rotas)
            motor=dirs_por_rota(st,routes.raw_paths(st));prev=dirs_por_rota(st,routes.preview(st))
            for a,r in zip(A,rotas):
                esp=esperado(rd,a,mode)
                assert motor.get(r.id)==esp,(mode,combo,a['layer'],motor.get(r.id),esp)
                assert prev.get(r.id)==esp,('prévia diverge do motor',mode,combo,a['layer'])
                ef=resolver_eixo(st,dict(points=a['points'],layer=a['layer'],level=0))['efetivo']
                assert ef==(direction_for(rd,'axis:'+a['fp'],a['layer'])),('política diverge',ef)
                checadas+=1
    assert checadas==2*27*6
def test_mudar_um_eixo_nao_muda_os_outros():
    A=eixos();rotas=[rota(a,'meio') for a in A]
    base={'axis:'+a['fp']:'forward' for a in A};antes=dirs_por_rota(S(base,rotas),routes.raw_paths(S(base,rotas)))
    for k,a in enumerate(A):
        rd=dict(base);rd['axis:'+a['fp']]='reverse';depois=dirs_por_rota(S(rd,rotas),routes.raw_paths(S(rd,rotas)))
        mudou=[r.name for r in rotas if depois[r.id]!=antes[r.id]]
        assert mudou==[rotas[k].name],(k,mudou)
def test_glossario_unico_python_e_js():
    g=(JS/'00_glossario.js').read_text(encoding='utf-8')
    for chave,rotulo in ROTULO.items():
        assert rotulo in g,(chave,rotulo)
    assert 'RodoviaGlossario' in g
def test_nenhum_rotulo_de_sentido_divergente_fora_do_glossario():
    ruins=['Crescente (km aumenta)','Crescente (no sentido do desenho)','Decrescente (contra o desenho)']
    for f in JS.glob('*.js'):
        if f.name=='00_glossario.js':continue
        t=f.read_text(encoding='utf-8')
        for r in ruins:assert r not in t,(f.name,r)
