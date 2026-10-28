import json,os,shutil,errno
from pathlib import Path
import ezdxf,pytest
from app import assisted_execution as E,project_state as P,store,artifacts
from app.models import Settings,FlowOverride
from app.render import Scene


def publish(d,s):
 scene=Scene.light(d,s);doc=scene.editor_data();store.write_json(d/'editor.json',doc)
 for name in ('analysis.json','vectors.json'):store.write_json(d/name,{})
 ticket=artifacts.begin(d,'test','analyze',s);artifacts.finish(d,ticket);return doc

@pytest.fixture
def corner(tmp_path):
 d=tmp_path/('a'*32);d.mkdir();doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
 m.add_lwpolyline([(500050,7800000),(500200,7800000),(500200,7800150)],dxfattribs={'layer':'EIXO'})
 h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799980),(500500,7799980),(500500,7800200),(500000,7800200)],is_closed=True);doc.saveas(d/'input.dxf')
 s=Settings(width=1280,fps=24,duration_s=3,imagery='neutral',hydrography=False,route_directions={'axis:'+__import__('app.native_axes',fromlist=['axis_fingerprint']).axis_fingerprint([(500050,7800000),(500200,7800000),(500200,7800150)],'EIXO',0):'forward'},coordinates_confirmed=True)
 P.save_config(d,s.model_dump());data=publish(d,s);assert data['segments'][0]['technical_status']=='problem';return d,s,data

def propose(corner):
 d,s,data=corner;return E.preview(d,dict(signature=E.signature(d),segment=data['segments'][0]['id'],action='auto'))

def test_real_motor_previews_applies_revalidates_and_undoes_without_touching_dxf(corner):
 d,s,data=corner;before=P.read_config(d);source=(d/'input.dxf').read_bytes();plan=propose(corner)
 assert plan['can_apply'] and plan['checks']['all_paths_motion_valid'] and plan['action']=='reconstruct'
 assert P.read_config(d)==before and not before['flow_recoveries']
 result=E.apply(d,plan['id']);assert result['state']=='aplicada_pendente_revalidacao'
 with pytest.raises(__import__('fastapi').HTTPException):E.outcome(d,plan['id'])
 publish(d,Settings.model_validate(P.read_config(d)));assert E.outcome(d,plan['id'])['resolved']
 E.undo(d,plan['id']);assert P.read_config(d)==before and (d/'input.dxf').read_bytes()==source


def test_proposal_binds_content_even_when_timestamp_and_size_are_kept(corner):
 d,s,data=corner;plan=propose(corner);source=d/'input.dxf';info=source.stat();raw=source.read_bytes();source.write_bytes(raw.replace(b'500050',b'500051',1));os.utime(source,ns=(info.st_atime_ns,info.st_mtime_ns))
 assert source.stat().st_size==len(raw)
 with pytest.raises(P.Conflict):E.apply(d,plan['id'])
 assert not P.read_config(d)['flow_recoveries']


def test_obsolete_or_cross_project_proposal_cannot_modify_config(corner,tmp_path):
 d,s,data=corner;plan=propose(corner);other=tmp_path/('b'*32);shutil.copytree(d,other)
 with pytest.raises(P.Conflict):E.apply(other,plan['id'])
 changed=P.read_config(d);changed['traffic_density']=7;P.save_config(d,changed)
 with pytest.raises(P.Conflict):E.apply(d,plan['id'])


def test_manual_disable_is_preserved(corner):
 d,s,data=corner;r=data['segments'][0];s.flow_overrides=[FlowOverride(id='manual',target_key=r['origin_key'],x=r['mid'][0],y=r['mid'][1],action='disable')];P.save_config(d,s.model_dump());publish(d,s)
 with pytest.raises(ValueError,match='manual'):E.preview(d,dict(signature=E.signature(d),segment=r['id'],action='auto'))
 assert P.read_config(d)['flow_overrides'][0]['action']=='disable'


def test_failure_before_commit_and_cancel_leave_project_unchanged(corner,monkeypatch):
 d,s,data=corner;before=(d/'config.json').read_bytes();plan=propose(corner)
 def fail(*a,**kw):raise OSError(errno.ENOSPC,'Disco cheio simulado')
 monkeypatch.setattr(E,'write_json',fail)
 with pytest.raises(OSError):E.apply(d,plan['id'])
 assert (d/'config.json').read_bytes()==before
 with pytest.raises(InterruptedError):E.preview(d,dict(signature=E.signature(d),segment=0,action='auto'),cancel=lambda:True)
 assert (d/'config.json').read_bytes()==before


def test_undo_never_discards_later_user_edits(corner):
 d,s,data=corner;plan=propose(corner);E.apply(d,plan['id']);config=P.read_config(d);config['name']='Edição posterior';P.save_config(d,config)
 with pytest.raises(P.Conflict):E.undo(d,plan['id'])
 assert P.read_config(d)['name']=='Edição posterior'


def test_unregistered_action_is_refused(corner):
 d,s,data=corner
 with pytest.raises(ValueError,match='cadastrada'):E.preview(d,dict(signature=E.signature(d),segment=0,action='remover_barreira'))


def test_physical_barrier_cannot_be_removed_by_proposal(corner):
 d,s,data=corner;doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('BARREIRA');m=doc.modelspace();m.add_line((500125,7799980),(500125,7800200),dxfattribs={'layer':'BARREIRA'});doc.saveas(d/'input.dxf');data=publish(d,s);before=P.read_config(d);source=(d/'input.dxf').read_bytes()
 plan=E.preview(d,dict(signature=E.signature(d),segment=data['segments'][0]['id'],action='reconstruct'))
 # Recuperação pode manter apenas partes seguras; nunca atravessar ou apagar a barreira.
 assert P.read_config(d)==before and (d/'input.dxf').read_bytes()==source
 assert plan['checks']['all_paths_motion_valid']
 if plan['can_apply']:
  E.apply(d,plan['id']);new=P.read_config(d);assert new['layers']==before['layers'] and new['crossing_zones']==before['crossing_zones']
 else:
  with pytest.raises(ValueError):E.apply(d,plan['id'])
