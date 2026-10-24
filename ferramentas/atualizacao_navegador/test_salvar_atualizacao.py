import json
import functools
import http.server
import threading
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]
RELEASE=json.loads((REPO/'atualizacoes/canal_estavel.json').read_text())
ZIP=(REPO/'atualizacoes'/RELEASE['filename']).read_bytes()

PAGE_URL=''

@pytest.fixture(scope='session',autouse=True)
def serve_helper():
    global PAGE_URL
    class Silent(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Silent,directory=str(BASE)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    PAGE_URL=f'http://127.0.0.1:{server.server_port}/Salvar_Atualizacao_Rodovia_Studio.html'
    yield
    server.shutdown();thread.join(timeout=5);server.server_close()


@pytest.fixture
def browser():
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        yield b
        b.close()


def load(browser,*,data=None,body=ZIP,existing=False,folder='atualizacoes',cancel=False,denied=False,unsupported=False):
    page=browser.new_page(viewport={'width':1280,'height':900});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('https://raw.githubusercontent.com/**',lambda r:r.fulfill(status=200,body=json.dumps(data or RELEASE) if r.request.url.endswith('.json') else body,headers={'Access-Control-Allow-Origin':'*','Content-Type':'application/json' if r.request.url.endswith('.json') else 'application/zip'}))
    page.add_init_script('window.__written=null;window.__created=0;window.__aborted=0;')
    if unsupported:page.add_init_script('window.showDirectoryPicker=undefined')
    page.goto(PAGE_URL)
    supported=page.evaluate("({secure:isSecureContext,picker:typeof showDirectoryPicker==='function'})")
    assert supported=={'secure':True,'picker':not unsupported}
    if not unsupported:page.evaluate("""(opt)=>{
      const handle={name:opt.folder,getFileHandle:async(name,options)=>{
       if(!options?.create){if(opt.existing)return {};throw new DOMException('Não encontrado','NotFoundError')}
       window.__created++;if(opt.denied)throw new DOMException('Permissão negada','NotAllowedError');
       return {createWritable:async()=>({write:async bytes=>{window.__written=bytes.byteLength},close:async()=>{},abort:async()=>{window.__aborted++}})};
      }};
      window.showDirectoryPicker=async()=>{if(opt.cancel)throw new DOMException('Cancelado','AbortError');return handle};
    }""",dict(folder=folder,existing=existing,cancel=cancel,denied=denied))
    page.wait_for_function("document.getElementById('version').textContent!=='Consultando a atualização disponível…'")
    return page,errors


def test_verified_bytes_are_saved_only_after_folder_choice(browser):
    page,errors=load(browser)
    assert page.locator('#save').is_disabled()
    page.locator('#choose').click();page.locator('#save').click()
    page.wait_for_function('window.__written!==null')
    assert page.evaluate('__written')==len(ZIP)
    assert 'SHA-256 conferido' in page.locator('#status').inner_text()
    assert not errors
    out=REPO/'ferramentas/atualizacao_navegador/evidencias';out.mkdir(exist_ok=True)
    page.screenshot(path=str(out/'pagina_gravacao_validada.png'))


def test_hash_mismatch_never_creates_file(browser):
    page,errors=load(browser,body=b'arquivo alterado')
    page.locator('#choose').click();page.locator('#save').click()
    page.get_by_text('SHA-256 divergente.',exact=False).wait_for()
    assert page.evaluate('__created')==0 and page.evaluate('__written') is None
    assert not errors


def test_existing_zip_is_preserved(browser):
    page,errors=load(browser,existing=True)
    page.locator('#choose').click();page.locator('#save').click()
    page.get_by_text('Esse ZIP já existe',exact=False).wait_for()
    assert page.evaluate('__created')==0 and page.evaluate('__written') is None
    assert not errors


def test_wrong_folder_refused(browser):
    page,errors=load(browser,folder='Documentos')
    page.locator('#choose').click()
    assert page.locator('#save').is_disabled()
    assert 'Pasta incorreta' in page.locator('#folder').inner_text()
    assert not errors


def test_cancel_does_not_grant_access(browser):
    page,errors=load(browser,cancel=True)
    page.locator('#choose').click()
    assert page.locator('#save').is_disabled()
    assert 'cancelada' in page.locator('#status').inner_text()
    assert not errors


def test_invalid_release_metadata_blocks_download(browser):
    data={**RELEASE,'filename':'outro.zip'}
    page,errors=load(browser,data=data)
    page.locator('#choose').click()
    assert page.locator('#save').is_disabled()
    assert 'inválidos' in page.locator('#status').inner_text()
    assert not errors


def test_revoked_write_permission_is_reported(browser):
    page,errors=load(browser,denied=True)
    page.locator('#choose').click();page.locator('#save').click()
    page.get_by_text('Permissão negada',exact=False).wait_for()
    assert page.evaluate('__written') is None
    assert not errors


def test_unsupported_browser_offers_manual_download(browser):
    page,errors=load(browser,unsupported=True)
    assert page.locator('#choose').is_disabled() and page.locator('#save').is_disabled()
    assert page.locator('#manual').is_visible()
    assert 'não oferece escolha de pasta' in page.locator('#status').inner_text()
    assert not errors
