"""1.10: anotações do vídeo — marcos de km inicial/final, seta de sentido do estaqueamento e cidades próximas."""
import math
import numpy as np
import cv2
from PIL import Image,ImageDraw

def _text_patch(text,font,size,bold,fill=(255,255,255),stroke=(8,22,35),pad=4):
    f=font(size,bold);probe=ImageDraw.Draw(Image.new('L',(1,1)));w=int(probe.textlength(text,font=f))+2*pad+4;h=int(f.size*1.45)+2*pad
    img=Image.new('RGBA',(max(1,w),max(1,h)),(0,0,0,0));d=ImageDraw.Draw(img)
    d.text((pad+2,pad),text,font=f,fill=fill+(255,),stroke_width=max(1,int(size/9)),stroke_fill=stroke+(255,))
    return np.array(img)

def _blit(im,patch,x,y,top=0,bottom=None,alpha=1.):
    H,W=im.shape[:2];bottom=H if bottom is None else bottom
    h,w=patch.shape[:2];x=int(round(x));y=int(round(y))
    x0,y0=max(0,x),max(top,y);x1,y1=min(W,x+w),min(bottom,y+h)
    if x1<=x0 or y1<=y0:return
    p=patch[y0-y:y1-y,x0-x:x1-x].astype(np.float32);a=p[:,:,3:4]/255*alpha
    roi=im[y0:y1,x0:x1].astype(np.float32);im[y0:y1,x0:x1]=(roi*(1-a)+p[:,:,:3]*a).astype(np.uint8)

def km_marker_items(scene):
    """Pontos do km inicial e final (no CRS) com os textos."""
    s=scene.s;st=scene.stationing;out=[]
    from .chainage import fmt
    if scene.km_active:
        lo,hi=st.km_range()
        for km,tag in [(s.km_start_m,'Início'),(s.km_end_m,'Fim')]:
            if lo-1<=km<=hi+1:out.append({'xy':st.point(km),'name':f'{tag} • km {fmt(km)}','tag':tag})
    else:
        a=scene.axis[0];b=scene.axis[-1]
        out=[{'xy':np.asarray(a,float),'name':f'Início • km {fmt(s.km_start_m)}','tag':'Início'},{'xy':np.asarray(b,float),'name':f'Fim • km {fmt(s.km_end_m)}','tag':'Fim'}]
    for o in out:o['chain']=float(scene.ch[scene.tree.query(o['xy'])[1]])
    return out

def draw_km_markers(im,scene,cam,width,progress,font,top,bottom):
    sc=scene.scale
    if not hasattr(scene,'_km_items'):scene._km_items=km_marker_items(scene)
    for o in scene._km_items:
        if o['chain']>progress*scene.length+25:continue
        q=scene.screen(o['xy'][None],cam,width)[0]
        if not(0<q[0]<scene.W and top<q[1]<bottom):continue
        x,y=q;r=max(6,round(13*sc))
        # Haste com bandeira (marco), tamanho fixo na tela.
        pole=int(46*sc)
        cv2.line(im,(int(x),int(y)),(int(x),int(y)-pole),(8,22,35),max(3,round(6*sc)),cv2.LINE_AA)
        cv2.line(im,(int(x),int(y)),(int(x),int(y)-pole),(255,214,107),max(1,round(3*sc)),cv2.LINE_AA)
        cv2.circle(im,(int(x),int(y)),r,(8,22,35),-1,cv2.LINE_AA);cv2.circle(im,(int(x),int(y)),max(3,r-max(2,round(3*sc))),(255,214,107),-1,cv2.LINE_AA)
        key=('km',o['name'],round(sc,3))
        cache=scene.__dict__.setdefault('_ann_cache',{})
        if key not in cache:
            f=font(20*sc,True);probe=ImageDraw.Draw(Image.new('L',(1,1)));pad=int(10*sc);tw=int(probe.textlength(o['name'],font=f))+2*pad;th=int(f.size*1.5)+pad
            img=Image.new('RGBA',(tw,th),(0,0,0,0));d=ImageDraw.Draw(img)
            d.rounded_rectangle((0,0,tw-1,th-1),radius=int(8*sc),fill=(8,22,35,236),outline=(255,214,107,255),width=max(1,round(2*sc)))
            d.text((pad,pad//2+int(2*sc)),o['name'],font=f,fill=(255,233,168,255));cache[key]=np.array(img)
        p=cache[key];_blit(im,p,x+6*sc,y-pole-p.shape[0]/2,top,bottom)

def direction_badge(im,scene,cam,width,font,top):
    """Seta no topo do quadro apontando para onde o km cresce, na posição atual da câmera."""
    sc=scene.scale;st=scene.stationing
    i=int(scene.tree.query(cam)[1]);a=scene.dense[max(0,i-3)];b=scene.dense[min(len(scene.dense)-1,i+3)]
    v=(b-a)*(st.direction if scene.km_active else 1)
    n=float(np.linalg.norm(v))
    if n<1e-6:return
    q=scene.screen(np.array([cam,cam+v/n*width*.05]),cam,width);d=q[1]-q[0];L=float(np.linalg.norm(d))
    if L<1e-6:return
    d/=L
    cx=scene.W/2;cy=top+int(44*sc)
    key=('badge',round(sc,3))
    cache=scene.__dict__.setdefault('_ann_cache',{})
    if key not in cache:
        f=font(18*sc,True);text='Sentido do estaqueamento (km crescente)';probe=ImageDraw.Draw(Image.new('L',(1,1)))
        tw=int(probe.textlength(text,font=f));w=tw+int(86*sc);h=int(52*sc)
        img=Image.new('RGBA',(w,h),(0,0,0,0));dr=ImageDraw.Draw(img)
        dr.rounded_rectangle((0,0,w-1,h-1),radius=h//2,fill=(8,22,35,226),outline=(255,214,107,255),width=max(1,round(2*sc)))
        dr.text((int(70*sc),(h-f.size*1.2)/2),text,font=f,fill=(255,233,168,255));cache[key]=np.array(img)
    p=cache[key];x0=cx-p.shape[1]/2;y0=cy-p.shape[0]/2;_blit(im,p,x0,y0)
    # Seta girada dentro do círculo à esquerda do texto.
    ax=x0+int(34*sc);ay=cy;R=18*sc;nrm=np.array([-d[1],d[0]])
    tip=np.array([ax,ay])+d*R;tail=np.array([ax,ay])-d*R
    head=[tip,tip-d*R*.8+nrm*R*.55,tip-d*R*.8-nrm*R*.55]
    cv2.line(im,tuple(np.int32(tail)),tuple(np.int32(tip-d*R*.5)),(255,214,107),max(2,round(4*sc)),cv2.LINE_AA)
    cv2.fillPoly(im,[np.int32(head)],(255,214,107),cv2.LINE_AA)

def draw_cities(im,scene,cam,width,font,top,bottom):
    s=scene.s
    if not s.cities_show or not s.cities:return
    sc=scene.scale;W=scene.W;cache=scene.__dict__.setdefault('_ann_cache',{});edge=[]
    for c in s.cities:
        if not c.show:continue
        xy=np.array([c.point.x,c.point.y]);q=scene.screen(xy[None],cam,width)[0];dist=float(np.linalg.norm(xy-cam))
        if 0<q[0]<W and top<q[1]<bottom:
            key=('city',c.name,round(sc,3))
            if key not in cache:cache[key]=_text_patch(c.name,font,26*sc,True)
            cv2.circle(im,(int(q[0]),int(q[1])),max(4,round(9*sc)),(8,22,35),-1,cv2.LINE_AA);cv2.circle(im,(int(q[0]),int(q[1])),max(2,round(6*sc)),(255,255,255),-1,cv2.LINE_AA)
            p=cache[key];_blit(im,p,q[0]+12*sc,q[1]-p.shape[0]/2,top,bottom)
        elif dist<=s.cities_radius_km*1000:edge.append((dist,c,q))
    # Fora do quadro: indicador na borda apontando a direção da cidade, com a distância.
    top2=top+int(84*sc) if s.direction_badge else top
    for dist,c,q in sorted(edge,key=lambda e:e[0])[:4]:
        center=np.array([W/2,(top2+bottom)/2]);d=q-center;n=float(np.linalg.norm(d))
        if n<1e-6:continue
        d/=n;mx=W/2-70*sc;my=(bottom-top2)/2-46*sc
        k=min(mx/max(abs(d[0]),1e-6),my/max(abs(d[1]),1e-6));p0=center+d*k
        km_txt=f'{dist/1000:.1f}'.replace('.',',')+' km'
        key=('cityedge',c.name,km_txt,round(sc,3))
        if key not in cache:cache[key]=_text_patch(f'{c.name} • {km_txt}',font,20*sc,True,(234,244,248))
        nrm=np.array([-d[1],d[0]]);R=14*sc;tip=p0+d*R
        cv2.fillPoly(im,[np.int32([tip+d*3*sc,tip-d*R*1.4+nrm*R,tip-d*R*1.4-nrm*R])],(8,22,35),cv2.LINE_AA)
        cv2.fillPoly(im,[np.int32([tip,tip-d*R*1.2+nrm*R*.8,tip-d*R*1.2-nrm*R*.8])],(234,244,248),cv2.LINE_AA)
        p=cache[key];lx=p0[0]-d[0]*R*2-(p.shape[1] if d[0]>0 else 0)*(abs(d[0])>.3)-(p.shape[1]/2 if abs(d[0])<=.3 else 0)
        ly=p0[1]-d[1]*R*2.2-p.shape[0]/2
        _blit(im,p,float(np.clip(lx,8,W-p.shape[1]-8)),float(np.clip(ly,top2+4,bottom-p.shape[0]-4)),top,bottom)
