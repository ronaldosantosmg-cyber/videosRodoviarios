"""1.40.9 — testes visuais e de interação ampliados."""
import pytest
pw=pytest.importorskip('playwright.sync_api')
from visual_harness import chromium_path,load_offline,rect,overlap,screenshot

@pytest.fixture(scope='module')
def pagefx():
    exe=chromium_path()
    if not exe:pytest.skip('Chromium não encontrado.')
    errors=[]
    with pw.sync_playwright() as p:
        b=p.chromium.launch(executable_path=exe,args=['--disable-gpu','--no-sandbox'])
        page=b.new_page(viewport={'width':1600,'height':900},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append('page: '+str(e)))
        page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
        load_offline(page)
        yield page,errors
        b.close()

def clean(page,errors):
    assert page.locator('.canvasWrap').is_visible();assert not errors,errors

def test_visual_01_logo_persistente_em_tema_e_foco(pagefx):
    page,errors=pagefx;logo=page.locator('.dev img[alt="GeoRas Consultoria"]');assert logo.is_visible()
    page.evaluate("if(typeof aplicarTema==='function')aplicarTema('escuro',false)");page.keyboard.press('F11');page.wait_for_timeout(80)
    assert logo.is_visible();page.keyboard.press('F11');page.evaluate("if(typeof aplicarTema==='function')aplicarTema('claro',false)")
    screenshot(page,'1409_01_logo_tema_foco');clean(page,errors)

def test_visual_02_matriz_responsiva_sem_overlay(pagefx):
    page,errors=pagefx
    for w,h in [(1920,1080),(1600,900),(1366,768),(1280,720),(1024,768)]:
        page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(60)
        page.evaluate("pnAbrir(pnItens[0].id);recolherDock(false)");page.wait_for_timeout(60)
        c=rect(page,'.canvasWrap');r=rect(page,'.editorSide');assert overlap(c,r)<1,(w,h,c,r)
        assert c['width']>=480 and c['height']>=280,(w,h,c)
        page.evaluate("pnAbrir(null);recolherDock(true)")
    screenshot(page,'1409_02_responsivo');clean(page,errors)

def test_visual_03_atalhos_repetidos_nao_quebram_layout(pagefx):
    page,errors=pagefx;page.set_viewport_size({'width':1366,'height':768});page.evaluate("pnAbrir(null);recolherDock(true)")
    for _ in range(12):
        page.keyboard.press('Control+Space');page.keyboard.press('Control+Space');page.keyboard.press('Control+B');page.keyboard.press('Control+B');page.keyboard.press('Control+Alt+B');page.keyboard.press('Control+Alt+B')
    c=rect(page,'.canvasWrap');assert c['width']>600 and c['height']>300
    screenshot(page,'1409_03_atalhos_stress');clean(page,errors)

def test_visual_04_regeneracao_100x_preserva_viewport(pagefx):
    page,errors=pagefx
    r=page.evaluate("""()=>{view.s=4.125;view.ox=121.75;view.oy=-63.5;const a={...view};for(let i=0;i<100;i++)regenScreen();return {a,b:{...view}}}""")
    assert r['a']==r['b'];screenshot(page,'1409_04_regen_100x');clean(page,errors)

def test_visual_05_selecao_sobreposta_e_ciclo(pagefx):
    page,errors=pagefx
    n=page.evaluate("""()=>{const om=meta,ob=baseImage,ov={...view},os=M.signs;try{meta={width_m:1000,screen_width:1000,screen_height:1000,camera:[0,0],right:[1,0],up:[0,1]};baseImage={width:1000,height:1000};view={s:1,ox:0,oy:0};const p={x:0,y:0},c=W2C(p);M.signs=[{point:p,name:'A'},{point:{...p},name:'B'},{point:{...p},name:'C'}];return hitObjects({cx:c[0],cy:c[1]}).length}finally{meta=om;baseImage=ob;view=ov;M.signs=os}}""")
    assert n>=3;screenshot(page,'1409_05_sobreposicao');clean(page,errors)

def test_visual_06_kmz_todos_os_estados(pagefx):
    page,errors=pagefx
    cases=[
      ({'present':True,'read_ok':True,'used':True,'required':True,'uses':['eixo_fallback']},'KMZ NECESSÁRIO'),
      ({'present':True,'read_ok':True,'used':True,'required':False,'uses':['georreferenciamento','pois']},'KMZ em uso'),
      ({'present':True,'read_ok':True,'used':False,'required':False,'uses':[]},'KMZ validado como referência')]
    for st,needle in cases:
        page.evaluate("([st])=>{analysis={kmz_status:st};filesUi({dxf:{name:'modelo.dxf',bytes:5000,sent:'agora'},kmz:{name:'referencia.kmz',bytes:6000,sent:'agora'}})}",[st])
        assert needle in page.inner_text('#fileState')
    screenshot(page,'1409_06_kmz_estados');clean(page,errors)

def test_visual_07_ordem_imagem_explicita(pagefx):
    page,errors=pagefx
    page.evaluate("""async()=>{eval("pid='11111111111111111111111111111111'");cfg={local_imagery:{image:'a.tif',name:'A',detail:true,editor:true,brightness:0,contrast:0,saturation:0,nodata:'borda'}};const info={gdal:true,pixel_m:.1,max_zoom:21,count:3,editor:true,sources:[0,1,2].map(i=>({index:i,name:'Orto '+(i+1),file:i+'.tif',size:[8000,6000],pixel_m:.1,crs:'EPSG:31983',bounds:[0,0,100,100],adjust:{shift_x:0,shift_y:0,rotation_deg:0,scale:1}}))};api=async u=>String(u).includes('/local/info')?info:{};await localUi()}""")
    txt=page.inner_text('#imgList');assert all(x in txt for x in ('Topo','▲','▼','Fundo','Orto 1','Orto 2','Orto 3'))
    screenshot(page,'1409_07_ordem_imagem');clean(page,errors)

def test_visual_08_rota_expoe_politica_de_ultrapassagem(pagefx):
    page,errors=pagefx
    ok=page.evaluate("""()=>{M.route_alignments=[{id:'r1',name:'Rota 01',points:[{x:0,y:0},{x:500,y:0}],lane_change:'marked',lane_change_sections:[{start_m:100,end_m:250,mode:'allow'}]}];sel={key:'route_alignments',i:0};showProps();return document.querySelector('#propPanel')?.innerText||''}""")
    assert 'Ultrapassagem e mudança de faixa' in ok and 'Somente em trechos permitidos' in ok and 'Trecho permitido' in ok
    screenshot(page,'1409_08_rota_politica');clean(page,errors)

def test_visual_09_erro_controlado_seguido_de_comando_valido(pagefx):
    page,errors=pagefx;page.evaluate("runCommand('INEXISTENTE_1409');runCommand('SNAP')")
    assert page.locator('#snapOn').is_checked();screenshot(page,'1409_09_erro_recuperacao');clean(page,errors)

def test_visual_10_100_ciclos_paineis_sem_deriva(pagefx):
    page,errors=pagefx;page.set_viewport_size({'width':1600,'height':900});page.evaluate("pnAbrir(null);recolherDock(true)");start=rect(page,'.canvasWrap')
    for _ in range(100):page.evaluate("pnAbrir(pnItens[0].id);pnAbrir(null);recolherDock(false);recolherDock(true)")
    end=rect(page,'.canvasWrap');assert abs(end['x']-start['x'])<2 and abs(end['width']-start['width'])<3
    screenshot(page,'1409_10_100_ciclos');clean(page,errors)

def test_visual_11_sem_overflow_horizontal_essencial(pagefx):
    page,errors=pagefx
    for w,h in [(1366,768),(1280,720),(1024,768)]:
        page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(40)
        m=page.evaluate("({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth})")
        assert m['sw']<=m['cw']+2,(w,m)
    screenshot(page,'1409_11_sem_overflow');clean(page,errors)

def test_visual_12_logo_nao_some_apos_stress(pagefx):
    page,errors=pagefx
    for _ in range(20):page.keyboard.press('F11');page.keyboard.press('F11')
    assert page.locator('.dev img[alt="GeoRas Consultoria"]').is_visible()
    screenshot(page,'1409_12_logo_stress');clean(page,errors)
