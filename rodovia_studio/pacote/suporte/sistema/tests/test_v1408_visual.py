"""1.40.8 — usabilidade visual do estado KMZ."""
import pytest
pw=pytest.importorskip('playwright.sync_api')
from visual_harness import chromium_path,load_offline,screenshot


def test_estado_kmz_necessario_visivel():
    exe=chromium_path()
    if not exe:pytest.skip('Chromium não encontrado.')
    errors=[]
    with pw.sync_playwright() as p:
        browser=p.chromium.launch(executable_path=exe,args=['--disable-gpu'])
        page=browser.new_page(viewport={'width':1366,'height':768},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append('page: '+str(e)))
        page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
        load_offline(page)
        page.evaluate("""()=>{
          analysis={kmz_status:{present:true,read_ok:true,used:true,required:true,uses:['eixo_fallback','pois'],message:'KMZ usado como eixo.'}};
          filesUi({dxf:null,kmz:{name:'referencia.kmz',bytes:123456,sent:'agora'}});
        }""")
        txt=page.inner_text('#fileState')
        assert 'KMZ NECESSÁRIO' in txt and 'eixo' in txt and 'POIs' in txt
        screenshot(page,'1408_01_kmz_necessario')
        assert not errors,errors
        browser.close()
