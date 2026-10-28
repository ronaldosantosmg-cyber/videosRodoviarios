"""Ícones reais: arquivo fornecido, renderização SVG e comandos existentes."""
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from test_v142_visual import page
from test_v1425_live_3d import live,gl_page,open3d
from visual_harness import screenshot

ASSET=Path(__file__).resolve().parents[1]/'app/icons/infrarail-sprite.svg'


def test_supplied_sprite_is_intact_and_contains_only_local_passive_graphics():
    assert hashlib.sha256(ASSET.read_bytes()).hexdigest()=='a54a83c01a61d34d60706f0d761e7d2226f36ba86dc9ebefd81989a72745e9dc'
    root=ET.fromstring(ASSET.read_bytes());symbols=root.findall('.//{*}symbol')
    assert len(symbols)==32 and len({s.attrib['id'] for s in symbols})==32
    for element in root.iter():
        assert element.tag.split('}')[-1] in {'svg','defs','symbol','path','circle','line','rect','text'}
        assert not any(k.lower().startswith('on') or 'href' in k.lower() for k in element.attrib)
        assert not any('url(' in value.lower() for value in element.attrib.values())


def test_technical_icons_render_and_keep_their_actual_commands_and_helpers(page):
    for tool,symbol in [('flowcut','delete-segment'),('flowjoin','merge-segments'),('railway','catenary-rail'),('traffic_signal','cantilever-signal'),('oae','oae-viaduct')]:
        button=page.locator(f'#rsToolRibbon [data-activity] [data-rs-tool="{tool}"]').first
        activity=button.evaluate('(b)=>b.closest("[data-activity]").dataset.activity')
        page.get_by_role('tab',name=activity,exact=True).click()
        page.locator('[data-activity="'+activity+'"] details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')
        assert button.count()==1
        assert button.locator('use').get_attribute('href')=='#infrarail-'+symbol
        assert button.get_attribute('aria-label')
        assert button.get_attribute('data-rs-help') or button.get_attribute('title')
        button.hover();assert page.locator('#rsToolHelp').is_visible()
        bounds=button.locator('use').evaluate('(e)=>{const b=e.getBBox();return [b.width,b.height]}')
        assert min(bounds)>0
        button.click();assert page.evaluate('tool')==tool
        page.evaluate("setTool('pan')")
    # Comandos sem equivalente continuam usando seus ícones existentes.
    assert page.locator('#rsQuickNavigation [data-rs-tool=pan] svg path').count()>0
    screenshot(page,'14211_01_icones_barra_tecnica')


def test_all_32_symbols_render_locally_in_the_real_application(gl_page):
    p=gl_page
    assert p.locator('symbol[id^=infrarail-]').count()==32
    p.evaluate("""()=>{const d=document.createElement('dialog');d.id='rsIconReview';d.style='width:850px';d.innerHTML='<h2>Pacote InfraRail — 32 símbolos locais</h2><div style="display:grid;grid-template-columns:repeat(8,1fr);gap:16px">'+[...document.querySelectorAll('symbol[id^=infrarail-]')].map(s=>'<div style="text-align:center">'+RodoviaInfraRail.icon(s.id.replace('infrarail-',''))+'</div>').join('')+'</div>';document.body.appendChild(d);d.showModal()}""")
    sizes=p.locator('#rsIconReview use').evaluate_all('(nodes)=>nodes.map(e=>{const b=e.getBBox();return [b.width,b.height]})')
    assert len(sizes)==32 and all(min(s)>0 for s in sizes)
    screenshot(p,'14211_02_pacote_32_simbolos')
    p.evaluate("document.getElementById('rsIconReview').remove()")
    p.evaluate('RodoviaAssetCatalog.open()');p.wait_for_selector('#rsAssetGallery [data-material=gas] use')
    assert p.locator('#rsAssetGallery [data-material=gas] use').get_attribute('href')=='#infrarail-gas-pipeline'
    p.locator('#rsAssetSearch').fill('erosao')
    assert p.locator('#rsAssetGallery [data-material=erosion] use').get_attribute('href')=='#infrarail-slope-erosion'
    p.locator('#rsAssetSearch').fill('');screenshot(p,'14211_03_catalogo_com_simbolos')
    p.locator('#rsAssetCatalog footer [data-close]').click()
    open3d(p)
    light=p.locator('[data-rs3d=light3d]')
    assert light.locator('use').get_attribute('href')=='#infrarail-day-mode'
    light.click();light.click()
    assert p.evaluate('Rodovia3D.stats().light')=='noite'
    assert light.locator('use').get_attribute('href')=='#infrarail-night-mode'
    light.click()


def test_recovery_and_flow_direction_icons_preserve_accessible_text(page):
    page.evaluate("editor={...editor,segments:[{id:0,points:[[0,0],[100,0]],mid:[50,0],both:true}]};selSeg=editor.segments[0];showSegProps()")
    assert page.locator('[data-flow-recovery=recover] use').get_attribute('href')=='#infrarail-auto-fix'
    assert page.locator('[data-flow-recovery=recover]').inner_text()=='Recuperar fluxo principal…'
    assert page.locator('.rsFlowDirection use').get_attribute('href')=='#infrarail-dual-flow'
    assert page.locator('.rsFlowDirection').inner_text()=='Sentido duplo'
