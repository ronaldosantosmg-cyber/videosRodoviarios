import numpy as np
from app.fantasmas import limpar,segmentos_fantasma,_dividir


def _curva(n=60,r=300.,passo=3.):
    th=np.arange(n)*passo/r
    return np.column_stack([r*np.sin(th),r*(1-np.cos(th))])


def _ent(role,pts,**k):
    return {'role':role,'layer':'x','closed':False,'points':np.asarray(pts,float),'holes':[],**k}


def test_corda_de_bordo_longe_do_pavimento_e_removida():
    eixo=_curva();pav=np.vstack([eixo+[0,-4],eixo[::-1]+[0,4]])
    bordo=np.vstack([eixo[:30]+[0,3.5],eixo[30]+[400,300],eixo[31:]+[0,3.5]])
    ents=[_ent('axis',eixo),_ent('pavement',pav,closed=True),_ent('edge_line',bordo)]
    w=[];out,n=limpar(ents,w)
    assert n>=1 and w and 'fantasma' in w[0]
    partes=[e for e in out if e['role']=='edge_line']
    assert len(partes)==2 and all(len(p['points'])>=2 for p in partes)
    assert max(np.linalg.norm(np.diff(p['points'],axis=0),axis=1).max() for p in partes)<10


def test_reta_real_apoiada_no_pavimento_e_preservada():
    eixo=np.array([[0,0],[200,0],[400,0.]]);pav=np.array([[0,-4],[400,-4],[400,4],[0,4.]])
    bordo=np.array([[0,3.5],[3,3.5],[6,3.5],[390,3.5],[393,3.5],[396,3.5]])
    out,n=limpar([_ent('axis',eixo),_ent('pavement',pav,closed=True),_ent('edge_line',bordo)],[])
    assert n==0 and len(out)==3


def test_entradas_invalidas_nao_quebram():
    for p in (None,[],[[0,0]],[[0,0],[np.nan,1],[2,2]],[[0,0],[np.inf,1],[2,2]],np.zeros((5,2))):
        assert segmentos_fantasma(p)==[]
    out,n=limpar([],None);assert out==[] and n==0
    out,n=limpar([_ent('edge_line',np.zeros((4,2)))],None);assert n==0


def test_dominio_corda_que_nao_acompanha_a_via():
    eixo=_curva(200,300.,3.);dom=eixo+[0,50]
    dom=np.vstack([dom[:20],dom[150:]])   # salto entre trechos
    ents=[_ent('axis',eixo),_ent('domain',dom)]
    out,n=limpar(ents,[])
    assert n==1 and len([e for e in out if e['role']=='domain'])==2


def test_dividir_preserva_pontas():
    P=np.arange(12,dtype=float).reshape(6,2)
    partes=_dividir(P,[2]);assert len(partes)==2 and len(partes[0])==3 and len(partes[1])==3


def test_cortar_transversais_divide_no_salto_de_deslocamento():
    from app.signage import cortar_transversais
    ref=np.column_stack([np.arange(10)*2.,np.zeros(10)])
    pts=ref+[0,3.5];pts[5:]+=[0,-7]          # salto lateral entre amostras 4 e 5
    partes=cortar_transversais(pts,ref)
    assert len(partes)==2 and all(len(p)>=2 for p in partes)
    assert len(cortar_transversais(ref+[0,3.5],ref))==1
    for ruim in (None,[],[[0,0]],np.full((4,2),np.nan)):
        assert cortar_transversais(ruim,ruim)


def test_eliminar_discrepancias_remove_transversal_gerada_e_preserva_dxf():
    from types import SimpleNamespace
    from app.traffic import TrafficNetwork
    eixo=np.column_stack([np.linspace(0,100,201),np.zeros(201)])
    import scipy.spatial as sp
    net=SimpleNamespace(markings=[(np.array([50.,-3]),np.array([50.,3]),(255,255,255)),
                                  (np.array([40.,3]),np.array([42.,3]),(255,255,255)),
                                  (np.array([60.,-3]),np.array([60.,3]),(255,255,255))],
                        mark_src=[0,0,-4],_axis_field=(sp.cKDTree(eixo),np.tile([1.,0],(len(eixo),1))),
                        signage_warnings=[])
    net.perpendicular_to_axis=lambda a,b,reach=30.,cos_max=.5:TrafficNetwork.perpendicular_to_axis(net,a,b,reach,cos_max)
    net.axis_field=lambda:net._axis_field
    net.near_authoritative=lambda mids,tol:np.zeros(len(mids),bool)
    TrafficNetwork.eliminar_discrepancias(net)
    assert net.discrepancias_removidas==1 and len(net.markings)==2 and net.mark_src==[0,-4]


def test_vectors_junta_interna_e_fim_de_bloco_nao_voltam_com_contornos_derivados():
    from app.webmap import vectors
    def bloco(x0,x1):
        return {'role':'pavement','layer':'P','closed':True,'hatch':True,'points':np.array([[x0,-4],[x1,-4],[x1,4],[x0,4],[x0,-4.]]),'holes':[]}
    eixo=np.column_stack([np.linspace(0,200,101),np.zeros(101)])
    # eixo da rotatória/ramo a 80 m do principal: fora do alcance de 30 m do eixo principal
    ramo=np.column_stack([np.linspace(0,200,101),np.full(101,80.)])
    bl=[bloco(0,100),bloco(100,200)]
    bl2={**bloco(0,100),'points':bloco(0,100)['points']+[0,80]}
    ents=bl+[bl2,{'role':'axis','layer':'E','closed':False,'points':ramo,'holes':[]}]
    V=vectors(ents,eixo,derived_contours=True)
    for rec in V['layers']['pavement']:
        assert set(rec['k'])<=set(rec['source_k']) or not rec.get('hatch_outline')
    # a junta x=100 entre os dois blocos não pode ser riscada
    visivel=[]
    for rec in V['layers']['pavement']:
        p=np.asarray(rec['p']);sk=set(rec['source_k'])
        for i in range(len(p)-1):
            if i not in sk and abs(p[i][0]-100)<1e-6 and abs(p[i+1][0]-100)<1e-6 and p[i][1]<20:visivel.append(i)
    assert not visivel
