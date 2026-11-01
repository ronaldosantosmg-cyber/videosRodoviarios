"""Verifica aplicação/rollback dos ZIPs exatos, a partir de uma base explícita."""
import argparse,hashlib,importlib.util,json,shutil,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/'rodovia_studio/pacote/suporte/sistema'
spec=importlib.util.spec_from_file_location('up',SYSTEM/'atualizador.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--base',required=True,type=Path);parser.add_argument('--version',required=True);args=parser.parse_args()
 old=json.loads((args.base/'suporte/sistema/VERSAO.json').read_text())['version'];results=[]
 with tempfile.TemporaryDirectory(prefix='rs-release-check-') as temp:
  temp=Path(temp)
  for suffix in ('','_leve'):
   filename='RodoviaStudio_'+args.version.replace('.','_')+'_atualizacao'+suffix+'.zip';archive=ROOT/'atualizacoes'/filename
   stage=temp/('pacote'+suffix);stage.mkdir()
   with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None;z.extractall(stage)
   package=stage/'pacote';up.validate_package(package,lambda *a:None)
   root=temp/('Instalação com espaço á'+suffix);(root/'sistema/programa/app').mkdir(parents=True)
   (root/'sistema/programa/app/server.py').write_text('# inicial')
   for source,target,_ in up._targets(args.base,root):target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
   assert up.installed_version(root)==old
   preserved={}
   for rel in ('projetos/exemplo/config.json','projetos/exemplo/input.kmz','projetos/_base_imagens/x/original.tif','videos/exemplo/video.mp4'):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(('preservar '+rel).encode());preserved[rel]=sha(p)
   before={t.relative_to(root).as_posix():sha(t) for _,t,_ in up._targets(args.base,root)}
   result=up.apply(package,root,lambda *a:None,check_running=False)
   assert up.installed_version(root)==args.version
   targets=list(up._targets(package,root));assert all(sha(s)==sha(t) for s,t,_ in targets)
   assert all(sha(root/rel)==h for rel,h in preserved.items())
   up.restore_previous(root,result['backup'],lambda *a:None,check_running=False)
   assert up.installed_version(root)==old and all(sha(root/r)==h for r,h in before.items())
   assert all(sha(root/rel)==h for rel,h in preserved.items())
   if suffix:
    (root/'sistema/programa/VERSAO.json').write_text(json.dumps({'version':'2.62'}))
    try:up.apply(package,root,lambda *a:None,check_running=False)
    except up.PackageError:pass
    else:raise AssertionError('Pacote leve aceito abaixo da base mínima.')
   results.append({'filename':filename,'sha256':sha(archive),'files_checked':len(targets),'apply':True,'rollback':True,'data_preserved':True,'older_base_refused':bool(suffix)})
 out=ROOT/'rodovia_studio/evidencias'/args.version/'pacotes-verificados.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps({'base_version':old,'platform':'Linux; não é homologação Windows nativa','packages':results},ensure_ascii=False,indent=2)+'\n');print(out)
if __name__=='__main__':main()
