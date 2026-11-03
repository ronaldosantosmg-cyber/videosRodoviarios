"""Confere a paleta e a textura de grama dos taludes no Canvas e no 3D."""
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
                page.goto(base)
                page.wait_for_function('window.RodoviaTexturasVivas')
                result=page.evaluate("""async()=>{
                 const T=RodoviaTexturasVivas;
                 const mean=s=>{const d=T.gerar(s,{},64),v=[0,0,0];for(let i=0;i<d.length;i+=4)for(let c=0;c<3;c++)v[c]+=d[i+c]/(d.length/4);return v};
                 const fill=mean('talude_aterro'),cut=mean('talude_corte');
                 const cv=document.createElement('canvas');cv.width=256;cv.height=128;const c=cv.getContext('2d');c.fillStyle='#ffffff';c.fillRect(0,0,256,128);
                 geo={R0:1,k:1};view.s=32;vecAlpha=1;
                 const polygon=new Path2D();polygon.rect(0,0,128,128);polygon.rect(40,40,48,48);
                 window.RodoviaAparencia={leitura:()=>({rc:{fill:'#3456ab'},tp:{}})};
                 T.pintarRole(c,'fill',{fill:polygon});
                 const sample=Array.from(c.getImageData(10,10,1,1).data),hole=Array.from(c.getImageData(64,64,1,1).data);
                 document.body.appendChild(cv);
                 const {RoadViewer}=await import('/webgl/viewer.mjs');
                 const host=document.createElement('div');host.style.cssText='width:320px;height:240px';document.body.appendChild(host);
                 const v=new RoadViewer(host);v.load({format:'rodovia-scene3d-1',origin_crs:[0,0,0],span_m:100,duration_s:20,meshes:[{role:'cut',positions:[0,0,0,20,0,0,0,0,20]},{role:'fill',positions:[30,0,0,50,0,0,30,0,20]},{role:'fill',color:'#3456ab',positions:[60,0,0,80,0,0,60,0,20]}],vehicles:[],terrain:{positions:[0,-1,0,100,-1,0,0,-1,100],indices:[0,1,2],label:'teste'},markings:[],diagnostics:[]});
                 const meshes=v.scene.children.filter(x=>['cut','fill'].includes(x.userData.role));
                 const colors=meshes.map(x=>x.material.color.getHexString());
                 const grass=v.texture('grass','leaf');const textured=meshes.every(x=>x.material.map===grass);
                 v.render();v.dispose();host.remove();return {fill,cut,sample,hole,colors,textured};
                }""")
                assert result['fill'][1]>180 and result['fill'][1]>result['fill'][0]>result['fill'][2],result
                assert result['cut'][0]>175 and result['cut'][0]>result['cut'][1]>result['cut'][2],result
                assert result['sample'][2]>result['sample'][1]>result['sample'][0],result
                assert result['hole']==[255,255,255,255],result
                assert result['colors']==['b76954','9cbd75','3456ab'] and result['textured'],result
                browser.close()
                print('Taludes2D/3D: grama, paleta clara/avermelhada, cor manual e vazio DXF preservado: OK')
        finally:
            process.terminate()
            process.wait(timeout=10)
