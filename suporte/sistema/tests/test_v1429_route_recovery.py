"""O diagnóstico não pode alterar nem reativar os dados do usuário."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from app.flow_diagnostics import flow_diagnostics

@pytest.mark.parametrize('points,disabled,minimum,status,text',[
    ([[0.,0.],[100.,0.]],False,50,'ok','Manter a circulação'),
    ([[0.,0.],[100.,0.]],True,50,'problem','não reativar'),
    ([[0.,0.],[30.,0.]],False,50,'adjustment','desligar a circulação'),
    ([[0.,0.],[0.,0.]],False,50,'problem','preservar o traçado'),
    ([[0.,0.],[None,0.]],False,50,'problem','preservar o traçado'),
    ([[0.,0.],['',0.]],False,50,'problem','preservar o traçado'),
    ([[0.,0.],[float('inf'),0.]],False,50,'problem','preservar o traçado'),
])
def test_recovery_guidance_preserves_geometry(points,disabled,minimum,status,text):
    raw={'base':0,'points':points,'disabled':disabled}
    n=SimpleNamespace(min_route=minimum,raw_info=[raw],edges=[{'base':0,'disabled':disabled}],paths=[{'edges':[0]}],short_ignored=set())
    before=deepcopy(raw)
    result=flow_diagnostics(n)[0]
    assert result['technical_status']==status
    assert text in result['technical_automatic']
    assert result['technical_manual']
    assert raw==before
