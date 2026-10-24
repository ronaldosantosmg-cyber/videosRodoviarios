"""Representação em planta. Dimensões ilustrativas, sem projeto de acessibilidade."""
import cv2
import numpy as np


def bridge_geometry(center, tangent, poi):
    c=np.asarray(center,float);u=np.asarray(tangent,float);u=u/max(np.linalg.norm(u),1e-9)
    a=np.deg2rad(poi.get('bridge_angle_deg',0));v=np.array([-u[1],u[0]])
    v=v*np.cos(a)+u*np.sin(a);u=np.array([v[1],-v[0]])
    span=poi.get('bridge_span_m') or 38;w=poi.get('bridge_width_m',3)
    deck=np.array([c-v*span/2-u*w/2,c+v*span/2-u*w/2,c+v*span/2+u*w/2,c-v*span/2+u*w/2])
    ramps=[];landings=[]
    for side in (-1,1):
        base=c+v*side*span/2
        if poi.get('bridge_access','ramps')=='none':continue
        flight=poi.get('ramp_flight_m',24) if poi.get('bridge_access','ramps')=='ramps' else 7
        # Four flights, linked by level landings, on each bank outside the deck.
        points=[base,base+v*side*3]
        for k in range(4):
            start=base+v*side*(3+k*3.2)+u*(flight if k%2 else 0)
            end=start+u*(flight if k%2==0 else -flight)
            points.extend([start,end]);landings.append(end)
        ramps.append(np.array(points))
    return {'deck':deck,'ramps':ramps,'landings':landings,'u':u,'v':v,'center':c,'width':w,'span':span}


def bus_geometry(center,tangent,poi):
    c=np.asarray(center,float);u=np.asarray(tangent,float);u/=max(np.linalg.norm(u),1e-9)
    if poi.get('bus_side','right')=='left':u=-u
    n=np.array([u[1],-u[0]]);L=poi.get('bus_length_m',30);d=poi.get('bus_depth_m',3);taper=15
    # User anchor is the inner edge of the bay, next to the carriageway.
    pavement=np.array([c-u*(L/2+taper),c-u*L/2+n*d,c+u*L/2+n*d,c+u*(L/2+taper)])
    platform=np.array([c-u*L/2+n*(d+.4),c+u*L/2+n*(d+.4),c+u*L/2+n*(d+2.4),c-u*L/2+n*(d+2.4)])
    return {'pavement':pavement,'platform':platform,'u':u,'n':n,'center':c,'length':L,'depth':d}


def draw_structure(im,poi,tangent,screen,pixels_per_m):
    def xy(p):return np.rint(screen(np.asarray(p,float))).astype(np.int32)
    def line(p,color,width):cv2.polylines(im,[xy(p)],False,color,max(1,round(width*pixels_per_m)),cv2.LINE_AA)
    def poly(p,color):cv2.fillPoly(im,[xy(p)],color,cv2.LINE_AA)
    c=np.array([poi['x'],poi['y']])
    if poi['kind']=='passarela':
        g=bridge_geometry(c,tangent,poi);w=g['width'];u=g['u'];v=g['v'];deck=g['deck']
        poly(deck+np.array([1.7,-2.2]),(47,54,48))
        for path in g['ramps']:
            line(path+np.array([1.7,-2.2]),(47,54,48),w+1)
            line(path,(63,70,72),w+1);line(path,(215,213,199),w)
            for a,b in zip(path[:-1],path[1:]):
                delta=b-a;length=np.linalg.norm(delta)
                if length<.2:continue
                normal=np.array([-delta[1],delta[0]])/length
                for side in (-1,1):line([a+normal*side*w/2,b+normal*side*w/2],(119,154,163),.17)
            if poi.get('bridge_access')=='stairs':
                for a,b in zip(path[:-1],path[1:]):
                    delta=b-a;length=np.linalg.norm(delta)
                    if length<5:continue
                    n=np.array([-delta[1],delta[0]])/length
                    for f in np.arange(.05,.99,.05):line([a+delta*f-n*w/2,a+delta*f+n*w/2],(126,133,130),.12)
        for end in (-1,1):
            base=c+v*end*(g['span']/2-2)
            poly(np.array([base-u*1.1-v*.65,base+u*1.1-v*.65,base+u*1.1+v*.65,base-u*1.1+v*.65]),(130,137,131))
        poly(deck,(225,223,207))
        for side in (-1,1):line([c-v*g['span']/2+u*side*w/2,c+v*g['span']/2+u*side*w/2],(112,151,163),.2)
        for f in np.arange(-g['span']/2,g['span']/2,1.5):line([c+v*f-u*w/2,c+v*f+u*w/2],(186,190,181),.08)
        return c+v*(g['span']/2+5)
    if poi['kind']=='onibus':
        g=bus_geometry(c,tangent,poi);u=g['u'];n=g['n'];L=g['length'];d=g['depth']
        poly(g['pavement'],(75,79,81));poly(g['platform'],(196,190,173))
        line(g['pavement'][[0,1,2,3]],(238,238,224),.18)
        for a in np.arange(-L/2-12,L/2+12,4):line([c+u*a,c+u*(a+2)],(243,239,205),.17)
        stop=c+n*d*.5
        poly(np.array([stop-u*5.5-n*1.2,stop+u*5.5-n*1.2,stop+u*5.5+n*1.2,stop-u*5.5+n*1.2]),(223,174,64))
        line([stop+u*4-n,stop+u*4+n],(50,77,92),.8)
        shelter=c+n*(d+1.4)
        poly(np.array([shelter-u*3-n*.8,shelter+u*3-n*.8,shelter+u*3+n*.8,shelter-u*3+n*.8]),(90,151,168))
        return c+n*(d+5)
    return c
