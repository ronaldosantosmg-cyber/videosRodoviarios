import json,socket,threading,time,os
from pathlib import Path
import pytest,uvicorn
from PIL import Image
from test_v1425_scene3d import project
from test_v1425_live_3d import gl_page
from app.render import Scene,render
from app.scene3d import build
from app.encoding import validate_mp4,ffmpeg_exe
from visual_harness import screenshot


@pytest.fixture(scope='module')
def live(tmp_path_factory):
    from app import store
    from app.server import app
    root=tmp_path_factory.mktemp('nos_arrasto');patch=pytest.MonkeyPatch();patch.setenv('RODOVIA_DATA',str(root));patch.setattr(store,'ROOT',root);patch.setattr(store,'DB',root/'studio.sqlite3');store.init()
    pid='f'*32;d=root/pid;d.mkdir();d,s=project(d)
    s=s.model_copy(update={'route_alignments':[]})
    (d/'config.json').write_text(s.model_dump_json());build(d,s)
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,s.name))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'));thread=threading.Thread(target=server.run,daemon=True);thread.start()
    for _ in range(150):
        if server.started:break
        time.sleep(.05)
    assert server.started
    yield f'http://127.0.0.1:{port}',pid,root
    server.should_exit=True;thread.join(timeout=15);assert not thread.is_alive();patch.undo()


def click_world(p,x,y):
    where=p.evaluate('p=>{const q=W2C(p),r=canvas.getBoundingClientRect();return {x:r.x+q[0]*r.width/canvas.width,y:r.y+q[1]*r.height/canvas.height}}',dict(x=x,y=y))
    p.mouse.click(where['x'],where['y'])


def apply(p,identity):
    p.locator('#'+identity+' [data-save]').click();p.locator('#'+identity).wait_for(state='detached',timeout=30000)


def test_node_buttons_add_edit_move_delete_and_undo_use_real_configuration(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    # Cadastra um ramal no contrato existente, sem modificar o DXF de referência.
    p.evaluate("""async()=>{M.route_alignments.push({id:'ramal',name:'Retorno',type:'unico',flow_role:'retorno',flow_start:'conexao',flow_end:'saida',points:[{x:500250,y:7800000},{x:500270,y:7800002},{x:500290,y:7800007},{x:500450,y:7800010}]});await save();await start('analyze')}""")
    source=(live[2]/live[1]/'input.dxf').read_bytes()
    p.get_by_role('tab',name='Tráfego',exact=True).click();p.set_viewport_size(dict(width=1366,height=620));p.wait_for_timeout(100)
    for name in ['Inserir nó de ligação','Selecionar nó','Editar nó','Mover nó de ligação','Apagar nó','Nó de entrada, saída ou fim','Inspecionar arrasto dos veículos','Modo clássico de fluxo']:
        b=p.get_by_role('button',name=name,exact=True);assert b.is_visible();assert b.evaluate('e=>e.getBoundingClientRect().right<=innerWidth')
    for b in p.locator('[data-activity="Tráfego"]>.rsPrimaryAction').all():
        assert b.evaluate('e=>[...e.children].filter(c=>c.tagName==="SPAN"&&getComputedStyle(c).display!=="none").every(c=>c.getBoundingClientRect().right<=e.getBoundingClientRect().right+1)')
    p.get_by_role('button',name='Inserir nó de ligação',exact=True).click()
    click_world(p,500246,7799998.35);click_world(p,500274,7800001.3)
    p.locator('#rsNodeEdit').wait_for(state='visible');assert p.evaluate('M.connection_rules.length')==0
    p.locator('#rsNodeEdit [data-name]').fill('Nó de saída para retorno');p.locator('#rsNodeEdit [data-share]').fill('20');apply(p,'rsNodeEdit')
    cfg=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];assert len(cfg['connection_rules'])==1 and cfg['connection_rules'][0]['share_pct']==20
    n=p.evaluate('RodoviaNodes.nodes().find(n=>n.rule).point')
    p.get_by_role('button',name='Editar nó',exact=True).click();click_world(p,n['x'],n['y']);p.locator('#rsNodeEdit [data-share]').fill('15');apply(p,'rsNodeEdit')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['connection_rules'][0]['share_pct']==15
    p.get_by_role('button',name='Mover nó de ligação',exact=True).click();click_world(p,500248,7799998.35);click_world(p,500276,7800001.8);apply(p,'rsNodeEdit')
    n=p.evaluate('RodoviaNodes.nodes().find(n=>n.rule).point');screenshot(p,'14234_botoes_nos')
    p.get_by_role('button',name='Apagar nó',exact=True).click();click_world(p,n['x'],n['y']);p.locator('#rsNodeDelete').wait_for(state='visible');apply(p,'rsNodeDelete')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['connection_rules'][0]['action']=='deny'
    p.locator('[data-quick=undo]').click();assert p.evaluate('M.connection_rules[0].action')=='force'
    p.wait_for_function('!savePending',timeout=30000)
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['connection_rules'][0]['action']=='force'
    assert (live[2]/live[1]/'input.dxf').read_bytes()==source


def test_swept_overlay_uses_api_without_video_or_repeated_processing_on_zoom(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    calls=[];p.on('request',lambda r:calls.append(r.url) if r.method=='POST' else None)
    p.get_by_role('tab',name='Tráfego',exact=True).click();p.get_by_role('button',name='Inspecionar arrasto dos veículos',exact=True).click();click_world(p,500120,7799998.35)
    p.locator('#rsSweptDialog [data-vehicle]').select_option('truck18');p.locator('#rsSweptDialog [data-show]').click();p.locator('#rsSweptDialog').wait_for(state='detached',timeout=30000)
    result=p.evaluate('RodoviaSwept.data');assert result['technical_only'] and result['bodies'] and result['using_calculated_trajectory']
    assert p.locator('#rsFlowInspectionCanvas').is_visible();assert not any(u.endswith('/render') or u.endswith('/preview') for u in calls)
    before=len([u for u in calls if u.endswith('/swept')]);p.evaluate('draw()');p.locator('[data-quick=zoom-in]').click();p.locator('[data-quick=zoom-out]').click()
    assert len([u for u in calls if u.endswith('/swept')])==before==1
    screenshot(p,'14234_arrasto_pesado')
    revision=result['revision'];bad=p.request.post(live[0]+'/api/projects/'+live[1]+'/flow-tools/swept',data=dict(segment=0,revision='0'*64,vehicle='car'));assert bad.status==409
    bad=p.request.post(live[0]+'/api/projects/'+live[1]+'/flow-tools/swept',data=dict(segment=0,revision=revision,vehicle='codigo_inexistente'));assert bad.status==422
    p.evaluate('RodoviaSwept.clear()');assert p.evaluate('RodoviaSwept.data===null')


def test_classic_button_persists_and_returns_to_normal_without_changing_safety_boxes(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    p.get_by_role('tab',name='Tráfego',exact=True).click();before=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']
    p.get_by_role('button',name='Modo clássico de fluxo',exact=True).click();p.locator('#rsClassicMode [data-classic]').check();apply(p,'rsClassicMode')
    after=p.request.get(live[0]+'/api/projects/'+live[1]).json()['config'];assert after['traffic_classic'] and p.locator('#rsClassicButton').get_attribute('aria-pressed')=='true'
    for key in ['traffic_prevent_collisions','traffic_respect_signals','traffic_no_median_crossing']:assert after[key]==before[key]
    p.get_by_role('button',name='Modo clássico de fluxo',exact=True).click();p.locator('#rsClassicMode [data-classic]').uncheck();apply(p,'rsClassicMode')
    assert not p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['traffic_classic']


def test_classic_mp4_and_3d_show_vehicles_with_explicit_illustrative_mode(tmp_path):
    d,s=project(tmp_path);s=s.model_copy(update={'traffic_classic':True,'camera_mode':'trafego','view_width_m':180,'render_workers':1,'imagery_pixels':2048})
    (d/'config.json').write_text(s.model_dump_json());original=(d/'input.dxf').read_bytes();scene=Scene(d,s);image,meta=scene.frame(1)
    assert meta['traffic_visibility']['drawn']>0 and isinstance(scene.traffic(),__import__('app.classic_traffic',fromlist=['ClassicTraffic']).ClassicTraffic)
    target=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));target.mkdir(exist_ok=True,parents=True);Image.fromarray(image).save(target/'14234_previa_classico.png')
    video=render(d,s);decoded=validate_mp4(ffmpeg_exe(),video,72,1280,720,24);assert decoded['ok']
    report=json.loads((d/'video.json').read_text());assert report['motion_audit']['model']=='classico_ilustrativo' and report['motion_audit']['collision_free'] is None
    data=build(d,s);assert data['simulation_mode']=='ensaio' and data['vehicles'] and data['simulation_report']['model']=='classico_ilustrativo'
    assert original==(d/'input.dxf').read_bytes()
    (target/'video_classico.json').write_text(json.dumps(dict(decoded=decoded,mode=data['simulation_mode'],report=data['simulation_report'],source_preserved=True),ensure_ascii=False,indent=2))


def test_automatic_nodes_can_be_selected_and_endpoint_type_can_be_confirmed(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    p.get_by_role('tab',name='Tráfego',exact=True).click()
    automatic=p.evaluate('RodoviaNodes.nodes().find(n=>n.automatic)?.point')
    if not automatic:
        # Remove somente a regra criada pelo ensaio anterior para conferir o nó nativo.
        p.evaluate("async()=>{M.connection_rules=[];await save();await start('analyze')}")
        automatic=p.evaluate('RodoviaNodes.nodes().find(n=>n.automatic)?.point')
    assert automatic
    p.get_by_role('button',name='Selecionar nó',exact=True).click();click_world(p,automatic['x'],automatic['y'])
    p.evaluate('RodoviaNodes.edit()');p.locator('#rsNodeEdit').wait_for(state='visible');assert 'automático' in p.locator('#rsNodeEdit [data-name]').input_value()
    p.locator('#rsNodeEdit [data-close]').last.click();assert p.locator('#rsNodeEdit').count()==0
    p.get_by_role('button',name='Nó de entrada, saída ou fim',exact=True).click();click_world(p,500450,7800010)
    p.locator('#rsNodeEdit [data-kind]').select_option('fim');apply(p,'rsNodeEdit')
    assert p.request.get(live[0]+'/api/projects/'+live[1]).json()['config']['route_alignments'][0]['flow_end']=='fim'
