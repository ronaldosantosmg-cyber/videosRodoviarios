import fnmatch,json,unicodedata
import numpy as np
import pytest
from app.layer_profiles import role_for,norm,BUILTIN,_normalized_name
from app.models import Settings
from app.geometry import analyze
from app.render import Scene
from test_v1425_scene3d import project


def old_norm(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(text).upper()) if not unicodedata.combining(c))


def test_mapping_remains_equal_and_custom_rules_do_not_stale():
    names=['EIXO LESTE','PAVIMENTO EXISTENTE','ACOSTAMENTO PROJETADO','CANTEIRO','OAE','FERROVIA','Árvore','HIDROLOGIA','GASMIG','CAMADA 0','sem classe']
    for name in names:
        expected=next((r['role'] for r in BUILTIN['rules'] if fnmatch.fnmatchcase(old_norm(name),old_norm(r['pattern']))),None)
        assert role_for(name,BUILTIN['rules'])==expected
    rules=[dict(pattern='*EIXO*',role='axis')]
    assert role_for('Eixo',rules)=='axis'
    rules[0]['role']='barrier'
    assert role_for('Eixo',rules)=='barrier'
    rules.insert(0,dict(pattern='*',role='median'))
    assert role_for('Eixo',rules)=='median'


def test_normalization_cache_is_bounded_and_long_names_not_retained():
    for i in range(2200):assert norm('Árvore '+str(i))=='ARVORE '+str(i)
    assert _normalized_name.cache_info().currsize<=2048
    before=_normalized_name.cache_info()
    assert norm('á'*2049)=='A'*2049
    assert _normalized_name.cache_info()==before


def test_handoff_preserves_editor_and_does_not_read_dxf_again(tmp_path,monkeypatch):
    import app.geometry as g
    d,s=project(tmp_path,hole=True);raw=(d/'input.dxf').read_bytes();reads=[];original=g.ezdxf.readfile
    monkeypatch.setattr(g.ezdxf,'readfile',lambda *a,**k:(reads.append(1),original(*a,**k))[1])
    preview=[];hatches={};geometry=analyze(d,s,preview,hatches)
    assert len(reads)==1 and hatches
    handoff=Scene.light(d,s,_geometry=geometry)
    assert len(reads)==1
    normal=Scene.light(d,s)
    assert handoff.editor_data()==normal.editor_data()
    assert raw==(d/'input.dxf').read_bytes()
    np.testing.assert_array_equal(handoff.axis,normal.axis)


@pytest.mark.parametrize('cancel_after_geometry',[False,True])
def test_worker_analysis_reads_once_and_publishes_current_outputs(tmp_path,monkeypatch,cancel_after_geometry):
    from app import store,worker
    import app.geometry as g
    root=tmp_path/'data';root.mkdir();monkeypatch.setattr(store,'ROOT',root);monkeypatch.setattr(store,'DB',root/'studio.sqlite3');store.init()
    pid='a'*32;d=root/pid;d.mkdir();project(d)
    with store.connect() as c:c.execute('INSERT INTO projects(id,name) VALUES(?,?)',(pid,'Abertura'))
    reads=[];original=g.ezdxf.readfile
    monkeypatch.setattr(g.ezdxf,'readfile',lambda *a,**k:(reads.append(1),original(*a,**k))[1])
    jid='b'*32
    with store.connect() as c:c.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,'analyze','queued','Na fila'))
    if cancel_after_geometry:
        read_geometry=worker.analyze
        def cancel_after(*a,**kw):
            result=read_geometry(*a,**kw);store.update(jid,state='cancel_requested');return result
        monkeypatch.setattr(worker,'analyze',cancel_after)
    assert worker.run(jid)==0
    if cancel_after_geometry:
        assert store.job(jid)['state']=='cancelled' and len(reads)==1
        assert not (d/'editor.json').exists()
        return
    assert store.job(jid)['state']=='done' and len(reads)==1
    for name in ('analysis.json','editor.json','vectors.json','hachuras_previa.json'):
        assert json.loads((d/name).read_text())
