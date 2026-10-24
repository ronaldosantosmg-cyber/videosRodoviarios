"""Integra os controles à câmera ilustrativa da cabine e desenha os equipamentos em perspectiva."""
import math
import numpy as np
import cv2
from .transport import Transport
from .vehicle_motion import PROFILES
from .transport_render import controller,cached_geometry,rectangle


def prepare_camera(cabin):
    sc=cabin.sc
    if not any(r.enabled for r in sc.s.railways) and not any(s.enabled for s in sc.s.traffic_signals):return
    controls=Transport(sc.s,sc.network);sim=sc.traffic();d=cabin.d0;speed=0.;clock=[];dt=.2
    for k in range(int(math.ceil(cabin.c.duration_s/dt))+2):
        t=k*dt;clock.append(d);gap=math.inf
        if sim:
            for vid,path,station,_,_ in sim.state(t):
                if path==cabin.i and station>d+1:
                    lead_type=sim.info[vid][1];lead_half=PROFILES.get(lead_type,PROFILES['car'])[0]/2
                    gap=min(gap,station-d-2.25-lead_half)
        actor={'p':cabin.i,'s':d,'L':4.5,'lc':None}
        gap=min(gap,controls.stop_gap(actor,t,gap),controls.stop_gap(actor,t+dt,gap))
        speed=min(cabin.speed,speed+1.2*dt,math.sqrt(max(0.,2*2.*(gap-.7))))
        travel=min(speed*dt,max(0.,gap-.7));d=min(cabin.path['length'],d+travel)
    cabin.control_clock=np.array(clock);cabin.reaches_end=bool(clock[-1]>=cabin.path['length']-.5)


def draw(cabin,im,cam,pos,t):
    sc=cabin.sc
    if not sc.s.railways and not sc.s.traffic_signals:return
    c=controller(sc);g=cached_geometry(sc)
    def project(points,height=0.):
        points=np.asarray(points,float);z=np.full(len(points),height)
        if cabin.terrain is not None:z+=cabin.terrain.sample(points[:,0],points[:,1])
        world=np.column_stack([points,z]);return cabin.project2(world) if cabin.terrain is not None else cabin.project(world,cam)
    def polygon(points,color,height=0):
        if np.min(np.linalg.norm(points-pos,axis=1))>400:return
        q,depth=project(points,height)
        if not np.isfinite(q).all() or (depth<1).any():return
        if cabin.terrain is not None:cabin._ztest_fill(im,q,float(depth.min()),color)
        else:cv2.fillPoly(im,[np.clip(q,-100000,100000).astype(np.int32)],color,cv2.LINE_AA)
    for bed in g['beds']:polygon(bed,(116,109,99),.03)
    for poly in g['crosswalks']:polygon(poly,(244,242,227),.05)
    for line in g['lines']:
        p=line['points']
        if np.min(np.linalg.norm(p-pos,axis=1))>350:continue
        q,z=project(p,.08)
        for i in range(1,len(q)):
            if min(z[i-1],z[i])>1 and np.isfinite(q[i-1:i+1]).all():cv2.line(im,tuple(np.clip(q[i-1],-100000,100000).astype(int)),tuple(np.clip(q[i],-100000,100000).astype(int)),(195,199,202) if line['kind']=='rail' else (236,235,222) if line['kind']=='stop' else (72,58,44),2,cv2.LINE_AA)
    colors={'red':(255,38,38),'amber':(255,182,32),'green':(36,235,90),'off':(58,61,64)}
    for head in g['heads']:
        q,z=project([head['point']],4.5)
        if z[0]<1 or not np.isfinite(q).all():continue
        point=np.round(q[0]).astype(int)
        if not(0<=point[0]<sc.W and 0<=point[1]<sc.H):continue
        radius=max(2,min(12,round(cabin.f*.18/max(z[0],1))))
        cv2.rectangle(im,tuple(point-[radius+2,3*radius+3]),tuple(point+[radius+2,3*radius+3]),(18,24,27),-1)
        state=c.signal_state(c.by_id[head['signal']],t)[head['axis']]
        for i,name in enumerate(['red','amber','green']):cv2.circle(im,tuple(point+[0,(i-1)*2*radius]),radius,colors[name] if state==name else (47,48,45),-1,cv2.LINE_AA)
    for part in sorted(c.train_parts(t),key=lambda p:-float(np.linalg.norm(p['p']-pos))):
        foot=rectangle(part['p'],part['heading'],part['length'],part['width']);q,z=project(foot,0.);top,zt=project(foot,3.8)
        if (z<1).any() or (zt<1).any() or not np.isfinite(q).all() or not np.isfinite(top).all():continue
        points=np.vstack([q,top]).astype(np.int32);color=(224,174,42) if part['locomotive'] else (122,157,170) if part['model']=='passageiros' else (141,88,58)
        cv2.fillConvexPoly(im,cv2.convexHull(points),tuple(int(v*.65) for v in color),cv2.LINE_AA);cv2.fillConvexPoly(im,points[4:],color,cv2.LINE_AA)
        if part['locomotive']:
            h=part['heading'];n=np.array([-h[1],h[0]])
            for side in (-1,1):
                lamp=part['p']+h*9+n*side;q,z=project([lamp],2.)
                if z[0]>1 and np.isfinite(q).all():cv2.circle(im,tuple(np.clip(q[0],-100000,100000).astype(int)),max(2,min(12,int(cabin.f*.14/z[0]))),(255,248,200),-1,cv2.LINE_AA)
