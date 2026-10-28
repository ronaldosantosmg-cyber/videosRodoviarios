import json
import ezdxf
from app import project_state as P
from app.models import Settings
from test_v14225_execution import publish
from test_v1425_live_3d import live,gl_page
from test_v142_visual import page
from visual_harness import screenshot


def test_cad_mode_keeps_quick_commands_and_saves_favorites(page):
 assert not page.evaluate("document.body.classList.contains('rsCadMode')")
 page.locator('#rsCadMode').click();assert page.locator('#rsCadMode').get_attribute('aria-pressed')=='true'
 assert page.locator('#rsQuickNavigation [data-quick=undo]').is_visible()
 page.locator('#rsFavoriteSettings').click();dialog=page.locator('.rsFavoriteDialog')
 checks=dialog.locator('input[type=checkbox]');checks.nth(0).check();checks.nth(1).check();dialog.get_by_role('button',name='Salvar preferências').click()
 assert page.locator('#rsFavoriteTools button').count()==2
 assert len(page.evaluate("JSON.parse(localStorage.getItem('rodovia_favorites'))"))==2
 screenshot(page,'14225_cad_compacto_favoritos')
 page.locator('#rsCadMode').click();assert not page.evaluate("document.body.classList.contains('rsCadMode')")


def test_protection_recovers_through_real_ui_and_keeps_corrupt_bytes(gl_page,live):
 p=gl_page;d=live[2]/live[1];good=P.read_config(d);(d/'config.json').write_text('{incompleto');(d/'.estado/config_atual.json').write_text('{')
 p.evaluate('RodoviaProtection.open(pid)');p.get_by_role('button',name='Restaurar esta cópia').first.wait_for()
 screenshot(p,'14225_protecao_configuracao_corrompida')
 p.once('dialog',lambda dialog:dialog.accept());p.get_by_role('button',name='Restaurar esta cópia').first.click()
 p.wait_for_function("document.querySelector('.rsExecutionDialog').textContent.includes('Estado: integro')")
 assert P.read_config(d)==good and any(f.read_text()=='{incompleto' for f in (d/'.estado/corrompidos').glob('*.json'))


def test_execution_reaches_real_worker_preview_commit_revalidation_and_undo(gl_page,live):
 p=gl_page;d=live[2]/live[1];doc=ezdxf.readfile(d/'input.dxf');m=doc.modelspace()
 for entity in list(m):m.delete_entity(entity)
 m.add_lwpolyline([(500050,7800000),(500200,7800000),(500200,7800150)],dxfattribs={'layer':'EIXO'})
 h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799980),(500500,7799980),(500500,7800200),(500000,7800200)],is_closed=True);doc.saveas(d/'input.dxf')
 data=P.read_config(d);data['route_directions']={'axis:'+__import__('app.native_axes',fromlist=['axis_fingerprint']).axis_fingerprint([(500050,7800000),(500200,7800000),(500200,7800150)],'EIXO'):'forward'};data['render_workers']=1;P.save_config(d,data);s=Settings.model_validate(data);publish(d,s);source=(d/'input.dxf').read_bytes()
 p.evaluate('(id)=>load(id,{resultsOnly:true,syncConfig:true})',live[1]);p.evaluate('RodoviaExecution.open()')
 p.get_by_role('button',name='Analisar e propor correção').first.click()
 p.get_by_role('button',name='Confirmar e aplicar correção').wait_for(timeout=90000)
 assert not P.read_config(d)['flow_recoveries'] and not p.get_by_role('button',name='Confirmar e aplicar correção').is_disabled()
 screenshot(p,'14225_previa_motor_antes_de_aplicar')
 p.get_by_role('button',name='Confirmar e aplicar correção').click();p.get_by_role('button',name='Revalidar resultado').wait_for()
 assert P.read_config(d)['flow_recoveries'] and (d/'input.dxf').read_bytes()==source
 p.get_by_role('button',name='Revalidar resultado').click()
 p.wait_for_function("document.querySelector('.rsExecutionDialog').textContent.includes('Correção aplicada com pendências')",timeout=90000)
 assert any(r['technical_circulation']['enabled'] and r['technical_status']=='adjustment' for r in __import__('json').loads((d/'editor.json').read_text())['segments'])
 screenshot(p,'14225_correcao_revalidada')
 p.get_by_role('button',name='Desfazer correção').click();p.wait_for_function("document.querySelector('.rsExecutionDialog').textContent.includes('Correção desfeita')")
 assert not P.read_config(d)['flow_recoveries'] and (d/'input.dxf').read_bytes()==source
