"""1.35: obras do PER (tipos, Excel/CSV/MS Project XML, modelo e exportação), linha do tempo pelo cronograma no vídeo,
mais categorias de destaque e esquema 28 (projetos anteriores com o vídeo de antes)."""
import datetime as dt,json
import numpy as np,pytest
from fastapi.testclient import TestClient
from test_v116 import S  # noqa: F401
from test_v110 import junction  # noqa: F401

XML='''<?xml version="1.0" encoding="UTF-8"?><Project xmlns="http://schemas.microsoft.com/project"><Name>PER</Name>
<ExtendedAttributes><ExtendedAttribute><FieldID>188743731</FieldID><FieldName>Text1</FieldName><Alias>Km inicial</Alias></ExtendedAttribute></ExtendedAttributes><Tasks>
<Task><UID>0</UID><Name>Projeto</Name><OutlineLevel>0</OutlineLevel><Summary>1</Summary><Start>2027-01-01T08:00:00</Start><Finish>2028-12-31T17:00:00</Finish></Task>
<Task><UID>1</UID><Name>Ano 3</Name><OutlineLevel>1</OutlineLevel><Summary>1</Summary><Start>2027-01-01T08:00:00</Start><Finish>2027-12-31T17:00:00</Finish></Task>
<Task><UID>2</UID><Name>Duplicação km 0+050 a 0+300</Name><OutlineLevel>2</OutlineLevel><Summary>0</Summary><Start>2027-02-01T08:00:00</Start><Finish>2027-10-31T17:00:00</Finish><PercentComplete>40</PercentComplete></Task>
<Task><UID>3</UID><Name>Iluminação do trevo</Name><OutlineLevel>2</OutlineLevel><Summary>0</Summary><Start>2027-05-01T08:00:00</Start><Finish>2027-08-31T17:00:00</Finish>
 <ExtendedAttribute><FieldID>188743731</FieldID><Value>0+180</Value></ExtendedAttribute></Task>
<Task><UID>4</UID><Name>Mobilização do canteiro</Name><OutlineLevel>2</OutlineLevel><Summary>0</Summary><Start>2027-01-02T08:00:00</Start><Finish>2027-01-30T17:00:00</Finish></Task>
</Tasks></Project>'''.encode('utf-8')

def test_tipos_e_textos():
    from app.obras import guess_kind,km_in_text,WORK_STYLE
    from app.models import WORK_KINDS
    assert set(WORK_STYLE)==set(WORK_KINDS)
    for t,k in [('Duplicação da BR','duplicacao'),('Implantação de 3ª faixa','faixa_adicional'),('Via Marginal Norte','via_marginal'),('Iluminação do trevo','iluminacao'),
                ('Alargamento da ponte sobre o rio','alargamento_oae'),('Viaduto km 12','oae'),('Retorno em nível','retorno'),('Contenção em solo grampeado','contencao'),('Pintura','outro')]:
        assert guess_kind('',t)==k,(t,guess_kind('',t))
    assert guess_kind('Via marginal','qualquer')=='via_marginal' and guess_kind('iluminacao')=='iluminacao'
    assert km_in_text('Duplicação km 325+850 a 326+200')==(325850,326200) and km_in_text('KM 12,5 - 13,1')==(12500,13100) and km_in_text('Passarela km 7+020')==(7020,7020) and km_in_text('Sem km') is None

def test_excel_modelo_ida_e_volta():
    from app.obras import template_xlsx,read_any,export_xlsx
    from app.planilha import read_xlsx
    x=template_xlsx();aba,rows=read_xlsx(x);assert aba=='Obras' and rows[0][0]=='Obra' and isinstance(rows[1][5],dt.date)
    w,warn=read_any(x,'modelo.xlsx');assert len(w)==4 and not warn
    assert [o['kind'] for o in w]==['duplicacao','via_marginal','iluminacao','passarela'] and w[1]['side']=='direito' and w[0]['start_date']=='2027-03-01' and w[0]['km_end_m']==328400
    w2,_=read_any(export_xlsx(w),'obras.xlsx');assert [(o['description'],o['km_start_m'],o['km_end_m'],o['start_date'],o['end_date']) for o in w2]==[(o['description'],o['km_start_m'],o['km_end_m'],o['start_date'],o['end_date']) for o in w]

def test_csv_e_porcentagem():
    from app.obras import read_any
    w,_=read_any('Obra;Km;Início;Término;% concluído\nDuplicação trecho 1;km 10+000 a 12+500;01/03/2027;30/06/2028;45%\nIluminação;11,2;;;\n'.encode('cp1252'),'a.csv')
    assert (w[0]['km_start_m'],w[0]['km_end_m'],w[0]['progress_pct'],w[0]['end_date'])==(10000,12500,45.,'2028-06-30') and w[1]['km_start_m']==11200 and w[1]['kind']=='iluminacao'
    with pytest.raises(ValueError):read_any(b'a;b\n1;2\n','x.csv')
    with pytest.raises(ValueError):read_any(b'x','x.xls')

def test_ms_project_xml():
    from app.obras import read_any
    w,warn=read_any(XML,'per.xml');com=[o for o in w if not o.get('sem_km')];sem=[o for o in w if o.get('sem_km')]
    assert [(o['description'],o['km_start_m'],o['km_end_m'],o['kind'],o['progress_pct']) for o in com]==[('Duplicação km 0+050 a 0+300',50,300,'duplicacao',40.),('Iluminação do trevo',180,180,'iluminacao',0.)]
    assert com[0]['start_date']=='2027-02-01' and com[0]['end_date']=='2027-10-31' and [o['description'] for o in sem]==['Mobilização do canteiro'] and not warn

def test_situacao_por_data():
    from app.obras import status
    w={'start_date':'2027-01-01','end_date':'2027-12-31'}
    assert status(w,dt.date(2026,12,1))[0]=='prevista' and status(w,dt.date(2028,1,1))==('concluida',1.)
    st,f=status(w,dt.date(2027,7,2));assert st=='execucao' and .45<f<.55 and status({},dt.date(2027,1,1))[0]=='sem_data'

def test_esquema_28_e_categorias():
    from app.models import Settings,Highlight,PERWork
    from app.migration import SCHEMA_VERSION
    assert SCHEMA_VERSION>=28
    old=Settings.model_validate({'schema_version':27,'km_start_m':0,'km_end_m':100});assert old.per_display=='chamada' and old.schedule_mode=='off'
    assert Settings().per_display=='trecho'
    assert Highlight(name='Torre',category='torre',point={'x':0,'y':0}).category=='torre'
    with pytest.raises(ValueError):PERWork(description='x',km_start_m=0,km_end_m=10,start_date='2027-05-01',end_date='2027-01-01')
    from app import visual
    for k in ('edificacao','interferencia','poste','rede','drenagem','acesso','outro'):assert k in visual.HIGHLIGHT_STYLE   # anteriores mantidas

def test_video_obras_e_linha_do_tempo(junction):
    from app.render import Scene
    W=[{'description':'Duplicação','kind':'duplicacao','km_start_m':100,'km_end_m':300,'start_date':'2027-01-01','end_date':'2027-12-31'}]
    v=((500200,7800000),300)
    base=Scene(junction,S(per_display='chamada')).frame(0,view=v)[0]
    cham=Scene(junction,S(works=W,per_display='chamada',per_callouts=False)).frame(0,view=v)[0]
    assert np.array_equal(base,cham)                     # só caixa (projetos anteriores): nada de faixa
    tre=Scene(junction,S(works=W,per_display='trecho',per_callouts=False)).frame(0,view=v)[0]
    assert np.abs(tre.astype(int)-base).sum(2).astype(bool).mean()>.01   # faixa colorida visível
    sc=Scene(junction,S(works=W,per_display='trecho',per_callouts=False,schedule_mode='linha_do_tempo',schedule_start='2026-07-01',schedule_end='2028-06-30',duration_s=30))
    from app.obras_video import day_at
    sc.frame(0);assert day_at(sc,0).isoformat()=='2026-07-01' and day_at(sc,15).isoformat()[:7]=='2027-07' and day_at(sc,30).isoformat()=='2028-06-30'

def test_api_obras(junction):
    from app.server import app
    from app.obras import template_xlsx
    c=TestClient(app);pid=c.post('/api/projects',json=S(name='Obras API').model_dump()).json()['id']
    assert len(c.get('/api/obras/tipos').json())==26 and c.get('/api/obras/modelo.xlsx').content[:2]==b'PK'
    r=c.post(f'/api/projects/{pid}/obras/ler',files={'file':('per.xml',XML)}).json();assert len(r['obras'])==2 and len(r['sem_km'])==1
    r=c.post(f'/api/projects/{pid}/obras/ler',files={'file':('m.xlsx',template_xlsx())}).json();assert len(r['obras'])==4
    assert c.post(f'/api/projects/{pid}/obras/ler',files={'file':('m.mpp',b'x')}).status_code==422
    cfg=c.get(f'/api/projects/{pid}').json()['config'];cfg['works']=[{k:v for k,v in o.items() if k!='sem_km'} for o in r['obras']]
    assert c.put(f'/api/projects/{pid}/config',json=cfg).status_code==200
    x=c.get(f'/api/projects/{pid}/obras.xlsx');assert x.status_code==200 and x.content[:2]==b'PK'
