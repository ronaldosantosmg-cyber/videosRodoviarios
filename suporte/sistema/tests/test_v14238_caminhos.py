"""1.42.38: nomes e caminhos longos (limite de 260 caracteres do Windows) e aviso do limite de 256 rotas."""
import io,json,os,zipfile
import numpy as np
import pytest
from pathlib import Path
from shapely.geometry import box


def test_limpar_e_nomes_reservados():
    from app import caminhos as c
    assert c.limpar('CON.txt')=='_CON.txt' and c.limpar('a:b*c?.tif')=='a_b_c_.tif' and c.limpar('../../x y.tif')=='x y.tif'
    assert c.limpar('  ..  ')=='arquivo'


def test_nome_curto_nao_muda_e_longo_cabe(tmp_path,monkeypatch):
    from app import caminhos as c
    monkeypatch.setenv('RODOVIA_LIMITE_CAMINHO','120')
    pasta=tmp_path/'p'
    assert c.encurtar(pasta,'ortofoto_trecho.tif')=='ortofoto_trecho.tif'
    nome='ortofoto_'+'x'*300
    tif=c.encurtar(pasta,nome+'.tif',extra=24);tfw=c.encurtar(pasta,nome+'.tfw',extra=24);prj=c.encurtar(pasta,nome+'.prj',extra=24)
    assert Path(tif).stem==Path(tfw).stem==Path(prj).stem      # imagem, mundo e .prj continuam casando pelo nome base
    for n in (tif,tfw,prj):assert c.comprimento(pasta/n)+24<=120
    assert c.encurtar(pasta,'ortofoto_'+'y'*300+'.tif',extra=24)!=tif   # nomes longos diferentes não se confundem


def test_pasta_longa_demais_gera_mensagem_clara(tmp_path,monkeypatch):
    from app import caminhos as c
    monkeypatch.setenv('RODOVIA_LIMITE_CAMINHO','90')
    with pytest.raises(ValueError,match='caminho curto'):c.encurtar(tmp_path/('x'*60),'a.tif')


def test_traduzir_erro_de_nome_longo():
    import errno
    from app import caminhos as c
    assert 'longo demais' in c.traduzir(OSError(errno.ENAMETOOLONG,'x'))
    assert c.traduzir(PermissionError(13,'x')) is None and c.traduzir(ValueError('x')) is None


def test_videos_cabem_no_limite(tmp_path,monkeypatch):
    from app import videos,store,caminhos as c
    from app.models import Settings
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'));monkeypatch.setenv('RODOVIA_LIMITE_CAMINHO','140')
    nome='Projeto de acesso '+'muito longo '*8
    pid='a'*32
    d=videos.project_folder(pid,nome)
    assert c.comprimento(d/('x'*16+'_2026-10-28_10h00_v01.mp4.tmp'))<=140
    assert videos.project_folder(pid,nome)==d                    # a mesma pasta é reencontrada
    # nome normal em pasta normal continua exatamente como antes
    monkeypatch.setenv('RODOVIA_LIMITE_CAMINHO','240')
    assert videos.project_folder('b'*32,'Trecho TH57').name=='Trecho TH57'


def test_arquivo_de_video_longo_mantem_versao_e_data(tmp_path,monkeypatch):
    from app import videos,caminhos as c
    from app.models import Settings
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'));monkeypatch.setenv('RODOVIA_LIMITE_CAMINHO','150')
    s=Settings(name='Nome do projeto bem comprido '*3)
    d=tmp_path/'proj';d.mkdir();(d/'video.mp4').write_bytes(b'0'*10)
    dst=videos.archive(d,'c'*32,s,{})
    assert dst.exists() and dst.with_suffix('.json').exists() and videos.NAME_OK.match(dst.name)
    assert dst.stem.endswith('_v01') and c.comprimento(dst.with_suffix('.json'))<=150


def test_unpack_grava_pelo_caminho_longo(tmp_path):
    from app.exporters import package,unpack
    d=tmp_path/'p';d.mkdir();(d/'config.json').write_text('{"name":"x"}',encoding='utf-8')
    out=tmp_path/'o';out.mkdir()
    m=unpack(package(d,'1.42.38'),out)
    assert (out/'config.json').read_text(encoding='utf-8')=='{"name":"x"}' and m['files']


def test_api_envio_com_nome_longo_e_saude(tmp_path,monkeypatch):
    """Antes, nomes acima de 120 caracteres perdiam a extensão (e a imagem e o arquivo de mundo viravam o mesmo arquivo)."""
    from fastapi.testclient import TestClient
    from app.server import app
    from app.models import Settings
    from app import store
    import cv2
    c=TestClient(app);h=c.get('/api/health').json();assert 'caminhos' in h and h['caminhos']['limite']>=60
    pid=c.post('/api/projects',json=Settings(name='Longo').model_dump()).json()['id']
    nome='ortofoto_'+'z'*220
    png=cv2.imencode('.png',np.zeros((8,8,3),np.uint8))[1].tobytes()
    r=c.post(f'/api/projects/{pid}/imagery',files=[('files',(nome+'.png',png,'image/png')),('files',(nome+'.pgw',b'1\n0\n0\n-1\n0\n8\n','text/plain'))],data={'crs':'EPSG:31983'})
    assert r.status_code in (200,201),r.text
    arquivos=sorted(os.listdir(store.ROOT/pid/'imagem_local'))
    assert len(arquivos)==2 and {Path(a).suffix for a in arquivos}=={'.png','.pgw'} and len({Path(a).stem for a in arquivos})==1
    assert all(len(a)<=120 for a in arquivos)


def test_aviso_do_limite_de_256_rotas():
    from app.models import Settings
    from app.traffic import TrafficNetwork
    from app.native_axes import axis_fingerprint
    axes=[np.array([[0.,i*30.],[100.,i*30.]]) for i in range(300)]
    s=Settings(derive_traffic_paths=False,hydrography=False,route_directions={'axis:'+axis_fingerprint(p):'forward' for p in axes})
    n=TrafficNetwork([box(-5,-10,105,9000)],[],[dict(points=p) for p in axes],axes[0],np.array([0.,100.]),s)
    assert len(n.paths)==256                                   # o corte acontece de verdade
    assert any('Limite de 256 rotas' in w and '44 segmento' in w for w in n.warnings)
    assert all(any(i in p['edges'] for p in n.paths) for i,e in enumerate(n.edges) if e['kind']=='main')   # o corte nunca tira o eixo principal
    p=np.array([[0.,0.],[400.,0.]])
    m=TrafficNetwork([box(-30,-12,430,12)],[],[dict(points=p)],p,np.array([0.,400.]),Settings(derive_traffic_paths=False))
    assert not any('256 rotas' in w for w in m.warnings)      # sem corte, sem aviso
