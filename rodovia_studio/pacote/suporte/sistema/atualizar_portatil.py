"""Atualização com Python aprovado, fora da pasta alterada; sem shell ou PowerShell."""
import argparse,os,shutil,subprocess,sys,tempfile
from pathlib import Path

def stage(root,temporary):
    root=Path(root).resolve();temporary=Path(temporary)
    installed=next((p for p in (root/'sistema/programa/atualizador.py',root/'suporte/sistema/atualizador.py') if p.is_file() and not p.is_symlink()),None)
    if installed is None:raise ValueError('Instalação não encontrada; nenhum arquivo foi alterado.')
    script=temporary/'atualizador.py';shutil.copy2(installed,script)
    executable=Path(sys.executable);home=executable.parent
    embedded=next(home.glob('python3*.zip'),None) if os.name=='nt' else None
    if embedded:
        for f in home.iterdir():
            if f.is_file() and not f.is_symlink() and f.suffix.lower() in ('.exe','.dll','.pyd','.zip'):shutil.copy2(f,temporary/f.name)
        (temporary/(embedded.stem+'._pth')).write_text(embedded.name+'\n.\n',encoding='ascii')
        runner=temporary/executable.name
    elif os.name=='nt':runner=Path(sys.base_prefix)/'python.exe'
    else:runner=executable
    if not runner.is_file():raise ValueError('Python de base indisponível. Solicite a TI a preparação da instalação.')
    return runner,script

def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',required=True);p.add_argument('--aguardar',type=int,default=90);p.add_argument('--restaurar-anterior',action='store_true');p.add_argument('--backup');args=p.parse_args()
    if not 0<=args.aguardar<=300:raise ValueError('Espera deve estar entre 0 e 300 s.')
    with tempfile.TemporaryDirectory(prefix='rodovia_atualizacao_') as temporary:
        runner,script=stage(args.raiz,temporary)
        command=[str(runner),'-X','utf8',str(script),'--raiz',str(Path(args.raiz).resolve()),'--aguardar',str(args.aguardar)]
        command+=['--restaurar-anterior'] if args.restaurar_anterior else ['--procurar']
        if args.backup:command+=['--backup',args.backup]
        return subprocess.run(command,cwd=temporary,check=False).returncode
if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError) as error:print('Atualização interrompida:',error);sys.exit(1)
