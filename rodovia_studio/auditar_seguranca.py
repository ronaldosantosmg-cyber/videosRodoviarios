#!/usr/bin/env python3
"""Inventário de distribuição e controles verificáveis. Não é um antivírus."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent

def audit(package):
    rows=[];findings=[];binaries=[]
    for f in sorted(Path(package).rglob('*')):
        if not f.is_file() or any(x in f.parts for x in ('tests','__pycache__','.pytest_cache')):continue
        if f.is_symlink():findings.append({'file':str(f),'rule':'link_simbolico'});continue
        data=f.read_bytes();name=f.relative_to(package).as_posix();rows.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        if data[:2]==b'MZ' or f.suffix.lower() in ('.exe','.dll','.scr','.com'):binaries.append(name)
        if f.suffix.lower() not in ('.py','.ps1','.cmd','.cs'):continue
        text=data.decode('utf-8-sig','replace')
        for rule,pattern in {'politica_bypass':r'(?i)-ExecutionPolicy\s+Bypass','powershell_codificado':r'(?i)-EncodedCommand\s','download_getpip':r'https://bootstrap\.pypa\.io','desativar_antivirus':r'(?i)(?:Set|Add)-MpPreference|DisableRealtimeMonitoring|Add-MpPreference','tls_sem_verificacao':r'verify\s*=\s*False','shell_interpolado':r'shell\s*=\s*True'}.items():
            if re.search(pattern,text):findings.append({'file':name,'rule':rule})
    return {'method':'inventario_e_regras_estaticas','antivirus':False,'files':rows,'pe_binaries':binaries,'findings':findings,'limitations':'Não comprova ausência de malware. Conferir antivírus corporativo, assinaturas, dependências e comportamento em Windows.'}

def zip_check(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        names=set()
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in info.filename or ':' in info.filename or info.filename in names or info.flag_bits&1 or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Entrada de ZIP inválida: '+info.filename)
            names.add(info.filename)
        if sum(x.file_size for x in z.infolist())>1024*1024*1024:raise ValueError('Pacote acima de 1 GiB.')
    return {'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'bytes':Path(path).stat().st_size,'zip_integrity':'ok'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zip');p.add_argument('--saida',required=True);args=p.parse_args()
    result=audit(ROOT/'pacote')
    if args.zip:result['archive']=zip_check(args.zip)
    Path(args.saida).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files':len(result['files']),'findings':result['findings'],'pe_binaries':result['pe_binaries']}))
    if result['findings'] or result['pe_binaries']:raise SystemExit(1)
