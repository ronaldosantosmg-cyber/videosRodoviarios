"""2.29: Central do projeto (limpeza protegida e reversível) e aritmética protegida."""
import json
from pathlib import Path
import numpy as np
import pytest
from app.models import Settings
from app import central
from app.seguro import sdiv,limitar,numero,exigir,media,unitario,raiz,logaritmo,validar_resultado,finito

def projeto(tmp_path,rd=None):
    d=tmp_path/'p';d.mkdir()
    (d/'input.dxf').write_text('0\nSECTION\n',encoding='utf-8');(d/'camadas').mkdir();(d/'camadas'/'a.dxf').write_text('x',encoding='utf-8')
    (d/'analysis.json').write_text(json.dumps({'routes':[{'direction_key':'axis:'+'a'*64}]}),encoding='utf-8')
    (d/'editor.json').write_text('{}',encoding='utf-8');(d/'editor').mkdir();(d/'editor'/'roads.wkb').write_bytes(b'1')
    (d/'video.mp4').write_bytes(b'v'*10);(d/'preview.png').write_bytes(b'p')
    s=Settings(route_directions=rd or {'axis:'+'a'*64:'forward','axis:'+'b'*64:'reverse','layer:EIXO_OESTE':'reverse'},crs='EPSG:31983')
    (d/'config.json').write_text(json.dumps(s.model_dump()),encoding='utf-8');return d,s

def test_estado_separa_entradas_derivados_e_resultados(tmp_path):
    d,s=projeto(tmp_path);e=central.estado(d,s)
    assert {x['nome'] for x in e['entradas']}>={'input.dxf','camadas','config.json'}
    assert {x['nome'] for x in e['derivados']}=={'analysis.json','editor.json','editor'}
    assert {x['nome'] for x in e['resultados']}=={'video.mp4','preview.png'}
    assert e['orfas']['route_directions']==['axis:'+'b'*64] and any('não correspondem' in a for a in e['alertas'])

def test_simulacao_nao_mexe_em_nada(tmp_path):
    d,s=projeto(tmp_path);novas,r=central.limpar(d,s,'dxf_novo',confirmar=False)
    assert r['simulacao'] and (d/'video.mp4').exists() and (d/'analysis.json').exists() and novas is s

def test_limpar_dxf_novo_move_para_limpeza_remove_orfas_e_preserva_entradas(tmp_path):
    d,s=projeto(tmp_path);novas,r=central.limpar(d,s,'dxf_novo',confirmar=True)
    assert not (d/'video.mp4').exists() and not (d/'editor.json').exists() and (d/'input.dxf').exists() and (d/'camadas'/'a.dxf').exists()
    assert (d/'_limpeza'/r['pasta']/'video.mp4').exists()                      # protegido: movido, não apagado
    assert 'axis:'+'b'*64 not in novas.route_directions and 'axis:'+'a'*64 in novas.route_directions and novas.route_directions['layer:EIXO_OESTE']=='reverse'
    # desfazer restaura arquivos e configuração
    s2,nome=central.desfazer(d)
    assert (d/'video.mp4').exists() and (d/'editor'/'roads.wkb').exists() and 'axis:'+'b'*64 in s2.route_directions

def test_escopo_resultados_nao_toca_derivados_nem_escolhas(tmp_path):
    d,s=projeto(tmp_path);novas,r=central.limpar(d,s,'resultados',confirmar=True)
    assert (d/'analysis.json').exists() and not (d/'video.mp4').exists() and novas.route_directions==s.route_directions

def test_escopo_invalido_e_sem_limpeza_para_desfazer(tmp_path):
    d,s=projeto(tmp_path)
    with pytest.raises(ValueError):central.limpar(d,s,'tudo',True)
    with pytest.raises(ValueError):central.desfazer(d)

def test_mudanca_de_dxf_e_detectada(tmp_path):
    d,s=projeto(tmp_path);assert central.estado(d,s)['dxf']['mudou'] is False
    (d/'input.dxf').write_text('0\nOUTRO\n',encoding='utf-8');e=central.estado(d,s)
    assert e['dxf']['mudou'] is True and any('DXF' in a for a in e['alertas'])
    central.limpar(d,s,'dxf_novo',True);assert central.estado(d,s)['dxf']['mudou'] is False

def test_aritmetica_protegida():
    assert sdiv(6,3)==2 and sdiv(1,0)==0 and sdiv(1,0,-1)==-1 and sdiv(1,float('nan'))==0 and sdiv(float('inf'),2)==0
    assert np.allclose(sdiv([1,2,3],[1,0,3]),[1,0,1]) and sdiv(np.array([1.,2.]),2).tolist()==[.5,1.]
    assert limitar(float('nan'),0,1)==0 and limitar(5,0,1)==1 and numero('x',7)==7 and numero(float('inf'),3)==3
    assert media([])==0 and unitario([0,0]).tolist()==[0,0] and np.allclose(unitario([3,4]),[.6,.8])
    assert raiz(-4)==0 and logaritmo(0)==0 and finito([1,2]) and not finito([1,float('nan')])
    for ruim in ('',None,'  ',[]):
        with pytest.raises(ValueError):exigir(ruim,'Nome')
    with pytest.raises(ValueError):validar_resultado(float('inf'),'Velocidade')

def test_divisoes_protegidas_no_motor_continuam_dando_o_mesmo_resultado():
    # o motor passou a usar sdiv: entradas normais iguais à divisão comum
    for a,b in ((7.,2.),(-3.,4.),(0.,5.),(1e9,3.)):assert sdiv(a,b)==a/b

def test_mapa_de_dependencias_diz_o_que_cada_mudanca_invalida(tmp_path):
    assert 'geometria' in central.invalida('crs') and 'rede de tráfego' in central.invalida('route_directions')
    assert 'rede de tráfego' not in central.invalida('traffic_density') and 'vídeo' in central.invalida('traffic_density')
    assert central.invalida('preview_time_s')==['prévia']
    d,s=projeto(tmp_path);assert 'route_directions' in central.estado(d,s)['dependencias']

def test_api_central_e_erro_de_divisao_por_zero_amigavel(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from app.server import app
    from app import server
    @app.get('/api/_teste_zero')
    def _z():return 1/0
    r=TestClient(app,raise_server_exceptions=False).get('/api/_teste_zero')
    assert r.status_code==422 and 'zerada ou vazia' in r.json()['detail']

def test_pare_e_siga_com_duas_faixas_por_lado_e_recusado_com_mensagem_clara():
    """Causa de 'Não foi possível salvar' na janela de seções: o motivo ficava escondido atrás do diálogo de confirmação."""
    from app.models import RouteAlignment
    P=dict(kind='pista',width_m=3.5);A=dict(kind='acostamento',width_m=2.5)
    rt=dict(id='r',name='Seção',points=[dict(x=0,y=0),dict(x=900,y=0)],cross_sections=[dict(id='s',start_m=0,end_m=900,type='simples',left=[P,P,A],right=[P,P,A])])
    zona=dict(id='z',route_id='r',start_m=100,end_m=800)
    Settings(route_alignments=[rt])                                   # sem pare e siga: válido
    with pytest.raises(ValueError,match='uma faixa operacional por sentido'):Settings(route_alignments=[rt],alternating_zones=[zona])

def test_js_confirmacao_mostra_o_motivo_real():
    import shutil,subprocess
    node=shutil.which('node')
    if not node:pytest.skip('node ausente')
    src=(Path(__file__).resolve().parents[1]/'app'/'js'/'64_janelas_modelagem.js').read_text(encoding='utf-8')
    assert "'Não foi possível salvar: '+motivo" in src
    src65=(Path(__file__).resolve().parents[1]/'app'/'js'/'65_secoes_pare_siga.js').read_text(encoding='utf-8')
    assert 'exige uma faixa por sentido' in src65

def test_sentido_do_eixo_manda_na_rota_gerada_pelas_faixas_e_tela_mostra_o_que_vale():
    src=(Path(__file__).resolve().parents[1]/'app'/'js'/'87_circulacao_simples.js').read_text(encoding='utf-8')
    assert "r.source==='eixo_faixas'?`<section>" in src             # rota gerada não tem select de sentido próprio
    assert "flow_direction:'automatico',flow_start:'automatico',flow_end:'automatico'" in src
    assert 'Vale agora:' in src and 'direction-report' in src
    assert "data-reverse-native=\"${i}\" ${routes" not in src        # reverter liberado para eixos com seção

def test_sdiv_preserva_float32_para_o_opencv():
    a=np.ones((3,3),np.float32);r=sdiv(a,2.0);assert r.dtype==np.float32 and r[0,0]==.5
    assert sdiv(a,np.zeros((3,3),np.float32)).dtype==np.float32
    assert sdiv(np.array([1,2]),np.array([2,0])).dtype==np.float64      # inteiros viram float64 como na divisão comum
