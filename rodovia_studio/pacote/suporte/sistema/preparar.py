"""Preparação explícita com Python já instalado; não baixa nem executa scripts remotos."""
import argparse,hashlib,os,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preparar-apenas',action='store_true');args=parser.parse_args()
    if sys.version_info[:2]!=(3,12):raise RuntimeError('Use Python 3.12 de origem oficial, aprovado pela TI. Nenhuma política de segurança será alterada.')
    runtime=BASE/'runtime';python=runtime/('python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():
        import venv
        venv.EnvBuilder(with_pip=True).create(runtime)
    req=BASE/('requirements-windows.lock' if os.name=='nt' else 'requirements.txt');fingerprint=hashlib.sha256(req.read_bytes()).hexdigest();stamp=runtime/'dependencias.ok'
    if not stamp.is_file() or stamp.read_text().strip()!=fingerprint:
        probe=subprocess.run([str(python),'-m','pip','--version'],capture_output=True)
        if probe.returncode:raise RuntimeError('pip ausente no runtime. A TI deve preparar Python/pip de origem oficial; o aplicativo não executa get-pip remoto.')
        wheels=BASE/'pacotes'
        source=['--no-index','--find-links',str(wheels)] if wheels.is_dir() else ['--index-url','https://pypi.org/simple']
        subprocess.run([str(python),'-m','pip','--isolated','install','--only-binary=:all:','--disable-pip-version-check',*source,'--require-hashes','-r',str(BASE/'pip-bootstrap.lock')],check=True)
        hashes=['--require-hashes'] if req.name.endswith('.lock') else []
        subprocess.run([str(python),'-m','pip','--isolated','install','--only-binary=:all:','--disable-pip-version-check',*source,*hashes,'-r',str(req)],check=True)
        subprocess.run([str(python),'-m','pip','check'],check=True)
        stamp.write_text(fingerprint+'\n')
    subprocess.run([str(python),str(BASE/'diagnostico.py')],cwd=BASE,check=True)
    if not args.preparar_apenas:subprocess.run([str(python),str(BASE/'run.py')],cwd=BASE,check=True)

if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,subprocess.CalledProcessError) as error:
        print('Preparação interrompida:',error);sys.exit(1)
