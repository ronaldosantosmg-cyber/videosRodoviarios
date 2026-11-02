"""1.42.41: cobertura e conflitos entre hachuras."""
import numpy as np
from app.hatch_coverage import analyze_coverage,coverage_raster

def R(x0,y0,x1,y1,role,closed=True):
    return {'layer':'L','role':role,'closed':closed,'points':np.array([[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]),'holes':[]}

def test_junta_estreita_e_vazio_largo():
    j=analyze_coverage([R(0,0,50,8,'pavement'),R(50.3,0,100,8,'pavement')])
    assert j['summary']['joints']==1 and j['summary']['voids']==0
    v=analyze_coverage([R(0,0,50,8,'pavement'),R(54,0,100,8,'pavement')])
    assert v['summary']['voids']==1 and v['summary']['joints']==0

def test_sobreposicao_prioridade_e_esperada():
    r=analyze_coverage([R(0,0,50,8,'pavement'),R(40,0,60,8,'existing_pavement'),R(0,0,20,8,'cut'),R(10,0,30,8,'median')])
    pairs={(o['under'],o['over']):o for o in r['overlaps']}
    assert pairs[('existing_pavement','pavement')]['expected'] and pairs[('cut','median')]['expected']
    assert pairs[('pavement','median')]['expected']

def test_sem_pavimento_e_degenerada_sem_erro():
    r=analyze_coverage([R(0,0,0.1,0.1,'pavement'),R(0,0,10,10,'median'),{'layer':'x','role':'pavement','closed':True,'points':np.array([[0,0],[1,1]]),'holes':[]}])
    codes={a['code'] for a in r['alerts']}
    assert 'sem_pavimento' in codes and r['degenerate']==2
    assert analyze_coverage([])['summary']['roles']==0

def test_raster_prioridade():
    g,codes,c=coverage_raster([R(0,0,20,20,'pavement'),R(0,0,10,20,'median')],(0,0,20,20),cell_m=2)
    assert g[5,2]==codes['median'] and g[5,8]==codes['pavement']
