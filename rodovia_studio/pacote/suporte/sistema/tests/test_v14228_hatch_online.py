"""Salvar/fechar hachuras sem descartar e conexão online com resposta estruturada."""
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_legacy_empty_origin_does_not_trap_hatch_editor(gl_page,live):
    p=gl_page
    p.evaluate("async()=>{fill({...cfg,origin:'',destination:''});await save();await start('analyze');openSection('Configuração')}")
    box=p.locator('#hatchBox');box.locator('summary').click()
    role=p.locator('#hatchList select[data-hk=role]').first;role.wait_for();sig=role.locator('..').locator('..').get_attribute('data-sig')
    role.select_option('oae');p.locator('#rsPanelSave').click()
    try:p.wait_for_function('!RodoviaPanels.opened',timeout=5000)
    except Exception:raise AssertionError(p.locator('#rsPanelStatus').inner_text())
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    assert saved['hatch_roles'][sig]['role']=='oae'
    assert saved['origin']=='' and saved['destination']==''
    p.evaluate("openSection('Configuração')")
    p.locator('#rsPanelCancel').click();assert p.locator('#rsPanelPopup').is_hidden()
    screenshot(p,'14228_hachura_salva_sem_descartar')


import json
import pytest
from app import small_ai as S
from app.project_state import read_config

@pytest.fixture(autouse=True)
def isolated_online_session(monkeypatch):
    monkeypatch.setattr(S,'_remote',None)


def test_close_then_save_hatch_changes_and_failed_save_preserves_draft(gl_page,live):
    p=gl_page;p.evaluate("openSection('Configuração')")
    p.locator('#hatchBox summary').click();role=p.locator('#hatchList [data-hk=role]').first
    role.select_option('median');p.locator('#rsPanelClose').click()
    p.get_by_role('button',name='Salvar',exact=True).click()
    p.wait_for_function('!RodoviaPanels.opened')
    p.evaluate("openSection('Configuração')")
    p.locator('#name').fill('');p.locator('#rsPanelSave').click()
    p.wait_for_function("document.querySelector('#rsPanelStatus').textContent.includes('nome do projeto')")
    assert p.locator('#rsPanelPopup').is_visible()
    p.locator('#name').fill('Projeto preservado após validação');p.locator('#rsPanelSave').click()
    p.wait_for_function('!RodoviaPanels.opened')


def test_online_configuration_secret_is_memory_only_and_never_echoed(gl_page,live):
    p=gl_page;secret='sk-test-NAO-E-CHAVE-REAL-1234567890'
    r=p.request.post(live[0]+'/api/assistencia/conexao',data={'provider':'openai','model':'gpt-4.1-mini','key':secret})
    assert r.ok and secret not in r.text()
    status=p.request.get(live[0]+'/api/assistencia/modelo').json()
    assert status['online_configured'] and status['online_host']=='api.openai.com'
    assert secret not in json.dumps(status)
    assert all(secret.encode() not in f.read_bytes() for f in live[2].rglob('*') if f.is_file())
    assert p.request.delete(live[0]+'/api/assistencia/conexao').ok
    assert not p.request.get(live[0]+'/api/assistencia/modelo').json()['online_configured']


@pytest.mark.parametrize('data',[
 {'provider':'openai','model':'gpt-4.1-mini','key':'segredo\nHeader: x'},
 {'provider':'intruso','model':'teste','key':'sk-test-valor123'},
 {'provider':'openai','model':'modelo','key':'sk-test-valor123','url':'https://127.0.0.1/admin'}])
def test_invalid_connection_returns_no_secret_or_unapproved_target(gl_page,live,data):
    r=gl_page.request.post(live[0]+'/api/assistencia/conexao',data=data)
    assert r.status==422 and data['key'] not in r.text()


def test_online_ui_contract_reply_reaches_review_and_confirmed_engine_apply(gl_page,live,monkeypatch):
    p=gl_page;d=live[2]/live[1];seen=[];secret='sk-test-CHAVE-SIMULADA-12345678'
    def provider(url,body=None,token=None,**kwargs):
        seen.append((url,body))
        assert token==secret
        assert body['response_format']['type']=='json_schema'
        assert body['response_format']['json_schema']['schema']['additionalProperties'] is False
        return {'choices':[{'message':{'content':json.dumps({'summary':'Conferir material desta camada.','steps':['Confira a amostra antes de aplicar.'],'action':'textures','layers':[{'layer':'PAVIMENTO','role':'pavement','material':'concrete'}]})}}]}
    monkeypatch.setattr(S,'_http',provider)
    p.evaluate("RodoviaSmallAI.open('textures')")
    dialog=p.get_by_role('dialog',name='IA de apoio e mini prompts')
    dialog.get_by_role('button',name='Conectar API online',exact=True).click()
    config=p.get_by_role('dialog',name='Conectar API online')
    assert config.get_by_role('link',name='Obter chave no provedor').get_attribute('href')=='https://platform.openai.com/api-keys'
    config.get_by_label('Chave da API',exact=True).fill(secret)
    config.get_by_role('button',name='Usar conexão nesta sessão').click();config.wait_for(state='detached')
    assert dialog.get_by_label('Provedor IA').input_value()=='online'
    dialog.get_by_label('Camadas para consultar').fill('PAVIMENTO')
    dialog.get_by_role('button',name='Preparar mini prompt').click()
    dialog.get_by_role('button',name='Consultar IA',exact=True).wait_for(state='visible')
    p.wait_for_function("[...document.querySelectorAll('.rsSmallAI button')].some(b=>b.textContent==='Consultar IA'&&!b.disabled)")
    before=read_config(d)
    dialog.get_by_role('button',name='Consultar IA',exact=True).click()
    p.wait_for_function("document.querySelector('.rsSmallAI').textContent.includes('marque a autorização')")
    assert not seen
    dialog.get_by_role('checkbox').check();dialog.get_by_role('button',name='Consultar IA',exact=True).click()
    dialog.get_by_role('button',name='Revisar nas ferramentas do motor').wait_for()
    assert len(seen)==1 and read_config(d)==before
    screenshot(p,'14228_api_resposta_estruturada_revisavel')
    dialog.get_by_role('button',name='Revisar nas ferramentas do motor').click()
    p.locator('#rsIAStudio').wait_for();p.locator('#rsIAStudio [data-ia-layer="PAVIMENTO"]').wait_for(state='visible')
    assert read_config(d)==before
    p.locator('#rsIAStudio [data-ia-layer="PAVIMENTO"] input[type=checkbox]').check()
    p.get_by_role('button',name='Aplicar textura',exact=True).click()
    p.get_by_role('button',name='Confirmar aplicação',exact=True).click()
    p.wait_for_function("document.querySelector('#rsIAStatus').textContent.includes('aplicad')")
    after=read_config(d);assert after['layer_materials']['PAVIMENTO']=='concrete'
    assert after['hatch_roles']==before['hatch_roles']


def test_wrong_provider_reply_is_refused_without_applying(gl_page,live,monkeypatch):
    d=live[2]/live[1];before=read_config(d)
    S.configure_online({'provider':'openai','model':'gpt-4.1-mini','key':'sk-test-NUNCA-ENVIADA'})
    monkeypatch.setattr(S,'_http',lambda *a,**kw:{'choices':[{'message':{'content':json.dumps({'summary':'Remover tudo','steps':['Executar'],'action':'shell','code':'apagar'})}}]})
    prompt=S.prepare(d,{'phase':'general'})
    r=gl_page.request.post(live[0]+'/api/projects/'+live[1]+'/assistencia/modelo',data={'prompt_id':prompt['prompt_id'],'provider':'online','consent_online':True})
    assert r.status==422 and 'contrato' in r.json()['detail'] and read_config(d)==before


@pytest.mark.parametrize('code,expected',[(401,'Chave recusada'),(429,'Limite ou saldo')])
def test_provider_error_has_guidance_without_leaking_credentials(monkeypatch,code,expected):
    import urllib.error
    secret='sk-test-NAO-EXIBIR-123456789'
    S.configure_online({'provider':'openai','model':'gpt-4.1-mini','key':secret})
    def denied(*a,**k):raise urllib.error.HTTPError('https://api.openai.com/v1/chat/completions',code,secret,{},None)
    monkeypatch.setattr(S,'_http',denied)
    with pytest.raises(ValueError) as e:S._online([],True)
    assert expected in str(e.value) and secret not in str(e.value)


def test_cancel_does_not_block_waiting_for_connection_close(monkeypatch):
    import threading
    started=threading.Event();release=threading.Event();ended=threading.Event()
    class Connection:
        def close(self):started.set();release.wait(2);ended.set()
    monkeypatch.setattr(S,'_state',{'active':True,'project':'a'*32,'cancelled':False,'process':None,'connection':Connection()})
    try:
        assert S.cancel('a'*32) and started.wait(1)
        assert not ended.is_set()  # A solicitação retorna sem esperar o socket.
    finally:release.set();assert ended.wait(2)


def test_online_cancel_allows_close_and_discards_late_response(gl_page,live,monkeypatch):
    import threading,time
    p=gl_page;d=live[2]/live[1];started=threading.Event();release=threading.Event()
    S.configure_online({'provider':'openai','model':'gpt-4.1-mini','key':'sk-test-SEM-ENVIO-REAL'})
    def slow(*a,**k):
        started.set();release.wait(8)
        return {'choices':[{'message':{'content':json.dumps({'summary':'Resposta tardia','steps':['Revisar'],'action':'diagnostics','layers':[]})}}]}
    monkeypatch.setattr(S,'_http',slow)
    p.evaluate('RodoviaSmallAI.open()');dialog=p.get_by_role('dialog',name='IA de apoio e mini prompts')
    dialog.get_by_role('button',name='Preparar mini prompt').click()
    p.wait_for_function("[...document.querySelectorAll('.rsSmallAI button')].some(b=>b.textContent==='Consultar IA'&&!b.disabled)")
    before=read_config(d);dialog.get_by_role('checkbox').check()
    try:
        dialog.get_by_role('button',name='Consultar IA',exact=True).click();assert started.wait(5)
        dialog.get_by_role('button',name='Cancelar consulta').click();dialog.get_by_role('button',name='Fechar',exact=True).click()
        assert dialog.count()==0
    finally:release.set()
    deadline=time.monotonic()+5
    while S.active() and time.monotonic()<deadline:time.sleep(.02)
    assert not S.active() and read_config(d)==before
