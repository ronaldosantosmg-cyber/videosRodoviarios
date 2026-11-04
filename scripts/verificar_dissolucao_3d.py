"""Compila os shaders reais e confere dissolução por instância no Chromium."""
import functools
import http.server
import os
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]/'suporte/sistema/app'
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page();errors=[]
        page.route('**/favicon.ico',lambda route:route.fulfill(status=204,body=''))
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'favicon' not in m.text else None)
        page.goto(f'http://127.0.0.1:{server.server_port}/webgl/viewer.mjs')
        result=page.evaluate('''async()=>{
          document.body.innerHTML='<div id="v" style="width:800px;height:600px"></div>';
          const {RoadViewer}=await import('/webgl/viewer.mjs');
          const view=new RoadViewer(document.getElementById('v'));
          const vehicle={id:1,type:'car',length:4.5,width:1.8,color:'#ff0000',samples:[[0,0,1,0,1,0,0],[2,10,1,0,1,0,0]],fades:[[0,1],[1,.5],[2,0]]};
          view.load({format:'rodovia-scene3d-1',origin_crs:[0,0,0],span_m:100,duration_s:2,meshes:[],vehicles:[vehicle],terrain:{positions:[-50,0,-50,50,0,-50,50,0,50,-50,0,50],indices:[0,1,2,0,2,3],label:'Teste'},markings:[]});
          const counts=[view.geometries.size,view.materials.size];
          const values=[];for(const t of [0,1,2]){view.setTime(t);view.render();values.push(view.vehicleBatches[0].body.userData.fadeAttribute.getX(0));}
          for(let i=0;i<100;i++)view.setTime((i%20)/10);
          const stable=counts[0]===view.geometries.size&&counts[1]===view.materials.size;
          const programs=view.renderer.info.programs.map(p=>p.diagnostics?.runnable!==false);
          view.dispose();return {values,stable,programs};
        }''')
        assert result['values']==[1,.5,0],result
        assert result['stable'] and all(result['programs']),result
        assert not errors,errors
        browser.close();print('WebGL: shaders compilados, dissolução 1/0,5/0 e recursos estáveis em 100 atualizações.')
finally:
    server.shutdown();server.server_close();thread.join()
