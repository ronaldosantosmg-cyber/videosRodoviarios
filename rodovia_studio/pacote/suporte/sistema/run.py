import socket,threading,webbrowser,os,sys,json,urllib.request,traceback,time
from pathlib import Path
import uvicorn
BASE=Path(__file__).resolve().parent

def running_studio(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=2) as r:return json.loads(r.read()).get('status')=='ok'
    except Exception:return False

def free(port):
    with socket.socket() as s:
        try:s.bind(('127.0.0.1',port));return True
        except OSError:return False

def write_port(port):
    """Informa ao iniciador (.exe) a porta em uso."""
    f=os.environ.get('RODOVIA_PORT_FILE')
    if f:
        try:Path(f).parent.mkdir(parents=True,exist_ok=True);Path(f).write_text(str(port),encoding='ascii')
        except OSError:pass

def organizar_pasta():
    """1.32: raiz só com o arquivo principal e as pastas projetos, videos, atualizacoes e sistema."""
    try:
        if BASE.name=='programa' and BASE.parent.name=='sistema':
            import atualizador
            atualizador.organize_root(BASE.parents[1],say=print)
    except Exception as e:print('Aviso: não foi possível organizar a pasta principal:',e)

if __name__=='__main__':
    organizar_pasta()
    port=int(os.environ.get('RODOVIA_PORT','8765'))
    if not free(port):
        if running_studio(port):
            print(f'O Rodovia Studio já está aberto em http://127.0.0.1:{port}. Usando essa janela.');write_port(port)
            if not os.environ.get('RODOVIA_NO_BROWSER'):webbrowser.open(f'http://127.0.0.1:{port}')
            raise SystemExit(0)
        # Outro programa ocupa a porta: procura a próxima livre em vez de encerrar.
        for p in range(port+1,port+20):
            if free(p):print(f'A porta {port} está ocupada por outro programa; usando {p}.');port=p;break
        else:print(f'Nenhuma porta livre entre {port} e {port+19}.');raise SystemExit(1)
    write_port(port)
    # 1.23: o Rodovia Studio.exe abre a janela por conta própria (RODOVIA_NO_BROWSER).
    if not os.environ.get('RODOVIA_NO_BROWSER'):threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{port}')).start()
    print(f'Rodovia Studio: http://127.0.0.1:{port}\nMantenha esta janela aberta durante a geração. Ctrl+C encerra o aplicativo.')
    try:uvicorn.run('app.server:app',host='127.0.0.1',port=port,log_level='info')
    except Exception:
        # Registra a causa no log de instalação para diagnóstico.
        with open(BASE/'servidor_erro.log','a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+traceback.format_exc()+'\n')
        traceback.print_exc();raise SystemExit(1)
