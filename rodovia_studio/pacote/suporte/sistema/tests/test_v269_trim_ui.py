import hashlib
import pytest
from test_v1425_live_3d import live as old_live,gl_page
from visual_harness import screenshot

@pytest.fixture(scope='module')
def live(tmp_path_factory):
    gen=old_live.__wrapped__(tmp_path_factory);info=next(gen)
    try:
        import ezdxf
        from app.models import Settings
        from app.scene3d import build
        d=info[2]/info[1];doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('LINHA A RECORTAR');doc.modelspace().add_lwpolyline([(500100,7800010),(500300,7800010)],dxfattribs={'layer':'LINHA A RECORTAR'});doc.saveas(d/'input.dxf');s=Settings.model_validate_json((d/'config.json').read_text());s.layers['domain']=['LINHA A RECORTAR'];s.presentation_guides=True;(d/'config.json').write_text(s.model_dump_json());build(d,s);yield info
    finally:next(gen,None)


def settled(p):p.wait_for_function('!task&&!taskRequestPending&&!RodoviaUpdates.snapshot().requests',timeout=90000)
def phase(p,name):
    try:p.wait_for_function('(phase)=>RodoviaTrimController.snapshot()?.phase===phase',arg=name,timeout=15000)
    except Exception:raise AssertionError(str(p.evaluate('RodoviaTrimController.snapshot()'))+' | '+p.locator('#message').inner_text())

def test_trim_commands_menu_context_confirm_undo_redo_reload_restore(gl_page,live):
    p=gl_page;dxf=live[2]/live[1]/'input.dxf';before=hashlib.sha256(dxf.read_bytes()).hexdigest();settled(p)
    p.wait_for_function('!!window.RodoviaIconPack&&RodoviaIconPack.count===148')
    assert p.evaluate("RodoviaIconPack.byLabel('Prévia')==='video-previa'&&RodoviaIconPack.byLabel('TRIM — ocultar trecho')==='editar-recortar-segmento'")
    assert p.evaluate("COMANDOS.has('TRIM')&&COMANDOS.has('APARAR')&&COMANDOS.has('RESTAURARTRECHOS')&&COMANDOS.has('APARARINTERSECOES')")
    # Menu suspenso e menu principal usam o mesmo comando.
    p.get_by_role('tab',name='Editar',exact=True).click();assert p.locator('#rsTrim').is_visible();p.wait_for_function("document.querySelector('#rsTrim svg')?.dataset.rsPackIcon==='editar-recortar-segmento'");p.wait_for_function("document.querySelector('.psHub[data-pshub=layers] .pnIco svg')?.dataset.rsPackIcon==='camadas-camadas'");assert p.locator('.psHub[data-pshub=layers] svg').count()==1;assert p.get_by_role('button',name='Opções do TRIM',exact=True).locator('svg').count()==0;screenshot(p,'269_icones_usuario');p.get_by_role('button',name='Opções do TRIM',exact=True).click();assert p.get_by_role('menuitem',name='TRIM — ocultar trecho',exact=True).is_visible();p.keyboard.press('Escape')
    definitions=p.evaluate("RodoviaMenus.definitions().find(m=>m.t==='Editar').sub.map(x=>x.t)");assert 'TRIM — ocultar trecho da linha' in definitions
    p.evaluate('openCanvasMenu(300,300,{x:500120,y:7800010})');p.get_by_role('menuitem',name='TRIM — ocultar trecho da linha',exact=True).click();phase(p,'start');p.evaluate("runCommand('')");p.evaluate('draw()')
    p.evaluate("runCommand('TRIM')");phase(p,'select');p.evaluate('feedPoint({x:500120,y:7800010})');phase(p,'start');p.evaluate('feedPoint({x:500150,y:7800010})');phase(p,'end');p.evaluate('feedPoint({x:500220,y:7800010})');phase(p,'confirm');screenshot(p,'269_trim_confirmacao')
    blocked={'done':False}
    def fail_once(route):
        if route.request.method=='PUT' and not blocked['done']:
            blocked['done']=True;route.fulfill(status=507,content_type='application/json',body='{"detail":"Falha de gravação simulada; tente novamente."}')
        else:route.continue_()
    p.route('**/api/projects/'+live[1]+'/config',fail_once)
    p.locator('#rsTrimConfirm [data-save]').click();p.wait_for_function('document.querySelector("#rsTrimConfirm [data-error]").textContent.includes("simulada")')
    assert p.evaluate('M.dxf_line_trims.length')==0
    p.unroute('**/api/projects/'+live[1]+'/config',fail_once)
    p.locator('#rsTrimConfirm [data-save]').click();p.wait_for_function('!document.getElementById("rsTrimConfirm")');settled(p)
    saved=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['dxf_line_trims'];assert len(saved)==1 and saved[0]['start_m']==pytest.approx(50) and saved[0]['end_m']==pytest.approx(120)
    def parts():return p.evaluate("()=>{const r=vec.layers.domain.find(r=>r.trim_id===M.dxf_line_trims[0]?.source_id)||vec.layers.domain[0];return RodoviaTrimController.records(r).map(p=>p.p)}")
    assert parts()==[[[500100,7800010],[500150,7800010]],[[500220,7800010],[500300,7800010]]]
    p.evaluate('undo()');assert p.evaluate('M.dxf_line_trims.length')==0;p.evaluate('redo()');assert len(parts())==2;p.evaluate('save()');settled(p)
    p.evaluate('(id)=>load(id)',live[1]);settled(p);assert len(parts())==2
    p.evaluate('RodoviaTrimController.manager()');p.locator('#rsTrimManager [data-restore]').click();p.wait_for_function('M.dxf_line_trims.length===0');settled(p);assert len(parts())==1;p.locator('#rsTrimManager [data-close]').first.click()
    # A correlação suspeita de desapropriação exige conferência; os dados ficam restauráveis.
    p.evaluate("()=>{M.pavement_areas.push({id:'suspeita',name:'Pista nova (DESAPROPRIAÇÃO)',kind:'pavement',points:[{x:500120,y:7800001},{x:500140,y:7800001},{x:500140,y:7800004}],source:'picked',material:'auto',enabled:true});RodoviaContourReview.open()}")
    p.locator('#rsLayerQuality [data-calculate]').click();p.wait_for_function('!document.getElementById("rsLayerQuality")');settled(p)
    assert p.evaluate("M.pavement_areas.find(a=>a.id==='suspeita').enabled") is False
    # Cancelar antes de confirmar não altera o projeto.
    p.evaluate('RodoviaTrimController.start({x:500120,y:7800010})');phase(p,'start');p.evaluate('feedPoint({x:500150,y:7800010})');p.evaluate('feedPoint({x:500220,y:7800010})');phase(p,'confirm');p.locator('#rsTrimConfirm [data-close]').first.click();p.wait_for_function('!document.getElementById("rsTrimConfirm")');assert p.evaluate('M.dxf_line_trims.length')==0
    assert p.evaluate("(()=>{const s=[RodoviaIconPack.icon('sinalizacao-zebrado-branco'),RodoviaIconPack.icon('sinalizacao-zebrado-branco')].join('');const d=new DOMParser().parseFromString(s,'text/html'),ids=[...d.querySelectorAll('[id]')].map(e=>e.id);return ids.length===new Set(ids).size})()")
    assert hashlib.sha256(dxf.read_bytes()).hexdigest()==before
