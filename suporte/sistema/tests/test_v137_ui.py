"""1.37 (tela): vegetação (árvore, pincel, área), caminho de pedestres, frota e pedestres gravados, abrir DWG."""
import os,threading,time
import pytest
from test_v132 import S
from test_v132_ui import free_port
from test_workflow import settings  # noqa: F401
from test_v110 import junction  # noqa: F401
from test_v137 import conversor_falso

def test_ui_137(junction,tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'));monkeypatch.setenv('RODOVIA_ODA',str(conversor_falso(tmp_path,junction/'input.dxf')))
    (tmp_path/'trecho.dwg').write_bytes(b'AC1032'+b'\0'*300)
    from app.server import app
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json=S(name='Trecho UI 137').model_dump()).json()['id']
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1700,'height':950})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/tiles/esri/**',lambda r:r.fulfill(status=404,body=b''))
            page.add_init_script(f"localStorage.setItem('rodovia_project','{pid}');localStorage.removeItem('rodovia_veg')")
            page.goto(base);page.wait_for_function('typeof cfg!=="undefined"&&cfg&&pid&&SCHEMA&&cfg.name==="Trecho UI 137"',timeout=20000);ev=page.evaluate
            # Abrir DWG: convertido em DXF e analisado como sempre.
            page.set_input_files('#fileDxf',str(tmp_path/'trecho.dwg'));page.wait_for_function("filesInfo&&filesInfo.dxf&&filesInfo.dxf.convertido==='DWG'",timeout=20000)
            assert 'convertido do DWG' in page.inner_text('.fileTable tr[data-fk="dxf"]')
            ev("$('analyze').click()");page.wait_for_function('typeof geo!=="undefined"&&geo&&vec&&editor&&ready()',timeout=40000);ev("fitView()")
            P=lambda x,y:ev(f"(()=>{{const [ix,iy]=worldToImg({{x:{x},y:{y}}});const r=canvas.getBoundingClientRect();return [r.left+(view.ox+ix*view.s)*r.width/canvas.width,r.top+(view.oy+iy*view.s)*r.height/canvas.height]}})()")
            # Vegetação: árvore avulsa, pincel (arrastar) e área.
            ev("setTool('veg')");page.select_option('#vegModo','arvore');page.select_option('#vegKind','ipe');page.mouse.click(*P(500100,7800050))
            assert ev("M.vegetation_points.length")==1 and ev("M.vegetation_points[0].kind")=='ipe'
            page.select_option('#vegModo','pincel');page.fill('#vegDens','8');page.locator('#vegDens').dispatch_event('change')
            a=P(500050,7800060);bb=P(500350,7800060);page.mouse.move(*a);page.mouse.down();page.mouse.move(*bb,steps=20);page.mouse.up()
            n=ev("M.vegetation_points.length");assert 30<=n<=45,n
            ev("undo()");assert ev("M.vegetation_points.length")==1      # um Ctrl+Z desfaz o traço inteiro
            page.select_option('#vegModo','area');page.select_option('#vegKind','eucalipto')
            for x,y in [(500100,7800030),(500200,7800030),(500200,7800070)]:page.mouse.click(*P(x,y))
            page.focus('#canvas');page.keyboard.press('Enter');assert ev("M.vegetation_areas.length")==1 and ev("M.vegetation_areas[0].kind")=='eucalipto' and ev("tool")=='veg'
            page.keyboard.press('Escape');page.wait_for_timeout(100)
            if ev("document.getElementById('confirmDlg').open"):page.keyboard.press('Enter')
            # Caminho de pedestres liga os pedestres.
            ev("$('pedestrians').checked=false;setTool('pedestres')");page.mouse.click(*P(500050,7800040));page.mouse.click(*P(500300,7800040));page.focus('#canvas');page.keyboard.press('Enter')
            assert ev("M.pedestrian_paths.length")==1 and ev("$('pedestrians').checked")
            # Selecionar a área de vegetação e mudar a densidade nas propriedades.
            ev("setTool('pan');(()=>{sel={key:'vegetation_areas',i:0};selSet=[];showProps()})()");d=page.locator('#propPanel [data-pp="density"]');d.fill('20');d.press('Enter')
            assert ev("M.vegetation_areas[0].density")==20
            ev("openSection('Câmera, clima')");page.select_option('#vehicle_mix','classico');ev("scheduleSave()");page.wait_for_timeout(1800)
            cfg=c.get(f'/api/projects/{pid}').json()['config']
            assert len(cfg['vegetation_points'])==1 and len(cfg['vegetation_areas'])==1 and len(cfg['pedestrian_paths'])==1 and cfg['pedestrians'] is True and cfg['vehicle_mix']=='classico'
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
