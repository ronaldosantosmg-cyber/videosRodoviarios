"""1.42.38: invariantes do fluxo, determinísticos e sem navegador/vídeo/3D (cada teste roda em poucos segundos).
Substituem, na checagem rápida, cenários lentos que só confirmavam o mesmo comportamento por imagem."""
import hashlib
import numpy as np
from shapely.geometry import box
from app.models import Settings
from app.native_axes import axis_fingerprint
from app.traffic import TrafficNetwork


def rede(linhas,m=50,largura=(-9,11),**kw):
    axis=np.asarray(linhas[0]);ds=np.array([0.,float(np.max(axis[:,0]))])
    d={'axis:'+axis_fingerprint(p):'forward' for p in linhas}
    s=Settings(derive_traffic_paths=False,hydrography=False,min_route_segment_m=m,median_crossing='free',route_directions=d,**kw)
    return TrafficNetwork([box(-1,largura[0],float(max(p[:,0].max() for p in map(np.asarray,linhas)))+1,largura[1])],[],[{'points':np.asarray(p)} for p in linhas],axis,ds,s)


def assinatura(n):
    h=hashlib.sha256()
    for p in n.paths:h.update(np.round(p['p'],4).tobytes());h.update(repr(p['edges']).encode())
    return h.hexdigest()


def test_eixo_reto_gera_rota_unica_sem_oscilacao():
    n=rede([[[0.,0.],[400.,0.]]])
    assert len(n.paths)==1 and float(np.ptp(n.paths[0]['p'][:,1]))<.05
    assert not n.short_ignored and not n.warnings


def test_resultado_e_deterministico():
    a=[[0.,0.],[180.,0.]];z=[[183.,0.],[193.,6.],[203.,0.]];b=[[206.,0.],[400.,0.]]
    assert assinatura(rede([a,z,b]))==assinatura(rede([a,z,b]))


def test_trecho_curto_nunca_entra_em_rota_nem_causa_desvio():
    a=[[0.,0.],[180.,0.]];z=[[183.,0.],[193.,6.],[203.,0.]];b=[[206.,0.],[400.,0.]]
    for m in (0,50):
        n=rede([a,z,b],m)
        assert all(float(np.ptp(p['p'][:,1]))<.05 for p in n.paths)   # nenhum veículo faz zigue-zague
    n=rede([a,z,b],50)
    assert all(not set(p['edges'])&n.short_ignored for p in n.paths)
    assert all(e['length']>=50 for e in n.edges)


def test_limite_de_rotas_curtas_acompanha_a_configuracao():
    curto=[[[0.,0.],[40.,0.]]]
    assert not rede(curto,50).paths          # abaixo do mínimo: ignorada
    assert rede(curto,0).paths               # mínimo zerado: aceita


def test_diagnostico_nao_altera_a_geometria_das_rotas():
    from app.flow_diagnostics import flow_diagnostics
    n=rede([[[0.,0.],[400.,0.]]]);antes=assinatura(n)
    flow_diagnostics(n)
    assert assinatura(n)==antes


def test_segmento_sem_rota_informa_o_motivo():
    a=[[0.,0.],[180.,0.]];z=[[183.,0.],[193.,6.],[203.,0.]];b=[[206.,0.],[400.,0.]]
    n=rede([a,z,b],0)
    aviso=[w for w in n.warnings if 'sem itinerário seguro completo' in w]
    assert aviso and 'Motivos:' in aviso[0] and 'reprovado' in aviso[0]
    assert sum(n.missing_summary.values())>0
    ok=rede([[[0.,0.],[400.,0.]]]);assert not any('Motivos:' in w for w in ok.warnings)     # sem pendência, sem texto extra


def test_ordem_de_processamento_so_muda_acima_do_limite():
    # abaixo de 256 trechos o conjunto e a ordem das rotas são os de sempre (um ramal não muda o eixo principal)
    base=rede([[[0.,0.],[400.,0.]]]);com=rede([[[0.,0.],[400.,0.]],[[150.,0.],[250.,60.]]],largura=(-9,70))
    assert assinatura(base)==assinatura(rede([[[0.,0.],[400.,0.]]]))
    assert len(com.paths)>=len(base.paths)
