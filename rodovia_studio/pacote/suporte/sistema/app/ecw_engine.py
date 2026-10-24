"""1.24: leitor ECW interno — converte ECW/JP2/MrSID para GeoTIFF em blocos sem QGIS, mantendo a georreferência.

O Rodovia Studio instala no próprio Python portátil (sem administrador):
- GDAL para Python (rodas binárias para Windows de Christoph Gohlke, pelo índice Geospatial Wheels Index);
- o plugin ECW do GDAL (pacote `gdal-ecw`, DLLs do ERDAS ECW/JP2 SDK distribuídas pelo GISInternals).
Também aceita as rodas (.whl) copiadas para a pasta `pacotes_ecw` (instalação sem internet).

A conversão roda dentro do aplicativo (osgeo.gdal) e confere, antes de aceitar o resultado, que o tamanho,
a geotransformação (origem e pixel), o sistema de coordenadas e os quatro cantos são os mesmos do original.
Além das etiquetas GeoTIFF, grava .tfw e .prj ao lado (dupla garantia da georreferência).
"""
import os,sys,glob,json,math,subprocess
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OFFLINE=BASE/'pacotes_ecw'
GWI_INDEX='https://gisidx.github.io/gwi/'
GDAL_SPEC='gdal>=3.11,<3.12'
ECW_SPEC='gdal-ecw>=3.11,<3.12'

def _plugin_dirs():
    out=[]
    for sp in sys.path:
        for d in (Path(sp)/'osgeo'/'gdalplugins',Path(sp)/'gdalplugins'):
            if d.is_dir():out.append(d)
    return out

def py_gdal():
    """Módulo osgeo.gdal (com o plugin ECW ativado, se instalado) ou None."""
    for d in _plugin_dirs():
        cur=os.environ.get('GDAL_DRIVER_PATH','')
        if str(d) not in cur.split(os.pathsep):os.environ['GDAL_DRIVER_PATH']=(cur+os.pathsep if cur else '')+str(d)
    try:
        from osgeo import gdal
    except Exception:
        return None
    try:gdal.UseExceptions()
    except Exception:pass
    try:gdal.AllRegister()
    except Exception:pass
    return gdal

def status():
    g=py_gdal();out={'python_gdal':None,'ecw':False,'jp2ecw':False,'mrsid':False,'offline_wheels':sorted(p.name for p in OFFLINE.glob('*.whl')) if OFFLINE.is_dir() else []}
    if g is not None:
        out['python_gdal']=g.__version__ if hasattr(g,'__version__') else g.VersionInfo('RELEASE_NAME')
        out['ecw']=g.GetDriverByName('ECW') is not None
        out['jp2ecw']=g.GetDriverByName('JP2ECW') is not None
        out['mrsid']=g.GetDriverByName('MrSID') is not None
    from .local_tiles import find_gdal
    ext=find_gdal();out['external']=ext['bin'] if ext else None
    out['ready']=bool(out['ecw'] or ext)
    return out

# 1.38: fontes das rodas prontas (nunca compila do código-fonte).
GDAL_WHEEL_URL='https://github.com/cgohlke/geospatial-wheels/releases/download/v2025.10.25/gdal-3.11.4-{tag}-{tag}-{plat}.whl'
ECW_JSON_URL='https://pypi.org/pypi/gdal-ecw/3.11.3/json'
ECW_PAGE='https://pypi.org/project/gdal-ecw/#files'

def _tags():
    v=sys.version_info;tag=f'cp{v.major}{v.minor}'
    import struct;plat=('win_amd64' if struct.calcsize('P')==8 else 'win32') if sys.platform=='win32' else None
    return tag,plat

def gdal_wheel_url():
    tag,plat=_tags();return GDAL_WHEEL_URL.format(tag=tag,plat=plat) if plat else None

def _proxy():
    """Proxy do Windows (Opções da Internet), que o pip não lê sozinho."""
    try:
        import urllib.request;px=urllib.request.getproxies()
        return px.get('https') or px.get('http')
    except Exception:return None

def _fetch(url,dest,timeout=600):
    """Baixa com o proxy e os certificados do Windows (urllib + ssl padrão lê o repositório do Windows)."""
    import urllib.request,ssl,shutil
    req=urllib.request.Request(url,headers={'User-Agent':'RodoviaStudio'})
    with urllib.request.urlopen(req,timeout=timeout,context=ssl.create_default_context()) as r,open(dest,'wb') as f:shutil.copyfileobj(r,f)
    return dest

def _ecw_wheel_url(fetch_json):
    info=fetch_json(ECW_JSON_URL)
    tag,plat=_tags()
    for u in info.get('urls',[]):
        if u.get('filename','').endswith(f'-{plat}.whl'):return u['url'],u['filename']
    raise ValueError(f'gdal-ecw sem roda para {plat}.')

def _json(url):
    import urllib.request,ssl
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RodoviaStudio'}),timeout=60,context=ssl.create_default_context()) as r:
        return json.loads(r.read().decode('utf-8'))

def _resumo(txt):
    """Só as linhas úteis do pip (sem o rastreamento interno)."""
    txt=txt or ''
    linhas=[l.strip() for l in txt.splitlines() if l.strip().startswith(('ERROR:','WARNING: Retrying','error:'))]
    if any(k in txt for k in ('get_requires_for_build_wheel','Building wheel','setup.py','gdal-config','Microsoft Visual C++ 14.0')):
        linhas.insert(0,'o pip não encontrou o GDAL pronto para este Python e tentou compilá-lo do código-fonte (impossível sem compilador)')
    if 'CERTIFICATE_VERIFY_FAILED' in txt:linhas.insert(0,'certificado recusado (inspeção SSL da rede da empresa)')
    if any(k in txt for k in ('ProxyError','407','Failed to establish a new connection','getaddrinfo failed','Name or service not known')):
        linhas.insert(0,'sem acesso ao servidor (proxy ou bloqueio da rede)')
    return '; '.join(dict.fromkeys(linhas))[:400] or txt.strip()[-300:]

def install(status_cb=lambda *a:None,run=subprocess.run,fetch=None,fetch_json=None):
    """Instala GDAL + plugin ECW no Python em uso (portátil do aplicativo), só com rodas prontas. Retorna o status final.

    Ordem: 1) rodas na pasta pacotes_ecw (sem internet); 2) pip com --only-binary (índice GWI + PyPI, proxy do Windows);
    3) baixa as duas rodas diretamente (GitHub de C. Gohlke e PyPI) com o proxy e os certificados do Windows,
    guarda em pacotes_ecw e instala sem internet. O pip nunca tenta compilar o GDAL."""
    fetch=fetch or _fetch;fetch_json=fetch_json or _json
    py=sys.executable
    base=[py,'-m','pip','install','--disable-pip-version-check','--no-warn-script-location','--upgrade','--only-binary=:all:','--prefer-binary']
    px=_proxy()
    net=base+(['--proxy',px] if px else [])
    offline=lambda:base+['--no-index','--find-links',str(OFFLINE),GDAL_SPEC,ECW_SPEC]
    log=[];erros=[]
    def tentar(cmd,rot,p):
        status_cb(p,rot)
        r=run(cmd,capture_output=True,text=True,timeout=1800)
        out=(r.stdout or '')+'\n'+(r.stderr or '')
        log.append(f'$ {rot}\n'+out[-1500:])
        if r.returncode!=0:erros.append(rot+': '+_resumo(out))
        return r.returncode==0
    ok=False
    if OFFLINE.is_dir() and list(OFFLINE.glob('*.whl')):
        ok=tentar(offline(),'Instalando GDAL + plugin ECW da pasta pacotes_ecw (sem internet)',.2)
    if not ok:
        ok=(tentar(net+['--index-url',GWI_INDEX,'--extra-index-url','https://pypi.org/simple',GDAL_SPEC],'Baixando GDAL para Python (Geospatial Wheels Index)',.15)
            and tentar(net+[ECW_SPEC],'Baixando o plugin ECW (PyPI)',.45))
    if not ok and gdal_wheel_url():
        status_cb(.55,'Baixando as rodas diretamente (GitHub e PyPI, proxy do Windows)')
        try:
            OFFLINE.mkdir(parents=True,exist_ok=True)
            u=gdal_wheel_url();fetch(u,OFFLINE/u.rsplit('/',1)[1])
            eu,en=_ecw_wheel_url(fetch_json);fetch(eu,OFFLINE/en)
            ok=tentar(offline(),'Instalando as rodas baixadas (pacotes_ecw)',.7)
        except Exception as e:
            erros.append('download direto: '+_resumo(str(e)) if str(e) else 'download direto: '+type(e).__name__)
    if not ok:
        tag,plat=_tags()
        try:(BASE/'pacotes_ecw_log.txt').write_text('\n\n'.join(log),encoding='utf-8')
        except OSError:pass
        raise ValueError('A instalação do leitor ECW falhou.\nMotivo: '+' | '.join(erros[-3:])+
            f'\n\nComo resolver sem depender da rede do aplicativo: baixe no navegador os 2 arquivos abaixo e copie-os para a pasta\n{OFFLINE}\n'
            f'(crie a pasta se não existir) e clique de novo em “Instalar leitor ECW interno”:\n'
            f'1) GDAL: {gdal_wheel_url() or f"gdal-3.11.x-{tag}-{tag}-win_amd64.whl"}\n'
            f'2) plugin ECW: {ECW_PAGE} (arquivo gdal_ecw-3.11.3-py3-none-{plat or "win_amd64"}.whl)\n'
            'Se a rede da empresa bloquear, peça à TI para liberar github.com, objects.githubusercontent.com, pypi.org e files.pythonhosted.org.')
    # Recarrega para enxergar o que acabou de ser instalado.
    for m in [m for m in list(sys.modules) if m=='osgeo' or m.startswith('osgeo.')]:sys.modules.pop(m,None)
    import importlib;importlib.invalidate_caches()
    st=status();st['log']='\n'.join(log)[-3000:]
    if not st['ecw']:raise ValueError('GDAL instalado, mas o driver ECW não carregou. Se aparecer “Can\'t load requested DLL”, o Windows precisa do Microsoft Visual C++ 2015-2022 (x64), que a TI instala. Detalhes: '+st['log'][-400:])
    return st

def _corners(gt,w,h):
    return [(gt[0]+gt[1]*x+gt[2]*y,gt[3]+gt[4]*x+gt[5]*y) for x,y in ((0,0),(w,0),(w,h),(0,h))]

def world_file(gt):
    """Arquivo de mundo (.tfw): centro do pixel superior esquerdo."""
    return '\n'.join(f'{v:.12f}' for v in (gt[1],gt[4],gt[2],gt[5],gt[0]+gt[1]/2+gt[2]/2,gt[3]+gt[4]/2+gt[5]/2))+'\n'

def convert_py(src,dst,status=lambda *a:None,gdal=None,tol_m=1e-6):
    """ECW/JP2/MrSID -> GeoTIFF em blocos (Deflate) com visões reduzidas, .tfw e .prj; confere a georreferência."""
    gdal=gdal or py_gdal()
    if gdal is None:raise ValueError('GDAL para Python não está instalado. Use “Instalar leitor ECW interno”.')
    src=Path(src);dst=Path(dst);tmp=dst.with_name(dst.stem+'.parcial.tif')
    for f in (tmp,tmp.with_suffix('.tfw'),tmp.with_suffix('.prj')):
        try:f.unlink()
        except OSError:pass
    ds=gdal.Open(str(src))
    if ds is None:raise ValueError('O GDAL não abriu o arquivo (formato sem driver?).')
    drv=ds.GetDriver().ShortName
    W,H,n=ds.RasterXSize,ds.RasterYSize,ds.RasterCount
    gt0=tuple(ds.GetGeoTransform(can_return_null=True) or ())
    if len(gt0)!=6 or (gt0==(0.,1.,0.,0.,0.,1.)):raise ValueError('O arquivo não traz georreferência (geotransformação). Envie junto o arquivo de mundo e o .prj.')
    srs0=ds.GetSpatialRef()
    bands=[1,2,3] if n>=3 else [1]
    alpha=None
    for b in range(1,n+1):
        if ds.GetRasterBand(b).GetColorInterpretation()==gdal.GCI_AlphaBand:alpha=b
    if alpha and alpha not in bands:bands.append(alpha)
    co=['TILED=YES','BLOCKXSIZE=512','BLOCKYSIZE=512','COMPRESS=DEFLATE','PREDICTOR=2','BIGTIFF=IF_SAFER','NUM_THREADS=ALL_CPUS']
    if len(bands)>=3:co.append('PHOTOMETRIC=RGB')
    if alpha:co.append('ALPHA=YES')
    status(.08,f'Convertendo {src.name} ({drv}, {W}×{H} px) dentro do aplicativo')
    cb=lambda f,*_:(status(.08+.62*float(f),f'Convertendo {src.name}: {int(100*float(f))}%') or 1)
    out=gdal.Translate(str(tmp),ds,options=gdal.TranslateOptions(format='GTiff',bandList=bands,creationOptions=co,callback=cb))
    if out is None:raise ValueError('A conversão não gerou o arquivo.')
    out=None
    status(.72,'Gerando visões reduzidas')
    gdal.SetConfigOption('COMPRESS_OVERVIEW','DEFLATE')
    o=gdal.Open(str(tmp),gdal.GA_Update)
    levels=[f for f in (2,4,8,16,32,64,128) if max(W,H)/f>=256] or [2]
    o.BuildOverviews('AVERAGE',levels,callback=lambda f,*_:(status(.72+.2*float(f),'Gerando visões reduzidas') or 1))
    o=None
    # Conferência da georreferência (antes de aceitar o resultado).
    c=gdal.Open(str(tmp))
    gt1=tuple(c.GetGeoTransform());srs1=c.GetSpatialRef()
    if (c.RasterXSize,c.RasterYSize)!=(W,H):raise ValueError('Tamanho diferente do original após a conversão.')
    dev=max(math.hypot(a[0]-b[0],a[1]-b[1]) for a,b in zip(_corners(gt0,W,H),_corners(gt1,W,H)))
    if dev>tol_m:raise ValueError(f'Georreferência alterada na conversão (canto deslocado {dev:.6f} m). Resultado descartado.')
    same_srs=None
    if srs0 is not None:
        same_srs=bool(srs1 is not None and srs0.IsSame(srs1))
        if not same_srs:raise ValueError('Sistema de coordenadas diferente após a conversão. Resultado descartado.')
    c=None;ds=None
    tmp.with_suffix('.tfw').write_text(world_file(gt0),encoding='ascii')
    if srs0 is not None:
        e=srs0.Clone()
        try:e.MorphToESRI()
        except Exception:pass
        tmp.with_suffix('.prj').write_text(e.ExportToWkt(),encoding='ascii')
    for sfx in ('.tif','.tfw','.prj'):
        a=tmp.with_suffix(sfx) if sfx!='.tif' else tmp;b=dst.with_suffix(sfx)
        if a.exists():a.replace(b)
    status(.95,'Georreferência conferida')
    return {'file':dst.name,'driver':drv,'size':[W,H],'bands':len(bands),'alpha':bool(alpha),'geotransform':list(gt0),
            'crs_wkt':srs0.ExportToWkt() if srs0 is not None else None,'corner_deviation_m':dev,'same_crs':same_srs,'overviews':levels,
            'world':dst.with_suffix('.tfw').name,'prj':dst.with_suffix('.prj').name if srs0 is not None else None}
