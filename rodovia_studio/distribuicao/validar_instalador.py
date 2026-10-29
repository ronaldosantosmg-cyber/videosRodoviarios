"""Testes do complemento de distribuição; o produto 2.02 continua byte a byte igual."""
import json,os,subprocess,sys,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
from gerar_instalador import HERE,REPO,BASE,source_digest,compile_cs,compiler

def main():
    evidence=HERE/'evidencias';evidence.mkdir(exist_ok=True);initial=source_digest();xml=evidence/'pytest.xml'
    with (evidence/'validacao.log').open('w') as log:
        subprocess.run([sys.executable,'-m','pytest','-q',str(HERE/'tests'),'--junitxml='+str(xml)],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
        counts={key:sum(int(s.get(key,0)) for s in ET.parse(xml).getroot().findall('.//testsuite')) for key in ('tests','failures','errors','skipped')}
        if not counts['tests'] or any(counts[k] for k in ('failures','errors','skipped')):raise RuntimeError('Instalador não aprovado.')
        with tempfile.TemporaryDirectory(prefix='rs_setup_checks_') as tmp:
            tmp=Path(tmp);assembly=tmp/'AssemblyInfo.cs';assembly.write_text('using System.Reflection;[assembly: AssemblyCompany("Ronaldo Santos")][assembly: AssemblyProduct("Rodovia Studio")][assembly: AssemblyFileVersion("2.2.0.0")]')
            source=tmp/'Instalador.cs';source.write_text((HERE/'Instalador.cs').read_text().replace('@MANIFEST_SHA@','0'*64).replace('@SIGNING_NOTICE@','Sem certificado Authenticode: fornecedor desconhecido no Windows.'))
            binary=tmp/'Instalador.exe';compile_cs(source,binary,assembly)
            compile_cs(BASE/'iniciador/RodoviaStudio.cs',tmp/'Rodovia Studio.exe',assembly,Path(os.environ.get('WEBVIEW2_LIB','/workspace/.tools/webview2')))
            mono=compiler()[0];env=dict(os.environ,DISPLAY=os.environ.get('DISPLAY',':91'))
            subprocess.run([mono,str(binary),'--capturar',str(evidence/'instalador.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
            helper=tmp/'Metadados.cs';helper.write_text('using System;using System.Diagnostics;class X {static void Main(string[] a){var f=FileVersionInfo.GetVersionInfo(a[0]);if(f.CompanyName!="Ronaldo Santos"||f.FileVersion!="2.2.0.0")throw new Exception("Metadados incorretos");Console.WriteLine(f.CompanyName+" | "+f.FileVersion);}}')
            subprocess.run(compiler()+['/nologo','/out:'+str(tmp/'Metadados.exe'),str(helper)],check=True,stdout=log,stderr=subprocess.STDOUT)
            for binary in (binary,tmp/'Rodovia Studio.exe'):subprocess.run([mono,str(tmp/'Metadados.exe'),str(binary)],check=True,stdout=log,stderr=subprocess.STDOUT)
    if initial!=source_digest():raise RuntimeError('Fontes de distribuição mudaram durante a validação.')
    from PIL import Image
    with Image.open(evidence/'instalador.png') as image:
        if image.width<650 or image.height<500:raise RuntimeError('Imagem do instalador ausente ou incompleta.')
    report=dict(approved=True,source_sha256=initial,pytest=counts,compiled=['instalador Windows x64','iniciador WebView2 Windows x64'],publisher_metadata='Ronaldo Santos',authenticode_signed=False,visual='Mono/Xvfb',windows_native=False,scope='Ensaios de arquivos usam o atualizador e o ZIP 2.02 reais; subprocessos Windows simulados. Compilação/GUI Mono não comprovam execução nativa Windows.')
    (evidence/'testes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
