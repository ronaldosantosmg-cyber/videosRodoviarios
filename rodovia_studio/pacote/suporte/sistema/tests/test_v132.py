"""1.32: pasta principal só com o arquivo principal (auxiliares em sistema/), vídeos guardados sem substituir os
anteriores, limpeza de resíduos, qualidade do vídeo (Alta/Máxima) e atualização pelo aplicativo."""
import json,os,shutil,subprocess,time,zipfile
from pathlib import Path
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import settings,drawing
from test_v110 import junction
from app.models import Settings
import atualizador as U

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})
REAL=open('atualizador.py',encoding='utf-8').read()

def install_131(root,exe=True):
    """Instalação como a 1.31 deixava (organização 1.8: suporte/...)."""
    files={'ABRIR RODOVIA STUDIO.cmd':'abrir antigo','ATUALIZAR RODOVIA STUDIO.cmd':'atualizar antigo','COMPILAR INICIADOR.cmd':'compilar antigo','LEIA-ME.txt':'leia antigo',
           'suporte/sistema/app/server.py':'# 1.31','suporte/sistema/run.py':'run','suporte/sistema/runtime/python.exe':'py','suporte/sistema/VERSAO.json':json.dumps({'version':'1.31.0'}),
           'suporte/sistema/atualizador.py':'# velho','suporte/documentacao/ATUALIZACAO_1_31.md':'doc','suporte/logs/instalacao.log':'log','suporte/backups/antes_v1_31_0_x/a.txt':'b',
           'projetos/abc/config.json':'{}','atualizacoes/aplicadas/RodoviaStudio_1_31_atualizacao.zip':'z'}
    if exe:files['Rodovia Studio.exe']='exe 1.1'
    for f,t in files.items():
        p=root/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')

def package(tmp,version='1.32.0'):
    pk=tmp/f'pkg_{version}'/'pacote'
    for f,t in {'manifest.json':json.dumps({'version':version}),'raiz/ABRIR RODOVIA STUDIO.cmd':'abrir 1.32','raiz/ATUALIZAR RODOVIA STUDIO.cmd':'atualizar 1.32',
                'raiz/COMPILAR INICIADOR.cmd':'compilar 1.32','raiz/LEIA-ME.txt':'leia 1.32','suporte/sistema/app/server.py':'# 1.32','suporte/sistema/run.py':'run 1.32',
                'suporte/sistema/VERSAO.json':json.dumps({'version':version}),'suporte/sistema/atualizador.py':REAL,'suporte/documentacao/ATUALIZACAO_1_32.md':'doc 1.32'}.items():
        p=pk/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')
    return pk

def test_layout_132_from_131_with_old_exe(tmp_path):
    root=tmp_path/'Rodovia_Studio';install_131(root)
    res=U.apply(package(tmp_path),root,say=lambda *a:None,check_running=False)
    assert res['layout_before']=='nova' and res['old_exe_saved'] and res['previous']=='1.31.0'
    s=root/'sistema';p=s/'programa'
    assert not (root/'suporte').exists() and (p/'app/server.py').read_text()=='# 1.32' and (p/'runtime/python.exe').exists()
    assert (s/'documentacao/ATUALIZACAO_1_31.md').exists() and (s/'documentacao/ATUALIZACAO_1_32.md').exists() and (s/'logs/instalacao.log').exists() and (s/'backups/antes_v1_31_0_x/a.txt').exists()
    # O .exe antigo (procura suporte\sistema) foi guardado; o .cmd volta a ser o arquivo principal; recompila na próxima abertura.
    assert not (root/'Rodovia Studio.exe').exists() and any(x.name=='Rodovia Studio.exe' for x in (s/'backups').rglob('*')) and (s/'logs/recompilar_iniciador.txt').exists()
    assert (root/'ABRIR RODOVIA STUDIO.cmd').read_text()=='abrir 1.32' and (s/'ABRIR RODOVIA STUDIO.cmd').read_text()=='abrir 1.32'
    assert (s/'COMPILAR INICIADOR.cmd').read_text()=='compilar 1.32' and (s/'LEIA-ME.txt').read_text()=='leia 1.32' and (s/'ATUALIZAR RODOVIA STUDIO.cmd').read_text()=='atualizar 1.32'
    # O ATUALIZAR antigo da raiz pode estar em execução: só sai na próxima abertura (run.py -> organize_root).
    assert (root/'ATUALIZAR RODOVIA STUDIO.cmd').exists() and not (root/'COMPILAR INICIADOR.cmd').exists() and not (root/'LEIA-ME.txt').exists()
    U.organize_root(root,say=lambda *a:None)
    assert {x.name for x in root.iterdir()}=={'ABRIR RODOVIA STUDIO.cmd','projetos','videos','atualizacoes','sistema'}
    assert any(x.read_text(encoding='utf-8')=='atualizar antigo' for x in (s/'backups').rglob('ATUALIZAR RODOVIA STUDIO.cmd'))
    assert U.find_root(root)==(root,'sistema') and U.installed_version(root)=='1.32.0'
    # Com o .exe novo (compilado), a raiz fica só com ele; o .cmd fica de reserva em sistema/.
    (root/'Rodovia Studio.exe').write_text('exe 1.2');U.organize_root(root,say=lambda *a:None)
    assert {x.name for x in root.iterdir()}=={'Rodovia Studio.exe','projetos','videos','atualizacoes','sistema'} and (s/'ABRIR RODOVIA STUDIO.cmd').exists()
    # Atualização seguinte (já na organização 1.32): nada é movido e o .exe não é mexido.
    r2=U.apply(package(tmp_path,'1.33.0'),root,say=lambda *a:None,check_running=False)
    assert r2['layout_before']=='sistema' and not r2['old_exe_saved'] and (root/'Rodovia Studio.exe').read_text()=='exe 1.2' and not (root/'ABRIR RODOVIA STUDIO.cmd').exists()

def test_search_and_apply_delegates_to_new_updater_from_131(tmp_path,monkeypatch):
    """O atualizador da 1.31 (instalado) entrega o pacote ao da 1.32, que reorganiza as pastas."""
    root=tmp_path/'R';install_131(root,exe=False)
    old=tmp_path/'old_updater.py';old.write_text(open('tests/atualizador_1_31.py',encoding='utf-8').read() if Path('tests/atualizador_1_31.py').exists() else REAL,encoding='utf-8')
    pk=package(tmp_path);z=root/'atualizacoes'/'RodoviaStudio_1_32_atualizacao.zip'
    with zipfile.ZipFile(z,'w') as zf:
        for f in pk.rglob('*'):
            if f.is_file():zf.write(f,'RS132/pacote/'+f.relative_to(pk).as_posix())
    env=dict(os.environ,HOME=str(tmp_path/'home'),USERPROFILE=str(tmp_path/'home'))
    r=subprocess.run([__import__('sys').executable,'-I',str(old),'--raiz',str(root),'--procurar','--sem-verificar-aberto'],capture_output=True,text=True,env=env,timeout=120)
    assert r.returncode==0,r.stdout+r.stderr
    assert (root/'sistema/programa/app/server.py').read_text()=='# 1.32' and not (root/'suporte').exists() and (root/'atualizacoes/aplicadas'/z.name).exists()

def make_mp4(path,frames=12,size=(320,180)):
    from app.encoding import ffmpeg_exe
    p=subprocess.Popen([ffmpeg_exe(),'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}','-r','12','-i','-','-c:v','libx264','-pix_fmt','yuv420p',str(path)],stdin=subprocess.PIPE)
    for k in range(frames):p.stdin.write(np.full((size[1],size[0],3),k*20%255,np.uint8).tobytes())
    p.stdin.close();p.wait();return path

def test_video_archive_keeps_every_generation(tmp_path,monkeypatch):
    from app import store,videos
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    d=tmp_path/'proj';d.mkdir();pid='a'*32;s=S(name='Trecho: BR/381 <km 12>')
    info={'width':320,'height':180,'fps':12,'duration_s':1,'frames':12,'encoder':'libx264'}
    make_mp4(d/'video.mp4');a=videos.archive(d,pid,s,info,3.2);time.sleep(.01)
    (d/'video.mp4').write_bytes((d/'video.mp4').read_bytes()+b'');b=videos.archive(d,pid,s,info,4.0)
    assert a!=b and a.exists() and b.exists() and a.name.endswith('_v01.mp4') and b.name.endswith('_v02.mp4')
    assert a.parent.name=='Trecho BR 381 km 12' and not any(c in a.name for c in ':/<>')
    meta=json.loads(b.with_suffix('.json').read_text(encoding='utf-8'));assert meta['numero']==2 and meta['configuracao']['name']==s.name and meta['tempo_geracao_s']==4.0
    L=videos.listing(pid);assert [v['nome'] for v in L['videos']]==[b.name,a.name] and 'configuracao' not in L['videos'][0]
    # Outro projeto com o mesmo nome não se mistura; renomear o projeto mantém a pasta.
    c=videos.archive(d,'b'*32,s,info);assert c.parent!=a.parent and videos.find_folder(pid)==a.parent
    assert videos.archive(d,pid,S(name='Novo nome'),info).parent==a.parent
    with pytest.raises(FileNotFoundError):videos.path_of(pid,'../x.mp4')
    with pytest.raises(FileNotFoundError):videos.path_of(pid,'nao_existe.mp4')
    t=videos.remove(pid,a.name);assert (tmp_path/'videos/_lixeira'/t).exists() and not a.exists()
    # Último vídeo: cópia do projeto; sem ela (limpeza), o da pasta de vídeos.
    (d/'video.json').write_text(json.dumps({**info,'arquivo':b.name,'pasta_videos':str(b.parent)}),encoding='utf-8')
    assert videos.current(d)==d/'video.mp4';(d/'video.mp4').unlink();assert videos.current(d)==b

def test_render_job_archives_without_replacing(drawing,monkeypatch,tmp_path):
    from app import store
    import app.worker as w
    monkeypatch.setenv('RODOVIA_VIDEOS',str(tmp_path/'videos'))
    from app.server import app
    c=TestClient(app);pid=c.post('/api/projects',json=settings().model_dump()|{'duration_s':3,'width':1280,'name':'Vídeo teste'}).json()['id']
    d=store.ROOT/pid;shutil.copy(drawing/'input.dxf',d/'input.dxf')
    for k in range(2):
        jid=f'{k}'*32
        with store.connect() as con:con.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'render','running',''))
        assert w.run(jid)==0;assert 'guardado em videos' in store.job(jid)['message']
    L=c.get(f'/api/projects/{pid}/videos').json()['videos'];assert len(L)==2 and L[0]['nome'].endswith('_v02.mp4') and L[0]['largura']==1280
    r=c.get(f"/api/projects/{pid}/videos/{L[1]['nome']}");assert r.status_code==200 and r.headers['content-type']=='video/mp4' and len(r.content)>1000
    assert 'attachment' in c.get(f"/api/projects/{pid}/videos/{L[1]['nome']}?baixar=1").headers.get('content-disposition','')
    assert c.get(f'/api/projects/{pid}/videos/..%2Fconfig.json').status_code==404
    assert json.loads((d/'video.json').read_text())['arquivo']==L[0]['nome']
    monkeypatch.setenv('RODOVIA_SEM_EXPLORER','1');r=c.post('/api/abrir_pasta',json={'tipo':'videos_projeto','pid':pid}).json();assert r['pasta'].endswith('Vídeo teste') and not r['aberta']
    assert c.post('/api/abrir_pasta',json={'tipo':'../../etc'}).status_code==422
    assert c.delete(f"/api/projects/{pid}/videos/{L[1]['nome']}").status_code==200 and len(c.get(f'/api/projects/{pid}/videos').json()['videos'])==1

def test_cleanup_categories(tmp_path):
    from app.maintenance import survey,clean_categories
    root=tmp_path/'projetos';inst=tmp_path;vid=tmp_path/'videos';p=root/('c'*32);p.mkdir(parents=True)
    keep={'input.dxf':b'K','config.json':b'{}','imagem_local/x.tif':b'K','imagens/a.png':b'K'}
    for f,t in keep.items():(p/f).parent.mkdir(parents=True,exist_ok=True);(p/f).write_bytes(t)
    junk={'cache_geometria/a':100,'cache_detalhe/k/im.jpg':200,'video.partial.mp4':30,'upload.dxf.tmp':5,'render_tmp/0.raw':40,'ffmpeg.log':7,'logs/execucao.1.jsonl':9}
    for f,n in junk.items():(p/f).parent.mkdir(parents=True,exist_ok=True);(p/f).write_bytes(b'x'*n)
    (root/'_ladrilhos/esri/19').mkdir(parents=True);(root/'_ladrilhos/esri/19/1.jpg').write_bytes(b'x'*50)
    old=time.time()-40*86400
    (p/'logs/execucao.jsonl').write_bytes(b'x'*11);os.utime(p/'logs/execucao.jsonl',(old,old))
    for k in range(5):f=p/f'config_antes_limpeza_{k}.json';f.write_bytes(b'x'*3);os.utime(f,(old+k,old+k))
    (root/'_lixeira/proj_velho').mkdir(parents=True);(root/'_lixeira/proj_velho/a').write_bytes(b'x'*60)
    (vid/'_lixeira').mkdir(parents=True);(vid/'_lixeira/v.mp4').write_bytes(b'x'*70)
    b=inst/'sistema/backups'
    for k in range(4):d=b/f'antes_v1_3{k}_0_x';d.mkdir(parents=True);(d/'f').write_bytes(b'x'*8);os.utime(d,(old+k,old+k))
    ap=inst/'atualizacoes/aplicadas';ap.mkdir(parents=True)
    for k in range(3):z=ap/f'RodoviaStudio_1_3{k}_atualizacao.zip';z.write_bytes(b'x'*4);os.utime(z,(old+k,old+k))
    (vid/'Proj').mkdir();(vid/'Proj/p_v01.mp4').write_bytes(b'v'*25);(p/'video.mp4').write_bytes(b'v'*25)
    (p/'video.json').write_text(json.dumps({'arquivo':'p_v01.mp4','pasta_videos':str(vid/'Proj')}))
    S_=({c['id']:c for c in survey(root,inst,vid)})
    assert S_['caches']['bytes']==350 and S_['temporarios']['bytes']==75 and S_['registros']['bytes']==27 and S_['copias_config']['itens']==2
    assert S_['lixeira']['bytes']==130 and S_['atualizacoes']['itens']==4 and S_['copias_video']['bytes']==25 and not S_['copias_video']['padrao']
    r=clean_categories(root,[k for k,v in S_.items() if v['padrao']],inst,vid);assert not r['errors'] and r['bytes']==350+75+27+6+130+16+8
    for f,t in keep.items():assert (p/f).read_bytes()==t
    assert (p/'video.mp4').exists() and (vid/'Proj/p_v01.mp4').exists() and len(list(p.glob('config_antes_*.json')))==3
    assert sorted(x.name for x in b.iterdir())==['antes_v1_32_0_x','antes_v1_33_0_x'] and [z.name for z in ap.iterdir()]==['RodoviaStudio_1_32_atualizacao.zip']
    assert clean_categories(root,['copias_video'],inst,vid)['bytes']==25 and not (p/'video.mp4').exists() and (vid/'Proj/p_v01.mp4').exists()
    with pytest.raises(ValueError):clean_categories(root,['tudo'],inst,vid)

def test_cleanup_api(tmp_path):
    from app.server import app
    c=TestClient(app);r=c.get('/api/limpeza').json()['categorias'];assert {x['id'] for x in r}>={'caches','temporarios','registros','lixeira','atualizacoes','copias_video'}
    assert c.post('/api/limpeza',json={'categorias':['xx']}).status_code==422
    assert c.post('/api/limpeza',json={'categorias':['temporarios']}).status_code==200
    u=c.get('/api/atualizacao').json();assert u['modo']=='desenvolvimento' and u['instalada'] and not u['pode_atualizar']
    assert c.post('/api/atualizacao/aplicar').status_code==409

def test_quality_settings_and_encoder():
    from app.encoding import options,select_encoder
    assert Settings.model_validate({'schema_version':25,'km_start_m':0,'km_end_m':100}).video_quality=='padrao'   # projetos antigos: vídeo igual
    assert Settings(name='novo').video_quality=='alta' and S(width=3840).width==3840
    assert options('libx264','veryfast')==options('libx264','veryfast','padrao') and '-crf' in options('libx264') and options('libx264')[options('libx264').index('-crf')+1]=='16'
    a=options('libx264','veryfast','alta');m=options('libx264','veryfast','maxima')
    assert a[a.index('-crf')+1]=='14' and a[a.index('-preset')+1]=='medium' and m[m.index('-crf')+1]=='12' and m[m.index('-preset')+1]=='slow'
    n=options('h264_nvenc',quality='maxima');assert n[n.index('-cq')+1]=='14' and '-spatial-aq' in n
    seen=[]
    def runner(cmd,**k):seen.append(cmd);return type('R',(),{'returncode':0,'stderr':b''})()
    e=select_encoder('ff',1280,720,30,runner=runner,quality='alta');assert e['quality']=={'cq':16,'nivel':'alta'} and '-spatial-aq' in seen[0]
    assert select_encoder('ff',1280,720,30,runner=runner)['quality']=={'cq':19}

def test_sharpen_imagery():
    from app.render import sharpen_imagery
    rng=np.random.default_rng(1);flat=np.full((120,160,3),120,np.int16)+rng.integers(-1,2,(120,160,3))
    flat=flat.astype(np.uint8);assert np.array_equal(sharpen_imagery(flat,'alta'),flat)    # ruído fraco não é realçado
    img=np.zeros((120,160,3),np.uint8);img[:,80:]=200;img=cv2.GaussianBlur(img,(0,0),.8)
    g=lambda x:np.abs(np.diff(x.astype(float),axis=1)).max()
    assert g(sharpen_imagery(img,'alta'))>g(img)*1.15 and g(sharpen_imagery(img,'maxima'))>g(img)*1.3
    r=cv2.GaussianBlur(np.random.default_rng(0).integers(0,255,(120,160,3)).astype(np.uint8),(0,0),1.2)
    lap=lambda x:cv2.Laplacian(cv2.cvtColor(x,cv2.COLOR_RGB2GRAY),cv2.CV_64F).var()
    assert lap(sharpen_imagery(r,'alta'))>lap(r)*1.4

def test_quality_frames_and_detail(junction):
    from app.render import Scene
    p=Scene(junction,S(video_quality='padrao'));a=Scene(junction,S(video_quality='alta'));m=Scene(junction,S(video_quality='maxima'))
    assert p.detail.R==.2 and p.detail.zmax==19 and a.detail.zmax==19 and m.detail.R==.1 and m.detail.zmax==20
    assert len({p.detail.key,a.detail.key,m.detail.key})==3
    # Imagem Esri nível 20 quando existe; senão nível 19 (o ladrilho “sem dados” do nível 20 é recusado).
    det=m.detail;calls=[]
    def fake(z,x,y):
        calls.append(z)
        if z==20:return np.full((256,256,3),235,np.uint8)   # cinza claro sem cor = “Map data not yet available”
        r=np.random.default_rng(x*7+y);return r.integers(0,255,(256,256,3),dtype=np.uint8)
    det.esri=fake;det.offline=False;det.esri_ok=True
    i,j=0,0;out=det.esri_tile(i,j);assert out is not None and calls[0]==20 and 19 in calls
    calls.clear();det.esri=lambda z,x,y:(calls.append(z),np.random.default_rng(z).integers(0,255,(256,256,3),dtype=np.uint8))[1]
    assert det.esri_tile(i,j) is not None and set(calls)=={20}

def test_ssaa_render_dimensions(drawing):
    from app.render import render
    out=render(drawing,settings().model_copy(update={'duration_s':2,'width':1280,'video_quality':'maxima','traffic':False}))
    meta=json.loads((drawing/'video.json').read_text());assert meta['width']==1280 and meta['height']==720 and meta['superamostragem']==1.5 and meta['validation']['ok']
    cap=cv2.VideoCapture(str(out));assert int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))==1280;cap.release()
