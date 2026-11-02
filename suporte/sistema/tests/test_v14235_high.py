import json,time
import pytest
from app.render import Scene,render
from app.full_update import complete_update
from app.encoding import validate_mp4,ffmpeg_exe
from test_v1425_scene3d import project
from test_v14234_nodes_ui_video import live,gl_page
from visual_harness import screenshot


def test_scene_density_and_material_reuse_dxf_and_forced_rebuild_reads_again(tmp_path,monkeypatch):
    import ezdxf
    d,s=project(tmp_path);reads=[];original=ezdxf.readfile
    def read(*a,**kw):reads.append(str(a[0]));return original(*a,**kw)
    monkeypatch.setattr(ezdxf,'readfile',read)
    first=Scene(d,s);assert len(reads)==1
    density=s.model_copy(update={'traffic_density':2})
    second=Scene(d,density);assert len(reads)==1 and second.report['geometry_cache']['hit']
    material=density.model_copy(update={'pavement_material':'rigido'})
    third=Scene(d,material);assert len(reads)==1 and third.report['geometry_cache']['hit']
    with complete_update():fourth=Scene(d,material)
    assert len(reads)==2 and not fourth.report['geometry_cache']['hit']
    assert first.network.paths and second.network.paths
    context=second.editor_data()['segments'][0]['technical_context']
    assert context['base_registered'] and context['source'] and context['direction']


def test_refresh_reuses_geometry_but_diagnostic_rebuild_is_explicit(gl_page,live):
    p=gl_page;p.evaluate("RodoviaUpdatePolicy.setMode('manual')")
    p.evaluate("()=>start('refresh')")
    report=p.request.get(live[0]+'/api/projects/'+live[1]).json()
    assert report['analysis']['geometry_cache']['hit']
    p.locator('.rsUpdateAdvanced summary').click();p.locator('.rsUpdateAdvanced button').click()
    assert not p.locator('.rsUpdateAdvanced').evaluate('e=>e.open')
    p.locator('#confirmYes').click();p.wait_for_function("!task&&!taskRequestPending&&lastPolled",timeout=60000)
    job=p.request.get(live[0]+'/api/jobs/'+p.evaluate('lastPolled')).json()
    assert job['kind']=='rebuild' and job['state']=='done'
    report=p.request.get(live[0]+'/api/projects/'+live[1]).json()
    assert not report['analysis']['geometry_cache']['hit']
    screenshot(p,'14235_reconstrucao_explicita')


def test_current_source_catalog_does_not_resurrect_removed_layer(gl_page):
    p=gl_page
    result=p.evaluate('''()=>{
      const catalog=sourceLayerCatalog,previous=analysis;
      try {sourceLayerCatalog={source:'input.dxf',layers:[{name:'CAD_REAL',count:3,declared:true},{name:'CAD_VAZIA',count:0,declared:true}]};analysis={layers:[{name:'RESIDUO_ANTIGO',count:12}],routes:[],warnings:[],geometric_length_m:10};showLayers();return $('layers').innerText}
      finally {sourceLayerCatalog=catalog;analysis=previous;showLayers()}
    }''')
    assert 'RESIDUO_ANTIGO' not in result and 'CAD_REAL' in result and 'CAD_VAZIA' in result and 'declarada vazia' in result


def test_parallel_video_is_decodable_and_circulation_reported(tmp_path):
    d,s=project(tmp_path);s=s.model_copy(update={'duration_s':5,'render_workers':2,'camera_mode':'trafego','imagery_pixels':2048,'view_width_m':180})
    (d/'config.json').write_text(s.model_dump_json())
    original=(d/'input.dxf').read_bytes();video=render(d,s)
    check=validate_mp4(ffmpeg_exe(),video,120,1280,720,24)
    assert check['ok'] and (d/'input.dxf').read_bytes()==original
    report=json.loads((d/'video.json').read_text());assert report['validation']['ok']
    assert report['motion_audit']['spawned']>0 if 'spawned' in report['motion_audit'] else report['motion_audit']['flow_balance']['entered']>0
    from pathlib import Path
    import os
    folder=Path(os.environ.get('VISUAL_ARTIFACTS',tmp_path));folder.mkdir(parents=True,exist_ok=True)
    (folder/'video_paralelo.json').write_text(json.dumps({'video':report,'decoded':check},ensure_ascii=False,indent=2))
