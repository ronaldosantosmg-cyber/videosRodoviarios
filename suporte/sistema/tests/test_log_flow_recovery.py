"""Regressões dos erros enviados: UTF-8, prévia presa e vídeo sem rede."""
import json,zipfile
from pathlib import Path
import pytest
from app import project_state as P,store
from app.render import Scene,render
from app.traffic_presentation import preflight,project_status
from app.native_axes import axis_fingerprint
from app.geometry import read_kmz,analyze
from test_v1425_scene3d import project
from test_v14225_execution import corner,publish


def disabled_project(tmp_path):
    d,s=project(tmp_path)
    key='axis:'+axis_fingerprint([(500050,7800000),(500450,7800000)],'EIXO')
    s.camera_mode='trafego';s.preview_mode='video';s.route_directions={key:'off'}
    P.save_config(d,s.model_dump());return d,s


def test_assisted_correction_and_receipt_use_utf8_under_windows_default(corner,monkeypatch):
    from app import assisted_execution as E
    d,s,data=corner;data['segments'][0]['source']='Eixo “Leste” — correção';store.write_json(d/'editor.json',data)
    from app.artifacts import begin,finish
    finish(d,begin(d,'utf8-fixture','analyze',s))
    read=Path.read_text
    def windows(path,*args,**kwargs):
        if not args and 'encoding' not in kwargs:kwargs['encoding']='cp1252'
        return read(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',windows)
    request=dict(signature=E.signature(d),segment=data['segments'][0]['id'],action='auto')
    plan=E.preview(d,request);assert plan['can_apply']
    E.apply(d,plan['id']);assert E.load(d,plan['id'])['state']=='aplicada_pendente_revalidacao'
    publish(d,type(s).model_validate(P.read_config(d)));assert E.outcome(d,plan['id'])['resolved']


def test_no_routes_is_diagnostic_and_never_a_silent_empty_video(tmp_path):
    d,s=disabled_project(tmp_path);scene=Scene(d,s);result=preflight(scene)
    assert result['status']=='sem_itinerarios' and 'desligados' in result['notice']
    assert not scene.network.paths
    (d/'video.mp4').write_bytes(b'video anterior preservar')
    with pytest.raises(ValueError,match='Vídeo não gerado'):render(d,s)
    assert (d/'video.mp4').read_bytes()==b'video anterior preservar'
    record=json.loads((d/'traffic_export_check.json').read_text(encoding='utf-8'))
    assert record['presentation']['status']=='sem_itinerarios'
    assert project_status(d)['presentation']['status']=='sem_itinerarios'
    changed=P.read_config(d);changed['traffic_density']=2;P.save_config(d,changed)
    assert not project_status(d)['presentation']


def test_refresh_publishes_editor_and_overview_without_reactivating_routes(tmp_path,monkeypatch):
    from app.worker import run
    from app.artifacts import status
    root=tmp_path/'data';root.mkdir();pid='e'*32;d=root/pid;d.mkdir()
    monkeypatch.setenv('RODOVIA_DATA',str(root));monkeypatch.setattr(store,'ROOT',root);monkeypatch.setattr(store,'DB',root/'studio.sqlite3');store.init()
    d,s=disabled_project(d);before=P.read_config(d);source=(d/'input.dxf').read_bytes()
    jid='a'*32
    with store.connect() as c:
        c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,'Teste'))
        c.execute('INSERT INTO jobs(id,project,kind,state) VALUES(?,?,?,?)',(jid,pid,'refresh','queued'))
    assert run(jid)==0 and store.job(jid)['state']=='done'
    assert P.read_config(d)==before and (d/'input.dxf').read_bytes()==source
    assert status(d)['editor']['state']=='ready'
    doc=json.loads((d/'editor.json').read_text(encoding='utf-8'));assert doc['itineraries']==0
    preview=json.loads((d/'preview.json').read_text(encoding='utf-8'));assert preview['traffic_camera_fallback']
    assert project_status(d)['presentation']['status']=='sem_itinerarios'


def test_kmz_polygons_are_not_axes_or_charged_to_line_budget(tmp_path):
    p=tmp_path/'input.kmz'
    polygon='<Polygon><outerBoundaryIs><LinearRing><coordinates>'+('-43,-19 ' * 1000001)+'</coordinates></LinearRing></outerBoundaryIs></Polygon>'
    line='<LineString><coordinates>-43,-19 -43.001,-19.001</coordinates></LineString>'
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('doc.kml','<kml><Placemark>'+polygon+line+'</Placemark></kml>')
    stats={};lines,pois=read_kmz(p,'EPSG:31983',stats)
    assert len(lines)==1 and len(lines[0])==2 and not pois and stats['ignored_geometries']==1
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('doc.kml','<kml><Placemark>'+polygon+'</Placemark></kml>')
    assert read_kmz(p,'EPSG:31983')==([],[])


def test_missing_axis_identifies_unmapped_candidate_without_inventing_traffic(tmp_path):
    d,s=project(tmp_path);s.layers={'pavement':['PAVIMENTO']}
    with pytest.raises(ValueError,match='Candidatas: EIXO'):analyze(d,s)


def test_trial_notice_reports_exact_enabled_option_without_changing_settings():
    from app.models import Settings
    from app.traffic_presentation import operation_notice
    s=Settings();assert operation_notice(s)==''
    s.heavy_shoulder_overtake=True;before=s.model_dump()
    assert operation_notice(s)=='ENSAIO: ultrapassagem pelo acostamento habilitada'
    assert s.model_dump()==before
    s.heavy_shoulder_overtake=False;s.traffic_prevent_collisions=False
    assert operation_notice(s)=='ENSAIO: verificacao de colisoes desativada'
    s.traffic_respect_signals=False;assert 'semaforos' in operation_notice(s)
    s.traffic_classic=True;assert operation_notice(s)=='ENSAIO CLASSICO: somente canteiros'


def test_hatch_is_not_promoted_to_a_traffic_axis(tmp_path):
    import ezdxf
    d,s=project(tmp_path);doc=ezdxf.readfile(d/'input.dxf')
    for e in list(doc.modelspace()):
        if e.dxf.layer=='EIXO':doc.modelspace().delete_entity(e)
    h=doc.modelspace().add_hatch(dxfattribs={'layer':'EIXO'})
    h.paths.add_polyline_path([(500050,7800000),(500450,7800000),(500450,7800010)],is_closed=True);doc.saveas(d/'input.dxf')
    with pytest.raises(ValueError,match='Nenhum eixo encontrado'):analyze(d,s)
