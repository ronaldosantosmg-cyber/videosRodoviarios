"""1.40.7 — testes visuais ampliados de usabilidade e robustez.

Usa a interface real em Chromium com fixtures offline determinísticas. Valida logo, imagem local,
ordem visual, estabilidade do viewport/regeneração, seleção em pixels e erros de comando sem travar.
"""
import pytest
pw=pytest.importorskip('playwright.sync_api')
from visual_harness import chromium_path,load_offline,rect,overlap,screenshot

@pytest.fixture
def visual_page_1407():
    exe=chromium_path()
    if not exe:pytest.skip('Chromium não encontrado.')
    errors=[]
    with pw.sync_playwright() as p:
        browser=p.chromium.launch(executable_path=exe,args=['--disable-gpu'])
        page=browser.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append('page: '+str(e)))
        page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
        load_offline(page)
        yield page,errors
        browser.close()

def test_logo_permanece_em_layouts_e_modo_projeto(visual_page_1407):
    page,errors=visual_page_1407
    logo=page.locator('.dev img[alt="GeoRas Consultoria"]')
    assert logo.is_visible()
    b0=logo.bounding_box();assert b0 and b0['width']>=30 and b0['height']>=18
    page.evaluate("pnAbrir(pnItens[0].id);recolherDock(false)")
    page.keyboard.press('F11');page.wait_for_timeout(120)
    assert logo.is_visible(), 'O modo Projeto não pode remover o logo da aplicação.'
    screenshot(page,'1407_01_logo_modo_projeto')
    assert not errors,errors

def test_ordem_visual_de_imagens_exibe_topo_subir_descer_fundo(visual_page_1407):
    page,errors=visual_page_1407
    page.evaluate("""async()=>{
      window.__oldApi=window.api;
      eval("pid='11111111111111111111111111111111'");
      cfg={local_imagery:{image:'a.tif',name:'Orto A',detail:true,editor:true,brightness:0,contrast:0,saturation:0,nodata:'borda'}};
      const info={gdal:true,pixel_m:.12,max_zoom:21,count:2,editor:true,sources:[
        {index:0,name:'Orto A',file:'a.tif',size:[8000,6000],pixel_m:.12,crs:'EPSG:31983',bounds:[0,0,100,100],adjust:{shift_x:0,shift_y:0,rotation_deg:0,scale:1}},
        {index:1,name:'Orto B',file:'b.tif',size:[7000,5000],pixel_m:.15,crs:'EPSG:31983',bounds:[0,0,100,100],adjust:{shift_x:0,shift_y:0,rotation_deg:0,scale:1}}
      ]};
      api=async u=>String(u).includes('/local/info')?info:{};
      await localUi();
    }""")
    txt=page.inner_text('#imgList')
    assert all(x in txt for x in ('Topo','▲','▼','Fundo','Orto A','Orto B'))
    assert page.locator('#imgList [data-imgtop="1"]').is_enabled()
    assert page.locator('#imgList [data-imgbottom="0"]').is_enabled()
    screenshot(page,'1407_02_ordem_visual_imagens')
    assert not errors,errors

def test_regeneracao_nao_altera_viewport(visual_page_1407):
    page,errors=visual_page_1407
    result=page.evaluate("""()=>{
      view.s=3.25;view.ox=137.5;view.oy=-42.75;
      const a={...view};
      for(let i=0;i<50;i++)regenScreen();
      return {a,b:{...view}};
    }""")
    assert result['a']==result['b']
    screenshot(page,'1407_03_regeneracao_estavel')
    assert not errors,errors

def test_paineis_nao_sobrepoem_viewport_em_1024(visual_page_1407):
    page,errors=visual_page_1407
    page.set_viewport_size({'width':1024,'height':768});page.wait_for_timeout(120)
    page.evaluate("pnAbrir(pnItens[0].id);recolherDock(false)");page.wait_for_timeout(140)
    canvas=rect(page,'.canvasWrap');right=rect(page,'.editorSide')
    assert overlap(canvas,right)<1
    assert canvas['width']>500 and canvas['height']>300
    assert not page.evaluate("document.body.classList.contains('pnAberto')"), 'Ao abrir o painel direito em 1024 px, o esquerdo deve fechar para preservar o desenho.'
    screenshot(page,'1407_04_1024_paineis_sem_overlay')
    assert not errors,errors

def test_comando_invalido_nao_trava_interface(visual_page_1407):
    page,errors=visual_page_1407
    page.evaluate("runCommand('COMANDO_QUE_NAO_EXISTE_1407')")
    page.wait_for_timeout(50)
    assert page.locator('.canvasWrap').is_visible()
    assert page.locator('#menuBar').is_visible()
    # O sistema deve continuar aceitando um comando válido depois do erro controlado.
    page.evaluate("runCommand('SNAP')")
    assert page.locator('#snapOn').is_checked()
    screenshot(page,'1407_05_erro_controlado')
    assert not errors,errors

def test_hit_test_em_pixels_encontra_objetos_sobrepostos(visual_page_1407):
    page,errors=visual_page_1407
    count=page.evaluate("""()=>{
      const oldMeta=meta,oldBase=baseImage,oldMode=baseMode,oldSigns=M.signs,oldView={...view};
      try{
        meta={width_m:1000,screen_width:1000,screen_height:1000,camera:[0,0],right:[1,0],up:[0,1]};
        baseImage={width:1000,height:1000};baseMode='preview';view={s:1,ox:0,oy:0};
        const p={x:0,y:0},c=W2C(p);
        M.signs=[{point:p,name:'A'},{point:{...p},name:'B'}];
        return hitObjects({cx:c[0],cy:c[1]}).length;
      } finally { meta=oldMeta;baseImage=oldBase;baseMode=oldMode;M.signs=oldSigns;view=oldView; }
    }""")
    assert count>=2
    screenshot(page,'1407_06_selecao_sobreposta')
    assert not errors,errors

def test_stress_visual_50_ciclos_sem_deriva_ou_console_error(visual_page_1407):
    page,errors=visual_page_1407
    start=rect(page,'.canvasWrap')
    for _ in range(50):
        page.evaluate("pnAbrir(pnItens[0].id);pnAbrir(null);recolherDock(false);recolherDock(true);regenScreen()")
    end=rect(page,'.canvasWrap')
    assert abs(end['x']-start['x'])<2 and abs(end['y']-start['y'])<2
    assert abs(end['width']-start['width'])<3 and abs(end['height']-start['height'])<3
    screenshot(page,'1407_07_stress_50_ciclos')
    assert not errors,errors

def test_shell_comando_modo_projeto_e_1366(visual_page_1407):
    page,errors=visual_page_1407
    page.set_viewport_size({'width':1366,'height':768});page.wait_for_timeout(100)
    before=rect(page,'.canvasWrap')
    page.keyboard.press('Control+Space');page.wait_for_timeout(80)
    assert page.locator('#dwCommandDrawer').is_visible()
    after=rect(page,'.canvasWrap');drawer=rect(page,'#dwCommandDrawer')
    assert after['height']<before['height'] and overlap(after,drawer)<1
    page.keyboard.press('Control+Space')
    normal=rect(page,'.canvasWrap');page.keyboard.press('F11');page.wait_for_timeout(100)
    focus=rect(page,'.canvasWrap')
    assert focus['width']>=normal['width'] and page.locator('.dev img[alt="GeoRas Consultoria"]').is_visible()
    page.keyboard.press('F11')
    metrics=page.evaluate("({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth})")
    assert metrics['sw']<=metrics['cw']+2
    screenshot(page,'1407_08_shell_comando_foco_1366')
    assert not errors,errors

def test_alvos_interativos_essenciais_nao_ficam_microscopicos(visual_page_1407):
    page,errors=visual_page_1407
    vals=page.evaluate("""()=>[...document.querySelectorAll('button:not([hidden]), .mb:not([hidden])')].filter(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'}).map(e=>{const r=e.getBoundingClientRect();return {t:(e.innerText||e.title||'').trim(),w:r.width,h:r.height}})""")
    bad=[v for v in vals if v['w']>0 and v['h']>0 and (v['w']<22 or v['h']<22)]
    assert len(bad)<=3,bad[:10]
    screenshot(page,'1407_09_alvos_interativos')
    assert not errors,errors
