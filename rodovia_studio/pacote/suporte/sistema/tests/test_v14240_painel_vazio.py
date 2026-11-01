"""1.42.40: abrir uma seção pelo menu "Mais" (ex.: 2. Configuração) mostra só a janela destacada; a casca vazia do painel
não pode ficar aberta recolhendo a tela gráfica."""
from test_v1425_live_3d import live,gl_page


def _estado(p):
    return p.evaluate("""()=>{const a=document.querySelector('main>div.pnArea'),c=canvas;
      const vis=el=>!!el&&el.offsetParent!==null&&el.getBoundingClientRect().width>5;
      return {aberto:RodoviaPanels.opened,pnAberto:document.body.classList.contains('pnAberto'),areaVisivel:vis(a),areaLargura:a?a.getBoundingClientRect().width:0,
              dockAberta:!!document.querySelector('.editorSide.dock:not(.recolhida)'),canvas:c?c.getBoundingClientRect().width:0}}""")


def test_secao_configuracao_nao_deixa_painel_vazio_aberto(gl_page,live):
    p=gl_page;p.wait_for_timeout(500)
    p.evaluate("openSection('2. Configuração')");p.wait_for_function("RodoviaPanels.opened&&RodoviaPanels.opened.startsWith('section:')",timeout=10000);p.wait_for_timeout(500)
    e=_estado(p);assert not e['areaVisivel'] and not e['dockAberta'],e
    assert e['canvas']>700,e                                                       # a tela gráfica não foi recolhida
    p.evaluate("window.dispatchEvent(new Event('resize'))");p.wait_for_timeout(300)
    assert not _estado(p)['areaVisivel']                                           # nem depois de reposicionar
    p.evaluate('RodoviaPanels.requestClose?RodoviaPanels.requestClose():0');p.evaluate("document.getElementById('rsPanelCancel').click()");p.wait_for_function("!RodoviaPanels.opened",timeout=10000)
    assert not _estado(p)['areaVisivel']
