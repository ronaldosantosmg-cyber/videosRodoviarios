"""Imagem combinada não muda a rede; aviso de ensaio não é gravado nos pixels."""
import json,os
from pathlib import Path
import numpy as np
import pytest,tifffile
from PIL import Image
from app import imagery
from app.detail import Detail
from app.render import Scene,render
from app.encoding import validate_mp4,ffmpeg_exe
from app.geometry import guess
from test_v1425_scene3d import project


def local_image(d,s):
    folder=d/'imagem_local';folder.mkdir();p=folder/'local.tif'
    keys=[1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,31983]
    tifffile.imwrite(p,np.full((512,512,3),(42,115,72),np.uint8),photometric='rgb',extratags=[(33550,'d',3,(2.,2.,0.),False),(33922,'d',6,(0.,0.,0.,499738.,7800512.,0.),False),(34735,'H',len(keys),keys,False)])
    s.local_imagery.image=p.name;s.local_imagery.crs='EPSG:31983';s.local_imagery.detail=True


@pytest.mark.parametrize('offline',[False,True])
def test_mixed_imagery_exports_decoded_video_with_vehicles_and_no_trial_banner(tmp_path,monkeypatch,offline):
    d,s=project(tmp_path);local_image(d,s);s.imagery='esri';s.imagery_pixels=2048;s.camera_mode='trafego';s.view_width_m=350;s.render_workers=1;s.heavy_shoulder_overtake=True;s.render_profile='rapido'
    base=imagery._mosaic_base
    def web(directory,settings,bounds,status=lambda *a:None,warnings=None):
        if settings.imagery=='esri':
            if offline:raise OSError('Rede indisponível no teste')
            a,box,_=base(directory,settings.model_copy(update={'imagery':'neutral'}),bounds,status,warnings);a[:]=(100,130,170);return a,box,'Mapa simulado no teste'
        return base(directory,settings,bounds,status,warnings)
    monkeypatch.setattr(imagery,'_mosaic_base',web)
    monkeypatch.setattr(Detail,'esri_tile',lambda *a:None)
    (d/'config.json').write_text(s.model_dump_json(),encoding='utf-8')
    scene=Scene(d,s);network=[p['p'].copy() for p in scene.network.paths];first,meta=scene.frame(1.5)
    assert meta['traffic_visibility']['drawn']>0
    assert scene.report['traffic_operation_notice']=='ENSAIO: ultrapassagem pelo acostamento habilitada'
    scene.s=scene.s.model_copy(update={'heavy_shoulder_overtake':False});second,_=scene.frame(1.5)
    # A faixa de ensaio de 30 px foi removida; a informação continua no relatório.
    np.testing.assert_array_equal(first[-30:],second[-30:])
    assert all(np.array_equal(a,p['p']) for a,p in zip(network,scene.network.paths))
    if offline:assert any('Mapa web indisponível' in x for x in scene.report['warnings'])
    else:assert scene.detail.local is not None
    path=render(d,s);decoded=validate_mp4(ffmpeg_exe(),path,72,1280,720,24);assert decoded['ok']
    result=json.loads((d/'video.json').read_text(encoding='utf-8'))
    assert result['traffic_presentation']['status']=='visivel' and all(v['drawn']>0 for v in result['traffic_presentation']['samples'])
    assert 'acostamento habilitada' in result['traffic_operation_notice']
    target=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));target.mkdir(parents=True,exist_ok=True)
    Image.fromarray(first).save(target/f'imagem_mista_veiculos_{offline}.png')
    (target/f'imagem_mista_video_{offline}.json').write_text(json.dumps(dict(decoded=decoded,presentation=result['traffic_presentation'],notice=result['traffic_operation_notice'],web='simulado',offline=offline),ensure_ascii=False,indent=2),encoding='utf-8')


def test_pavement_hatch_names_retain_existing_or_projected_class():
    for name in ['HATCH_PAV_NOVO','F-HZ-HATCH (pista)','GEO-HZ-HATCH (pista)']:assert guess(name)=='pavement'
    for name in ['HATCH_PAV_EXISTENTE','HATCH_PAV_EXITENTE','F-HZ-HATCH (pista existente)']:assert guess(name)=='existing_pavement'


def test_mixed_imagery_does_not_treat_cancellation_as_network_failure(tmp_path,monkeypatch):
    from app.models import Settings
    s=Settings(imagery='esri');s.local_imagery.image='local.tif'
    def cancelled(*a,**kw):raise InterruptedError('Cancelado no teste')
    monkeypatch.setattr(imagery,'_mosaic_base',cancelled)
    with pytest.raises(InterruptedError,match='Cancelado no teste'):imagery.mosaic(tmp_path,s,[[0,0],[100,100]])
