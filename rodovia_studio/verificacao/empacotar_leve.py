"""Deriva atualização leve do pacote completo já aprovado, sem recompilar fontes."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True,type=Path);p.add_argument('--completo',required=True,type=Path);a=p.parse_args()
 manifest=json.loads((a.base/'manifest.json').read_text());base=manifest['version']
 if a.completo.parent.name!='atualizacoes':raise RuntimeError('ZIPs somente em atualizacoes/.')
 output=a.completo.with_name(a.completo.stem+'_leve.zip')
 if output.exists():raise RuntimeError('Preserve o ZIP histórico; destino já existe.')
 with zipfile.ZipFile(a.completo) as z:
  if z.testzip():raise RuntimeError('Completo corrompido.')
  current=json.loads(z.read('pacote/manifest.json'));version=current['version']
  proof=json.loads(z.read('pacote/suporte/documentacao/validacao_'+version.replace('.','_')+'/resultado.json'))
  if proof['version']!=version or not proof['pytest']['tests'] or any(proof['pytest'][k] for k in ('failures','errors','skipped')):raise RuntimeError('O completo não está aprovado.')
  files={}
  for rel,expected in current['files'].items():
   data=z.read('pacote/'+rel)
   if hashlib.sha256(data).hexdigest()!=expected:raise RuntimeError('Hash divergente no completo: '+rel)
   old=a.base/rel
   if not old.is_file() or old.read_bytes()!=data:files[rel]=data
  current.update(base_version=base,description=f'Atualização leve {version}; exige {base} ou posterior.',files={r:hashlib.sha256(d).hexdigest() for r,d in files.items()})
  with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
   out.writestr('pacote/manifest.json',json.dumps(current,ensure_ascii=False,indent=2)+'\n')
   for rel,data in sorted(files.items()):out.writestr('pacote/'+rel,data)
 digest=hashlib.sha256(output.read_bytes()).hexdigest();output.with_suffix('.sha256.txt').write_text(f'{digest}  {output.name}\n')
 print(f'{output}\n{digest}\n{len(files)} arquivos alterados/novos.')
if __name__=='__main__':main()
