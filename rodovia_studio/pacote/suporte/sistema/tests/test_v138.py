"""1.38: instalador do leitor ECW nunca compila o GDAL; cai para download direto das rodas e explica o erro."""
import subprocess,sys,pytest

FONTE=('Traceback (most recent call last):\n  File "pip\\_vendor\\pyproject_hooks\\_impl.py", line 196, in get_requires_for_build_wheel\n'
       '    return self._call_hook(\nERROR: Failed to build installable wheels for some pyproject.toml based projects (gdal)')

def preparar(monkeypatch,tmp_path,win=True):
    import app.ecw_engine as E
    monkeypatch.setattr(E,'OFFLINE',tmp_path/'pacotes_ecw');monkeypatch.setattr(E,'BASE',tmp_path)
    monkeypatch.setattr(E,'status',lambda:{'ecw':True,'python_gdal':'3.11.4','ready':True})
    monkeypatch.setattr(E,'_tags',lambda:('cp312','win_amd64' if win else None))
    monkeypatch.setattr(E,'_proxy',lambda:None)
    return E

def test_pip_so_binario(tmp_path,monkeypatch):
    E=preparar(monkeypatch,tmp_path);calls=[]
    def run(cmd,**kw):calls.append(cmd);return subprocess.CompletedProcess(cmd,0,'ok','')
    E.install(run=run)
    assert len(calls)==2 and all('--only-binary=:all:' in c for c in calls)

def test_compilacao_cai_para_download_direto(tmp_path,monkeypatch):
    E=preparar(monkeypatch,tmp_path);calls=[];baixados=[]
    def run(cmd,**kw):
        calls.append(cmd)
        if '--no-index' in cmd:return subprocess.CompletedProcess(cmd,0,'ok','')
        return subprocess.CompletedProcess(cmd,1,'',FONTE)
    def fetch(url,dest):baixados.append(url);dest.write_bytes(b'w');return dest
    fj=lambda u:{'urls':[{'filename':'gdal_ecw-3.11.3-py3-none-win32.whl','url':'https://x/32.whl'},
                         {'filename':'gdal_ecw-3.11.3-py3-none-win_amd64.whl','url':'https://x/64.whl'}]}
    st=E.install(run=run,fetch=fetch,fetch_json=fj)
    assert st['ecw']
    assert baixados[0].endswith('gdal-3.11.4-cp312-cp312-win_amd64.whl') and 'github.com/cgohlke' in baixados[0]
    assert baixados[1]=='https://x/64.whl'
    assert (tmp_path/'pacotes_ecw'/'gdal_ecw-3.11.3-py3-none-win_amd64.whl').exists()
    assert '--no-index' in calls[-1]

def test_mensagem_clara_sem_rede(tmp_path,monkeypatch):
    E=preparar(monkeypatch,tmp_path)
    def run(cmd,**kw):return subprocess.CompletedProcess(cmd,1,'',FONTE)
    def fetch(url,dest):raise OSError('[Errno 11001] getaddrinfo failed')
    with pytest.raises(ValueError) as e:E.install(run=run,fetch=fetch,fetch_json=lambda u:{})
    m=str(e.value)
    assert 'compilá-lo do código-fonte' in m and 'sem acesso ao servidor' in m
    assert 'gdal-3.11.4-cp312-cp312-win_amd64.whl' in m and 'gdal_ecw-3.11.3' in m and str(tmp_path/'pacotes_ecw') in m
    assert '_impl.py' not in m and 'Traceback' not in m
    assert (tmp_path/'pacotes_ecw_log.txt').exists()

def test_proxy_do_windows_passado_ao_pip(tmp_path,monkeypatch):
    E=preparar(monkeypatch,tmp_path);monkeypatch.setattr(E,'_proxy',lambda:'http://proxy.empresa:8080');calls=[]
    def run(cmd,**kw):calls.append(cmd);return subprocess.CompletedProcess(cmd,0,'ok','')
    E.install(run=run)
    assert calls[0][calls[0].index('--proxy')+1]=='http://proxy.empresa:8080'
    assert '--proxy' not in [x for c in calls if '--no-index' in c for x in c]

def test_url_da_roda_pela_versao_do_python():
    import app.ecw_engine as E
    v=sys.version_info;u=E.GDAL_WHEEL_URL.format(tag=f'cp{v.major}{v.minor}',plat='win_amd64')
    assert u.endswith(f'-cp{v.major}{v.minor}-cp{v.major}{v.minor}-win_amd64.whl')
