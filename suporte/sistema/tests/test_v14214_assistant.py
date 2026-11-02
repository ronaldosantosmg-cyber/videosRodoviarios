import hashlib
import numpy as np
from app.models import Settings
from app.flow_assistant import guidance
from app.flow_diagnostics import flow_diagnostics
from test_v14213_continuity import network,AXIS


def test_small_nodes_are_removed_only_from_derived_path_and_old_disable_stays_valid():
    p=np.array([[0.,0.],[200.,0.],[200.005,.004],[200.006,0.],[600.,0.]])
    original=p.copy();n=network([dict(points=p)])
    assert n.native_axis_report['removed_nodes']>=2
    assert n.paths and max(path['length'] for path in n.paths)>590
    np.testing.assert_array_equal(p,original)
    q=np.round(p,3).astype('<f8');key=hashlib.sha256(b'0|0'+min(q.tobytes(),q[::-1].tobytes())).hexdigest()
    off=network([dict(points=p)],flow_overrides=[dict(id='old',x=300,y=0,target_key=key,action='disable')])
    assert not off.paths and all(r['disabled'] for r in off.raw_info)


def test_disable_of_a_joined_axis_survives_recalculation():
    axes=[dict(points=AXIS)]+[dict(layer='EIXO',points=np.array([[100.+i*30,30.],[130.+i*30,30.]])) for i in range(3)]
    first=network(axes);target=next(r for r in first.raw_info if r.get('native_id')=='1,2,3')
    off=network(axes,flow_overrides=[dict(id='off',x=145,y=30,target_key=target['origin_key'],action='disable')])
    assert any(r.get('native_id')=='1,2,3' and r['disabled'] for r in off.raw_info)


def test_expert_guidance_is_local_explainable_and_does_not_reactivate_short_or_disabled_flows():
    for kw in [dict(disabled=True,length=200),dict(length=19)]:
        g=guidance('problem',[],**kw)
        assert g['method']=='sistema_especialista_local'
        assert not any(s['action'] in ('recalculate','recover') for s in g['steps'])
    g=guidance('problem',['corpo_fora_da_pista'],length=600,points=[dict(point=[300,0])])
    assert g['point']==[300,0] and [s['action'] for s in g['steps']]==['locate','layers',None,'recalculate']
    assert all(s['instruction'] and s['why'] for s in g['steps'])


def test_engine_provides_specific_guide_for_a_real_block():
    from shapely.geometry import box
    n=network([dict(points=AXIS)],obstacles=[box(290,-20,310,220)])
    d=next(d for d in flow_diagnostics(n) if 'corpo_fora_da_pista' in d['technical_reasons'])
    assert d['technical_assistant']['point']
    assert 'pista' in d['technical_assistant']['title']
