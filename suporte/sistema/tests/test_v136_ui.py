"""1.36 (tela): pontos-chave da câmera (adicionar a vista atual, título, parada, ordem, ir para, excluir, desfazer),
clima, sol e antes/depois gravados na configuração."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401

def test_ui_136(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='Trecho UI 136').model_dump()).json()['id']
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())})
    j=c.post(f'/api/projects/{pid}/analyze').json()
    for _ in range(300):
        if c.get('/api/jobs/'+j['id']).json()['state'] in ('done','failed'):break
        time.sleep(.2)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1700,'height':950})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()&&SCHEMA&&cfg.name==="Trecho UI 136"',timeout=20000);ev=page.evaluate
            # Duas vistas: a atual e uma aproximada; o voo passa a “pontos-chave”.
            ev("fitView()");ev("runCommand('PC')");assert ev("M.camera_keys.length")==1 and ev("$('camera_mode').value")!='pontos'
            ev("view.s*=3;draw()");ev("openSection('Câmera, clima')");page.click('#ckAdd')
            K=ev("M.camera_keys");assert len(K)==2 and K[1]['width_m']<K[0]['width_m']*.5 and ev("$('camera_mode').value")=='pontos'
            page.fill('[data-ck="0"] [data-ckf="title"]','Visão geral');page.keyboard.press('Enter');page.fill('[data-ck="1"] [data-ckf="hold_s"]','5');page.keyboard.press('Tab')
            assert ev("M.camera_keys[0].title")=='Visão geral' and ev("M.camera_keys[1].hold_s")==5
            page.click('[data-ck="1"] [data-cka="sobe"]');assert ev("M.camera_keys[0].hold_s")==5;ev("undo()");assert ev("M.camera_keys[1].hold_s")==5
            ev("fitView()");s0=ev("view.s");page.click('[data-ck="1"] [data-cka="ver"]');assert ev("view.s")>s0*2
            # Clima, sol e antes/depois.
            page.select_option('#weather','chuva');ev("$('weather_intensity').value='0.8';$('weather_intensity').dispatchEvent(new Event('input'))");assert ev("$('wiVal').textContent")=='80%'
            page.check('#sun_shadows');ev("$('sun_hour').value='7.5';$('sun_hour').dispatchEvent(new Event('input'))");assert ev("$('shVal').textContent")=='7h30'
            page.check('#before_after');ev("scheduleSave()");page.wait_for_timeout(1800)
            cfg=c.get(f'/api/projects/{pid}').json()['config']
            assert (cfg['camera_mode'],len(cfg['camera_keys']),cfg['camera_keys'][0]['title'],cfg['weather'],cfg['weather_intensity'],cfg['sun_shadows'],cfg['sun_hour'],cfg['before_after'])==('pontos',2,'Visão geral','chuva',.8,True,7.5,True)
            page.click('[data-ck="0"] [data-cka="del"]');assert ev("M.camera_keys.length")==1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
