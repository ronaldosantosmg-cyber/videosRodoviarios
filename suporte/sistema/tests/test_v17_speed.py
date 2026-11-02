"""1.7: montagem em vários processos, perfil rápido, ficha técnica de referência."""
import json,hashlib
import numpy as np
import pytest
import cv2
from test_workflow import drawing,settings
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),**kw})

def frames_of(path):
    cap=cv2.VideoCapture(str(path));out=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        out.append(f)
    cap.release();return out

def test_plan_workers_by_cores_and_memory():
    from app.parallel import plan_workers
    G=1024**3
    assert plan_workers(3,2560,1440,6000,True)[0]==3
    assert plan_workers(0,2560,1440,60,True)[0]==1                       # vídeo curto
    assert plan_workers(0,2560,1440,6000,True,cores=16,memory=32*G)[0]==12  # limite superior
    assert plan_workers(0,2560,1440,6000,False,cores=8,memory=32*G)[0]==7   # NVENC: sem núcleo reservado ao encoder
    assert plan_workers(0,2560,1440,6000,True,cores=8,memory=3*G)[0]==1     # pouca memória
    assert plan_workers(0,2560,1440,6000,True,cores=2,memory=8*G)[0]==1

def test_parallel_render_gives_same_frames(drawing,monkeypatch,tmp_path):
    """Os quadros entregues ao codificador são idênticos (hash por quadro); o MP4 pode variar em bits no x264 sob carga."""
    from app.render import render
    logs={}
    for w in (1,3):
        log=tmp_path/f'q{w}.txt';monkeypatch.setenv('RODOVIA_FRAME_LOG',str(log))
        render(drawing,S(duration_s=4,render_workers=w));meta=json.loads((drawing/'video.json').read_text(encoding='utf-8'))
        assert meta['workers']==w and meta['frames']==120;logs[w]=log.read_text().splitlines()
    assert len(logs[1])==120 and logs[1]==logs[3]
    assert len(frames_of(drawing/'video.mp4'))==120 and not (drawing/'render_tmp').exists()

def test_parallel_cabin(drawing,monkeypatch,tmp_path):
    from app.render import render
    from app.models import TrafficPath,Point
    lane=[TrafficPath(name='Pista',kind='main',direction='growing',points=[Point(x=500005,y=7799995),Point(x=500295,y=7799995)]).model_dump()]
    cfg=dict(derive_traffic_paths=False,traffic_paths=lane,cabin={'enabled':True,'start':{'x':500040,'y':7799995},'duration_s':3})
    logs={}
    for w in (1,2):
        log=tmp_path/f'c{w}.txt';monkeypatch.setenv('RODOVIA_FRAME_LOG',str(log));render(drawing,S(render_workers=w,**cfg));logs[w]=log.read_text().splitlines()
    assert len(logs[1])==90 and logs[1]==logs[2]

def test_fast_profile_is_faster_path(drawing):
    from app.render import Scene
    import time
    v=((500150,7800000),300)
    a=Scene(drawing,S(render_profile='final'));b=Scene(drawing,S(render_profile='rapido'))
    tex=cv2.GaussianBlur(np.random.default_rng(3).integers(0,255,a.map.shape,dtype=np.uint8),(0,0),2);a.map=tex;b.map=tex
    f=a.frame(0,view=v)[0];r=b.frame(0,view=v)[0]
    assert f.shape==r.shape and not np.array_equal(f,r)
    assert np.abs(f.astype(int)-r.astype(int)).mean()<6  # mesma cena, sem a superamostragem

def test_video_profile_and_comparison(drawing):
    from app.render import render
    from app.video_profile import profile,compare,image_metrics
    p=render(drawing,S(duration_s=3))
    prof=profile(p,instants=(1,),extra_samples=3)
    assert prof['file']['width']==1280 and prof['file']['height']==720 and prof['file']['fps']==30 and prof['file']['frames']==90
    assert len(prof['samples'])==4 and prof['image_median']['sharpness_lap_var']>0 and len(prof['file']['sha256'])==64
    ref=json.loads(open('assets/th57/referencia_ficha.json',encoding='utf-8').read())
    rows=compare(ref,prof);w=next(r for r in rows if r['key']=='width');assert w['reference']==2560 and w['current']==1280 and w['delta_pct']==-50
    # Métricas respondem ao conteúdo: imagem borrada tem nitidez menor.
    im=np.random.default_rng(1).integers(0,255,(1440,2560,3),dtype=np.uint8);bl=cv2.GaussianBlur(im,(0,0),4)
    assert image_metrics(im)['sharpness_lap_var']>image_metrics(bl)['sharpness_lap_var']
    lines=np.full((720,1280,3),90,np.uint8)
    for x in range(100,1200,60):cv2.line(lines,(x,100),(x,600),(245,245,240),3)
    assert image_metrics(lines)['marking_pixels_pct']>1

def test_reference_profile_job_removes_video_only_after_sheet(drawing,tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from app.render import render
    import app.worker as w,app.server as srv
    from app import store
    assets=tmp_path/'assets';(assets/'th57').mkdir(parents=True)
    video=render(drawing,S(duration_s=3));(assets/'th57/referencia.mp4').write_bytes(video.read_bytes())
    (assets/'th57/referencia_ficha.json').write_text(json.dumps({'file':{'sha256':'x'}}),encoding='utf-8')
    monkeypatch.setattr(w,'ASSETS',assets)
    # 1.31: as rotas ficam em app/rotas (antes em server.py).
    import app.rotas.tarefas as rt;monkeypatch.setattr(rt,'ASSETS',assets)
    with TestClient(srv.app) as c:
        pid=c.post('/api/projects',json=settings().model_dump()).json()['id']
        assert c.get('/api/reference/profile').json()['video_present']
        jid='e'*32
        with store.connect() as con:con.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'reference_profile_remove','running',''))
        assert w.run(jid)==0
        ficha=json.loads((assets/'th57/referencia_ficha.json').read_text(encoding='utf-8'))
        assert ficha['status']=='completa' and ficha['image_median'] and ficha['sha256_matches_1_0'] is False
        assert not (assets/'th57/referencia.mp4').exists()
        r=c.post(f'/api/projects/{pid}/reference');assert r.status_code==410
        assert c.post(f'/api/projects/{pid}/reference_profile').status_code==410
