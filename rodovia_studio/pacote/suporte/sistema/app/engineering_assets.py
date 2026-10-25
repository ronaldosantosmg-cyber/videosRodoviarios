"""Interferências CAD e superfícies ilustrativas locais; sem inferir cotas ausentes."""
import math
import numpy as np
from shapely.geometry import LineString,Polygon


def oae_grade_separated(settings,point,road_heading,rail_heading,road_level,rail_level):
    if road_level!=rail_level:return True
    # Nível categórico e cota em metros não são somados ou convertidos entre si.
    if road_level!=0 or rail_level!=0:return False
    for mark in getattr(settings,'oae_marks',[]):
        if abs(mark.level_m)<.1:continue
        a=np.array([mark.start.x,mark.start.y]);b=np.array([mark.end.x,mark.end.y]);v=b-a;length=np.linalg.norm(v)
        if length<.1:continue
        footprint=Polygon([(p.x,p.y) for p in mark.polygon]) if mark.polygon else LineString([a,b]).buffer(mark.width_m/2,cap_style=2)
        if not footprint.is_valid:footprint=footprint.buffer(0)
        if not footprint.covers(point):continue
        direction=v/length;road=abs(float(direction@road_heading));rail=abs(float(direction@rail_heading))
        if (road>.9 and road-rail>.02) or (rail>.9 and rail-road>.02):return True
    return False


def draw_map(scene,image,cam,width):
    """Símbolos e texturas locais em planta e MP4, ancorados nas feições."""
    import cv2
    from .asset_catalog import ASSET_ROLES,CATALOG,image as texture_image
    scale=scene.W/max(float(width),1.);cache={}
    def screen(p):return np.clip(scene.screen(np.asarray(p,float),cam,width),-1000000,1000000).astype(np.int32)
    for feature in scene.items:
        role=feature['role'];key=feature.get('asset_material')
        if role not in ASSET_ROLES and not (role in ('cut','fill') and key=='gabion'):continue
        points=feature['points'];q=screen(points)
        if not len(q) or q[:,0].max()<-20 or q[:,0].min()>scene.W+20 or q[:,1].max()<-20 or q[:,1].min()>scene.H+20:continue
        row=CATALOG.get(key) or CATALOG.get(role)
        if row is None:continue
        color=tuple(int(row['color'][i:i+2],16) for i in (1,3,5))
        if feature.get('closed') and len(q)>=3:
            x0,y0=np.maximum(q.min(0),[0,0]);x1,y1=np.minimum(q.max(0)+1,[scene.W,scene.H])
            if x1>x0 and y1>y0:
                mask=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillPoly(mask,[q-[x0,y0]],255)
                for hole in feature.get('holes',[]):cv2.fillPoly(mask,[screen(hole)-[x0,y0]],0)
                if row['id'] not in cache:cache[row['id']]=texture_image(row['id'],128)
                tex=cache[row['id']];Y,X=np.indices(mask.shape)
                tile=tex[(Y+y0-q[0,1])%128,(X+x0-q[0,0])%128]
                roi=image[y0:y1,x0:x1];roi[mask>0]=tile[mask>0]
            cv2.polylines(image,[q],True,tuple(int(v*.6) for v in color),max(1,min(4,round(.15*scale))),cv2.LINE_AA)
        elif len(q)>1:
            cv2.polylines(image,[q],False,(35,40,44),max(2,min(10,round(.35*scale)+2)),cv2.LINE_AA)
            cv2.polylines(image,[q],False,color,max(1,min(8,round(.25*scale))),cv2.LINE_AA)
            if role=='railway':
                from .transport import at,stations
                d=stations(points)
                for station in np.arange(0,d[-1],max(1.,d[-1]/2000)):
                    c,h=at(points,d,station);n=np.array([-h[1],h[0]])
                    a,b=screen([c-n*1.2,c+n*1.2]);cv2.line(image,tuple(a),tuple(b),(78,66,52),max(1,round(.16*scale)),cv2.LINE_AA)
        if width>5000:continue
        # Símbolos de cadastro: sem inventar coordenadas ou profundidades reais.
        positions=[q[0]] if not feature.get('closed') else [q.mean(0).astype(int)]
        for center in positions:
            x,y=map(int,center);r=max(3,min(10,round(1.3*scale)))
            if role=='vegetation':
                cv2.circle(image,(x,y),r+2,(42,79,38),-1,cv2.LINE_AA);cv2.circle(image,(x-r//3,y-r//3),r,color,-1,cv2.LINE_AA)
            elif role in ('pole','electric'):
                cv2.circle(image,(x,y),r,(75,75,70),-1,cv2.LINE_AA);cv2.line(image,(x-r-2,y),(x+r+2,y),color,2,cv2.LINE_AA)
            elif role=='tower':
                poly=np.array([[x,y-r],[x-r,y+r],[x+r,y+r]],np.int32);cv2.polylines(image,[poly],True,color,2,cv2.LINE_AA);cv2.line(image,(x-r,y+r),(x+r//2,y),color,1)
            elif role=='radar':
                cv2.rectangle(image,(x-r,y-r//2),(x+r,y+r//2),color,-1);cv2.line(image,(x,y),(x,y+r*2),color,2)
            elif role in ('gas','fiber'):
                cv2.circle(image,(x,y),r+2,(32,37,42),-1,cv2.LINE_AA);cv2.putText(image,'G' if role=='gas' else 'F',(x-r//2,y+r//2),cv2.FONT_HERSHEY_SIMPLEX,.35,color,1,cv2.LINE_AA)


def asset_meshes(items,local,role_colors=None):
    """Modelos ilustrativos com cotas padrão identificadas; nenhuma cota é tratada como levantamento."""
    from .asset_catalog import ASSET_ROLES,CATALOG,DEFAULT
    import shapely
    grouped={};labels={}
    def add(role,layer,points,material):
        k=(role,layer,material);grouped.setdefault(k,[]).extend(points.ravel().tolist());labels[k]={'role':role,'layer':layer,'asset_material':material,'name':layer+' · dimensões ilustrativas','illustrative_dimensions':True,'color':(role_colors or {}).get(role) or CATALOG[material]['color'],'texture_pattern':CATALOG[material]['pattern']}
    def prism(role,layer,a,b,width,height,material,bottom_height=0.):
        delta=b-a;n=np.array([-delta[1],delta[0]]);n=n/max(np.linalg.norm(n),1e-9)*width/2
        base=np.array([a-n,b-n,b+n,a+n]);top=local(base,height);bottom=local(base,bottom_height+.03)
        triangles=[top[[0,1,2]],top[[0,2,3]]]
        for i in range(4):j=(i+1)%4;triangles.extend([np.array([bottom[i],bottom[j],top[j]]),np.array([bottom[i],top[j],top[i]])])
        add(role,layer,np.concatenate(triangles),material)
    budget=0;tree_limit=max(8,1800//max(1,sum(e['role']=='vegetation' for e in items)))
    for feature in items:
        role=feature['role'];p=feature['points'];layer=feature.get('layer','');material=feature.get('asset_material') or DEFAULT.get(role)
        if role not in ASSET_ROLES or material not in CATALOG:continue
        if role in ('building','erosion','anchored_wall','earthwork') and feature.get('closed') and len(p)>=3:
            poly=Polygon(p,holes=feature.get('holes',[])).buffer(0)
            height=float(feature.get('height_m',6.)) if role=='building' else 3. if role=='anchored_wall' else .05
            for triangle in shapely.constrained_delaunay_triangles(poly).geoms:add(role,layer,local(np.asarray(triangle.exterior.coords)[:3],height),material)
            if role in ('building','anchored_wall'):
                for a,b in zip(p,np.roll(p,-1,axis=0)):prism(role,layer,a,b,.12,height,feature.get('wall_material',material) if role=='building' else material)
        elif role=='vegetation':
            candidates=p[:1]
            if feature.get('closed') and len(p)>=3:
                poly=Polygon(p,holes=feature.get('holes',[])).buffer(0);x0,y0,x1,y1=poly.bounds;step=max(10.,math.sqrt(max(poly.area,1)/tree_limit))
                X,Y=np.meshgrid(np.arange(x0+step/2,x1,step),np.arange(y0+step/2,y1,step));candidates=np.column_stack([X.ravel(),Y.ravel()]);candidates=candidates[shapely.contains_xy(poly,candidates[:,0],candidates[:,1])][:tree_limit]
            for center in candidates:
                angles=np.arange(9)*math.pi/4;ring=center+np.column_stack([np.cos(angles),np.sin(angles)])*2.4;height=float(feature.get('height_m',6.));tip=local(center[None],height)[0];base=local(ring,height*.25)
                add(role,layer,np.concatenate([np.array([base[i],base[i+1],tip]) for i in range(8)]),material)
                prism(role,layer,center+[-.1,0],center+[.1,0],.25,min(2.,height*.35),'wood')
        elif role in ('gas','fiber','electric','railway') and len(p)>1:
            height=float(feature.get('height_m',2. if material=='fence' else 8.)) if role=='electric' else .18;width=.15 if role!='railway' else 1.6
            for a,b in zip(p,p[1:]):
                if np.linalg.norm(b-a)>.01:prism(role,layer,a,b,width,height,material,max(0,height-.15) if role=='electric' and material!='fence' else 0.)
            if role=='electric':
                for center in p[::max(1,len(p)//100)]:prism('pole',layer,center+[-.1,0],center+[.1,0],.25,height,'pole')
        elif role in ('pole','tower','radar'):
            center=p[0];height={'pole':8.,'tower':20.,'radar':3.}[role];prism(role,layer,center+[-.1,0],center+[.1,0],.3,height,material)
            if role in ('radar','tower'):prism(role,layer,center+[-1.,0],center+[1.,0],.8,height,material)
        budget=sum(len(v)//3 for v in grouped.values())
        if budget>300000:raise ValueError('Interferências excedem o orçamento 3D; divida o trecho ou oculte camadas.')
    return [dict(labels[k],id='asset-'+str(i),positions=value) for i,(k,value) in enumerate(grouped.items())]
