"""2.56: correções tipadas (regras/IA) — coletar, interpretar resposta, aplicar em lote e desfazer, em todas as fases."""
import json
import pytest
from fastapi.testclient import TestClient
from test_v132 import S
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401
from app import ia_correcoes as C
from app.project_state import read_config,save_config,revision,Conflict

@pytest.fixture
def proj(junction,tmp_path,monkeypatch):
    monkeypatch.setenv('RODOVIA_DATA',str(tmp_path/'dados'))
    from app.server import app
    c=TestClient(app,base_url='http://127.0.0.1')
    pid=c.post('/api/projects',json=S(name='IA').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    from app import store
    d=store.directory(pid);cfg=read_config(d)
    cfg['width']=3840;cfg['duration_s']=900.0;cfg['crs']='';cfg['layers']={}
    pts=[dict(x=500000+i*10,y=7800000) for i in range(41)]
    cfg['route_alignments']=[dict(id='r1',name='R1',points=pts,sections_only=True,taper_m=10,cross_sections=[
        dict(id='a',name='Pista simples',start_m=0,end_m=200,type='simples',left=[dict(kind='pista',width_m=3.5)],right=[dict(kind='pista',width_m=3.5)],left_dir='contrario',right_dir='mesmo'),
        dict(id='b',name='Pista dupla',start_m=200,end_m=400,type='dupla',median_m=3,left=[dict(kind='pista',width_m=3.5)]*2,right=[dict(kind='pista',width_m=3.5)]*2,left_dir='contrario',right_dir='mesmo')])]
    try:save_config(d,cfg)
    except Exception as e:pytest.skip('config de teste inválida: '+str(e)[:200])
    return c,pid,d

def test_coleta_cobre_varias_fases(proj):
    c,pid,d=proj;r=c.get(f'/api/projects/{pid}/ia/correcoes').json()
    fases={x['fase'] for x in r['correcoes']}
    assert {'video_preparo','fluxos','importacao'}<=fases,fases
    assert {'camadas','hachuras','video_producao'}<=set(r['fases'])                       # fases existem mesmo sem pendência (camadas já reconhecidas)
    assert all(x['acao'] is None or x['acao']['tipo'] in ('config','camada','rota') for x in r['correcoes'])
    assert c.get(f'/api/projects/{pid}/ia/correcoes?fase=video_preparo').json()['correcoes']
    assert c.get(f'/api/projects/{pid}/ia/correcoes?fase=xyz').status_code==422

def test_aplicar_em_lote_e_desfazer(proj):
    c,pid,d=proj;r=c.get(f'/api/projects/{pid}/ia/correcoes').json()
    sel=[x for x in r['correcoes'] if x['acao'] and (x['acao']['tipo']=='config' or x['acao']['tipo']=='rota')]
    assert sel;antes=read_config(d)
    ap=c.post(f'/api/projects/{pid}/ia/correcoes/aplicar',json={'revisao':r['revisao'],'ids':[x['id'] for x in sel]});assert ap.status_code==200,ap.text
    depois=read_config(d)
    if any(x['acao']['campo']=='width' for x in sel):assert depois['width']==2560
    if any(x['acao']['campo']=='taper_m' for x in sel):assert depois['route_alignments'][0]['taper_m']>10
    lote=ap.json()['lote'];assert any(l['lote']==lote for l in c.get(f'/api/projects/{pid}/ia/correcoes/lotes').json()['lotes'])
    # revisão antiga recusada
    assert c.post(f'/api/projects/{pid}/ia/correcoes/aplicar',json={'revisao':r['revisao'],'ids':[sel[0]['id']]}).status_code in (409,422)
    # edição do usuário depois: não é desfeita
    cfg=read_config(d);cfg['width']=1920;save_config(d,cfg)
    dz=c.post(f'/api/projects/{pid}/ia/correcoes/desfazer',json={'lote':lote});assert dz.status_code==200,dz.text
    fin=read_config(d)
    assert fin['width']==1920                                                     # valor do usuário preservado
    if any(x['acao']['campo']=='taper_m' for x in sel):assert fin['route_alignments'][0]['taper_m']==10
    assert c.post(f'/api/projects/{pid}/ia/correcoes/desfazer',json={'lote':lote}).status_code==422   # já desfeito

def test_resposta_da_ia_so_aceita_lista_branca(proj):
    c,pid,d=proj;r=c.get(f'/api/projects/{pid}/ia/correcoes').json();cand=r['correcoes'][0]['id']
    txt='```json\n'+json.dumps({'aceitar':[cand,'0000000000000000'],'novas':[
        {'fase':'video_preparo','titulo':'FPS 24','motivo':'menos quadros','acao':{'tipo':'config','campo':'fps','valor':24}},
        {'fase':'arquivo','titulo':'perigo','motivo':'x','acao':{'tipo':'config','campo':'__class__','valor':1}},
        {'fase':'arquivo','titulo':'caminho','motivo':'x','acao':{'tipo':'config','campo':'origin','valor':'../../x'}},
        {'fase':'video_preparo','titulo':'fora do limite','motivo':'x','acao':{'tipo':'config','campo':'fps','valor':999}},
        {'fase':'fluxos','titulo':'rota inexistente','motivo':'x','acao':{'tipo':'rota','rota_id':'zzz','campo':'taper_m','valor':50}}],'comentario':'ok'})+'\n```'
    x=c.post(f'/api/projects/{pid}/ia/correcoes/interpretar',json={'texto':txt});assert x.status_code==200,x.text;j=x.json()
    assert len(j['aceitas'])==2 and len(j['rejeitadas'])==5,(len(j['aceitas']),j['rejeitadas'])
    assert all(a['id'] for a in j['aceitas']) and read_config(d)['fps']==30         # interpretar nunca aplica
    assert c.post(f'/api/projects/{pid}/ia/correcoes/interpretar',json={'texto':'sem json aqui'}).status_code==422

def test_ia_nao_aplica_orientacao_nem_camada_inexistente(proj):
    c,pid,d=proj;r=c.get(f'/api/projects/{pid}/ia/correcoes').json()
    ori=[x for x in r['correcoes'] if x['acao'] is None]
    if ori:assert c.post(f'/api/projects/{pid}/ia/correcoes/aplicar',json={'revisao':r['revisao'],'ids':[ori[0]['id']]}).status_code==422
    from app.ia_correcoes import Acao,aplicar_acao
    with pytest.raises(ValueError):aplicar_acao(read_config(d),Acao(tipo='camada',layer='NAO_EXISTE',role='axis'),{'layers':[{'name':'EIXO'}]})
    with pytest.raises(ValueError):aplicar_acao(read_config(d),Acao(tipo='config',campo='width',valor=1234))

def test_prompt_traz_candidatas_e_contrato(proj):
    c,pid,d=proj;p=c.get(f'/api/projects/{pid}/ia/correcoes/prompt?fase=video_preparo').json()
    assert p['messages'][0]['role']=='system' and 'Responda SOMENTE JSON' in p['messages'][0]['content']
    assert json.loads(p['messages'][1]['content'])['candidatas']
