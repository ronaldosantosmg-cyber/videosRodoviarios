from types import SimpleNamespace
import numpy as np
import pytest
from app.flow_diagnostics import flow_diagnostics


def net(length=100,disabled=False,used=True,edge_disabled=False):
    return SimpleNamespace(raw_info=[{'base':0,'points':np.array([[0.,0.],[length,0.]]),'disabled':disabled}],edges=[{'base':0,'disabled':edge_disabled}],paths=[{'edges':[0]}] if used else [],short_ignored=set())


@pytest.mark.parametrize('n,status',[(net(),'ok'),(net(disabled=True),'problem'),(net(0),'problem'),(net(float('nan')),'problem'),(net(49.9),'adjustment'),(net(used=False),'adjustment'),(net(edge_disabled=True),'problem')])
def test_diagnostics_from_engine(n,status):
    assert flow_diagnostics(n)[0]['technical_status']==status


def test_diagnostics_do_not_modify_video_frames(drawing):
    from app.render import Scene
    from test_workflow import settings
    scene=Scene(drawing,settings())
    a,_=scene.frame(1.)
    data=scene.editor_data()
    assert data['segments'] and all('technical_status' in s for s in data['segments'])
    # A fonte longa fora da pista permanece vermelha; os 18 m utilizáveis não geram veículo.
    assert not scene.network.edges and scene.network.auto_pruned
    assert all(s['technical_status']=='problem' and s['length_m']>=50 for s in data['segments'])
    b,_=scene.frame(1.)
    assert np.array_equal(a,b), 'As linhas do estudo técnico não podem entrar no vídeo.'


# Importa somente a fixture já usada pelo renderizador real.
from test_workflow import drawing
