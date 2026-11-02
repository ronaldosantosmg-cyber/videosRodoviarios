"""1.40.6 — testes visuais funcionais do shell desktop.

Estes testes usam o HTML/CSS/JS reais. Não são testes de strings: medem geometria na tela,
acionam painéis/atalhos e capturam screenshots quando VISUAL_ARTIFACTS está definido.
"""
import os, pytest
pw=pytest.importorskip('playwright.sync_api')
from visual_harness import chromium_path,load_offline,rect,overlap,screenshot

@pytest.fixture
def visual_page():
    exe=chromium_path()
    if not exe:pytest.skip('Chromium não encontrado. Defina CHROMIUM ou instale o navegador de testes.')
    errors=[]
    with pw.sync_playwright() as p:
        browser=p.chromium.launch(executable_path=exe,args=['--disable-gpu'])
        page=browser.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append('page: '+str(e)))
        page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
        load_offline(page)
        yield page,errors
        browser.close()

def test_visual_shell_inicia_limpo_e_viewport_domina(visual_page):
    page,errors=visual_page
    assert not errors, errors
    body=page.inner_text('body')
    for forbidden in ('BR-381','BR 381','NOVA 381','TH57'):
        assert forbidden not in body
    assert page.locator('#menuBar').is_visible()
    tabs=page.locator('#menuBar .rbTabs .mb')
    assert tabs.count()>=6
    canvas=rect(page,'.canvasWrap')
    assert canvas['width'] >= 0.72*1600
    assert canvas['height'] >= 0.55*1000
    assert page.locator('#dwCommandDrawer').is_hidden()
    screenshot(page,'01_shell_inicial')

def test_visual_painel_esquerdo_redimensiona_sem_sobrepor(visual_page):
    page,errors=visual_page
    before=rect(page,'.canvasWrap')
    page.evaluate("pnAbrir(pnItens[0].id)")
    page.wait_for_timeout(250)
    panel=rect(page,'.pnArea')
    after=rect(page,'.canvasWrap')
    assert after['width'] < before['width']
    assert overlap(panel,after) < 1
    assert page.evaluate("document.body.classList.contains('pnAberto')")
    screenshot(page,'02_painel_projeto')
    assert not errors,errors

def test_visual_painel_direito_e_recolhimento(visual_page):
    page,errors=visual_page
    page.evaluate("recolherDock(false)")
    page.wait_for_timeout(200)
    canvas=rect(page,'.canvasWrap');side=rect(page,'.editorSide')
    assert overlap(canvas,side)<1
    w_open=canvas['width']
    page.evaluate("recolherDock(true)")
    page.wait_for_timeout(200)
    assert rect(page,'.canvasWrap')['width']>w_open
    screenshot(page,'03_painel_lateral_recolhido')
    assert not errors,errors

def test_visual_linha_comando_e_gaveta_nao_sobrepoe(visual_page):
    page,errors=visual_page
    before=rect(page,'.canvasWrap')
    page.keyboard.press('Control+Space')
    page.wait_for_timeout(180)
    assert page.locator('#dwCommandDrawer').is_visible()
    drawer=rect(page,'#dwCommandDrawer');after=rect(page,'.canvasWrap')
    pos=page.evaluate("getComputedStyle(document.getElementById('dwCommandDrawer')).position")
    assert pos not in ('fixed','absolute')
    assert after['height'] < before['height']
    assert overlap(drawer,after)<1
    screenshot(page,'04_linha_comando')
    page.keyboard.press('Control+Space')
    assert page.locator('#dwCommandDrawer').is_hidden()
    assert not errors,errors

def test_visual_modo_projeto_maximiza_area(visual_page):
    page,errors=visual_page
    page.evaluate("pnAbrir(pnItens[0].id);recolherDock(false)")
    page.wait_for_timeout(150)
    normal=rect(page,'.canvasWrap')
    page.keyboard.press('F11')
    page.wait_for_timeout(250)
    focus=rect(page,'.canvasWrap')
    assert page.evaluate("document.body.classList.contains('dwProjectFocus')")
    assert focus['width']>normal['width']
    assert page.locator('#atividades').is_hidden()
    screenshot(page,'05_modo_projeto')
    page.keyboard.press('F11')
    assert not errors,errors

def test_visual_responsivo_1366x768_sem_estouro_horizontal(visual_page):
    page,errors=visual_page
    page.set_viewport_size({'width':1366,'height':768});page.wait_for_timeout(220)
    metrics=page.evaluate("({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,sh:document.documentElement.scrollHeight,ch:document.documentElement.clientHeight})")
    assert metrics['sw'] <= metrics['cw']+2
    assert rect(page,'.canvasWrap')['width']>700
    screenshot(page,'06_1366x768')
    assert not errors,errors

def test_visual_logo_permanece_visivel(visual_page):
    page,errors=visual_page
    logo=page.locator('.dev img[alt="GeoRas Consultoria"]')
    assert logo.is_visible()
    box=logo.bounding_box();assert box and box['width']>=30 and box['height']>=18
    ok=page.evaluate("""()=>{const i=document.querySelector('.dev img[alt=\"GeoRas Consultoria\"]');return i.complete&&i.naturalWidth>0&&i.naturalHeight>0}""")
    assert ok
    screenshot(page,'07_logo_preservado')
    assert not errors,errors

def test_visual_estabilidade_30_ciclos_paineis_sem_deriva(visual_page):
    page,errors=visual_page
    start=rect(page,'.canvasWrap')
    for _ in range(30):
        page.evaluate("pnAbrir(pnItens[0].id)")
        page.wait_for_timeout(8)
        page.evaluate("pnAbrir(null)")
        page.wait_for_timeout(8)
        page.evaluate("recolherDock(false)")
        page.wait_for_timeout(8)
        page.evaluate("recolherDock(true)")
    end=rect(page,'.canvasWrap')
    assert abs(end['x']-start['x'])<2
    assert abs(end['y']-start['y'])<2
    assert abs(end['width']-start['width'])<3
    assert abs(end['height']-start['height'])<3
    screenshot(page,'08_estabilidade_30_ciclos')
    assert not errors,errors

def test_visual_1280x720_controles_essenciais_acessiveis(visual_page):
    page,errors=visual_page
    page.set_viewport_size({'width':1280,'height':720});page.wait_for_timeout(220)
    metrics=page.evaluate("({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth})")
    assert metrics['sw']<=metrics['cw']+2
    assert page.locator('#menuBar').is_visible()
    assert rect(page,'.canvasWrap')['width']>620
    assert rect(page,'.canvasWrap')['height']>340
    screenshot(page,'09_1280x720')
    assert not errors,errors

def test_visual_alternancia_rapida_comando_foco_sem_erro(visual_page):
    page,errors=visual_page
    for _ in range(12):
        page.keyboard.press('Control+Space');page.wait_for_timeout(10)
        page.keyboard.press('Control+Space');page.wait_for_timeout(10)
        page.keyboard.press('F11');page.wait_for_timeout(10)
        page.keyboard.press('F11');page.wait_for_timeout(10)
    assert page.locator('#dwCommandDrawer').is_hidden()
    assert not page.evaluate("document.body.classList.contains('dwProjectFocus')")
    screenshot(page,'10_stress_comando_foco')
    assert not errors,errors

def test_visual_elementos_interativos_sem_alvos_minimos_criticos(visual_page):
    page,errors=visual_page
    vals=page.evaluate("""()=>[...document.querySelectorAll('button:not([hidden]), .mb:not([hidden])')].filter(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'}).map(e=>{const r=e.getBoundingClientRect();return {t:(e.innerText||e.title||'').trim(),w:r.width,h:r.height}})""")
    bad=[v for v in vals if v['w']>0 and v['h']>0 and (v['w']<22 or v['h']<22)]
    assert len(bad)<=3,bad[:10]
    screenshot(page,'11_alvos_interativos')
    assert not errors,errors
