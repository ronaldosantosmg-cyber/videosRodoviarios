"""Contrato/proteções do adaptador. Testes com dublê NÃO validam um modelo 3B real."""
import json,hashlib,threading,time
from pathlib import Path
import pytest
from app import small_ai as S,store,assistance as A
from app.project_state import read_config,save_config,Conflict
from test_v1425_scene3d import project
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot

@pytest.fixture
def sample(tmp_path,monkeypatch):
    root=tmp_path/'data';root.mkdir();monkeypatch.setattr(store,'ROOT',root);monkeypatch.setattr(store,'DB',root/'studio.sqlite3');monkeypatch.setattr(store,'INSTALL',None);store.init()
    d=root/('a'*32);d.mkdir();d,s=project(d)
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(d.name,s.name))
    S._verified.clear();return d

def response(action='diagnostics',layers=None):return {'choices':[{'message':{'content':json.dumps({'summary':'Proposta a conferir.','steps':['Confirme a entrada e revalide.'],'action':action,'layers':layers or []})}}]}

def test_prepare_is_redacted_bounded_and_never_changes_configuration(sample):
    before=(sample/'config.json').read_bytes();p=S.prepare(sample,{'task':'token=SEGREDO C:\\Users\\operador\\documento.dxf'})
    assert 'SEGREDO' not in json.dumps(p['messages']) and p['prompt_id']
    assert len(p['messages'][1]['content'])<=4200 and before==(sample/'config.json').read_bytes()

def test_reply_is_validated_and_configuration_unchanged(sample,monkeypatch):
    p=S.prepare(sample,{});before=(sample/'config.json').read_bytes();monkeypatch.setattr(S,'_local',lambda _:response())
    r=S.run(sample,{'prompt_id':p['prompt_id']});assert r['reply']['action']=='diagnostics'
    assert not S.active() and before==(sample/'config.json').read_bytes()

@pytest.mark.parametrize('bad',[{'code':'executar'}, {'summary':'x','steps':['x'],'action':'apagar_tudo'}, {'summary':'x','steps':['x'],'action':'video','layers':[]}])
def test_code_unknown_or_out_of_scope_action_is_rejected(sample,monkeypatch,bad):
    p=S.prepare(sample,{});monkeypatch.setattr(S,'_local',lambda _:{'choices':[{'message':{'content':json.dumps(bad)}}]})
    with pytest.raises(ValueError):S.run(sample,{'prompt_id':p['prompt_id']})
    assert not S.active()

def test_stale_and_copied_prompts_are_rejected(sample,monkeypatch):
    p=S.prepare(sample,{});s=read_config(sample);s['traffic_density']=2;save_config(sample,s)
    monkeypatch.setattr(S,'_local',lambda _:pytest.fail('Não pode consultar um contexto obsoleto.'))
    with pytest.raises(Conflict):S.run(sample,{'prompt_id':p['prompt_id']})

def test_result_changed_during_inference_is_discarded(sample,monkeypatch):
    p=S.prepare(sample,{})
    def query(_):
        s=read_config(sample);s['traffic_density']=2;save_config(sample,s);return response()
    monkeypatch.setattr(S,'_local',query)
    with pytest.raises(Conflict):S.run(sample,{'prompt_id':p['prompt_id']})
    assert not S.active()

def test_online_never_sends_without_explicit_consent(sample,monkeypatch):
    p=S.prepare(sample,{});monkeypatch.setattr(S,'_http',lambda *a,**kw:pytest.fail('Envio não autorizado.'))
    with pytest.raises(ValueError,match='confirmação'):S.run(sample,{'prompt_id':p['prompt_id'],'provider':'online'})

def test_known_texture_is_reviewed_not_applied(sample,monkeypatch):
    p=S.prepare(sample,{'phase':'textures','layers':['PAVIMENTO']});before=read_config(sample)
    monkeypatch.setattr(S,'_local',lambda _:response('textures',[{'layer':'PAVIMENTO','role':'pavement','material':'concrete','selected':True}]))
    r=S.run(sample,{'prompt_id':p['prompt_id']});assert r['review']['layers'][0]['selected'] is False and read_config(sample)==before

def test_invented_layer_is_rejected(sample,monkeypatch):
    p=S.prepare(sample,{'phase':'textures','layers':['PAVIMENTO']});monkeypatch.setattr(S,'_local',lambda _:response('textures',[{'layer':'INVENTADA','role':'axis'}]))
    with pytest.raises(ValueError,match='fora do mini'):S.run(sample,{'prompt_id':p['prompt_id']})

def test_memory_guard_no_process_and_missing_model_status(sample,monkeypatch):
    from app import parallel
    monkeypatch.setattr(parallel,'available_memory',lambda:1024**3)
    monkeypatch.setattr(S.subprocess,'Popen',lambda *a,**k:pytest.fail('Memória insuficiente.'))
    with pytest.raises(ValueError,match='Memória'):S._local([])
    assert not S.status()['installed']

def test_model_hash_and_paths_are_checked_before_execution(sample):
    root=S.assets();(root/'runtime').mkdir(parents=True);model=root/'modelo.gguf';model.write_bytes(b'GGUF teste-nao-e-modelo')
    exe=root/('runtime/llama-server.exe' if S.os.name=='nt' else 'runtime/llama-server');exe.write_bytes(b'naoexecutar')
    files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (model,exe)}
    m=root/'modelo.json';m.write_text(json.dumps({'parameters_billions':3,'quantization':'Q4_K_M','files':files}))
    assert S._verify()[1]==model
    model.write_bytes(b'alterado')
    with pytest.raises(ValueError,match='alterado'):S._verify()
    files['../escape']='0'*64;m.write_text(json.dumps({'parameters_billions':3,'quantization':'Q4_K_M','files':files}))
    with pytest.raises(ValueError,match='fora'):S._verify()

def test_concurrent_work_and_cancel_do_not_apply(sample,monkeypatch):
    from app.rotas.comum import enqueue
    from fastapi import HTTPException
    started=threading.Event();done=threading.Event();p=S.prepare(sample,{})
    def query(_):started.set();done.wait(5);return response()
    monkeypatch.setattr(S,'_local',query);errors=[]
    def run():
        try:S.run(sample,{'prompt_id':p['prompt_id']})
        except Exception as e:errors.append(e)
    t=threading.Thread(target=run);t.start();assert started.wait(5)
    try:
        with pytest.raises(HTTPException) as e:enqueue(sample.name,'render')
        assert e.value.status_code==409
        with pytest.raises(ValueError,match='andamento'):S.run(sample,{'prompt_id':p['prompt_id']})
        assert S.cancel(sample.name)
    finally:done.set();t.join(5)
    assert errors and isinstance(errors[0],InterruptedError) and not S.active()

def test_small_model_ui_previews_without_loading_missing_weights(gl_page,live):
    p=gl_page;p.evaluate('RodoviaSmallAI.open()');d=p.get_by_role('dialog',name='IA local 3B e mini prompts')
    d.get_by_role('button',name='Preparar mini prompt').click()
    p.wait_for_function("document.querySelector('.rsMiniPrompt').textContent.includes('system')")
    d.get_by_role('button',name='Consultar IA',exact=True).click()
    p.wait_for_function("document.querySelector('.rsSmallAI').textContent.includes('não há inferência local habilitada')")
    assert not S.active();screenshot(p,'ia3b_mini_prompt_modelo_ausente')
    d.get_by_role('button',name='Fechar',exact=True).click();assert d.count()==0


def test_actual_managed_process_protocol_and_unload_with_non_generative_stub(sample,tmp_path,monkeypatch):
    """Servidor HTTP de teste: comprova transporte/encerramento, NÃO inferência de LLM."""
    import subprocess,sys
    from app import parallel
    monkeypatch.setattr(parallel,'available_memory',lambda:8*1024**3)
    script=tmp_path/'provider_test.py'
    script.write_text('''import sys,json
from http.server import HTTPServer,BaseHTTPRequestHandler
port=int(sys.argv[sys.argv.index('--port')+1])
key=sys.argv[sys.argv.index('--api-key')+1]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b'{"status":"ok"}')
 def do_POST(self):
  assert self.headers['Authorization']=='Bearer '+key
  request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  assert request['max_tokens']==512 and request['stream'] is False
  reply={"summary":"Dublê de protocolo, não LLM.","steps":["Revisar."],"action":"diagnostics","layers":[]}
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({"choices":[{"message":{"content":json.dumps(reply)}}]}).encode())
HTTPServer(('127.0.0.1',port),Handler).serve_forever()
''')
    monkeypatch.setattr(S,'_verify',lambda:(tmp_path/'llama-server',tmp_path/'modelo.gguf'))
    popen=subprocess.Popen;children=[]
    def managed(args,**kwargs):
        assert args[args.index('--host')+1]=='127.0.0.1' and '--ctx-size' in args
        p=popen([sys.executable,str(script),*args[1:]],**kwargs);children.append(p);return p
    monkeypatch.setattr(S.subprocess,'Popen',managed)
    p=S.prepare(sample,{});result=S.run(sample,{'prompt_id':p['prompt_id']})
    assert result['reply']['summary'].startswith('Dublê') and children[0].poll() is not None
    assert not S.active() and S._state['process'] is None


def test_textures_response_reaches_existing_review_ui_without_applying(gl_page,live):
    p=gl_page;d=live[2]/live[1];before=read_config(d)
    report=A.report(d,d.name)
    result=A.import_response(d,{'format':'rodovia-ia-resposta-1','report_id':report['report_id'],'layers':[{'layer':'PAVIMENTO','role':'pavement','material':'concrete'}]})
    p.evaluate('(data)=>RodoviaIA.accept(data)',result)
    p.wait_for_function("document.querySelector('#rsIAStudio')?.open")
    assert p.locator('#rsIAStudio [data-ia-layer="PAVIMENTO"]').is_visible()
    assert read_config(d)==before


def test_retention_only_removes_old_derived_prompt_pairs(sample):
    first=None
    for i in range(21):
        p=S.prepare(sample,{'task':str(i)})
        folder=sample/'ia/mini_prompts'
        if first is None:first=p['prompt_id'];(folder/'anotacao.txt').write_text('preservar')
        (folder/(p['prompt_id']+'-resposta.json')).write_text('{}')
    assert not (folder/(first+'.json')).exists() and not (folder/(first+'-resposta.json')).exists()
    assert (folder/'anotacao.txt').read_text()=='preservar'
    assert len(list(folder.glob('*-resposta.json')))==20


@pytest.mark.parametrize('value',[{'segment':True},{'layers':['x'*301]},{'layers':[None]},{'phase':'executar_codigo'}])
def test_invalid_input_is_rejected_before_context_or_provider(value):
    with pytest.raises(ValueError):S.Query.model_validate(value)


def test_texture_scope_cannot_reclassify_axis(sample,monkeypatch):
    p=S.prepare(sample,{'phase':'textures','layers':['EIXO']})
    monkeypatch.setattr(S,'_local',lambda _:response('textures',[{'layer':'EIXO','role':'axis'}]))
    with pytest.raises(ValueError,match='fora do mini'):S.run(sample,{'prompt_id':p['prompt_id']})


def test_corrupt_manifest_is_unavailable_instead_of_server_error(sample):
    root=S.assets();root.mkdir();(root/'modelo.json').write_text('[]')
    assert S.status()['installed'] is False
