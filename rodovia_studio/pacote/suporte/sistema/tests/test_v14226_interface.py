"""Contrato da nova página e integração real com os módulos existentes."""
from pathlib import Path
from html.parser import HTMLParser
import json
import pytest
from fastapi.testclient import TestClient
from app.server import app
from test_v142_visual import page
from visual_harness import screenshot

APP=Path(__file__).resolve().parents[1]/'app'

class Contract(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.fields={};self.scripts=[];self.inline=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag in ('input','select','textarea','canvas') and a.get('id'):self.fields[a['id']]=[tag,a.get('type'),a.get('value')]
        if tag=='script':self.scripts.append(a.get('src'))
        self.inline.extend(k for k in a if k.startswith('on'))


def test_document_keeps_motor_contract_without_inline_scripts():
    current=Contract((APP/'index.html').read_text())
    previous=json.loads((Path(__file__).parent/'fixtures/interface_14225.json').read_text())
    assert current.fields==previous['fields']
    assert set(previous['ids'])<=set(current.ids)
    assert len(current.ids)==len(set(current.ids))
    assert current.scripts==['/interface/tema.js'] and not current.inline
    assert '<head>' in (APP/'index.html').read_text() and '<body ' in (APP/'index.html').read_text()


def test_server_composes_interface_and_serves_only_known_assets():
    with TestClient(app) as client:
        r=client.get('/');assert r.status_code==200
        assert 'RODOVIA_INTERFACE_MODULES' not in r.text
        assert '/js/81_contrato_interface.js' in r.text
        assert '<script src="/app.js">' not in r.text
        for name in ('tema.js','estrutura.css'):
            r=client.get('/interface/'+name);assert r.status_code==200
            assert r.headers['cache-control']=='no-store'
        assert client.get('/interface/segredo.txt').status_code==404


@pytest.mark.parametrize('size',[(1920,1080),(1366,768),(1024,768),(760,720)])
def test_responsive_interface_and_canvas_keep_commands(page,size):
    page.set_viewport_size({'width':size[0],'height':size[1]});page.wait_for_timeout(250)
    assert page.evaluate('RodoviaInterface.ready')
    assert page.get_by_role('tab',name='Todas',exact=True).count()==0
    for name in ('Projeto','Editar','Tráfego','Cena','Vídeo'):
        tab=page.get_by_role('tab',name=name,exact=True)
        tab.click();assert tab.get_attribute('aria-selected')=='true'
    rect=page.locator('#canvas').bounding_box();assert rect and rect['width']>size[0]*.6 and rect['height']>200
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
    assert page.locator('#rsStatusActions #rsUpdateProject').count()==1
    screenshot(page,'14226_interface_'+str(size[0]))


def test_keyboard_skip_and_theme(page):
    page.locator('.rsSkipLink').focus();page.keyboard.press('Enter')
    assert page.evaluate('document.activeElement.id')=='projectWorkspace'
    assert page.evaluate("['claro','escuro'].includes(document.documentElement.dataset.tema)")


def test_missing_or_incompatible_document_is_reported_without_automatic_restore(tmp_path,monkeypatch):
    from app.rotas import paginas
    monkeypatch.setattr(paginas,'BASE',tmp_path)
    with TestClient(app) as client:
        r=client.get('/');assert r.status_code==503 and 'quarentena' in r.json()['detail']
        folder=tmp_path/'app';folder.mkdir();(folder/'index.html').write_text('<html></html>')
        r=client.get('/');assert r.status_code==503 and 'incompatível' in r.json()['detail']


def test_external_dialog_close_preserves_existing_button_action(page):
    page.evaluate("document.getElementById('helpDialog').showModal()")
    page.locator('#helpDialog [data-dialog-close]').click()
    assert page.locator('#helpDialog').get_attribute('open') is None
