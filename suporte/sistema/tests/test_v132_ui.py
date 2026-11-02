"""1.32 (tela): qualidade do vídeo na configuração, vídeos gerados (assistir, apagar), limpar memória e atualizar."""
import os,socket,threading,time,json
import numpy as np,pytest
from test_workflow import settings
from test_v132 import make_mp4,S

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def test_editor_132_ui(tmp_path,monkeypatch):
    pw=pytest.importorskip('playwright.sync_api')
    import uvicorn,httpx
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    from app import store,videos
    port=free_port();server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    th=threading.Thread(target=server.run,daemon=True);th.start();base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        try:httpx.get(base+'/api/health');break
        except Exception:time.sleep(.1)
    c=httpx.Client(base_url=base,timeout=60)
    pid=c.post('/api/projects',json={'name':'Trecho UI 132'}).json()['id'];d=store.ROOT/pid
    s=store_settings=S(name='Trecho UI 132')
    info={'width':320,'height':180,'fps':12,'duration_s':1,'frames':12,'encoder':'libx264'}
    make_mp4(d/'video.mp4');v1=videos.archive(d,pid,s,info,2.0);v2=videos.archive(d,pid,s,info,2.5)
    errors=[]
    try:
        with pw.sync_playwright() as p:
            exe=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            b=p.chromium.launch(executable_path=exe if os.path.exists(exe) else None);page=b.new_page(viewport={'width':1500,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script(f"localStorage.setItem('rodovia_paineis','0');localStorage.setItem('rodovia_project','{pid}')")
            page.goto(base);page.wait_for_function('typeof cfg!=="undefined"&&cfg&&pid&&SCHEMA&&cfg.name==="Trecho UI 132"',timeout=20000);ev=page.evaluate
            # Projeto novo nasce com qualidade Alta; a escolha é salva.
            assert ev("document.getElementById('video_quality').value")=='alta' and ev("[...document.getElementById('width').options].map(o=>o.value)")[0]=='3840'
            page.select_option('#video_quality','maxima');ev("scheduleSave()");page.wait_for_timeout(1500)
            assert c.get(f'/api/projects/{pid}').json()['config']['video_quality']=='maxima'
            # Vídeos gerados: os dois aparecem (mais novo primeiro); assistir e apagar.
            ev("runCommand('VIDEOS')");page.wait_for_selector('#videosDlg[open]')
            rows=ev("[...document.querySelectorAll('#vdRows [data-vd]')].map(r=>r.dataset.vd)");assert rows==[v2.name,v1.name]
            page.click(f'#vdRows [data-vd="{v1.name}"] [data-vda="ver"]');page.wait_for_function("!document.getElementById('vdPlayer').hidden")
            assert v1.name in ev("decodeURIComponent(document.getElementById('vdPlayer').src)")
            page.click(f'#vdRows [data-vd="{v1.name}"] [data-vda="del"]');page.wait_for_selector('#confirmDlg[open]');page.click('#confirmYes')
            page.wait_for_function("document.querySelectorAll('#vdRows [data-vd]').length===1");assert not v1.exists()
            page.click('#vdClose')
            # Limpar memória: categorias com tamanhos; a lixeira dos vídeos tem o vídeo apagado.
            ev("runCommand('LIMPAR')");page.wait_for_selector('#cleanDlg[open]')
            t=page.inner_text('#cleanDlg');assert 'Caches regeneráveis' in t and 'Lixeira' in t
            assert ev("document.querySelector('#clRows [data-cl=\"lixeira\"]').checked")
            ev("document.querySelectorAll('#clRows [data-cl]').forEach(x=>x.checked=x.dataset.cl==='lixeira')")
            page.click('#clGo');page.wait_for_selector('#confirmDlg[open]');page.click('#confirmYes');page.wait_for_function("document.getElementById('clInfo').textContent.includes('Liberados')")
            assert not any((tmp_path/'videos'/'_lixeira').iterdir()) and v2.exists()
            page.click('#clClose')
            # Atualizar: mostra a versão instalada (fora do Windows/instalação, sem o botão de aplicar).
            ev("runCommand('ATUALIZAR')");page.wait_for_selector('#updDlg[open]');assert 'Versão instalada' in page.inner_text('#updDlg') and ev("document.getElementById('updGo').hidden")
            page.click('#updClose')
            # Menu Arquivo e faixa de opções.
            page.click('#menuBar .mb.file');t=page.inner_text('#menuDrop');assert 'Vídeos gerados' in t and 'Limpar memória' in t and 'Atualizar o Rodovia Studio' in t
            page.keyboard.press('Escape');page.mouse.click(5,600)
            page.click('#menuBar .mb:has-text("Vídeo")');assert page.locator('#menuBar .rb:has-text("Vídeos gerados")').count()==1
            b.close()
    finally:
        server.should_exit=True;th.join(timeout=10)
    assert not errors,errors
