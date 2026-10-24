"""Verifica recursos locais sem baixar instaladores ou contatar serviços externos."""
from pathlib import Path
import importlib.util,subprocess


def inspect_local():
    from .dwg import conversor
    from .encoding import ffmpeg_exe
    required=['fastapi','uvicorn','pydantic','ezdxf','numpy','scipy','shapely','pyproj','cv2','PIL','imageio_ffmpeg','rasterio','tifffile','skimage']
    modules={name:importlib.util.find_spec(name) is not None for name in required}
    ffmpeg=False;detail=None
    try:
        ff=ffmpeg_exe();r=subprocess.run([ff,'-version'],capture_output=True,text=True,timeout=5)
        ffmpeg=r.returncode==0;detail=r.stdout.splitlines()[0] if r.stdout else 'Sem resposta.'
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:detail=str(exc)[:300]
    drivers={}
    try:
        import rasterio
        with rasterio.Env() as env:drivers=env.drivers()
    except Exception:pass
    return {'dependencias_locais':modules,'ffmpeg':{'disponivel':ffmpeg,'detalhe':detail},
            'fontes_locais':(Path(__file__).resolve().parents[1]/'assets/fonts/DejaVuSans.ttf').is_file(),
            'recursos':{'DXF':modules['ezdxf'],'KMZ':True,'GeoTIFF':'GTiff' in drivers,'ECW':'ECW' in drivers,'MrSID':'MrSID' in drivers,'DWG_ODA':bool(conversor())},
            'dependem_de_internet':['Imagem aérea online sem cache','Consulta de cidades e hidrografia online','Download de atualizações e componentes opcionais'],
            'observacao':'Disponibilidade de driver não certifica um arquivo real. ECW/MrSID e DWG dependem de componentes opcionais; DXF, KMZ, GeoTIFF, edição, simulação, MP4 e prompt IA podem funcionar localmente.'}
