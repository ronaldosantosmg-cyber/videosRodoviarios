"""1.35: obras do PER no vídeo — faixa colorida do km inicial ao final (por tipo) e linha do tempo pelo cronograma.

Só atua com per_display='trecho' ou schedule_mode='linha_do_tempo' (projetos anteriores ficam com per_display='chamada'
e schedule_mode='off': vídeo idêntico)."""
import datetime as dt
import numpy as np,cv2
from PIL import Image,ImageDraw
from .obras import WORK_STYLE,status,schedule_range,date_label

def active(s):return bool(s.works) and (getattr(s,'per_display','chamada')=='trecho' or getattr(s,'schedule_mode','off')=='linha_do_tempo')

def _rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))

def prepare(scene):
    """Polilinha (mundo) de cada obra ao longo do eixo, deslocada para o lado escolhido."""
    s=scene.s;out=[]
    for w in s.works:
        if not w.show:continue
        a,b=float(w.km_start_m),float(w.km_end_m)
        if b-a<30:c=(a+b)/2;a,b=c-15,c+15
        n=max(2,int((b-a)/4)+1);kms=np.linspace(a,b,n)
        if scene.km_active:P=np.array([scene.stationing.point(k) for k in kms],float)
        else:
            span=max(1e-9,s.km_end_m-s.km_start_m);ch=np.clip((kms-s.km_start_m)/span,0,1)*scene.ds[-1];P=np.array([scene.at(c) for c in ch])
        if w.x is not None and w.y is not None and w.km_end_m-w.km_start_m<30:
            P=P-P.mean(0)+np.array([w.x,w.y])   # obra pontual com coordenada: a faixa fica no ponto
        if len(P)>1 and w.side!='ambos':
            T=np.gradient(P,axis=0);T/=np.maximum(np.linalg.norm(T,axis=1,keepdims=True),1e-9);N=np.column_stack([T[:,1],-T[:,0]])   # direita do sentido do km
            P=P+N*(7 if w.side=='direito' else -7)
        chains=scene.ch[scene.tree.query(P)[1]]
        out.append({'w':w,'P':P,'chain':chains,'width_m':14 if w.side!='ambos' else 26,'rgb':_rgb(w.color or WORK_STYLE.get(w.kind,WORK_STYLE['outro'])[1])})
    return out

def day_at(scene,t):
    r=getattr(scene,'_sched_range','x')
    if r=='x':r=scene._sched_range=schedule_range(scene.s)
    if r is None:return None
    a,b=r;T=max(1e-6,float(scene.s.duration_s));f=float(np.clip(t/T,0,1))
    return a+dt.timedelta(days=round(f*(b-a).days))

def _dashed(im,pts,color,th,dash=18,gap=12):
    seg=np.diff(pts,axis=0);L=np.hypot(seg[:,0],seg[:,1]);acc=0.;on=True;left=dash
    for (p,q),l in zip(zip(pts[:-1],pts[1:]),L):
        pos=0.
        while pos<l:
            step=min(left,l-pos);a=p+(q-p)*(pos/max(l,1e-9));b=p+(q-p)*((pos+step)/max(l,1e-9))
            if on:cv2.line(im,tuple(np.rint(a).astype(int)),tuple(np.rint(b).astype(int)),color,th,cv2.LINE_AA)
            pos+=step;left-=step
            if left<=1e-9:on=not on;left=dash if on else gap

def draw(scene,im,t,cam,width,progress,header,footer):
    if not hasattr(scene,'_work_bands'):scene._work_bands=prepare(scene)
    if not scene._work_bands:return None
    sched=getattr(scene.s,'schedule_mode','off')=='linha_do_tempo';day=day_at(scene,t) if sched else None
    m=scene.W/width;over=im.copy();lines=[];counts={'prevista':0,'execucao':0,'concluida':0}
    limit=progress*scene.length+25
    for b in scene._work_bands:
        st,f=status(b['w'].model_dump(),day) if day else ('sem_data',1.)
        if st in counts:counts[st]+=1
        keep=b['chain']<=limit
        if keep.sum()<2:continue
        Q=scene.screen(b['P'][keep],cam,width);th=max(4,int(round(b['width_m']*m)))
        if Q[:,0].max()<-th or Q[:,0].min()>scene.W+th or Q[:,1].max()<header or Q[:,1].min()>scene.H-footer:continue
        Qi=np.rint(Q).astype(np.int32);rgb=b['rgb']
        if st=='prevista':
            if scene.s.schedule_show_planned:lines.append(('dash',Q,rgb,max(2,th//5)))
            continue
        if st=='execucao':
            k=max(2,int(round(len(Qi)*f)))
            cv2.polylines(over,[Qi[:k]],False,rgb,th,cv2.LINE_AA);lines.append(('dash',Q[k-1:],rgb,max(2,th//5)))
            lines.append(('tick',Qi[k-1],rgb,th))
        else:cv2.polylines(over,[Qi],False,rgb,th,cv2.LINE_AA)
        lines.append(('edge',Qi,rgb,th))
    y0,y1=header,scene.H-footer
    im[y0:y1]=cv2.addWeighted(over[y0:y1],.42,im[y0:y1],.58,0)
    top,bot=im[:y0].copy(),im[y1:].copy()   # nada desenhado sobre o cabeçalho e o rodapé
    for kind,Q,rgb,th in lines:
        if kind=='dash':_dashed(im,np.asarray(Q,float),rgb,th)
        elif kind=='tick':
            x,y=int(Q[0]),int(Q[1]);r=max(4,th//2);cv2.circle(im,(x,y),r,(255,255,255),-1,cv2.LINE_AA);cv2.circle(im,(x,y),r,rgb,max(2,r//3),cv2.LINE_AA)
        else:
            e=max(1,th//10);cv2.polylines(im,[Q],False,tuple(int(c*.55) for c in rgb),e,cv2.LINE_AA)
    im[:y0]=top;im[y1:]=bot
    return (day,counts) if sched and day else None

def date_box(scene,im,day,counts,header,font):
    sc=max(scene.scale,.8);W=int(430*sc);H=int(118*sc);x0=scene.W-W-int(40*sc);y0=header+int(24*sc)
    box=Image.new('RGBA',(W,H),(8,22,35,215));dr=ImageDraw.Draw(box)
    dr.text((int(20*sc),int(10*sc)),date_label(day).upper(),font=font(int(44*sc),True),fill='#ffffff')
    txt=f"{counts['execucao']} em execução · {counts['concluida']} concluída(s) · {counts['prevista']} prevista(s)"
    dr.text((int(20*sc),int(66*sc)),txt,font=font(int(17*sc)),fill='#c9dbe7')
    x=int(20*sc);y=int(94*sc)
    for lab,kind in [('Concluída','solid'),('Em execução','half'),('Prevista','dash')]:
        if kind=='dash':
            for k in range(3):dr.line((x+k*int(9*sc),y+int(6*sc),x+k*int(9*sc)+int(5*sc),y+int(6*sc)),fill='#ffb347',width=max(2,int(3*sc)))
        else:dr.rectangle((x,y,x+int(24*sc),y+int(12*sc)),fill='#ffb347' if kind=='solid' else None,outline='#ffb347',width=max(1,int(2*sc)))
        if kind=='half':dr.rectangle((x,y,x+int(12*sc),y+int(12*sc)),fill='#ffb347')
        dr.text((x+int(30*sc),y-int(3*sc)),lab,font=font(int(14*sc)),fill='#d6e0e3');x+=int(30*sc)+int(dr.textlength(lab,font=font(int(14*sc))))+int(22*sc)
    a=np.array(box);rgb=a[:,:,:3].astype(np.float32);al=a[:,:,3:4].astype(np.float32)/255
    roi=im[y0:y0+H,x0:x0+W].astype(np.float32);im[y0:y0+H,x0:x0+W]=np.clip(roi*(1-al)+rgb*al,0,255).astype(np.uint8)
