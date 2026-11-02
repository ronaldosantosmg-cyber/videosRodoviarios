import os,sys,time,socket,tempfile,subprocess,json,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
r=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 with socket.socket() as sock:
  sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 data=Path(tmp)/'dados';base=f'http://127.0.0.1:{port}'
 env={**os.environ,'RODOVIA_DATA':str(data),'RODOVIA_NO_BROWSER':'1','RODOVIA_PORT':str(port)}
 with (Path(tmp)/'server.log').open('w') as log:
  proc=subprocess.Popen([sys.executable,str(r/'suporte/sistema/run.py')],env=env,stdout=log,stderr=log)
  try:
   for _ in range(100):
    try:
     urllib.request.urlopen(base+'/api/health',timeout=1);break
    except OSError:time.sleep(.1)
   else:raise RuntimeError('Servidor indisponível')
   req=urllib.request.Request(base+'/api/projects',data=b'{}',headers={'Content-Type':'application/json'})
   project=json.load(urllib.request.urlopen(req))['id']
   (data/project/'editor.json').write_text('{"engine_revision":"antiga"}')
   with sync_playwright() as p:
    options={'executable_path':os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']} if os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') else {}
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**options)
    page=browser.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda q:requests.append(q.url))
    page.goto(base);page.wait_for_function('typeof load === "function" && window.Rodovia3D')
    assert page.evaluate('(id)=>load(id)',project) is not False
    assert not any(x.endswith('/editor.json') for x in requests),requests
    page.evaluate("task='tarefa-ativa'")
    assert page.evaluate('()=>window.rodoviaPrepararAtualizacao()') is False
    assert page.evaluate('()=>Rodovia3D.open()') is False
    assert not any('/scene3d' in x and x.endswith('/scene3d') for x in requests)
    assert not errors,errors
    browser.close()
   print('Navegador: editor obsoleto não solicitado; atualização e 3D aguardam tarefa; sem erro JavaScript.')
  finally:
   proc.terminate();proc.wait(timeout=10)
