"""1.42.41: validação de continuidade dos eixos."""
import numpy as np
from app.axis_validation import validate_axes

def R(x0,y0,x1,y1,role='pavement'):
    return {'layer':'P','role':role,'closed':True,'points':np.array([[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]),'holes':[]}

def ax(p,layer='EIXO'):return {'points':np.array(p,float),'layer':layer}

def test_cobertura_e_trecho_fora():
    r=validate_axes([ax([[0,0],[200,0]])],[R(0,-5,100,5)])
    a=r['axes'][0];assert a['coverage']<0.6 and a['longest_off_m']>=90 and a['alerts'][0]['code']=='fora_do_pavimento'
    ok=validate_axes([ax([[0,0],[200,0]])],[R(-1,-5,201,5)]);assert not ok['axes'][0]['alerts']

def test_sem_pavimento_autointersecao_e_pontas_sem_erro():
    r=validate_axes([ax([[0,0],[10,10],[10,0],[0,10]])],[])
    codes={a['code'] for a in r['axes'][0]['alerts']};assert {'sem_pavimento','autointersecao'}<=codes
    assert validate_axes([],[])['summary']['axes']==0
    t=validate_axes([ax([[0,0],[100,0]]),ax([[100,0],[200,0]])],[R(-1,-5,201,5)])
    assert all('free_ends' in a and len(a['free_ends'])==1 for a in t['axes'])

def test_lacunas_de_secao():
    from app.models import RouteAlignment
    route=RouteAlignment(id='r',name='R',points=[dict(x=0,y=0),dict(x=300,y=0)],sections_only=True,cross_sections=[dict(id='a',start_m=0,end_m=100,left=[dict(kind='pista')],right=[dict(kind='pista')])])
    r=validate_axes([ax([[0,0],[300,0]])],[R(-1,-5,301,5)],[route])
    assert r['summary']['section_gaps']==1 and any(a['code']=='lacuna_de_secao' for a in r['alerts'])
