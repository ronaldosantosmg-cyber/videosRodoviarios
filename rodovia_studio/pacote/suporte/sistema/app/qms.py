"""1.25: catálogo QuickMapServices (NextGIS) — busca, teste no trecho e uso como fonte da imagem web.

API pública: https://qms.nextgis.com/api/v1/geoservices/ (lista filtrada e paginada) e
/geoservices/{id}/ (detalhes com url, camadas, zoom e licença). Só leitura; respostas guardadas em cache
local para funcionar sem internet nas buscas já feitas.

O serviço escolhido vira uma fonte 'xyz' ou 'wms' do projeto (mesmo caminho da 1.19), então a
georreferência continua a dos ladrilhos Web Mercator (EPSG:3857). Serviços em outros sistemas
(ex.: EPSG:3395, EPSG:4326) são listados, mas recusados com o motivo.
"""
import json,re,time,hashlib,urllib.request,urllib.parse,base64
from pathlib import Path
import numpy as np

API='https://qms.nextgis.com/api/v1/geoservices/'
UA={'User-Agent':'RodoviaStudio/1.25 (+QuickMapServices)'}
MERC_OK={None,3857,900913,3785,102100,102113}
IMAGERY_WORDS=('satell','sat ','imagery','image','imagem','ortho','orto','aerial','aero','foto','photo','spot','sentinel','landsat','drone','world_imagery','wayback','pleiades','maxar','planet','cbers')
# Provedores cujos termos costumam proibir o uso dos ladrilhos fora dos próprios aplicativos.
RESTRICTED=('google.','googleapis','virtualearth','bing.com','yandex','here.com','hereapi','mapbox','2gis','tianditu','autonavi','amap.com','baidu','apple.com','tomtom')
REF_Z=19      # escala de comparação da nitidez (≈0,3 m/pixel no equador)
OUT=512       # lado da amostra (pixels)

def _http(url,timeout=20):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def _cached_json(cache_root,url,max_age_s,fetch=None):
    """JSON da API com cópia local; sem internet usa a cópia (mesmo vencida)."""
    f=Path(cache_root)/'qms'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.json')
    if f.exists() and time.time()-f.stat().st_mtime<max_age_s:return json.loads(f.read_bytes()),'cache'
    try:
        data=(fetch or _http)(url);obj=json.loads(data)
        f.parent.mkdir(parents=True,exist_ok=True);tmp=f.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(f);return obj,'online'
    except Exception as e:
        if f.exists():return json.loads(f.read_bytes()),'cache (sem internet)'
        raise RuntimeError(f'Não foi possível consultar o QuickMapServices ({e.__class__.__name__}: {e}). Verifique a internet ou o bloqueio a qms.nextgis.com.') from e

def ewkt_bbox(s):
    """Retângulo [lon0,lat0,lon1,lat1] de um EWKT/WKT (POLYGON/MULTIPOLYGON)."""
    if not s:return None
    nums=[float(v) for v in re.findall(r'-?\d+(?:\.\d+)?(?:[eE]-?\d+)?',s.split(';',1)[-1])]
    if len(nums)<4:return None
    xs=nums[0::2];ys=nums[1::2];return [min(xs),min(ys),max(xs),max(ys)]

def is_imagery(name,desc=''):
    t=(' '+(name or '')+' '+(desc or '')+' ').lower();return any(w in t for w in IMAGERY_WORDS)

def is_restricted(url):
    u=(url or '').lower();return any(r in u for r in RESTRICTED)

def project_area_wgs84(crs,bounds,margin_m=0):
    from pyproj import Transformer
    (x0,y0),(x1,y1)=bounds;x0-=margin_m;y0-=margin_m;x1+=margin_m;y1+=margin_m
    tr=Transformer.from_crs(crs,4326,always_xy=True)
    xs,ys=tr.transform([x0,x1,x1,x0,(x0+x1)/2],[y0,y0,y1,y1,(y0+y1)/2])
    return [min(xs[:4]),min(ys[:4]),max(xs[:4]),max(ys[:4])],(xs[4],ys[4])

def search(cache_root,q='',kind='todos',area=None,works_only=True,imagery_only=True,limit=40,offset=0,fetch=None):
    """Busca no catálogo. area=[lon0,lat0,lon1,lat1] restringe aos serviços que cobrem o trecho."""
    p={'limit':max(1,min(100,int(limit))),'offset':max(0,int(offset)),'ordering':'name'}
    if q and q.strip():p['search']=q.strip()[:80]
    if kind in ('tms','wms'):p['type']=kind
    if works_only:p['cumulative_status']='works'
    if area:
        a,b,c,d=area;p['intersects_extent']=f'SRID=4326;POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))'
    url=API+'?'+urllib.parse.urlencode(p)
    obj,origem=_cached_json(cache_root,url,86400,fetch)
    rows=obj.get('results',obj if isinstance(obj,list) else [])
    out=[]
    for r in rows:
        t=r.get('type')
        if t not in ('tms','wms'):continue
        bb=ewkt_bbox(r.get('extent'));img=is_imagery(r.get('name'),r.get('desc'))
        if imagery_only and not img:continue
        area_deg=(bb[2]-bb[0])*(bb[3]-bb[1]) if bb else None
        out.append({'id':r.get('id'),'name':r.get('name') or '','type':t,'epsg':r.get('epsg'),'status':r.get('cumulative_status') or '',
                    'imagery':img,'extent':bb,'area_deg2':area_deg,'merc_ok':r.get('epsg') in MERC_OK,'desc':(r.get('desc') or '')[:300]})
    # Ordem: imagem aérea, funcionando, serviços locais (cobertura menor costuma ser ortofoto de maior resolução).
    out.sort(key=lambda r:(not r['imagery'],r['status']!='works',not r['merc_ok'],r['area_deg2'] if r['area_deg2'] is not None else 1e9,r['name'].lower()))
    return {'count':obj.get('count',len(out)) if isinstance(obj,dict) else len(out),'results':out,'origem':origem,
            'next':bool(isinstance(obj,dict) and obj.get('next')),'offset':p['offset'],'limit':p['limit']}

def detail(cache_root,sid,fetch=None):
    sid=int(sid)
    if sid<=0:raise ValueError('Identificador de serviço inválido.')
    obj,_=_cached_json(cache_root,f'{API}{sid}/',7*86400,fetch)
    if not isinstance(obj,dict) or obj.get('id')!=sid:raise ValueError('Serviço não encontrado no QuickMapServices.')
    return obj

def _params(s):
    return {k.upper():v for k,v in urllib.parse.parse_qsl(s or '',keep_blank_values=True)}

def to_web_imagery(d):
    """Converte o registro do QMS nos campos de WebImagery. Lança ValueError com o motivo se não der para usar."""
    t=d.get('type');epsg=d.get('epsg');url=(d.get('url') or '').strip()
    if t not in ('tms','wms'):raise ValueError(f'Tipo “{t}” não é imagem (só TMS/XYZ e WMS).')
    if epsg not in MERC_OK:raise ValueError(f'O serviço está em EPSG:{epsg}; o Rodovia Studio usa ladrilhos Web Mercator (EPSG:3857). Escolha outro serviço.')
    if not url.lower().startswith(('http://','https://')):raise ValueError('Serviço sem endereço http/https.')
    name=(d.get('name') or f'QMS {d.get("id")}').strip()
    cr=(d.get('copyright_text') or '').strip()
    attr=((cr+' · ' if cr else '')+name+' (via QuickMapServices)')[:200]
    terms=(d.get('terms_of_use_url') or d.get('license_url') or d.get('copyright_url') or '').strip()[:400]
    zmax=d.get('z_max');zmax=int(zmax) if isinstance(zmax,(int,float)) else 19;zmax=max(10,min(23,zmax))
    out={'source':'xyz' if t=='tms' else 'wms','url':'','wms_layers':'','attribution':attr,'max_zoom':zmax,
         'qms_id':int(d['id']),'qms_name':name[:120],'terms_url':terms,'wms_version':'1.3.0','wms_format':'image/jpeg','wayback_release':None,'wayback_label':''}
    if t=='tms':
        u=re.sub(r'\{switch:([^,}]+)[^}]*\}',r'\1',url)
        if d.get('y_origin_top') is False:u=u.replace('{y}','{-y}')
        if not(('{z}' in u and '{x}' in u) or '{q}' in u):raise ValueError('Endereço TMS sem {z}/{x}/{y} nem {q}.')
        out['url']=u[:600]
    else:
        p=_params(d.get('params'));base=url.split('?')[0] if 'REQUEST=' in url.upper() else url
        v=p.get('VERSION','1.3.0');out['wms_version']='1.1.1' if v.startswith('1.1') else '1.3.0'
        fmt=(d.get('format') or p.get('FORMAT') or 'image/jpeg').lower();out['wms_format']='image/png' if 'png' in fmt else 'image/jpeg'
        lay=(d.get('layers') or p.get('LAYERS') or '').strip()
        if not lay:raise ValueError('Serviço WMS sem camada informada no catálogo.')
        out['url']=base[:600];out['wms_layers']=lay[:200]
    return out

def summary(d):
    """Dados úteis para mostrar antes de usar."""
    try:wi=to_web_imagery(d);ok,why=True,''
    except ValueError as e:wi,ok,why=None,False,str(e)
    return {'id':d.get('id'),'name':d.get('name'),'type':d.get('type'),'epsg':d.get('epsg'),'status':d.get('cumulative_status'),
            'z_min':d.get('z_min'),'z_max':d.get('z_max'),'license_name':d.get('license_name') or '','license_url':d.get('license_url') or '',
            'copyright_text':d.get('copyright_text') or '','copyright_url':d.get('copyright_url') or '','terms_url':d.get('terms_of_use_url') or '',
            'restricted':is_restricted(d.get('url')),'usable':ok,'reason':why,'web_imagery':wi,'desc':(d.get('desc') or '')[:600],
            'extent':ewkt_bbox(d.get('extent'))}

def _merc(lon,lat):
    from pyproj import Transformer
    return Transformer.from_crs(4326,3857,always_xy=True).transform(lon,lat)

def sample(cache_root,wi,lon,lat,tile_fn=None,zoom=None):
    """Amostra de 512 px no centro do trecho, na escala do zoom 19, e medidas de qualidade.
    nitidez = variância do laplaciano (maior = mais detalhe); vazio = fração de ladrilhos lisos/ausentes."""
    import cv2
    from .webmap import WebSource,tile,MERC_HALF
    src=WebSource(wi['source'],wi['url'],None,wi.get('wms_layers',''),wi.get('max_zoom',19),wi.get('attribution',''),
                  version=wi.get('wms_version','1.3.0'),fmt=wi.get('wms_format','image/jpeg'))
    zt=int(zoom or min(REF_Z,src.max_zoom));mx,my=_merc(lon,lat)
    n=256*2**zt;px=(mx+MERC_HALF)/(2*MERC_HALF)*n;py=(MERC_HALF-my)/(2*MERC_HALF)*n
    w=OUT*2.0**(zt-REF_Z);x0=px-w/2;y0=py-w/2
    tx0,ty0,tx1,ty1=int(x0//256),int(y0//256),int((x0+w)//256),int((y0+w)//256)
    canvas=np.zeros(((ty1-ty0+1)*256,(tx1-tx0+1)*256,3),np.uint8);got=0;miss=0;flat=0;erros=[]
    for ty in range(ty0,ty1+1):
        for tx in range(tx0,tx1+1):
            try:
                data=(tile_fn or tile)(cache_root,zt,ty,tx,source=src)
                im=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
                if im is None:raise ValueError('imagem inválida')
                if im.shape[:2]!=(256,256):im=cv2.resize(im,(256,256),interpolation=cv2.INTER_AREA)
                canvas[(ty-ty0)*256:(ty-ty0+1)*256,(tx-tx0)*256:(tx-tx0+1)*256]=im;got+=1
                if float(im.std())<4:flat+=1
            except Exception as e:
                miss+=1
                if len(erros)<2:erros.append(f'{e.__class__.__name__}: {str(e)[:120]}')
    ox=x0-tx0*256;oy=y0-ty0*256
    M=np.float32([[OUT/w,0,-ox*OUT/w],[0,OUT/w,-oy*OUT/w]])
    out=cv2.warpAffine(canvas,M,(OUT,OUT),flags=cv2.INTER_CUBIC if w<OUT else cv2.INTER_AREA,borderMode=cv2.BORDER_REPLICATE)
    g=cv2.cvtColor(out,cv2.COLOR_BGR2GRAY)
    lap=float(cv2.Laplacian(g,cv2.CV_64F).var()) if got else 0.0
    total=got+miss;vazio=(miss+flat)/max(total,1)
    jpg=cv2.imencode('.jpg',out,[cv2.IMWRITE_JPEG_QUALITY,82])[1].tobytes()
    return {'zoom':zt,'m_por_pixel_amostra':round(2*MERC_HALF/(256*2**REF_Z)*float(np.cos(np.radians(lat))),3),'ladrilhos':total,'faltando':miss,'lisos':flat,
            'vazio':round(vazio,3),'nitidez':round(lap,1),'erros':erros,'jpeg_b64':base64.b64encode(jpg).decode()}
