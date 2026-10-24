"""1.8: estaqueamento automático/manual com fim e sentido, destaques, ajuda e atualizador organizado."""
import json,os,zipfile,shutil
import numpy as np
import pytest
from test_workflow import drawing,settings
from app.models import Settings,Point
from app.chainage import Stationing

def S(**kw):return Settings(**{**settings().model_dump(),**kw})
AX=np.array([[0.,0.],[1000.,0.]])

def test_stationing_auto_manual_end_direction_and_calibration():
    s=S(km_start_m=10000,km_end_m=11000,chainage={'mode':'auto'})
    st=Stationing.from_settings(AX,s);assert st.km([250,3])==pytest.approx(10250) and st.direction==1
    # Manual com seta (arraste) no sentido contrário ao eixo.
    st=Stationing.from_settings(AX,S(km_start_m=10000,km_end_m=11000,chainage={'mode':'manual','start':{'x':800,'y':0},'direction':-1}))
    assert st.km([700,0])==pytest.approx(10100) and st.km([900,0])==pytest.approx(9900)
    # Fim marcado define o sentido (prevalece sobre a seta) e o km final medido.
    st=Stationing.from_settings(AX,S(km_start_m=10000,km_end_m=10500,chainage={'mode':'manual','start':{'x':900,'y':0},'end':{'x':100,'y':0},'direction':1}))
    assert st.direction==-1 and st.km_end_geometric()==pytest.approx(10800)
    # Ajuste proporcional: 800 m medidos valem 500 m de km oficial.
    st=Stationing.from_settings(AX,S(km_start_m=10000,km_end_m=10500,chainage={'mode':'manual','start':{'x':900,'y':0},'end':{'x':100,'y':0},'calibrate':True}))
    assert st.scale==pytest.approx(.625) and st.km([100,0])==pytest.approx(10500) and st.km([500,0])==pytest.approx(10250)
    assert np.allclose(st.point(10250),[500,0]) and st.chain(10500)==pytest.approx(100)
    lo,hi=st.km_range();assert lo==pytest.approx(10000-100*.625) and hi==pytest.approx(10000+900*.625)
    with pytest.raises(ValueError):Stationing.from_settings(AX,S(km_start_m=10000,km_end_m=10500,chainage={'mode':'manual','start':{'x':100,'y':0},'end':{'x':50,'y':0},'calibrate':True,'direction':1}).model_copy(update={'km_end_m':9000}))

def test_migration_to_v8_keeps_previous_behaviour():
    old=Settings.model_validate({'schema_version':7,'pois':[{'title':'A','x':1,'y':2}]});legacy=Settings.model_validate({'km_start_m':0,'km_end_m':10});assert legacy.chainage.mode=='off';assert old.chainage.mode=='off'
    marked=Settings.model_validate({'schema_version':7,'chainage':{'start':{'x':1,'y':2}}});assert marked.chainage.mode=='manual'
    assert Settings().chainage.mode=='auto' and Settings().highlights==[]

def test_auto_mode_gives_items_km_and_off_does_not(drawing):
    from app.render import Scene
    poi=[{'id':'p','title':'Obra','x':500150,'y':7800000}]
    on=Scene(drawing,S(km_start_m=2000,km_end_m=3000,pois=poi,chainage={'mode':'auto'}));off=Scene(drawing,S(km_start_m=2000,km_end_m=3000,pois=poi,chainage={'mode':'off'}))
    assert on.pois[0]['km_m']==pytest.approx(2150,abs=1) and off.pois[0].get('km_m') is None

HL=[{'id':'h1','name':'Edifício Sede','category':'edificacao','description':'Prédio administrativo a 30 m da pista','point':{'x':500150,'y':7800012},'label':{'x':500190,'y':7800024}},
    {'id':'h2','name':'Poste 12','category':'poste','point':{'x':500220,'y':7799975},'stop':True}]

def test_highlights_drawn_with_callout_and_optional_stop(drawing):
    from app.render import Scene
    v=((500170,7800000),150)
    a=Scene(drawing,S(highlights=HL,chainage={'mode':'auto'}));b=Scene(drawing,S())
    fa=a.frame(0,view=v)[0];fb=b.frame(0,view=v)[0]
    diff=np.abs(fa.astype(int)-fb).max(2)>0;assert diff.sum()>2000
    # Caixa perto da posição escolhida (label) e marcador no ponto.
    q=a.screen(np.array([[500190,7800024]]),np.array(v[0]),v[1])[0].astype(int);assert diff[q[1]-5:q[1]+5,q[0]-5:q[0]+5].any()
    m=a.screen(np.array([[500150,7800012]]),np.array(v[0]),v[1])[0].astype(int);assert diff[m[1],m[0]]
    assert any(p.get('source')=='highlight' and p['title']=='Poste 12' for p in a.pois) and not any(p.get('title')=='Edifício Sede' for p in a.pois)
    hidden=Scene(drawing,S(highlights=[{**HL[0],'show_in_video':False}])).frame(0,view=v)[0];assert np.array_equal(hidden,fb)

def test_highlights_export_reimport(drawing):
    from app.render import Scene
    from app import exporters
    s=S(highlights=HL,chainage={'mode':'manual','start':{'x':500030,'y':7800000},'end':{'x':500280,'y':7800000},'calibrate':False});sc=Scene(drawing,s)
    feats=exporters.features(s,sc.stationing,sc.axes,sc.network.raw_info,sc.oae)
    assert any(p['rs_type']=='fim_km' for _,p in feats)
    back=exporters.read_any(exporters.geojson(feats,s.crs,True).encode(),'m.geojson',s.crs)
    cfg,counts=exporters.apply_import(settings().model_dump(),back);s2=Settings.model_validate(cfg)
    assert counts['highlights']==2 and [h.name for h in s2.highlights]==['Edifício Sede','Poste 12']
    assert abs(s2.highlights[0].point.x-500150)<2e-3 and s2.highlights[0].label.x==500190 and s2.highlights[1].stop
    assert s2.chainage.mode=='manual' and s2.chainage.end.x==500280

def test_help_page_and_icon():
    from fastapi.testclient import TestClient
    from app.server import app
    with TestClient(app) as c:
        r=c.get('/ajuda');assert r.status_code==200 and 'Como usar' in r.text and 'Destaque' in r.text and 'Fim do km' in r.text
        assert c.get('/favicon.ico').headers['content-type']=='image/png'

# ---------------- atualizador ----------------
import atualizador as U

def old_install(root):
    for f,t in {'app/server.py':'# antigo','app/render.py':'velho','runtime/python.exe':'exe','runtime/Lib/site-packages/x.py':'x','assets/th57/config.json':'{}',
                'dados/abc/config.json':'{"p":1}','dados/studio.sqlite3':'db','INICIAR.cmd':'old','ATUALIZAR.cmd':'old','atualizar.ps1':'old','LEIA-ME.txt':'old',
                'ATUALIZACAO_1_1.md':'doc','LEIA_PRIMEIRO.md':'doc','instalacao.log':'log','VERSAO.json':'{"version":"1.2.0"}','run.py':'run','requirements.txt':'r',
                'conferencia/a.png':'png','backup_antes_v1_2_x/app/a.py':'b','arquivos/app/x.py':'x','RodoviaStudio_1_6_atualizacao.zip':'z','meu_arquivo.txt':'meu'}.items():
        p=root/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')

REAL=open('atualizador.py',encoding='utf-8').read()
def package(tmp,version='1.8.0',server='# novo',updater=None):
    pk=tmp/f'pkg_{version}'/'pacote'
    for f,t in {'manifest.json':json.dumps({'version':version}),'raiz/ABRIR RODOVIA STUDIO.cmd':'abrir','raiz/ATUALIZAR RODOVIA STUDIO.cmd':'atualizar','raiz/LEIA-ME.txt':'novo',
                'suporte/sistema/app/server.py':server,'suporte/sistema/VERSAO.json':json.dumps({'version':version}),'suporte/sistema/atualizador.py':updater or REAL,
                'suporte/documentacao/ATUALIZACAO_1_8.md':'doc18'}.items():
        p=pk/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')
    return pk

def all_contents(root):return sorted(p.read_text(encoding='utf-8') for p in root.rglob('*') if p.is_file())

def test_updater_reorganizes_old_install_without_losing_files(tmp_path):
    # 1.32: a instalação antiga passa pela organização da 1.8 e chega à da 1.32 (raiz com o arquivo principal e pastas de dados).
    root=tmp_path/'Rodovia_Studio';old_install(root);before=all_contents(root)
    res=U.apply(package(tmp_path),root/'app',say=lambda *a:None,check_running=False)  # aceita subpasta escolhida por engano
    assert res['layout_before']=='antiga' and res['previous']=='1.2.0'
    top={p.name for p in root.iterdir()}
    assert top=={'ABRIR RODOVIA STUDIO.cmd','projetos','videos','atualizacoes','sistema','meu_arquivo.txt'},top
    s=root/'sistema';p=s/'programa'
    assert (p/'app/server.py').read_text()=='# novo' and (p/'app/render.py').read_text()=='velho' and (p/'runtime/Lib/site-packages/x.py').exists()
    assert (root/'projetos/abc/config.json').read_text()=='{"p":1}' and (s/'documentacao/ATUALIZACAO_1_1.md').exists() and (s/'documentacao/conferencia/a.png').exists()
    assert (s/'logs/instalacao.log').exists() and (s/'backups/backup_antes_v1_2_x/app/a.py').exists() and (root/'atualizacoes/aplicadas/RodoviaStudio_1_6_atualizacao.zip').exists()
    assert any(x.name=='INICIAR.cmd' for x in (s/'backups').rglob('*'))
    assert (s/'ATUALIZAR RODOVIA STUDIO.cmd').read_text()=='atualizar' and (s/'LEIA-ME.txt').read_text()=='novo' and (s/'ABRIR RODOVIA STUDIO.cmd').read_text()=='abrir'
    # Nada se perdeu: todo conteúdo anterior continua em algum lugar (substituídos guardados em backup).
    after=all_contents(root)
    for t in before:assert t in after
    assert json.loads((p/'VERSAO.json').read_text())['version']=='1.8.0'
    assert U.find_root(root)==(root,'sistema') and U.find_root(p)==(root,'sistema') and U.find_root(p/'app')==(root,'sistema')
    again=U.apply(package(tmp_path),root,say=lambda *a:None,check_running=False);assert again['copied']==0

def test_updater_rolls_back_if_a_move_fails(tmp_path,monkeypatch):
    root=tmp_path/'R';old_install(root);snapshot=sorted(str(p.relative_to(root)) for p in root.rglob('*'))
    real=os.replace;calls={'n':0}
    def flaky(a,b):
        calls['n']+=1
        if calls['n']==4:raise PermissionError('em uso')
        return real(a,b)
    monkeypatch.setattr(U.os,'replace',flaky)
    with pytest.raises(RuntimeError,match='nada foi alterado'):U.apply(package(tmp_path),root,say=lambda *a:None,check_running=False)
    monkeypatch.setattr(U.os,'replace',real)
    assert sorted(str(p.relative_to(root)) for p in root.rglob('*') if 'suporte' not in p.parts and p.name not in ('projetos','atualizacoes'))==[x for x in snapshot]

def test_search_and_apply_newest_zip(tmp_path,monkeypatch):
    root=tmp_path/'R';old_install(root);U.apply(package(tmp_path),root,say=lambda *a:None,check_running=False)
    monkeypatch.setattr(U.Path,'home',lambda:tmp_path/'home')
    def make_zip(version,server,updater=None):
        pk=package(tmp_path,version,server,updater);z=root/'atualizacoes'/f'RodoviaStudio_{version.replace(".","_")}_atualizacao.zip'
        with zipfile.ZipFile(z,'w') as zf:
            for f in pk.rglob('*'):
                if f.is_file():zf.write(f,'RodoviaStudio_x/pacote/'+f.relative_to(pk).as_posix())
        return z
    make_zip('1.7.0','# antigo zip');z=make_zip('1.9.0','# 1.9')
    msgs=[];res=U.search_and_apply(root,say=msgs.append,check_running=False)
    assert res['version']=='1.9.0' and (root/'sistema/programa/app/server.py').read_text()=='# 1.9' and (root/'atualizacoes/aplicadas'/z.name).exists()
    assert U.search_and_apply(root,say=msgs.append,check_running=False) is None and 'Já está atualizado' in msgs[-1]
    assert (root/'sistema/logs/atualizacao.log').read_text(encoding='utf-8').count('aplicada')==2
    # Pacote com atualizador diferente: ele é que aplica (permite reorganizações futuras).
    make_zip('2.0.0','# 2.0',REAL+'\n# versão futura\n');res=U.search_and_apply(root,say=msgs.append,check_running=False)
    assert res.get('delegated') and (root/'sistema/programa/app/server.py').read_text()=='# 2.0' and '# versão futura' in (root/'sistema/programa/atualizador.py').read_text(encoding='utf-8')

def test_store_root_for_organized_layout(tmp_path):
    import importlib.util
    old=os.environ.pop('RODOVIA_DATA',None)
    try:
        for n,sub in enumerate(['R/sistema/programa/app','L/suporte/sistema/app']):   # 1.32 e 1.8–1.31
            sysdir=tmp_path/sub;sysdir.mkdir(parents=True);shutil.copy('app/store.py',sysdir/'store.py')
            spec=importlib.util.spec_from_file_location(f'store_tmp{n}',sysdir/'store.py');m=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m);base=tmp_path/sub.split('/')[0]
            assert m.ROOT==(base/'projetos').resolve() and m.videos_root()==(base/'videos').resolve()
    finally:
        if old is not None:os.environ['RODOVIA_DATA']=old
