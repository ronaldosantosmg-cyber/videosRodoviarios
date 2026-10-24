"""Harness visual da interface real do Rodovia Studio.

Funciona em dois modos:
- integrado: servidor FastAPI + navegador, quando a política da máquina permite localhost;
- offline: usa index.html/CSS/JS reais, substituindo apenas APIs externas por fixtures determinísticas.

O modo offline existe para redes corporativas/CI que bloqueiam navegação HTTP local no Chromium.
"""
from __future__ import annotations
import base64, os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
APP = BASE / "app"
TRANSPARENT_GIF = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="

MOCK_BOOTSTRAP = r"""
<script>
(()=>{
  const mem=new Map();
  try{Object.defineProperty(window,'localStorage',{configurable:true,value:{
    getItem:k=>mem.has(k)?mem.get(k):null,
    setItem:(k,v)=>mem.set(k,String(v)),
    removeItem:k=>mem.delete(k),clear:()=>mem.clear()
  }})}catch(e){}
  window.fetch=async function(url,opt){
    const s=String(url); let data={};
    if(s.includes('/api/sobre')) data={app:'1.40.9-visual',schema:33,launcher:'visual-test',pastas:{projetos:'',videos:'',sistema:''},python:'3',system:'visual-test'};
    else if(s.includes('/api/esquema')) data={};
    else if(s.includes('/api/obras/tipos')) data=[];
    else if(s.endsWith('/api/projects')) data=[];
    else if(s.includes('/api/health')) data={status:'ok',version:'1.40.9-visual',ffmpeg:true,data:''};
    else if(s.includes('/api/modelos')) data=[];
    return {ok:true,status:200,json:async()=>data,text:async()=>'',blob:async()=>new Blob(),headers:new Headers()};
  };
  try{navigator.sendBeacon=()=>true}catch(e){}
  window.alert=()=>{}; window.confirm=()=>true; window.prompt=()=>null;
})();
</script>
"""

def chromium_path() -> str | None:
    candidates=[os.environ.get('CHROMIUM'),'/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome']
    for p in candidates:
        if p and Path(p).exists(): return p
    return None

def offline_html() -> str:
    html=(APP/'index.html').read_text(encoding='utf-8')
    css=(APP/'estilo.css').read_text(encoding='utf-8')
    html=html.replace('<link rel="stylesheet" href="/estilo.css">',MOCK_BOOTSTRAP+f'<style>{css}</style>')
    html=html.replace('<script src="/app.js"></script>','')
    def data_img(path):
        raw=Path(path).read_bytes();return 'data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
    html=html.replace('src="/marca/icone.png"',f'src="{data_img(APP/"icone.png")}"')
    html=html.replace('src="/marca/georas.png"',f'src="{data_img(APP/"georas_logo.png")}"')
    modules=[]
    for f in sorted((APP/'js').glob('[0-9][0-9]_*.js')):
        modules.append(f'<script>\n// visual: {f.name}\n{f.read_text(encoding="utf-8")}\n</script>')
    return html.replace('</html>','\n'.join(modules)+'</html>')

def load_offline(page, wait_ms: int=700):
    page.set_content(offline_html(),wait_until='load',timeout=30000)
    page.wait_for_timeout(wait_ms)
    return page

def rect(page, selector: str):
    r=page.locator(selector).bounding_box()
    assert r, f'Elemento sem retângulo: {selector}'
    return r

def overlap(a,b) -> float:
    x=max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']))
    y=max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']))
    return x*y

def screenshot(page, name: str):
    out=os.environ.get('VISUAL_ARTIFACTS')
    if not out:return None
    p=Path(out);p.mkdir(parents=True,exist_ok=True)
    target=p/f'{name}.png';page.screenshot(path=str(target),full_page=False)
    return target
