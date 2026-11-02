"""1.42.38: Retirar imagem dentro do painel de camadas (janela com edição pendente) realmente retira e não fecha a janela."""
import httpx
from test_v1425_live_3d import live,gl_page
from test_v117 import ortho,write_geotiff,X0


def test_retirar_imagem_com_edicao_pendente_no_painel(gl_page,live,tmp_path):
    base,pid,root=live;c=httpx.Client(base_url=base,timeout=60);p=gl_page
    for n,dx in (('a.tif',0),('b.tif',40)):
        write_geotiff(tmp_path/n,ortho(),x0=X0+dx)
        r=c.post(f'/api/projects/{pid}/imagery',files=[('files',(n,(tmp_path/n).read_bytes()))],data={'mode':'replace' if n=='a.tif' else 'add'});assert r.status_code==200,r.text
    p.evaluate('(pid)=>load(pid)',pid);p.wait_for_timeout(800);p.evaluate('()=>localUi()');p.wait_for_timeout(500)
    assert p.evaluate('localInfo.sources.length')==2
    p.evaluate("psOpenHub('layers')");p.wait_for_function("RodoviaPanels.opened==='hub:layers'")
    p.evaluate("document.querySelectorAll('#rsPanelBody details').forEach(d=>d.open=true)")
    # edição pendente na janela (o caso em que o botão antes não fazia nada)
    p.evaluate("()=>{const n=document.getElementById('name');n.value=n.value+'x';n.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert p.evaluate('RodoviaPanels.pending')
    deletes=[];p.on('request',lambda q:deletes.append(q.url) if q.method=='DELETE' else None)
    p.locator('[data-imgdel="1"]').click();p.wait_for_selector('#confirmDlg[open]');p.locator('#confirmNo').click()   # "Só retirar"

    p.wait_for_function('localInfo.sources.length===1',timeout=15000)
    assert any(u.endswith('/imagery/1') for u in deletes)
    assert p.evaluate('RodoviaPanels.opened')=='hub:layers'                  # a janela continua aberta, com a edição pendente
    assert p.evaluate('(cfg.local_imagery.others||[]).length')==0
    assert c.get(f'/api/projects/{pid}').json()['config']['local_imagery'].get('others',[])==[]
    p.evaluate('RodoviaPanels.saveAndClose()');p.wait_for_function("!RodoviaPanels.opened",timeout=15000);p.wait_for_timeout(1500)
    cfg=c.get(f'/api/projects/{pid}').json()['config']
    assert cfg['local_imagery'].get('others',[])==[] and cfg['name'].endswith('x')      # salvar não traz a imagem de volta
