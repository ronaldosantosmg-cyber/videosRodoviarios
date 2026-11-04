"""Aplica o complemento em bases reais e verifica HTML preservado, UI e reversão."""
import hashlib,json,os,socket,subprocess,sys,tempfile,time,urllib.request,zipfile,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
VERSION=json.loads((ROOT/'suporte/sistema/VERSAO.json').read_text())['version']
SLUG=VERSION.replace('.','_')
sys.path.insert(0,str(ROOT/'suporte/sistema'))
import atualizador
from portao import _install_sintetico


def extract(file,target):
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        archive.extractall(target)  # Pacotes locais do repositório, validados a seguir.
    package=target/'pacote';atualizador.validate_package(package,lambda *_:None);return package


def digest(file):return hashlib.sha256(file.read_bytes()).hexdigest()


def verify():
    rows=[];file=ROOT/f'atualizacoes/RodoviaStudio_{SLUG}_atualizacao_sem_html.zip'
    with zipfile.ZipFile(file) as patch,zipfile.ZipFile(ROOT/f'atualizacoes/RodoviaStudio_{SLUG}_atualizacao.zip') as complete:
        expected={n for n in complete.namelist() if Path(n).suffix.lower() not in ('.html','.htm')}
        assert set(patch.namelist())==expected
        for name in expected-{'pacote/manifest.json'}:assert patch.read(name)==complete.read(name),name
    with tempfile.TemporaryDirectory(prefix='studio-sem-html-') as tmp:
        tmp=Path(tmp);package=extract(file,tmp/'patch')
        assert not any(f.suffix.lower() in ('.html','.htm') for f in package.rglob('*') if f.is_file())
        # Sem base funcional, o atualizador precisa recusar antes de substituir o programa.
        fresh,program=_install_sintetico(tmp/'fresh')
        with_error=False
        try:atualizador.apply(package,fresh,lambda *_:None,check_running=False)
        except atualizador.PackageError:with_error=True
        assert with_error and json.loads((program/'VERSAO.json').read_text())['version']=='0.0'
        for version in ('3.18','3.21'):
            case=tmp/version;case.mkdir();base=extract(ROOT/f'atualizacoes/RodoviaStudio_{version.replace(".","_")}_atualizacao.zip',case/'base')
            install,program=_install_sintetico(case)
            atualizador.apply(base,install,lambda *_:None,check_running=False)
            htmls={name:digest(program/'app'/name) for name in ('index.html','ajuda.html')}
            atualizador.apply(package,install,lambda *_:None,check_running=False)
            assert htmls=={name:digest(program/'app'/name) for name in htmls}
            with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            url=f'http://127.0.0.1:{port}'
            env={**os.environ,'RODOVIA_DATA':str(case/'dados'),'RODOVIA_PORT':str(port),'RODOVIA_NO_BROWSER':'1'}
            with (case/'server.log').open('w') as log:
                proc=subprocess.Popen([sys.executable,str(program/'run.py')],cwd=program,env=env,stdout=log,stderr=log)
                try:
                    for _ in range(100):
                        try:
                            health=json.load(urllib.request.urlopen(url+'/api/health',timeout=1));break
                        except OSError:time.sleep(.1)
                    else:raise AssertionError('Servidor não iniciou: '+(case/'server.log').read_text())
                    assert health['version']==VERSION
                    req=urllib.request.Request(url+'/api/projects',data=b'{}',headers={'Content-Type':'application/json'})
                    pid=json.load(urllib.request.urlopen(req))['id']
                    with sync_playwright() as p:
                        browser=p.chromium.launch(headless=True,executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
                        page=browser.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                        page.add_init_script("localStorage.setItem('rodovia_base',JSON.stringify({mode:'none',ta:1,va:1}))")
                        page.goto(url);page.wait_for_function('typeof load==="function" && window.RodoviaMenus && window.RodoviaLighting')
                        page.evaluate('(id)=>load(id)',pid)
                        assert page.locator('[data-rs-menu]').count()==7
                        page.evaluate('RodoviaLighting.open()');page.locator('#rsDayNight [data-mode]').select_option('night')
                        page.locator('#rsDayNight [data-save]').click();page.locator('#rsDayNight').wait_for(state='detached')
                        assert page.evaluate('cfg.day_night')=='night'
                        assert not errors,errors
                        browser.close()
                    # Política carregada da instalação resultante, não do código-fonte do teste.
                    code="""from types import SimpleNamespace as S
from app.models import Settings
from app.fleet_policy import require_export
s=S(s=Settings(),simulation_complete=True,collisions=0,side_collisions=0,fleet_audit={'violations':[{'vehicle':1,'path':1,'station_m':135.37,'time_s':202.2,'gap_m':8.088,'reason':'lider','remaining_to_exit_m':432.1}]})
s.simulation_complete=False
require_export(s,s.s,allow_partial=True)
s.simulation_complete=True
require_export(s,s.s)
s.collisions=1
try:require_export(s,s.s)
except ValueError:pass
else:raise AssertionError('Colisão liberada')
print('Comboio não bloqueia; colisão continua bloqueando.')
"""
                    subprocess.run([sys.executable,'-c',code],cwd=program,env=env,check=True,capture_output=True,text=True)
                finally:proc.terminate();proc.wait(timeout=10)
            atualizador.restore_previous(install,None,lambda *_:None,check_running=False)
            assert json.loads((program/'VERSAO.json').read_text())['version']==version
            assert htmls=={name:digest(program/'app'/name) for name in htmls}
            # Reproduz metadado novo com política real antiga, depois repara a MESMA versão.
            atualizador.apply(package,install,lambda *_:None,check_running=False)
            policy=program/'app/fleet_policy.py'
            policy.write_bytes((base/'suporte/sistema/app/fleet_policy.py').read_bytes())
            old_case=code.split('s.simulation_complete=False')[0]+"\ntry:require_export(s,s.s)\nexcept ValueError as e:assert 'comboio' in str(e)\nelse:raise AssertionError('Não reproduziu política antiga')\n"
            subprocess.run([sys.executable,'-c',old_case],cwd=program,env=env,check=True,capture_output=True,text=True)
            pending=install/'atualizacoes'/file.name;shutil.copyfile(file,pending)
            repair=subprocess.run([sys.executable,str(program/'atualizador.py'),'--raiz',str(install),'--procurar','--sem-verificar-aberto'],cwd=program,env=env,check=True,capture_output=True,text=True)
            assert 'Reparando' in repair.stdout,repair.stdout
            assert policy.read_bytes()==(package/'suporte/sistema/app/fleet_policy.py').read_bytes()
            subprocess.run([sys.executable,'-c',code],cwd=program,env=env,check=True,capture_output=True,text=True)
            assert htmls=={name:digest(program/'app'/name) for name in htmls}
            rows.append({'base':version,'updated_version':VERSION,'html_files_preserved':True,'server_and_browser_ok':True,'lighting_saved':True,'convoy_does_not_block':True,'collisions_block':True,'rollback_ok':True,'real_old_policy_error_reproduced':True,'same_version_mixed_source_repaired':True})
    return {'archive':file.name,'sha256':digest(file),'html_in_archive':0,'other_payload_identical_to_complete_package':True,'fresh_install_rejected':True,'cases':rows,'defender_scan':'not_available_in_linux'}


if __name__=='__main__':
    report=verify();output=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dist/sem_html_validacao.json'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
