"""Geometria de apresentação e luzes de ferrovia e semáforos, usadas no MP4 e WebGL."""
import math
import numpy as np
import cv2
from .transport import Transport,at,stations

def controller(scene):
    if not hasattr(scene,'_transport_visual'):scene._transport_visual=Transport(scene.s)
    return scene._transport_visual

def rectangle(p,h,length,width):
    n=np.array([-h[1],h[0]])
    return np.array([p+h*x+n*y for x,y in [(-length/2,-width/2),(length/2,-width/2),(length/2,width/2),(-length/2,width/2)]])

def geometry(control):
    """Retângulos físicos; links de estudo não integram o vídeo."""
    beds=[];lines=[];crosswalks=[];heads=[]
    for rail in control.rails:
        p,d=rail['p'],rail['d'];t=np.gradient(p,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9);n=np.column_stack([-t[:,1],t[:,0]])
        for a,b in zip(p,p[1:]):
            h=(b-a)/max(float(np.linalg.norm(b-a)),1e-9);beds.append(rectangle((a+b)/2,h,float(np.linalg.norm(b-a)),4.))
        for side in (-1,1):lines.append({'points':p+n*(side*rail['config'].gauge_m/2),'kind':'rail'})
        for s in np.arange(0,d[-1],max(.7,d[-1]/5000)):
            c,h=at(p,d,s);normal=np.array([-h[1],h[0]]);lines.append({'points':np.array([c-normal*1.25,c+normal*1.25]),'kind':'sleeper'})
    for signal in control.signals:
        for a in control.approaches(signal):
            c,h=a['center'],a['direction'];n=np.array([-h[1],h[0]])
            lines.append({'points':np.array([a['a'],a['b']]),'kind':'stop'})
            heads.append({'point':c-n*(a['width']/2+1),'signal':signal.id,'axis':a['axis'],'heading':h,'arm_end':c,'kind':'signal'})
            if signal.phases==3:
                c=c+h*3
                for x in np.arange(-a['width']/2+.5,a['width']/2,.9):crosswalks.append(rectangle(c+n*x,h,3.,.45))
    return {'beds':beds,'lines':lines,'crosswalks':crosswalks,'heads':heads}

def cached_geometry(scene):
    if not hasattr(scene,'_transport_geometry'):scene._transport_geometry=geometry(controller(scene))
    return scene._transport_geometry

def draw_static(scene,im,cam,width):
    if not getattr(scene.s,'railways',[]) and not getattr(scene.s,'traffic_signals',[]):return
    g=cached_geometry(scene);scale=scene.W/max(width,1)
    def screen(p):return np.clip(scene.screen(p,cam,width),-1000000,1000000).astype(np.int32)
    def visible(p):return (p[:,0].max()>-20 and p[:,0].min()<scene.W+20 and p[:,1].max()>-20 and p[:,1].min()<scene.H+20)
    for bed in g['beds']:
        q=screen(bed)
        if visible(q):
            cv2.fillPoly(im,[q],(115,109,99),cv2.LINE_AA)
            # Lastro com grão determinístico de pedras, sem arquivos temporários.
            if scale>1:
                for p in bed[::2]:cv2.circle(im,tuple(screen(p[None])[0]),max(1,int(.12*scale)),(147,140,125),-1,cv2.LINE_AA)
    for kind,col,w in [('sleeper',(65,57,48),.23),('rail',(200,205,211),.14),('stop',(244,243,230),.35)]:
        paths=[screen(r['points']) for r in g['lines'] if r['kind']==kind];paths=[p for p in paths if visible(p)]
        if paths:cv2.polylines(im,paths,False,col,max(1,min(20,round(w*scale))),cv2.LINE_AA)
    for head in g['heads']:
        cv2.line(im,tuple(screen(np.asarray([head['point']]))[0]),tuple(screen(np.asarray([head['arm_end']]))[0]),(91,101,110),max(2,round(.16*scale)),cv2.LINE_AA)
    for poly in g['crosswalks']:
        q=screen(poly)
        if visible(q):cv2.fillPoly(im,[q],(244,243,230),cv2.LINE_AA)

def lamp(im,q,color,radius=3):
    q=tuple(np.asarray(q,int));r=max(2,min(16,int(radius)));cv2.circle(im,q,r+2,tuple(int(c*.3) for c in color),-1,cv2.LINE_AA);cv2.circle(im,q,r,color,-1,cv2.LINE_AA);cv2.circle(im,q,max(1,r//3),(255,255,240),-1,cv2.LINE_AA)

def draw_dynamic(scene,im,t,cam,width):
    if not getattr(scene.s,'railways',[]) and not getattr(scene.s,'traffic_signals',[]):return
    c=controller(scene);g=cached_geometry(scene);scale=scene.W/max(width,1)
    def screen(p):return np.clip(scene.screen(np.asarray(p,float),cam,width),-1000000,1000000).astype(np.int32)
    colors={'green':(45,238,92),'amber':(255,183,35),'red':(255,42,42),'off':(74,78,80)}
    for head in g['heads']:
        p=screen([head.get('arm_end',head['point'])])[0]
        if not (-20<p[0]<scene.W+20 and -20<p[1]<scene.H+20):continue
        signal=c.by_id[head['signal']];state=c.signal_state(signal,t)[head['axis']];r=max(2,min(9,round(.3*scale)))
        cv2.rectangle(im,tuple(p- [r+2,3*r+3]),tuple(p+[r+2,3*r+3]),(24,29,33),-1)
        for i,name in enumerate(['red','amber','green']):lamp(im,p+[0,(i-1)*2*r],colors[name] if state==name else (48,48,46),r if state==name else 2)
    for part in c.train_parts(t):
        p,h=part['p'],part['heading'];q=screen(rectangle(p,h,part['length'],part['width']))
        if q[:,0].max()<0 or q[:,0].min()>scene.W or q[:,1].max()<0 or q[:,1].min()>scene.H:continue
        body=(226,175,44) if part['locomotive'] else (117,158,174) if part['model']=='passageiros' else (141,88,59)
        night=float(getattr(scene,'_night',0));body=tuple(int(x*(1-night*.55)) for x in body)
        cv2.fillPoly(im,[q+ [2,2]],(25,26,27),cv2.LINE_AA);cv2.fillPoly(im,[q],body,cv2.LINE_AA);cv2.polylines(im,[q],True,(44,45,47),max(1,round(scale*.1)),cv2.LINE_AA)
        normal=np.array([-h[1],h[0]])
        if part['locomotive']:
            glass=screen(rectangle(p+h*5,h,3.,2.5));cv2.fillPoly(im,[glass],(35,60,76),cv2.LINE_AA)
            if night>.1:
                beam=screen(np.array([p+h*9-normal,p+h*45-normal*7,p+h*45+normal*7,p+h*9+normal]));glow=im.copy();cv2.fillPoly(glow,[beam],(255,244,183),cv2.LINE_AA);cv2.addWeighted(glow,.13*night,im,1-.13*night,0,im)
                for side in (-1,1):lamp(im,screen([p+h*9+normal*side])[0],(255,247,191),max(2,.17*scale))
        elif part['model']=='passageiros':
            for along in np.arange(-5,6,2):cv2.polylines(im,[screen(rectangle(p+h*along,h,.8,2.9))],True,(43,68,82),max(1,round(scale*.12)),cv2.LINE_AA)
    # Passagem em nível: luzes alternadas e cruz de Santo André em cada aproximação.
    if getattr(scene,'network',None):
        if not hasattr(scene,'_rail_stop_heads'):scene._rail_stop_heads=Transport(scene.s,scene.network)
        transport=scene._rail_stop_heads;seen=set()
        for rows in transport.stops:
            for stop in rows:
                if stop['kind']!='rail':continue
                rail=stop['rail'];point,_=at(rail['p'],rail['d'],stop['rail_s']);key=tuple(np.round(point,1))
                if key in seen:continue
                seen.add(key);p=screen([point])[0]+[12,-12];closed=transport.rail_stop_closed(stop,t)
                cv2.line(im,tuple(p+[-4,-4]),tuple(p+[4,4]),(240,240,226),2,cv2.LINE_AA);cv2.line(im,tuple(p+[-4,4]),tuple(p+[4,-4]),(240,240,226),2,cv2.LINE_AA)
                for side in (0,1):lamp(im,p+[side*7-3,8],(255,35,30) if closed and int(t*2)%2==side else (56,41,41),2)
