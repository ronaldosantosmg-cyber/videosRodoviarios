"""Exercita a fila real de imagens da aplicação, com rede controlada no Chromium."""
import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    options={'executable_path':os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']} if os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') else {}
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**options)
    page=browser.new_page()
    page.route('http://rodovia.test/',lambda route:route.fulfill(content_type='text/html',body='<canvas id="canvas"></canvas>'))
    page.goto('http://rodovia.test/')
    png=base64.b64decode(page.evaluate("""()=>{const c=document.createElement('canvas');c.width=c.height=256;const x=c.getContext('2d');x.fillStyle='#267934';x.fillRect(0,0,256,256);return c.toDataURL().split(',')[1]}"""))
    gray=base64.b64decode(page.evaluate("""()=>{const c=document.createElement('canvas');c.width=c.height=256;const x=c.getContext('2d');x.fillStyle='#cacaca';x.fillRect(0,0,256,256);return c.toDataURL().split(',')[1]}"""))
    calls=[]
    def image(route):
        url=route.request.url;calls.append(url)
        if '/tiles/esri/10/1/90' in url or '/tiles/esri/10/1/91' in url:
            route.fulfill(status=503,body='retry')
        elif '/tile/10/1/91' in url or '/local_tiles/10/1/93' in url:
            route.fulfill(status=503,body='fail')
        elif '/local_tiles/10/1/94' in url:
            route.fulfill(status=204,body='')
        elif '/tiles/esri/10/1/95' in url:
            route.fulfill(content_type='image/png',body=gray)
        else:
            route.fulfill(content_type='image/png',body=png)
    page.route('**/tiles/**',image)
    page.route('**/local_tiles/**',image)
    page.route('https://server.arcgisonline.com/**',image)
    page.add_script_tag(content="""let pid='p1',cfg={web_imagery:{source:'esri'}},projectSession={context:1};let baseImage=null,meta=null,analysis=null;function draw(){};window.decoded=new WeakSet();window.decodeInFlight=0;window.holdDecode=false;window.decodeWaiters=[];window.createdUrls=0;window.revokedUrls=0;const createURL=URL.createObjectURL.bind(URL),revokeURL=URL.revokeObjectURL.bind(URL);URL.createObjectURL=b=>{createdUrls++;return createURL(b)};URL.revokeObjectURL=u=>{revokedUrls++;return revokeURL(u)};window.decodeCount=0;window.maxSlots=0;window.earlyOk=false;const nativeDecode=HTMLImageElement.prototype.decode;HTMLImageElement.prototype.decode=async function(){decodeInFlight++;if(holdDecode)await new Promise(r=>decodeWaiters.push(r));else await new Promise(r=>setTimeout(r,30));await nativeDecode.call(this);window.decodeCount++;decoded.add(this);decodeInFlight--};""")
    page.add_script_tag(content=(ROOT/'suporte/sistema/app/js/02_vista_imagem_web.js').read_text(encoding='utf-8'))
    page.evaluate("""()=>{localInfo={key:'a'};window.entries=[];for(let i=0;i<18;i++)entries.push(i%2?getLocalTile(10,i,1):getTile(10,i,1));window.monitor=setInterval(()=>{maxSlots=Math.max(maxSlots,tilePipeline.active);if(entries.some(t=>t.ok&&!decoded.has(t.img)))earlyOk=true},1)}""")
    page.wait_for_function('entries.every(t=>t.ok)&&tilePipeline.active===0')
    assert page.evaluate('maxSlots')==6
    assert page.evaluate('decodeCount')==18 and not page.evaluate('earlyOk')
    page.evaluate("""()=>{window.fallback=getTile(10,90,1);window.failed=getTile(10,91,1);window.localFailed=getLocalTile(10,93,1);window.empty=getLocalTile(10,94,1)}""")
    page.wait_for_function('fallback.ok&&failed.fail&&localFailed.fail&&empty.empty&&tilePipeline.active===0')
    assert page.evaluate('fallback.direct&&!fallback.fail&&!empty.ok')
    page.evaluate('failed.failAt=-40000;window.retry=getTile(10,91,1)')
    page.wait_for_function('retry.fail&&tilePipeline.active===0')
    assert sum('/tiles/esri/10/1/91' in u for u in calls)==2
    page.evaluate('window.placeholder=getTile(10,95,1)')
    page.wait_for_function('placeholder.placeholder&&tilePipeline.active===0')
    assert page.evaluate('!placeholder.ok&&tiles.get(tileKey(9,47,0)).ok')
    page.evaluate("holdDecode=true;window.activeStale=getTile(10,98,1)")
    page.wait_for_function('decodeWaiters.length===1')
    page.evaluate("pid='abandoned';projectSession.context++;holdDecode=false;decodeWaiters.splice(0).forEach(resolve=>resolve())")
    page.wait_for_function('tilePipeline.active===0')
    assert page.evaluate('!activeStale.ok')
    before=len(calls)
    page.evaluate("""()=>{tiles.clear();localTiles.clear();window.stale=[];for(let i=100;i<130;i++)stale.push(getTile(10,i,1));pid='p2';projectSession.context++;}""")
    page.wait_for_function('tilePipeline.active===0&&tilePipeline.queue.length===0')
    assert len(calls)==before, (before,len(calls))
    assert page.evaluate('stale.every(t=>!t.ok)')
    page.evaluate("""()=>{pid='p3';window.evicted=getTile(10,140,1);tiles.clear();window.localEvicted=getLocalTile(10,141,1);localTiles.clear()}""")
    page.wait_for_function('tilePipeline.active===0')
    assert page.evaluate('evicted.cancelled&&localEvicted.cancelled&&!evicted.ok&&!localEvicted.ok&&tiles.bytes===0&&localTiles.bytes===0')
    page.evaluate("""()=>{const cache=new PixelTileCache(2*256*256*4);for(let i=0;i<3;i++)cache.set(String(i),tileEntry());window.lru=cache.size===2&&!cache.has('0');cache.get('1');cache.set('3',tileEntry());window.lru=lru&&!cache.has('2');cache.clear()}""")
    assert page.evaluate('lru')
    # Ausência de decode continua usando onload, sem aceitar imagens antes de carregadas.
    page.evaluate("""()=>{HTMLImageElement.prototype.decode=undefined;window.legacy=getTile(10,150,1)}""")
    page.wait_for_function('legacy.ok&&tilePipeline.active===0')
    assert page.evaluate('createdUrls===revokedUrls'),page.evaluate('({createdUrls,revokedUrls})')
    browser.close()
print('Fila compartilhada <=6, decode, fallback/retry, 204, cancelamento stale/clear, LRU e compatibilidade sem decode: OK')
