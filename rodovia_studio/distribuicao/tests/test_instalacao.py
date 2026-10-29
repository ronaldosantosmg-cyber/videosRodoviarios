import hashlib,io,json,os,stat,sys,zipfile
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import instalar as I
sha=lambda b:hashlib.sha256(b).hexdigest()

@pytest.fixture
def bundle(tmp_path):
    root=tmp_path/'pacote';(root/'payload/webview2').mkdir(parents=True)
    repo=Path(__file__).resolve().parents[3]
    (root/'payload/aplicativo.zip').write_bytes((repo/'atualizacoes/RodoviaStudio_2_02_atualizacao.zip').read_bytes())
    with zipfile.ZipFile(root/'payload/python.nupkg','w') as z:z.writestr('tools/python.exe',b'python aprovado')
    (root/'payload/Rodovia Studio.exe').write_bytes(b'iniciador aprovado');(root/'payload/webview2/loader.dll').write_bytes(b'loader aprovado')
    m=dict(version='2.02',architecture='win_amd64',authenticode_signed=False,dependencies=[],files={p.relative_to(root).as_posix():I.sha(p) for p in root.rglob('*') if p.is_file()})
    f=root/'distribuicao.json';f.write_text(json.dumps(m));return root,I.sha(f)

@pytest.mark.parametrize('name',['../fora','/absoluto','C:/disco','pasta\\arquivo','a/../../b'])
def test_zip_paths_cannot_escape(name,tmp_path):
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as f:f.writestr(name,b'x')
    with pytest.raises(ValueError):I.unpack(z,tmp_path/'dest')
    assert not (tmp_path/'fora').exists()


def test_zip_link_is_refused(tmp_path):
    z=tmp_path/'link.zip';info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
    with zipfile.ZipFile(z,'w') as f:f.writestr(info,b'/etc/passwd')
    with pytest.raises(ValueError,match='Links'):I.unpack(z,tmp_path/'dest')


def test_manifest_and_payload_tamper_are_refused(bundle):
    root,digest=bundle;assert I.verify(root,digest)['version']=='2.02'
    (root/'payload/Rodovia Studio.exe').write_bytes(b'alterado')
    with pytest.raises(ValueError,match='alterado'):I.verify(root,digest)
    with pytest.raises(ValueError,match='Manifesto'):I.verify(root,'0'*64)


def test_cancel_does_not_touch_destination(bundle,tmp_path,monkeypatch):
    root,digest=bundle;monkeypatch.setattr(I,'os',SimpleNamespace(name='nt'));cancel=tmp_path/'cancel';cancel.touch();dest=tmp_path/'novo'
    with pytest.raises(I.Cancelled):I.install(root,dest,digest,cancel)
    assert not dest.exists() and not list(tmp_path.glob('.rodovia-instalar-*'))


def test_existing_project_is_never_overwritten(bundle,tmp_path,monkeypatch):
    root,digest=bundle;monkeypatch.setattr(I,'os',SimpleNamespace(name='nt'));dest=tmp_path/'existente';dest.mkdir();data=dest/'projeto.json';data.write_text('preservar')
    with pytest.raises(ValueError,match='pasta nova'):I.install(root,dest,digest)
    assert data.read_text()=='preservar'


def test_clean_install_uses_real_app_updater_and_pinned_local_wheels(bundle,tmp_path,monkeypatch):
    root,digest=bundle;monkeypatch.setattr(I,'os',SimpleNamespace(name='nt'));calls=[];monkeypatch.setattr(I,'run',lambda a,*args,**k:calls.append(a))
    dest=tmp_path/'pasta com espaço ç'/'novo';I.install(root,dest,digest)
    program=dest/'sistema/programa'
    assert (program/'app/index.html').is_file() and (program/'app/flow_reconstruction.py').is_file()
    assert (dest/'Rodovia Studio.exe').is_file() and (program/'runtime/python.exe').is_file()
    assert all((dest/p).is_dir() for p in ('projetos','videos','atualizacoes'))
    installs=[a for a in calls if 'install' in a]
    assert len(installs)==2 and all('--no-index' in a and '--require-hashes' in a for a in installs)
    assert len([a for a in calls if str(a[-1]).endswith('diagnostico.py')])==2
    assert (program/'runtime/dependencias.ok').read_text().strip()==I.sha(program/'requirements-windows.lock')
    assert not list(dest.parent.glob('.rodovia-instalar-*'))


@pytest.mark.parametrize('at_commit',[False,True])
def test_failed_preparation_cleans_stage_and_failed_final_probe_preserves_data(bundle,tmp_path,monkeypatch,at_commit):
    root,digest=bundle;monkeypatch.setattr(I,'os',SimpleNamespace(name='nt'));dest=tmp_path/'nova';other=tmp_path/'dados';other.write_text('preservar')
    def fail(a,*args,**k):
        if dest.exists()==at_commit:
            if at_commit:(dest/'projetos/dado-recebido.json').write_text('preservar também')
            raise RuntimeError('falha dirigida')
    monkeypatch.setattr(I,'run',fail)
    with pytest.raises(RuntimeError,match='falha dirigida'):I.install(root,dest,digest)
    assert other.read_text()=='preservar' and not list(tmp_path.glob('.rodovia-instalar-*'))
    if at_commit:
        assert (dest/'projetos/dado-recebido.json').read_text()=='preservar também'
        assert json.loads((dest/'sistema/distribuicao.json').read_text())['installation_complete'] is False
    else:assert not dest.exists()


def test_destination_parent_link_refused(tmp_path):
    real=tmp_path/'real';real.mkdir();link=tmp_path/'link';link.symlink_to(real,target_is_directory=True)
    with pytest.raises(ValueError,match='links'):I.destination(link/'novo')


@pytest.mark.parametrize('url',['http://files.pythonhosted.org/x','https://evil.example/x','https://127.0.0.1/x'])
def test_download_refuses_unapproved_origin(url,tmp_path):
    with pytest.raises(ValueError,match='Origem'):I.download(dict(filename='a.whl',sha256='0'*64,url=url,bytes=1),tmp_path)


def test_download_verifies_size_hash_and_reuses_only_matching_file(tmp_path,monkeypatch):
    data=b'wheel aprovado';url='https://files.pythonhosted.org/a.whl';row=dict(filename='a.whl',sha256=sha(data),url=url,bytes=len(data));calls=[]
    def get(u,**kwargs):
        calls.append(u);f=io.BytesIO(data);f.url=url;return f
    monkeypatch.setattr(I.urllib.request,'urlopen',get)
    path=I.download(row,tmp_path);assert path.read_bytes()==data;I.download(row,tmp_path);assert len(calls)==1
    path.write_bytes(b'corrompido');I.download(row,tmp_path);assert len(calls)==2
    path.unlink();row['sha256']='0'*64
    with pytest.raises(ValueError,match='Hash'):I.download(row,tmp_path)
    assert not list(tmp_path.glob('*.download')) and not path.exists()


def test_signature_flow_does_not_create_or_trust_certificate():
    source=(Path(__file__).resolve().parents[1]/'assinar.ps1').read_text()
    assert 'Set-AuthenticodeSignature' in source and '1.3.6.1.5.5.7.3.3' in source and 'Ronaldo Santos' in source
    assert all(s not in source for s in ('New-SelfSignedCertificate','Import-Certificate','ExecutionPolicy Bypass','Set-MpPreference'))


def test_null_path_is_refused_before_extraction():
    with pytest.raises(ValueError):I.safe_name("bad\x00name")


def test_manifest_requests_current_user_without_elevation():
    import xml.etree.ElementTree as ET
    document=ET.parse(Path(__file__).resolve().parents[1]/'aplicativo.manifest')
    level=document.find('.//{urn:schemas-microsoft-com:asm.v3}requestedExecutionLevel')
    assert level.get('level')=='asInvoker' and level.get('uiAccess')=='false'
