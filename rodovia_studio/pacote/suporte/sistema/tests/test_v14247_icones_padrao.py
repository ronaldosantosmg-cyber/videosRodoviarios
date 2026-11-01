"""2.18: todo ícone automático tem glifo SVG (sem emoji) e rótulos continuam sem ícone duplicado."""
import json,re,shutil,subprocess
from pathlib import Path
import pytest

JS=Path(__file__).resolve().parents[1]/'app'/'js'
NODE=shutil.which('node')

SCRIPT=r'''
const fs=require('fs'),vm=require('vm');
const src45=fs.readFileSync(process.argv[1],'utf8'),src92=fs.readFileSync(process.argv[2],'utf8');
const a=src45.indexOf('const ICO={'),b=src45.indexOf('const ICO_REGRAS');
const ctx={globalThis:null};ctx.globalThis=ctx;vm.createContext(ctx);
vm.runInContext(src45.slice(a,b).replace('const ICO','var ICO')+";function icoSvg(n){const p=ICO[n];return p?'<svg>'+p+'</svg>':''}",ctx);
vm.runInContext(src92.split("if(typeof document!=='undefined')")[0].replace("})(typeof window!=='undefined'?window:globalThis)","})(globalThis)"),ctx);
const T=ctx.RodoviaIcones;const out={missing:[],emoji:[]};
const rules=[...src92.matchAll(/\[\/[^\]]*?\/,'([^']+)'\]/g)].map(m=>m[1]);
for(const ic of new Set(rules)){if(!T.NOME[ic])out.missing.push(ic)}
for(const n of Object.values(T.NOME)){if(!ctx.ICO[n])out.missing.push('glifo:'+n)}
for(const l of ['Salvar','Abrir pasta','Exportar vídeo','Congelar camada','Comparar','Aviso','Ajuda','Mais resultados']){const s=T.svgFor(l);if(!s||/[\u{1F000}-\u{1FAFF}]/u.test(s))out.emoji.push(l)}
console.log(JSON.stringify(out));
'''

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_todo_icone_automatico_tem_svg():
    r=subprocess.run([NODE,'-e',SCRIPT,str(JS/'45_menus_windows.js'),str(JS/'92_icones_menus.js')],capture_output=True,text=True,timeout=60)
    assert r.returncode==0,r.stderr
    out=json.loads(r.stdout.strip().splitlines()[-1])
    assert out['missing']==[],out
    assert out['emoji']==[],out

def test_sem_fallback_de_emoji_e_com_dedupe():
    t=(JS/'92_icones_menus.js').read_text(encoding='utf-8')
    assert 's.textContent=ic' not in t
    assert 'function dedupe' in t and 'nameIconOnly' in t
