"""Percurso real de criação, gravação e referência persistente de imagem convertida."""
import hashlib
import numpy as np
import tifffile
from test_v1425_live_3d import live,gl_page
from visual_harness import screenshot


def test_create_save_and_reopen_identified_project_from_empty_browser(gl_page,live):
    context=gl_page.context.browser.new_context(viewport={'width':1440,'height':900})
    p=context.new_page()
    p.route('**/*',lambda r:r.continue_() if r.request.url.startswith(live[0]+'/') else r.abort())
    try:
        p.goto(live[0],wait_until='networkidle')
        p.wait_for_function('!!window.RodoviaNewProject')
        assert not p.evaluate('pid')
        p.get_by_role('menuitem',name='Arquivo',exact=True).click()
        p.locator('.rsCascade').get_by_role('menuitem',name='Novo projeto',exact=True).click()
        for field,value in [('Name','Projeto novo validado'),('Origin','Origem de teste'),('Destination','Destino de teste'),('Start','284+000'),('End','285+000')]:p.locator('#rsNew'+field).fill(value)
        p.locator('#rsNewCreate').click()
        p.wait_for_function('!!pid && !document.querySelector("#rsNewProject").open',timeout=15000)
        identity=p.evaluate('pid');url=live[0]+'/api/projects/'+identity
        p.evaluate("async()=>{$('name').value='Projeto novo salvo';scheduleSave();await save()}")
        p.reload(wait_until='networkidle');p.wait_for_function('(id)=>pid===id && cfg.name===\"Projeto novo salvo\"',arg=identity,timeout=15000)
        screenshot(p,'1429_01_novo_projeto_reaberto')
        config=p.request.get(url).json()['config']
        assert config['origin']=='Origem de teste' and config['destination']=='Destino de teste'
        assert config['km_start_m']==284000 and config['km_end_m']==285000
    finally:context.close()


def test_cached_conversion_reference_survives_ui_save_mixed_mode_and_reload(gl_page,live,tmp_path):
    from app.imagery_cache import register
    p=gl_page;url=live[0]+'/api/projects/'+live[1]
    source=tmp_path/'imagem.ecw';source.write_bytes(b'fonte-de-teste-cache-1429')
    converted=tmp_path/'convertida.tif'
    pixels=np.full((128,128,3),(35,125,185),dtype=np.uint8)
    keys=[1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,31983]
    tifffile.imwrite(converted,pixels,photometric='rgb',extratags=[(33550,'d',3,(4.,4.,0.),False),(33922,'d',6,(0.,0.,0.,499226.,7801024.,0.),False),(34735,'H',len(keys),keys,False)])
    entry=register(source,converted,extra={'format':'GeoTIFF'})
    response=p.request.post(url+'/imagery',multipart={'files':{'name':source.name,'mimeType':'application/octet-stream','buffer':source.read_bytes()},'mode':'replace'})
    assert response.ok,response.text()
    # O upload altera a revisão no servidor; a interface real recarrega antes de converter.
    p.evaluate('(id)=>load(id)',live[1])
    p.evaluate("async()=>{await start('imagery/convert')}")
    assert p.evaluate('cfg.local_imagery.image')=='imagem_convertido.tif'
    assert p.evaluate('projectSession.revision')==p.request.get(url).json()['config_revision']
    p.get_by_role('tab',name='Projeto',exact=True).click()
    p.locator('#rsTechnicalOptions').locator('..').evaluate('(el)=>el.open=true')
    p.locator('#rsPresentationBase').select_option('mixed')
    p.evaluate('save()')
    p.reload(wait_until='networkidle')
    p.wait_for_function('!!cfg.local_imagery?.image',timeout=15000)
    saved=p.request.get(url).json()['config']
    assert saved['imagery']=='esri'
    assert saved['local_imagery']['image']=='imagem_convertido.tif'
    assert p.locator('#rsPresentationBase').input_value()=='mixed'
    output=live[2]/live[1]/'imagem_local'/'imagem_convertido.tif'
    assert hashlib.sha256(output.read_bytes()).digest()==hashlib.sha256(converted.read_bytes()).digest()
    assert entry['tif'].is_file()
    screenshot(p,'1429_02_imagem_convertida_mista')
