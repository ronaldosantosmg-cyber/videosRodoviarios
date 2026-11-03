"""Confere comandos de iluminação, persistência e ajuda viva no Chromium."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='studio-ajuda-') as temporary:
    with socket.socket() as socket_:
        socket_.bind(('127.0.0.1', 0))
        port = socket_.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    env = {**os.environ, 'RODOVIA_DATA': str(Path(temporary)/'dados'), 'RODOVIA_NO_BROWSER': '1', 'RODOVIA_PORT': str(port)}
    with (Path(temporary)/'servidor.log').open('w') as log:
        process = subprocess.Popen([sys.executable, str(ROOT/'suporte/sistema/run.py')], env=env, stdout=log, stderr=log)
        try:
            for _ in range(120):
                try:
                    health = json.load(urllib.request.urlopen(base+'/api/health', timeout=1))
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Servidor indisponível')
            request = urllib.request.Request(base+'/api/projects', data=b'{}', headers={'Content-Type':'application/json'})
            project = json.load(urllib.request.urlopen(request))['id']
            with sync_playwright() as playwright:
                launch = {'executable_path':os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']} if os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') else {}
                browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'], **launch)
                page = browser.new_page(viewport={'width':1366,'height':768})
                errors=[]
                page.on('pageerror', lambda error:errors.append(str(error)))
                page.goto(base)
                page.wait_for_function('window.RodoviaLighting && window.RodoviaHelp')
                page.evaluate('(id)=>load(id)', project)
                assert page.evaluate("()=>COMANDOS.get('NOITE')()")
                assert page.request.get(base+'/api/projects/'+project).json()['config']['day_night']=='night'
                page.evaluate("document.getElementById('duration_s').value='3';document.getElementById('night_start_s').value='40'")
                assert page.evaluate("()=>COMANDOS.get('ANOITECER')()")
                config=page.request.get(base+'/api/projects/'+project).json()['config']
                assert config['day_night']=='transition' and config['night_start_s']==1.5 and config['night_transition_s']==1.5, config
                assert page.evaluate("()=>COMANDOS.get('DIA')()")
                assert page.request.get(base+'/api/projects/'+project).json()['config']['day_night']=='off'
                result=page.evaluate("""async()=>{
                  const {RoadViewer}=await import('/webgl/viewer.mjs');
                  const host=document.createElement('div');host.style.cssText='width:320px;height:240px';document.body.appendChild(host);
                  const v=new RoadViewer(host);v.load({format:'rodovia-scene3d-1',origin_crs:[0,0,0],span_m:100,duration_s:20,meshes:[],vehicles:[],terrain:{positions:[0,0,0,100,0,0,0,0,100],indices:[0,1,2],label:'teste'},markings:[],diagnostics:[]});
                  v.setLighting({day_night:'transition',night_start_s:4,night_transition_s:8});
                  const geometries=v.stats().geometries,values=[];
                  for(const t of [0,4,6,8,10,12,20,0]){v.setTime(t);values.push(v.stats().nightFactor)}
                  const stable=v.stats().geometries===geometries;
                  v.setLight('noite');v.setTime(0);const manual=v.stats().light==='noite'&&!v.stats().lighting;
                  v.setLighting({day_night:'off'});const restored=v.stats().nightFactor===0;
                  v.dispose();host.remove();return {values,stable,manual,restored};
                }""")
                assert result['values']==[0,0,.15625,.5,.84375,1,1,0],result
                assert result['stable'] and result['manual'] and result['restored'],result
                page.keyboard.press('F1')
                page.locator('#helpDialog').wait_for(state='visible')
                assert health['version'] in page.locator('#helpBody h2').first.inner_text()
                assert page.locator('#rsCurrentCommandHelp tbody tr').count()>50
                pending=page.evaluate("RodoviaHelp.commands().filter(x=>x.instruction.startsWith('Ajuda específica')).map(x=>x.names[0])")
                print('Comandos sem ajuda específica:', pending)
                assert not pending, pending
                assert not errors, errors
                browser.close()
            print('Iluminação persistida e ajuda da versão/F1/catálogo verificadas.')
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
