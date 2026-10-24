"""1.35: obras do PER — importação de planilha (Excel .xlsx ou CSV) e de cronograma (MS Project XML ou Excel com datas),
reconhecimento do tipo da obra pelo texto e situação de cada obra numa data (prevista, em execução, concluída)."""
import csv,io,re,unicodedata,datetime as dt
from xml.etree import ElementTree as ET
from .per import parse_km,fmt_km
from .planilha import read_xlsx,write_xlsx

# código -> (rótulo, cor RGB hex, sigla). As 8 primeiras já existiam (cores das caixas não mudam).
WORK_STYLE={
 'duplicacao':('Duplicação','#ff9f1c','DUP'),'faixa_adicional':('Faixa adicional (3ª faixa)','#ffd166','3F'),'via_marginal':('Via marginal','#4cc9f0','M'),
 'iluminacao':('Iluminação','#fff275','IL'),'passarela':('Passarela','#f72585','P'),'oae':('OAE (ponte/viaduto)','#b5179e','OAE'),
 'alargamento_oae':('Alargamento de OAE','#9d4edd','AO'),'intersecao':('Interseção/dispositivo','#7209b7','D'),'retorno':('Retorno','#8e7dff','R'),
 'acesso':('Acesso','#b48cff','A'),'correcao':('Correção de traçado','#ef476f','CT'),'acostamento':('Acostamento','#c9ada7','AC'),
 'pavimento':('Pavimento (restauração)','#adb5bd','PV'),'drenagem':('Drenagem','#4fd1c5','DR'),'contencao':('Contenção/talude','#d4886a','CN'),
 'sinalizacao':('Sinalização','#f8f9fa','SN'),'defensa':('Defensa/barreira','#e9ecef','DF'),'ciclovia':('Ciclovia','#80ed99','CV'),
 'calcada':('Calçada/passeio','#d8e2dc','CL'),'pedagio':('Praça de pedágio','#ffb703','PD'),'posto':('Posto/base operacional','#90e0ef','PO'),
 'cerca':('Cerca/alambrado','#c9a97a','CE'),'fauna':('Passagem de fauna','#57cc99','PF'),'onibus':('Baia de ônibus','#7ee0a8','BUS'),
 'travessia':('Travessia de pedestres','#ffffff','TP'),'outro':('Outra obra','#ff8a3d','O')}

KEYWORDS=[('alargamento_oae',r'alargamento.*(oae|ponte|viaduto)|(oae|ponte|viaduto).*alargamento'),('duplicacao',r'duplica'),
 ('faixa_adicional',r'(terceira|3a|3ª) faixa|faixa adicional|faixas? adicionais'),('via_marginal',r'marginal'),('iluminacao',r'ilumina'),
 ('passarela',r'passarela'),('oae',r'\boae\b|ponte|viaduto|obra de arte|trincheira'),('retorno',r'retorno'),
 ('intersecao',r'interse|trevo|dispositivo|rotatoria|diamante|entroncamento'),('acesso',r'\bacesso'),('acostamento',r'acostamento'),
 ('pavimento',r'pavimen|recapea|restaura|fresagem|recuperacao de pista'),('drenagem',r'drenag|bueiro|galeria'),
 ('contencao',r'conten|cortina|arrimo|solo grampeado|estabiliza'),('sinalizacao',r'sinaliza'),('defensa',r'defensa|barreira|new jersey'),
 ('ciclovia',r'ciclo(via|faixa)'),('calcada',r'calcada|passeio'),('pedagio',r'pedagio|praca de'),('posto',r'\bposto\b|\bprf\b|\bsau\b|base operacional'),
 ('cerca',r'cerca|alambrado'),('correcao',r'correcao|variante|tracado|curva'),('fauna',r'fauna'),('onibus',r'onibus|\bbaia|parada'),
 ('travessia',r'travessia|faixa de pedestre|semaforo')]

def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',str(s or '').lower()) if not unicodedata.combining(c)).strip()

def guess_kind(*texts):
    t=' '.join(norm(x) for x in texts if x)
    if t in WORK_STYLE:return t
    for code,lab in WORK_STYLE.items():
        if t==norm(lab[0]):return code
    for code,rx in KEYWORDS:
        if re.search(rx,t):return code
    return 'outro'

KM_RX=re.compile(r'km\s*(\d{1,4}\s*[+,.]\s*\d{1,3})(?:\s*(?:a|ao|até|ate|-|–|—|/)\s*(?:km\s*)?(\d{1,4}\s*[+,.]\s*\d{1,3}))?',re.I)
def km_in_text(text):
    """Km no texto da tarefa: “km 325+850 a 326+200”, “km 325,8 - 326,2”, “km 325+850”. None se não houver."""
    m=KM_RX.search(str(text or ''))
    if not m:return None
    def conv(v):
        v=re.sub(r'\s','',v)
        if ',' in v or '.' in v:
            a,b=re.split(r'[,.]',v);return int(a)*1000+int((b+'000')[:3])
        return parse_km(v)
    a=conv(m.group(1));b=conv(m.group(2)) if m.group(2) else a
    return (min(a,b),max(a,b))

def to_date(v):
    if v is None or v=='':return ''
    if isinstance(v,dt.datetime):return v.date().isoformat()
    if isinstance(v,dt.date):return v.isoformat()
    if isinstance(v,(int,float)):
        from .planilha import serial_to_date
        return serial_to_date(v).isoformat() if 20000<v<80000 else ''
    s=str(v).strip()
    m=re.match(r'^(\d{4})-(\d{2})-(\d{2})',s)
    if m:return f'{m[1]}-{m[2]}-{m[3]}'
    m=re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})',s)
    if m:
        y=int(m[3]);y=y+2000 if y<100 else y
        try:return dt.date(y,int(m[2]),int(m[1])).isoformat()
        except ValueError:return ''
    return ''

def _km_value(v):
    if v is None or v=='':return None
    if isinstance(v,(int,float)):
        v=float(v);return v*1000 if v<5000 else v   # 325,85 (km) ou 325850 (m)
    s=str(v).strip().lower().replace('km','').strip()
    if not s:return None
    if '+' in s:return parse_km(s.replace(' ',''))
    s=s.replace(' ','')
    if s.count(',')==1 and '.' not in s:s=s.replace(',','.')
    elif s.count('.')>1:s=s.replace('.','')
    f=float(s);return f*1000 if f<5000 else f

COLS=[('km_start',r'^km\s*(inicial|inicio|ini|de)\b|^inicio\s*\(?km|^km\s*i$'),('km_end',r'^km\s*(final|fim|ate|termino)\b|^fim\s*\(?km|^km\s*f$'),
 ('km',r'^km$|^quilometro|^localiza'),('description',r'^(obra|descricao|nome|tarefa|servico|intervencao|nome da tarefa)'),('kind',r'^(tipo|categoria|classe)'),
 ('side',r'^(lado|sentido|pista)'),('per_year',r'^ano'),('per_table',r'^(tabela|item|codigo|cod\b|edt|wbs)'),
 ('start_date',r'^(inicio|data\s*(de\s*)?inicio|inicio\s*previsto|start|comeco)'),('end_date',r'^(termino|fim|data\s*(de\s*)?(fim|termino)|conclusao|termino\s*previsto|finish)'),
 ('progress_pct',r'^(%|porcentagem|percentual|avanco|progresso|concluido|% concluid)'),('x',r'^x\b|^este|^coord.*x'),('y',r'^y\b|^norte|^coord.*y')]

def _map_header(row):
    m={}
    for k,h in enumerate(row):
        n=norm(h)
        if not n:continue
        for key,rx in COLS:
            if key not in m and re.search(rx,n):m[key]=k;break
    return m

def rows_from_table(rows):
    """Tabela (lista de linhas) -> (obras, avisos). Acha o cabeçalho nas 15 primeiras linhas."""
    head=None
    for i,r in enumerate(rows[:15]):
        m=_map_header(r)
        if 'description' in m and ({'km_start','km'}&set(m) or 'start_date' in m):head=(i,m);break
    if head is None:raise ValueError('Cabeçalho não encontrado. A planilha precisa das colunas “Obra” e “Km inicial” (ou “Km”), e opcionalmente “Km final”, “Tipo”, “Lado”, “Início”, “Término”, “% concluído”.')
    i0,m=head;out=[];warn=[]
    for n,r in enumerate(rows[i0+1:],i0+2):
        g=lambda k:(r[m[k]] if k in m and m[k]<len(r) else None)
        desc=str(g('description') or '').strip()
        if not desc:continue
        try:
            a=_km_value(g('km_start') if 'km_start' in m else None);b=_km_value(g('km_end')) if 'km_end' in m else None
            if a is None and 'km' in m:
                t=g('km');rng=km_in_text('km '+str(t)) if t is not None and not isinstance(t,(int,float)) else None
                a,b=(rng if rng else (_km_value(t),None))
            if a is None:
                rng=km_in_text(desc)
                if rng:a,b=rng
            if b is None:b=a
        except (ValueError,TypeError) as e:warn.append(f'Linha {n}: km inválido ({e}).');continue
        side=norm(g('side'));side='direito' if side.startswith(('dir','d','cresc','norte','n')) and side else 'esquerdo' if side.startswith(('esq','e','decresc','sul','s')) and side else 'ambos'
        pct=g('progress_pct')
        try:pct=None if pct in (None,'') else float(str(pct).replace('%','').replace(',','.').strip())
        except ValueError:pct=None
        def num(v):
            if v in (None,''):return None
            try:return float(str(v).replace(' ','').replace(',','.')) if not isinstance(v,(int,float)) else float(v)
            except ValueError:return None
        w={'description':desc[:300],'kind':guess_kind(g('kind'),'' if g('kind') else desc),'km_start_m':a,'km_end_m':b,'side':side,
           'per_year':str(g('per_year') or '').strip()[:70],'per_table':str(g('per_table') or '').strip()[:70],
           'start_date':to_date(g('start_date')),'end_date':to_date(g('end_date')),'progress_pct':pct,
           'x':num(g('x')),'y':num(g('y')),'task':desc[:300]}
        if w['progress_pct'] is not None:w['progress_pct']=max(0.,min(100.,w['progress_pct']))
        if isinstance(w['per_year'],str) and re.fullmatch(r'\d+\.0',w['per_year']):w['per_year']=w['per_year'][:-2]
        if (w['x'] is None)!=(w['y'] is None):w['x']=w['y']=None
        if w['start_date'] and w['end_date'] and w['end_date']<w['start_date']:w['start_date'],w['end_date']=w['end_date'],w['start_date']
        if a is None:w['sem_km']=True
        out.append(w)
    P=[w['progress_pct'] for w in out if w['progress_pct'] is not None]
    if P and max(P)<=1 and any(0<v<1 for v in P):   # Excel guarda 45% como 0,45
        for w in out:
            if w['progress_pct'] is not None:w['progress_pct']=round(w['progress_pct']*100,1)
    if not out:raise ValueError('Nenhuma obra encontrada abaixo do cabeçalho.')
    if len(out)>1000:raise ValueError('Limite de 1000 obras por projeto.')
    return out,warn

def read_table(data,filename):
    ext=(filename or '').lower().rsplit('.',1)[-1]
    if ext in ('xlsx','xlsm'):
        _,rows=read_xlsx(data);return rows_from_table(rows)
    if ext=='xls':raise ValueError('Formato .xls antigo: abra no Excel e salve como .xlsx (Pasta de Trabalho do Excel).')
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError:text=data.decode('cp1252')
    try:dialect=csv.Sniffer().sniff(text[:4096],delimiters=';,\t')
    except csv.Error:
        class dialect(csv.excel):delimiter=';'
    return rows_from_table(list(csv.reader(io.StringIO(text),dialect)))

def read_msproject(data):
    """Cronograma do MS Project salvo como XML. Lê as tarefas (nome, início, término, % concluída); o km vem do nome
    (“Duplicação km 325+850 a 326+200”) ou de um campo personalizado com “km” no nome."""
    try:root=ET.fromstring(data)
    except ET.ParseError as e:raise ValueError('XML inválido: '+str(e)[:120])
    ns=root.tag[1:].split('}')[0] if root.tag.startswith('{') else ''
    q=lambda t:f'{{{ns}}}{t}' if ns else t
    if not root.tag.endswith('Project'):raise ValueError('O XML não é um cronograma do MS Project (salve no Project como “XML”).')
    alias={}
    for ea in root.iter(q('ExtendedAttribute')):
        fid=ea.findtext(q('FieldID'));name=ea.findtext(q('Alias')) or ea.findtext(q('FieldName')) or ''
        if fid and name:alias[fid]=norm(name)
    tasks=[]
    for t in root.iter(q('Task')):
        name=(t.findtext(q('Name')) or '').strip()
        if not name or t.findtext(q('IsNull'))=='1':continue
        ext={}
        for ea in t.findall(q('ExtendedAttribute')):
            a=alias.get(ea.findtext(q('FieldID')) or '','')
            if a:ext[a]=ea.findtext(q('Value')) or ''
        rng=km_in_text(name)
        if not rng:
            ki=next((v for k,v in ext.items() if 'km' in k and re.search(r'ini|de\b',k)),None);kf=next((v for k,v in ext.items() if 'km' in k and re.search(r'fim|final|ate',k)),None)
            k1=next((v for k,v in ext.items() if 'km' in k),None)
            try:
                if ki:a=_km_value(ki);rng=(a,_km_value(kf) if kf else a)
                elif k1:rng=km_in_text('km '+k1) or (_km_value(k1),_km_value(k1))
            except ValueError:rng=None
        tasks.append({'uid':t.findtext(q('UID')),'name':name,'level':int(t.findtext(q('OutlineLevel')) or 0),'summary':t.findtext(q('Summary'))=='1',
                      'start':to_date(t.findtext(q('Start'))),'finish':to_date(t.findtext(q('Finish'))),'pct':float(t.findtext(q('PercentComplete')) or 0),
                      'km':rng,'tipo':next((v for k,v in ext.items() if k.startswith(('tipo','categoria'))),'')})
    if not tasks:raise ValueError('Cronograma sem tarefas.')
    leaves=[t for t in tasks if not t['summary'] and t['level']>0]
    use=[t for t in leaves if t['km']] or [t for t in tasks if t['km'] and t['level']>0]
    out=[{'description':t['name'][:300],'kind':guess_kind(t['tipo'],'' if t['tipo'] else t['name']),'km_start_m':t['km'][0],'km_end_m':t['km'][1],'side':'ambos',
          'per_year':'','per_table':'','start_date':t['start'],'end_date':t['finish'],'progress_pct':t['pct'],'x':None,'y':None,'task':t['name'][:300]} for t in use]
    sem=[{'description':t['name'][:300],'start_date':t['start'],'end_date':t['finish'],'progress_pct':t['pct'],'task':t['name'][:300],'sem_km':True,
          'kind':guess_kind(t['tipo'],t['name']),'km_start_m':None,'km_end_m':None,'side':'ambos','per_year':'','per_table':'','x':None,'y':None}
         for t in leaves if not t['km']][:500]
    warn=[] if out else ['Nenhuma tarefa tem km no nome (ex.: “Duplicação km 325+850 a 326+200”) nem em campo com “km”. Ligue as tarefas às obras na lista.']
    return out+sem,warn

def read_any(data,filename):
    ext=(filename or '').lower().rsplit('.',1)[-1]
    if ext=='xml':return read_msproject(data)
    if ext=='mpp':raise ValueError('Arquivo .mpp: no MS Project use Arquivo › Salvar como › XML e importe o .xml.')
    return read_table(data,filename)

def merge(existing,imported,mode):
    """mode: substituir | acrescentar | datas (atualiza início, término e % das obras de mesmo nome/tarefa)."""
    if mode=='substituir':return [w for w in imported if not w.get('sem_km')],len([w for w in imported if not w.get('sem_km')])
    if mode=='acrescentar':
        new=[w for w in imported if not w.get('sem_km')];return existing+new,len(new)
    key=lambda s:re.sub(r'\s+',' ',norm(s))
    by={}
    for w in imported:
        for k in (w.get('task'),w.get('description')):
            if k:by.setdefault(key(k),w)
    n=0;out=[]
    for e in existing:
        w=by.get(key(e.get('task') or ''),None) or by.get(key(e.get('description') or ''),None)
        if w:
            e={**e,'start_date':w.get('start_date') or e.get('start_date',''),'end_date':w.get('end_date') or e.get('end_date',''),
               'progress_pct':w.get('progress_pct') if w.get('progress_pct') is not None else e.get('progress_pct'),'task':w.get('task') or e.get('task','')};n+=1
        out.append(e)
    return out,n

def template_xlsx():
    head=['Obra','Tipo','Km inicial','Km final','Lado','Início','Término','% concluído','Ano PER','Tabela PER']
    ex=[['Duplicação do segmento A','Duplicação','325+000','328+400','Ambos',dt.date(2027,3,1),dt.date(2028,6,30),0,'Ano 3','Tab. 7.1'],
        ['Via marginal bairro Centro','Via marginal','326+100','326+900','Direito',dt.date(2027,8,1),dt.date(2028,2,28),0,'Ano 3',''],
        ['Iluminação do trevo','Iluminação','327+300','327+700','Ambos',dt.date(2028,1,10),dt.date(2028,4,30),0,'Ano 4',''],
        ['Passarela km 326+500','Passarela','326+500','','Ambos',dt.date(2027,5,1),dt.date(2027,11,30),0,'Ano 3','']]
    tipos=[[ 'Tipo','Para que serve' ]]+[[v[0],code] for code,v in WORK_STYLE.items()]
    return write_xlsx([('Obras',[head]+ex,[38,26,12,12,10,12,12,13,10,12]),('Tipos aceitos',tipos,[34,20])])

def export_xlsx(works):
    head=['Obra','Tipo','Km inicial','Km final','Lado','Início','Término','% concluído','Ano PER','Tabela PER','X','Y']
    rows=[head]
    for w in works:
        d=lambda s:dt.date.fromisoformat(s) if s else ''
        rows.append([w['description'],WORK_STYLE.get(w['kind'],WORK_STYLE['outro'])[0],fmt_km(w['km_start_m']),fmt_km(w['km_end_m']),w.get('side','ambos').capitalize(),
                     d(w.get('start_date')),d(w.get('end_date')),w.get('progress_pct') if w.get('progress_pct') is not None else '',w.get('per_year',''),w.get('per_table',''),
                     w.get('x') if w.get('x') is not None else '',w.get('y') if w.get('y') is not None else ''])
    return write_xlsx([('Obras',rows,[38,26,12,12,10,12,12,13,10,12,14,14])])

# ---------------- situação numa data ----------------
def status(w,day):
    """'prevista' (antes do início), 'execucao' (fração do prazo decorrida), 'concluida' ou 'sem_data'."""
    if not w.get('start_date') or not w.get('end_date'):return 'sem_data',1.
    a=dt.date.fromisoformat(w['start_date']);b=dt.date.fromisoformat(w['end_date'])
    if day<a:return 'prevista',0.
    if day>=b:return 'concluida',1.
    return 'execucao',max(.02,min(.98,(day-a).days/max(1,(b-a).days)))

def schedule_range(s):
    ds=[w.start_date for w in s.works if w.start_date]+[w.end_date for w in s.works if w.end_date]
    a=s.schedule_start or (min(ds) if ds else '');b=s.schedule_end or (max(ds) if ds else '')
    if not a or not b or b<=a:return None
    return dt.date.fromisoformat(a),dt.date.fromisoformat(b)

MESES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
def date_label(d):return f'{MESES[d.month-1]}/{d.year}'
