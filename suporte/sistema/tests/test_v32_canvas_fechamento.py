import shutil,subprocess,pathlib,pytest

JS=pathlib.Path(__file__).resolve().parents[1]/'app/js/02_vista_imagem_web.js'


def test_fonte_fecha_no_primeiro_vertice_apos_trecho_oculto():
    t=JS.read_text(encoding='utf-8')
    assert 'path.lineTo(x0,y0)' in t and 'closePath volta ao último moveTo' in t


@pytest.mark.skipif(not shutil.which('node'),reason='node ausente')
def test_closePath_apos_moveTo_gera_corda_e_a_correcao_nao(tmp_path):
    js=r"""
class P{constructor(){this.s=[];this.c=null;this.t=null}moveTo(x,y){this.c=[x,y];this.t=[x,y]}lineTo(x,y){this.s.push([this.c,[x,y]]);this.c=[x,y]}closePath(){this.s.push([this.c,this.t]);this.c=this.t}}
function b(p,k,fx){const a=new P(),sk=new Set(k);p.forEach((q,i)=>{if(i&&!sk.has(i-1))a.lineTo(q[0],q[1]);else a.moveTo(q[0],q[1])});
 if(!sk.has(p.length-1)){if(fx&&sk.size)a.lineTo(p[0][0],p[0][1]);else a.closePath()}return a.s}
const r=[[0,0],[10,0],[10,10],[0,10],[0,0.0001]];
const m=s=>Math.max(...s.map(([u,v])=>Math.hypot(u[0]-v[0],u[1]-v[1])));
console.log(m(b(r,[1],false))>12?'ANTIGO_CORDA':'ANTIGO_OK',m(b(r,[1],true))<11?'NOVO_OK':'NOVO_CORDA')
"""
    f=tmp_path/'t.js';f.write_text(js)
    out=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=20).stdout.strip()
    assert out=='ANTIGO_CORDA NOVO_OK'
