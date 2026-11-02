"""1.37: abrir DWG — convertido para DXF pelo ODA File Converter (gratuito, da Open Design Alliance) instalado no
computador. O DWG original não é alterado; o DXF convertido fica no projeto (input.dxf) e uma cópia do DWG em input.dwg."""
import os,glob,shutil,subprocess,tempfile,sys
from pathlib import Path

AJUDA=('Para abrir DWG, instale o ODA File Converter (gratuito, da Open Design Alliance: opendesign.com › Guest Files › '
       'ODA File Converter) e abra o DWG de novo. Outra opção: no AutoCAD/Civil 3D, Salvar como › DXF.')

def conversor():
    """Caminho do ODAFileConverter (variável RODOVIA_ODA, pasta sistema/ferramentas ou instalação padrão do Windows)."""
    env=os.environ.get('RODOVIA_ODA')
    if env and Path(env).exists():return str(Path(env))
    raiz=Path(__file__).resolve().parents[2]
    cand=[str(raiz/'ferramentas'/'ODAFileConverter'/'ODAFileConverter.exe')]
    for base in [os.environ.get('ProgramFiles',r'C:\Program Files'),os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'),
                 os.path.join(os.environ.get('LOCALAPPDATA',''),'Programs')]:
        if base:cand+=sorted(glob.glob(os.path.join(base,'ODA','ODAFileConverter*','ODAFileConverter.exe')),reverse=True)
    cand+=[shutil.which('ODAFileConverter') or '',shutil.which('ODAFileConverter.exe') or '','/usr/bin/ODAFileConverter']
    for c in cand:
        if c and Path(c).exists():return c
    return None

def converter(dwg_bytes,nome='desenho.dwg',timeout=300):
    """Converte o DWG (bytes) em DXF (bytes). ValueError com orientação se não houver conversor ou se falhar."""
    if not dwg_bytes[:6].startswith(b'AC10'):raise ValueError('O arquivo não parece um DWG (cabeçalho AC10xx ausente).')
    exe=conversor()
    if not exe:raise LookupError(AJUDA)
    with tempfile.TemporaryDirectory(prefix='rs_dwg_') as tmp:
        ent=Path(tmp)/'entrada';sai=Path(tmp)/'saida';ent.mkdir();sai.mkdir()
        (ent/'desenho.dwg').write_bytes(dwg_bytes)
        # Entrada, saída, versão, tipo, recursivo, auditar, filtro (sintaxe do ODA File Converter).
        cmd=[exe,str(ent),str(sai),'ACAD2018','DXF','0','1','*.DWG']
        kw={}
        if sys.platform=='win32':
            si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0;kw={'startupinfo':si,'creationflags':0x08000000}
        try:r=subprocess.run(cmd,capture_output=True,timeout=timeout,**kw)
        except subprocess.TimeoutExpired:raise ValueError(f'A conversão do DWG passou de {timeout//60} min e foi interrompida.')
        except OSError as e:raise ValueError(f'Não foi possível executar o ODA File Converter: {e}')
        out=[p for p in sai.iterdir() if p.suffix.lower()=='.dxf']
        if not out:
            err=(r.stderr or b'').decode('utf-8','replace').strip()[-300:]
            erros=list(sai.glob('*.err'))
            if erros:err=(erros[0].read_text(encoding='utf-8',errors='replace')[-300:] or err)
            raise ValueError('O ODA File Converter não gerou o DXF'+(f': {err}' if err else '. Confira se o DWG abre no AutoCAD.'))
        return out[0].read_bytes()
