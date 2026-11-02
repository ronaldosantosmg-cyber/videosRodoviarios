import io,threading,time,uuid
import ezdxf
from fastapi.testclient import TestClient
from app.server import app
from app import store


def dxf_bytes():
    d=ezdxf.new();d.modelspace().add_line((0,0),(10,0));b=io.StringIO();d.write(b);return b.getvalue().encode()


def running_job(pid,state='running'):
    jid=uuid.uuid4().hex
    with store.connect() as c:c.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'analyze',state,'teste'))
    return jid


def test_substituir_dxf_com_motor_ocupado_exige_pedido_explicito_e_solta_o_motor(monkeypatch):
    monkeypatch.setenv('RODOVIA_RELEASE_WAIT_S','10')
    with TestClient(app) as c:
        pid=c.post('/api/projects',json={}).json()['id']
        assert c.post(f'/api/projects/{pid}/files',files={'file':('a.dxf',dxf_bytes())}).status_code==200
        jid=running_job(pid)
        r=c.post(f'/api/projects/{pid}/files',files={'file':('b.dxf',dxf_bytes())})
        assert r.status_code==409 and 'tarefa' in r.json()['detail']          # sem pedido: continua protegido
        def supervisor():                                                     # simula o supervisor encerrando o processo do motor
            for _ in range(50):
                if store.job(jid)['state']=='cancel_requested':store.update(jid,state='cancelled',message='encerrado');return
                time.sleep(.1)
        t=threading.Thread(target=supervisor);t.start()
        r=c.post(f'/api/projects/{pid}/files?force=1',files={'file':('b.dxf',dxf_bytes())});t.join()
        assert r.status_code==200,r.text
        assert store.job(jid)['state']=='cancelled'


def test_motor_que_nao_encerra_devolve_erro_claro_sem_tocar_no_projeto(monkeypatch):
    monkeypatch.setenv('RODOVIA_RELEASE_WAIT_S','1')
    with TestClient(app) as c:
        pid=c.post('/api/projects',json={}).json()['id']
        assert c.post(f'/api/projects/{pid}/files',files={'file':('a.dxf',dxf_bytes())}).status_code==200
        running_job(pid)
        before=(store.directory(pid)/'input.dxf').read_bytes()
        r=c.post(f'/api/projects/{pid}/files?force=1',files={'file':('b.dxf',dxf_bytes()+b'\n')})
        assert r.status_code==409 and 'preservados' in r.json()['detail']
        assert (store.directory(pid)/'input.dxf').read_bytes()==before


def test_troca_tenta_de_novo_quando_o_arquivo_esta_momentaneamente_em_uso(tmp_path,monkeypatch):
    from app import project_state as ps
    calls=[]
    real=ps.os.replace
    def flaky(a,b):
        calls.append(1)
        if len(calls)<3:raise PermissionError('em uso')
        return real(a,b)
    monkeypatch.setattr(ps.os,'replace',flaky);monkeypatch.setattr(ps.time,'sleep',lambda s:None)
    a=tmp_path/'a';b=tmp_path/'b';a.write_text('x');ps._replace_retry(a,b)
    assert b.read_text()=='x' and len(calls)==3
