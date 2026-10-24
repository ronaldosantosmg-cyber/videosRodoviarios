"""PER rows use metres internally; text/CSV accepts Brazilian km notation."""
import csv,io,re,unicodedata
import numpy as np

def parse_km(value):
    s=str(value).strip()
    if not s:raise ValueError('Quilômetro vazio.')
    if '+' in s:
        if not re.fullmatch(r'\d+\+\d{1,3}',s):raise ValueError('Use km como 325+850 ou 325,850.')
        a,b=s.split('+');return int(a)*1000+int(b)
    if not re.fullmatch(r'\d+(?:[.,]\d{1,3})?',s):raise ValueError('Quilômetro inválido: '+s)
    return float(s.replace(',','.'))*1000

def fmt_km(value):
    m=round(value);return f'{m//1000}+{m%1000:03d}'

def read_csv(data):
    from .models import PERWork
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError:text=data.decode('cp1252')
    def normal(k):return ''.join(c for c in unicodedata.normalize('NFKD',k.lower()) if not unicodedata.combining(c)).strip().replace('_',' ')
    try:dialect=csv.Sniffer().sniff(text[:4096],delimiters=';,\t')
    except csv.Error:dialect=csv.excel;dialect.delimiter=';'
    rows=[]
    aliases={'descricao':'description','obra':'description','description':'description','km inicial':'km_start','km inicio':'km_start','km final':'km_end','km fim':'km_end','tipo':'kind','categoria':'kind','ano per':'per_year','ano':'per_year','tabela per':'per_table','tabela':'per_table','x':'x','y':'y','coordenada x':'x','coordenada y':'y','e':'x','n':'y'}
    for i,r in enumerate(csv.DictReader(io.StringIO(text),dialect=dialect),2):
        if not any(str(v or '').strip() for v in r.values()):continue
        d={aliases.get(normal(k),normal(k)):str(v or '').strip() for k,v in r.items() if k is not None}
        try:
            a=parse_km(d.get('km_start',''));b=parse_km(d.get('km_end','') or d.get('km_start',''))
            kind=d.get('kind','outro') or 'outro'
            translations={'passarela':'passarela','oae':'oae','marginal':'via_marginal','via marginal':'via_marginal','retorno':'intersecao','diamante':'intersecao','intersecao':'intersecao','correcao':'correcao','fauna':'fauna','urbano':'outro'}
            kind=translations.get(normal(kind),kind)
            def num(v):
                v=str(v or '').strip().replace(' ','')
                if not v:return None
                if v.count(',')==1 and '.' not in v:v=v.replace(',','.')
                return float(v)
            x=num(d.get('x'));y=num(d.get('y'))
            rows.append(PERWork(description=d.get('description',''),km_start_m=a,km_end_m=b,kind=kind if kind in ('oae','passarela','intersecao','via_marginal','correcao','fauna','onibus','outro') else 'outro',per_year=d.get('per_year',''),per_table=d.get('per_table',''),x=x,y=y))
        except ValueError as e:raise ValueError(f'Linha {i}: {e}') from e
    if not rows:raise ValueError('CSV sem obras. Use Descrição;Km inicial;Km final;Tipo;Ano PER;Tabela PER.')
    if len(rows)>1000:raise ValueError('Limite de 1000 obras por projeto.')
    return rows

def export_csv(works):
    f=io.StringIO(newline='');w=csv.writer(f,delimiter=';');w.writerow(['Descrição','Km inicial','Km final','Tipo','Ano PER','Tabela PER'])
    for row in works:w.writerow([row.description,fmt_km(row.km_start_m),fmt_km(row.km_end_m),row.kind,row.per_year,row.per_table])
    return '\ufeff'+f.getvalue()

def works_to_pois(settings,axis,ds,stationing=None):
    """Obras da tabela PER como chamadas. Com estaqueamento definido, o km localiza a obra
    pela distância percorrida ao longo do eixo; obra com X/Y em modo auto recebe km calculado."""
    result=[]
    for i,row in enumerate(settings.works):
        located=row.x is not None and row.y is not None
        a,b=row.km_start_m,row.km_end_m
        if located and row.km_mode=='auto' and stationing is not None:a=b=stationing.km([row.x,row.y])
        if b<settings.km_start_m or a>settings.km_end_m:continue
        km=(a+b)/2
        if located:p=[row.x,row.y]
        elif stationing is not None:p=stationing.point(km).tolist()
        else:
            ch=np.clip((km-settings.km_start_m)/(settings.km_end_m-settings.km_start_m),0,1)*ds[-1];p=[float(np.interp(ch,ds,axis[:,k])) for k in range(2)]
        sub='km '+fmt_km(a)+((' a '+fmt_km(b)) if b!=a else '')
        parts=[sub]+[s for s in [row.per_table,row.per_year] if s]
        result.append({'id':row.id or 'per-'+str(i),'title':row.description,'subtitle':' • '.join(parts),'kind':row.kind,'x':p[0],'y':p[1],'km_mode':'manual','per_location':'coordenada' if located else ('estaqueamento' if stationing is not None else 'interpolação por km'),'km_start_m':a,'km_end_m':b})
    return result
