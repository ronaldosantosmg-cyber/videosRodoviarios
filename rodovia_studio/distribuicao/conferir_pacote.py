"""Conferência do ZIP real; execução de binários Windows não é simulada como aprovação nativa."""
import hashlib,json,shutil,sys,tempfile,zipfile
from pathlib import Path
from types import SimpleNamespace
import instalar as I
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]

def main():
    proof=json.loads((HERE/'evidencias/pacote.json').read_text());p=REPO/'atualizacoes'/proof['zip']
    assert I.sha(p)==proof['sha256']
    with tempfile.TemporaryDirectory(prefix='rs_instalador_real_') as temporary:
        tmp=Path(temporary);I.unpack(p,tmp/'entrada');root=tmp/'entrada/Rodovia Studio 2.02';m=I.verify(root,proof['manifest_sha256'])
        assert proof['manifest_sha256'].encode('utf-16le') in (root/'INSTALAR RODOVIA STUDIO.exe').read_bytes()
        assert all(b'asInvoker' in f.read_bytes() for f in (root/'INSTALAR RODOVIA STUDIO.exe',root/'payload/Rodovia Studio.exe'))
        assert I.sha(root/'payload/aplicativo.zip')=='2654167d0fadbf9b293f15ecd8bdf89eccc19c069b137ee630f1c0863b7bc0ed'
        assert (root/'payload/aplicativo.zip').read_bytes()==(REPO/'atualizacoes/RodoviaStudio_2_02_atualizacao.zip').read_bytes()
        calls=[]
        def local_wheel(row,directory,cancel=None):
            source=Path('/tmp/rodovia-distribuicao-cache/wheels')/row['filename'];assert I.sha(source)==row['sha256'];Path(directory).mkdir(parents=True,exist_ok=True);shutil.copy2(source,Path(directory)/source.name)
        # Somente os subprocessos Windows são substituídos. Hashes, extração,
        # mapeamento, cópia, estado final e caminho com acento são executados de fato.
        I.os=SimpleNamespace(name='nt');I.run=lambda args,*a,**k:calls.append([str(x) for x in args]);I.download=local_wheel
        target=tmp/'Instalação com espaços ç';I.install(root,target,proof['manifest_sha256'])
        program=target/'sistema/programa';checked=0
        with zipfile.ZipFile(root/'payload/aplicativo.zip') as archive:
            prefix='pacote/suporte/sistema/'
            for name in archive.namelist():
                if name.startswith(prefix):assert (program/name[len(prefix):]).read_bytes()==archive.read(name);checked+=1
        assert json.loads((target/'sistema/distribuicao.json').read_text())['installation_complete']
        assert all((program/'pacotes'/row['filename']).is_file() for row in m['dependencies'])
        result=dict(zip_sha256=I.sha(p),manifest_hash_embedded_in_exe=True,all_payload_hashes_checked=True,embedded_application_bytes_unchanged=True,program_files_compared=checked,python_extracted=True,windows_wheels_staged=len(m['dependencies']),path_with_spaces_and_accents=True,completion_state=True,subprocesses_recorded=calls,windows_native_executed=False,scope='Layout e integridade reais; pip, imports e FFmpeg Windows não foram executados neste Linux. Os scripts de instalação os executam no PC de destino antes da conclusão.')
        (HERE/'evidencias/pacote-real.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='subprocesses_recorded'},ensure_ascii=False))

if __name__=='__main__':main()
