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
        points=[base,base+v*side*3];pitch=max(3.2,w+1.4)   # lances separados por vão visível (antes 3,2 m ≈ largura → fundiam)
        for k in range(4):
            start=base+v*side*(3+k*pitch)+u*(flight if k%2 else 0)
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


def draw_structure(im,poi,tangent,screen,pixels_per_m,realista=False):
    def xy(p):return np.rint(screen(np.asarray(p,float))).astype(np.int32)
    def line(p,color,width):cv2.polylines(im,[xy(p)],False,color,max(1,round(width*pixels_per_m)),cv2.LINE_AA)
    def poly(p,color):cv2.fillPoly(im,[xy(p)],color,cv2.LINE_AA)
    c=np.array([poi['x'],poi['y']])
    if poi['kind']=='passarela':
        g=bridge_geometry(c,tangent,poi);w=g['width'];u=g['u'];v=g['v'];deck=g['deck']
        if realista:
            try:return _passarela_real(im,poi,g,screen,pixels_per_m,c)
            except Exception:pass
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
        _postes(im,poi,g,xy,lambda wm:max(1,round(wm*pixels_per_m)),c)
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


def _passarela_real(im,poi,g,screen,ppm,c):
    """2.51: passarela com concreto texturizado (ancorado no mundo), sombra suave, juntas, meios-fios, guarda-corpo com montantes, tela de proteção e degraus com espelho.
    Só muda a aparência: a geometria vem de bridge_geometry (inalterada). Devolve o mesmo ponto de ancoragem do desenho simples."""
    from . import relevo
    H,W=im.shape[:2];w=g['width'];u=g['u'];v=g['v'];deck=g['deck'];span=g['span']
    xy=lambda p:np.rint(screen(np.asarray(p,float))).astype(np.int32)
    th=lambda wm:max(1,int(round(wm*ppm)))
    def mpoly(pts):
        m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[xy(pts)],255,cv2.LINE_AA);return m>127
    def mline(pts,wm):
        m=np.zeros((H,W),np.uint8);cv2.polylines(m,[xy(pts)],False,255,th(wm),cv2.LINE_AA);return m>127
    # sombra suave (duas camadas, deslocada para sudeste)
    sh=np.zeros((H,W),np.float32);off=np.array([1.7,-2.2])
    cv2.fillPoly(sh,[xy(deck+off)],1.0,cv2.LINE_AA)
    for path in g['ramps']:cv2.polylines(sh,[xy(path+off)],False,1.0,th(w+1),cv2.LINE_AA)
    k=max(3,int(ppm*1.2))|1;sh=cv2.GaussianBlur(sh,(k,k),0)
    base=im.astype(np.float32);im[:]=np.clip(base*(1-.38*sh[...,None]),0,255).astype(np.uint8)
    # corpo de concreto: rampas (laje) + tabuleiro
    laje=np.zeros((H,W),bool)
    for path in g['ramps']:laje|=mline(path,w+.5)
    laje|=mpoly(deck)
    im[laje]=(176,174,168)
    relevo.texturizar_tela(im,laje,screen,'novo',seed=23)
    # meios-fios (laterais mais escuros) nas rampas e no tabuleiro
    for path in g['ramps']:
        for a,b in zip(path[:-1],path[1:]):
            d=b-a;L=np.linalg.norm(d)
            if L<.2:continue
            n=np.array([-d[1],d[0]])/L
            for sd in(-1,1):cv2.polylines(im,[xy([a+n*sd*w/2,b+n*sd*w/2])],False,(112,112,108),th(.22),cv2.LINE_AA)
    for sd in(-1,1):cv2.polylines(im,[xy([c-v*span/2+u*sd*w/2,c+v*span/2+u*sd*w/2])],False,(112,112,108),th(.25),cv2.LINE_AA)
    # juntas de dilatação do tabuleiro (a cada 12 m) e topo/pé das rampas
    for f in np.arange(-span/2,span/2+.1,12.):cv2.polylines(im,[xy([c+v*f-u*w/2,c+v*f+u*w/2])],False,(70,70,68),th(.07),cv2.LINE_AA)
    # patamares de giro e setas de declive (rampa i≤8,33%: seta aponta para baixo, ao chão)
    if poi.get('bridge_access','ramps')=='ramps':
        for path in g['ramps']:
            for q in path[2::2]:
                cv2.polylines(im,[xy(np.array([q-u*w/2-v*w/2,q+u*w/2-v*w/2,q+u*w/2+v*w/2,q-u*w/2+v*w/2]))],True,(96,96,92),th(.06),cv2.LINE_AA)
            for a,b in zip(path[2:-1:2],path[3::2]):
                d=b-a;L=np.linalg.norm(d)
                if L<8:continue
                t=d/L;n=np.array([-t[1],t[0]])
                for f in np.arange(4,L-3,6.):
                    c0=a+t*f;tip=c0-t*1.0;cv2.polylines(im,[xy([c0+t*1.0+n*.5,tip,c0+t*1.0-n*.5])],False,(120,120,116),th(.08),cv2.LINE_AA)
    # degraus (se escada): borda clara + espelho escuro, sempre perpendiculares ao lance
    if poi.get('bridge_access')=='stairs':
        for path in g['ramps']:
            for a,b in zip(path[:-1],path[1:]):
                d=b-a;L=np.linalg.norm(d)
                if L<5:continue
                n=np.array([-d[1],d[0]])/L
                for f in np.arange(.05,.99,.05):
                    q=a+d*f;cv2.polylines(im,[xy([q-n*w/2,q+n*w/2])],False,(205,203,196),th(.08),cv2.LINE_AA)
                    q2=q+d*.012;cv2.polylines(im,[xy([q2-n*w/2,q2+n*w/2])],False,(96,96,92),th(.05),cv2.LINE_AA)
    # tela de proteção (malha fina semitransparente) sobre o tabuleiro: duas faixas laterais
    ov=im.copy()
    for sd in(-1,1):
        for f in np.arange(-span/2,span/2,.5):
            q=c+v*f+u*sd*w/2;cv2.polylines(ov,[xy([q,q+v*.5+u*sd*.0])],False,(150,170,176),1,cv2.LINE_AA)
    cv2.addWeighted(ov,.45,im,.55,0,im)
    # guarda-corpo: corrimão contínuo + montantes a cada 2 m
    for sd in(-1,1):
        cv2.polylines(im,[xy([c-v*span/2+u*sd*w/2,c+v*span/2+u*sd*w/2])],False,(118,150,160),th(.12),cv2.LINE_AA)
        for f in np.arange(-span/2,span/2+.01,2.):
            x,y=xy(c+v*f+u*sd*w/2);cv2.circle(im,(int(x),int(y)),max(1,th(.1)),(70,82,88),-1,cv2.LINE_AA)
    for path in g['ramps']:
        for a,b in zip(path[:-1],path[1:]):
            d=b-a;L=np.linalg.norm(d)
            if L<.2:continue
            n=np.array([-d[1],d[0]])/L
            for sd in(-1,1):cv2.polylines(im,[xy([a+n*sd*w/2,b+n*sd*w/2])],False,(118,150,160),th(.12),cv2.LINE_AA)
    # apoios (sapatas/pilares) nas cabeceiras
    for end in(-1,1):
        base_=c+v*end*(span/2-2)
        q=np.array([base_-u*1.1-v*.65,base_+u*1.1-v*.65,base_+u*1.1+v*.65,base_-u*1.1+v*.65])
        m=mpoly(q);im[m]=(150,150,145);relevo.texturizar_tela(im,m,screen,'novo',seed=29)
        cv2.polylines(im,[xy(q)],True,(88,88,84),th(.1),cv2.LINE_AA)
    _postes(im,poi,g,xy,th,c)
    return c+v*(span/2+5)

def poste_pontos(g,modo):
    """posições (x,y) dos postes e direção do braço (para o lado externo da rampa). Mesma geometria da passarela; só desenho."""
    out=[]
    if modo in('landings','both'):
        for path in g['ramps']:
            mu=np.mean([x@g['u'] for x in path])
            for q in path[3::2]:                                  # fim de cada lance = patamar; poste fora da laje
                sg=1 if q@g['u']>mu else -1
                out.append((np.asarray(q,float)+g['u']*sg*(g['width']/2+.5),g['u']*sg))
    if modo=='both':
        for end in(-1,1):
            base=g['center']+g['v']*end*(g['span']/2-.5)
            for sd in(-1,1):out.append((base+g['u']*sd*(g['width']/2+.6),-g['u']*sd))
    return out

def _postes(im,poi,g,xy,th,c):
    modo=poi.get('bridge_poles','none')
    if modo=='none':return
    for p,arm in poste_pontos(g,modo):
        base=np.asarray(p,float);head=base-arm*1.8
        H,W=im.shape[:2];m=np.zeros((H,W),np.float32);cv2.circle(m,tuple(int(x) for x in xy(head)),max(4,th(5.0)),1.0,-1,cv2.LINE_AA)   # área iluminada (suave)
        k=max(3,th(3.0))|1;m=cv2.GaussianBlur(m,(k,k),0)*.28
        im[:]=np.clip(im*(1-m[...,None])+np.array([236,226,170],np.float32)*m[...,None],0,255).astype(np.uint8)
        cv2.polylines(im,[xy([base,base+np.array([3.0,-4.0])])],False,(46,52,46),max(2,th(.28)),cv2.LINE_AA)        # sombra do fuste
        cv2.polylines(im,[xy([base,head])],False,(92,96,98),max(2,th(.22)),cv2.LINE_AA)                             # braço
        cv2.circle(im,tuple(int(x) for x in xy(head)),max(3,th(.55)),(238,236,214),-1,cv2.LINE_AA)                   # luminária
        cv2.circle(im,tuple(int(x) for x in xy(head)),max(3,th(.55)),(70,74,76),1,cv2.LINE_AA)
        cv2.circle(im,tuple(int(x) for x in xy(base)),max(3,th(.42)),(64,68,70),-1,cv2.LINE_AA)                      # base do poste
