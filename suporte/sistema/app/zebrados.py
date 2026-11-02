"""2.68: canalização derivada de contornos DXF; orientação não altera a rede viária."""
import hashlib,json,math,re,unicodedata
import numpy as np
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
MAX_SOURCES=200


def named_layer(name):
    text=''.join(c for c in unicodedata.normalize('NFKD',str(name).upper()) if not unicodedata.combining(c))
    words=re.findall(r'[A-Z]+',text)
    return bool(set(words)&{'ZEBRA','ZEBRADO','ZEBRADOS','ZEBRADA','ZEBRADAS'}) and not bool(set(words)&{'SEM','NAO'})


def is_source(e):return bool(e.get('closed') and e.get('role')=='sign_h' and named_layer(e.get('layer','')))


def _ring(points):
    # Identidade independente do vértice inicial e da ordem de desenho.
    q=[tuple(round(float(c),6) for c in p[:2]) for p in points]
    q=[p for i,p in enumerate(q) if i==0 or p!=q[i-1]]
    while len(q)>1 and q[-1]==q[0]:q.pop()
    if not q:return []
    def rotate(r):
        start=min(range(len(r)),key=lambda i:r[i]);return r[start:]+r[:start]
    return min(rotate(q),rotate(q[::-1]))


def source_id(e):
    body=[str(e.get('overlay','base')),str(e.get('layer','')),_ring(e['points']),sorted(_ring(h) for h in e.get('holes',[]))]
    return 'dxf-zebra-'+hashlib.sha256(json.dumps(body,separators=(',',':')).encode()).hexdigest()[:32]


class FlowIndex:
    def __init__(self,net):
        self.lines=[];self.levels=[]
        for path in getattr(net,'paths',[]):
            p=np.asarray(path.get('p',[]),float)
            if len(p)<2 or not np.isfinite(p).all():continue
            line=LineString(p)
            if line.length<.1:continue
            self.lines.append(line)
            levels={getattr(net,'edges',[])[i].get('level',0) for i in path.get('edges',[]) if 0<=i<len(getattr(net,'edges',[]))}
            self.levels.append(next(iter(levels)) if len(levels)==1 else (0 if not levels else None))
        self.tree=STRtree(self.lines)

    def nearby(self,area):
        center=area.centroid;out=[]
        for i in self.tree.query(center.buffer(50)):
            line=self.lines[int(i)];s=line.project(center);q=line.interpolate(s)
            if q.distance(center)>50:continue
            a=np.asarray(line.interpolate(max(0,s-.5)).coords[0]);b=np.asarray(line.interpolate(min(line.length,s+.5)).coords[0]);t=b-a;L=np.linalg.norm(t)
            if L<1e-8:continue
            t=t/L;angle=math.degrees(math.atan2(t[1],t[0]));point=list(q.coords[0])
            if any(math.dist(point,v['point'])<.8 and math.cos(math.radians(angle-v['heading_deg']))>.98 for v in out):continue
            out.append({'point':point,'heading_deg':angle,'distance_m':float(q.distance(center)),'level':self.levels[int(i)],'crosses':bool(line.intersects(area.buffer(-.05)))})
        out.sort(key=lambda v:v['distance_m']);return out


def describe(e,index):
    sid=source_id(e);points=np.asarray(e['points'],float);holes=[np.asarray(h,float) for h in e.get('holes',[])]
    area=Polygon(points,holes=holes)
    row={'source_id':sid,'layer':str(e.get('layer','')),'points':points.tolist(),'holes':[h.tolist() for h in holes],'status':'pending','message':'Informe os sentidos laterais ou um ângulo manual.','color':'white','angle_deg':None,'guides':[]}
    if e.get('virtual'):
        row['message']='O contorno contém fechamento virtual de uma borda aberta. Desenhe um contorno fechado válido.';return row
    if not area.is_valid or area.area<.01:
        row['message']='Contorno inválido: corrija os vértices ou desenhe um novo contorno.';return row
    if len(points)>300 or len(holes)>30 or any(len(h)>300 for h in holes):
        row['message']='Contorno muito detalhado para edição: desenhe uma área de zebrado mais simples.';return row
    nearby=index.nearby(area)
    if not nearby:return row
    reference=nearby[0];theta=math.radians(reference['heading_deg']);n=np.array([-math.sin(theta),math.cos(theta)]);c=np.asarray(area.centroid.coords[0]);sides={}
    for g in nearby:
        side=float((np.asarray(g['point'])-c)@n);key=1 if side>=0 else -1
        if key not in sides:sides[key]=g
    selected=list(sides.values());row['guides']=[{'point':v['point'],'heading_deg':v['heading_deg']} for v in selected]
    for v in nearby:
        if v['distance_m']>reference['distance_m']+3:continue
        if v['crosses'] or v['level']!=reference['level'] or abs(math.sin(math.radians(v['heading_deg']-reference['heading_deg'])))>.26:
            row['message']='Movimentos laterais ambíguos ou atravessando o contorno: confira os sentidos.';return row
    if any(abs(math.sin(math.radians(g['heading_deg']-reference['heading_deg'])))>.26 for g in selected):
        row['message']='Os fluxos laterais divergem: escolha os sentidos e o ângulo.';return row
    row['angle_deg']=((reference['heading_deg']+45+180)%360)-180
    row['color']='yellow' if len(selected)==2 and math.cos(math.radians(selected[0]['heading_deg']-selected[1]['heading_deg']))<0 else 'white'
    words=str(e.get('layer','')).upper()
    if 'AMAREL' in words or 'YELLOW' in words:row['color']='yellow'
    elif 'BRANC' in words or 'WHITE' in words:row['color']='white'
    row.update(status='automatic',message='Orientação sugerida pelos fluxos laterais; configuração editável.')
    return row


def collect(net,entities):
    entities=[e for e in entities if is_source(e)]
    if not entities:return []
    index=FlowIndex(net);seen=set();rows=[];count=0
    for e in entities:
        sid=source_id(e)
        if sid in seen:continue
        seen.add(sid);count+=1
        if len(rows)<MAX_SOURCES:rows.append(describe(e,index))
    if count>MAX_SOURCES:getattr(net,'warnings',[]).append('Zebrados: mais de 200 contornos; divida o desenho para configurar os demais.')
    return rows


def resolve(net,entities):
    """Uma derivação por fonte; configurações manuais têm precedência e podem desativar a área."""
    from .models import HatchArea
    rows=collect(net,entities);overrides={h.source_id:h for h in net.s.hatch_areas if h.source_id};paint=[];found=set()
    for row in rows:
        sid=row['source_id'];found.add(sid);h=overrides.get(sid)
        if h is not None:
            row.update(status='configured' if h.enabled else 'disabled',message='Configuração salva pelo usuário.',points=[[p.x,p.y] for p in h.points],holes=[[[p.x,p.y] for p in ring] for ring in h.holes],color=h.color,angle_deg=h.angle_deg,guides=[{'point':[g.point.x,g.point.y],'heading_deg':g.heading_deg} for g in h.flow_guides])
            if h.enabled:paint.append(h)
        elif row['status']=='automatic':
            try:paint.append(HatchArea(points=[{'x':x,'y':y} for x,y in row['points']],holes=[[{'x':x,'y':y} for x,y in ring] for ring in row['holes']],name='Zebrado '+row['layer'][:60],source_id=sid,color=row['color'],angle_deg=row['angle_deg'],world_aligned=True))
            except ValueError:row.update(status='pending',message='Área excede os limites de pintura: divida o contorno.')
        if row['status']=='pending':getattr(net,'warnings',[]).append('Zebrado '+row['layer']+': '+row['message'])
    for sid,h in overrides.items():
        if sid not in found:
            getattr(net,'warnings',[]).append('Zebrado '+h.name+': contorno DXF de origem ausente ou alterado. Confira os zebrados do DXF.')
            rows.append({'source_id':sid,'layer':h.source_layer,'points':[[p.x,p.y] for p in h.points],'holes':[], 'status':'missing','message':'Contorno de origem ausente ou alterado. Selecione o contorno atual; a configuração antiga foi preservada.','color':h.color,'angle_deg':h.angle_deg,'guides':[]})
    net.zebra_sources=rows
    return paint+[h for h in net.s.hatch_areas if not h.source_id and h.enabled]
