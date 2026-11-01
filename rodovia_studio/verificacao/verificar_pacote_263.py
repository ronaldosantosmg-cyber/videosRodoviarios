"""Aplica os ZIPs publicados a cópias isoladas da 2.62 e confere rollback/dados."""
import hashlib,importlib.util,json,shutil,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/'rodovia_studio/pacote/suporte/sistema'
spec=importlib.util.spec_from_file_location('up',SYSTEM/'atualizador.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
BASE=Path('/workspace/onboarding/inspecao-2.62/pacote')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify():
 results=[]
 with tempfile.TemporaryDirectory(prefix='rs263-pacotes-') as temp:
  temp=Path(temp)
  for filename in ['RodoviaStudio_2_63_atualizacao.zip','RodoviaStudio_2_63_atualizacao_leve.zip']:
   archive=ROOT/'atualizacoes'/filename;stage=temp/filename.removesuffix('.zip');stage.mkdir()
   with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    z.extractall(stage)
   package=stage/'pacote';up.validate_package(package,lambda *a:None)
   root=temp/('Instalação '+filename);(root/'sistema/programa/app').mkdir(parents=True)
   (root/'sistema/programa/app/server.py').write_text('# inicial')
   for source,target,_ in up._targets(BASE,root):target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
   assert up.installed_version(root)=='2.62'
   data={}
   for rel in ['projetos/exemplo/config.json','projetos/exemplo/input.kmz','projetos/_base_imagens/x/imagem.tif','videos/exemplo/video.mp4']:
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(('preservar '+rel).encode());data[rel]=sha(p)
   before={target.relative_to(root).as_posix():sha(target) for _,target,_ in up._targets(BASE,root)}
   result=up.apply(package,root,lambda *a:None,check_running=False)
   assert up.installed_version(root)=='2.63'
   targets=list(up._targets(package,root))
   assert all(sha(source)==sha(target) for source,target,_ in targets)
   assert all(sha(root/rel)==value for rel,value in data.items())
   up.restore_previous(root,result['backup'],lambda *a:None,check_running=False)
   assert up.installed_version(root)=='2.62'
   assert all(sha(root/rel)==value for rel,value in before.items())
   assert all(sha(root/rel)==value for rel,value in data.items())
   if 'leve' in filename:
    (root/'sistema/programa/VERSAO.json').write_text(json.dumps({'version':'2.60'}))
    try:up.apply(package,root,lambda *a:None,check_running=False)
    except up.PackageError as e:assert '2.62' in str(e)
    else:raise AssertionError('Pacote leve foi aceito numa base anterior à exigida.')
   results.append({'filename':filename,'sha256':sha(archive),'installed_files_checked':len(targets),'apply':True,'rollback':True,'persistent_data_preserved':True,'older_base_refused':True if 'leve' in filename else None})
 output=ROOT/'rodovia_studio/evidencias/2.63/pacotes-verificados.json';output.write_text(json.dumps({'platform':'Linux; não equivale a validação Windows nativa','packages':results},ensure_ascii=False,indent=2)+'\n')
 print(output)
if __name__=='__main__':verify()
