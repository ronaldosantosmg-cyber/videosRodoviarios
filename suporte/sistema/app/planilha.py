"""1.35: leitura e gravação de planilhas Excel (.xlsx) sem dependências novas (o .xlsx é um ZIP com XML).

Lê a primeira planilha (ou a de nome indicado): textos, números, datas (número de série do Excel) e células
com fórmula (usa o valor guardado). Grava planilhas simples (cabeçalho em negrito, largura das colunas).
"""
import io,re,zipfile,datetime as dt
from xml.etree import ElementTree as ET

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel':'http://schemas.openxmlformats.org/package/2006/relationships'}
DATE_FMTS={14,15,16,17,18,19,20,21,22,27,30,36,45,46,47,50,57}

def _col(ref):
    n=0
    for ch in re.match(r'[A-Z]+',ref).group(0):n=n*26+ord(ch)-64
    return n-1

def serial_to_date(v):
    return (dt.datetime(1899,12,30)+dt.timedelta(days=float(v))).date()

def read_xlsx(data,sheet=None,max_rows=20000):
    """Devolve (nome_da_planilha, linhas) — linhas é uma lista de listas (str, float, datetime.date ou None)."""
    try:z=zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:raise ValueError('O arquivo não é uma planilha .xlsx válida (salve como “Pasta de Trabalho do Excel”).')
    names=set(z.namelist())
    shared=[]
    if 'xl/sharedStrings.xml' in names:
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS):
            shared.append(''.join(t.text or '' for t in si.iter('{%s}t'%NS['m'])))
    date_styles=set()
    if 'xl/styles.xml' in names:
        st=ET.fromstring(z.read('xl/styles.xml'));custom={}
        for f in st.findall('m:numFmts/m:numFmt',NS):
            code=f.get('formatCode','').lower();custom[int(f.get('numFmtId'))]=bool(re.search(r'(^|[^a-z"])(d{1,4}|m{1,4}|y{2,4})([^a-z"]|$)',re.sub(r'"[^"]*"|\[[^\]]*\]','',code)))
        for k,xf in enumerate(st.findall('m:cellXfs/m:xf',NS)):
            fid=int(xf.get('numFmtId','0'))
            if fid in DATE_FMTS or custom.get(fid):date_styles.add(k)
    wb=ET.fromstring(z.read('xl/workbook.xml'));rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    targets={r.get('Id'):r.get('Target') for r in rels.findall('rel:Relationship',NS)}
    sheets=[(s.get('name'),targets[s.get('{%s}id'%NS['r'])]) for s in wb.findall('m:sheets/m:sheet',NS)]
    if not sheets:raise ValueError('Planilha sem abas.')
    pick=sheets[0]
    if sheet:
        want=[x for x in sheets if x[0].strip().lower()==sheet.strip().lower()]
        if want:pick=want[0]
    path=pick[1].lstrip('/');path=path if path.startswith('xl/') else 'xl/'+path
    root=ET.fromstring(z.read(path));rows=[]
    for r in root.iter('{%s}row'%NS['m']):
        line=[]
        for c in r.findall('m:c',NS):
            k=_col(c.get('r','A1'));t=c.get('t');s=int(c.get('s','0'));v=c.find('m:v',NS);val=None
            if t=='s' and v is not None:val=shared[int(v.text)]
            elif t=='inlineStr':val=''.join(x.text or '' for x in c.iter('{%s}t'%NS['m']))
            elif t in ('str','e'):val=v.text if v is not None else None
            elif t=='b':val=bool(int(v.text)) if v is not None else None
            elif v is not None and v.text is not None:
                num=float(v.text);val=serial_to_date(num) if s in date_styles and 1<num<2958466 else num
            while len(line)<k:line.append(None)
            line.append(val)
        rows.append(line)
        if len(rows)>max_rows:raise ValueError(f'Planilha com mais de {max_rows} linhas.')
    return pick[0],rows

def _esc(s):return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def _ref(r,c):
    s='';c+=1
    while c:c,m=divmod(c-1,26);s=chr(65+m)+s
    return f'{s}{r+1}'

def write_xlsx(sheets):
    """sheets: [(nome, linhas, larguras)] -> bytes. A 1ª linha de cada aba é o cabeçalho (negrito, congelado).
    Valores datetime.date viram datas do Excel (dd/mm/aaaa)."""
    out=io.BytesIO();z=zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)
    n=len(sheets)
    z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
               +''.join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(n))+'</Types>')
    z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    z.writestr('xl/workbook.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
               +''.join(f'<sheet name="{_esc(name[:31])}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i,(name,_,_) in enumerate(sheets))+'</sheets></workbook>')
    z.writestr('xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               +''.join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(n))
               +f'<Relationship Id="rId{n+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
    z.writestr('xl/styles.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><numFmts count="1"><numFmt numFmtId="164" formatCode="dd/mm/yyyy"/></numFmts><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="3"><xf/><xf fontId="1" fillId="2" applyFont="1" applyFill="1"/><xf numFmtId="164" applyNumberFormat="1"/></cellXfs></styleSheet>')
    for i,(name,rows,widths) in enumerate(sheets):
        cols=''.join(f'<col min="{k+1}" max="{k+1}" width="{w}" customWidth="1"/>' for k,w in enumerate(widths or []))
        body=[]
        for r,row in enumerate(rows):
            cells=[]
            for c,v in enumerate(row):
                if v is None or v=='':continue
                ref=_ref(r,c)
                if isinstance(v,dt.date):cells.append(f'<c r="{ref}" s="2"><v>{(dt.datetime(v.year,v.month,v.day)-dt.datetime(1899,12,30)).days}</v></c>')
                elif isinstance(v,(int,float)) and not isinstance(v,bool):cells.append(f'<c r="{ref}"{" s=\"1\"" if r==0 else ""}><v>{v}</v></c>')
                else:cells.append(f'<c r="{ref}" t="inlineStr"{" s=\"1\"" if r==0 else ""}><is><t xml:space="preserve">{_esc(v)}</t></is></c>')
            body.append(f'<row r="{r+1}">{"".join(cells)}</row>')
        z.writestr(f'xl/worksheets/sheet{i+1}.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
                   +(f'<cols>{cols}</cols>' if cols else '')+f'<sheetData>{"".join(body)}</sheetData></worksheet>')
    z.close();return out.getvalue()
