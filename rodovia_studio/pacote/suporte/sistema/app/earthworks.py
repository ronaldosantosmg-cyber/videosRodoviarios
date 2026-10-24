"""Hachuras estáveis no terreno, com limites legíveis e sem alargar offsets."""
import cv2
import numpy as np

def earthwork_style(mask, lines, role, meters_per_pixel, phase=(0,0), look='hatch'):
    if role not in ('cut','fill'):raise ValueError('Categoria de talude inválida')
    if look=='natural':return natural_style(mask,lines,role,meters_per_pixel)
    h,w=mask.shape
    pitch=max(7,round(4/meters_per_pixel))
    thickness=max(2,min(5,round(.65/meters_per_pixel)))
    # Broadcasting avoids two full-resolution index matrices.
    y=np.arange(h,dtype=np.int32)[:,None]+int(phase[1]);x=np.arange(w,dtype=np.int32)[None,:]+int(phase[0])
    stripes=((x+(y if role=='cut' else -y))%pitch)<thickness
    alpha=np.where(mask>0,np.where(stripes,215,98),0).astype(np.uint8)
    boundary=cv2.morphologyEx(mask,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))
    # Keep outlines inside the native polygon and its exclusions.
    edge=(boundary>0)&(mask>0)
    lineweight=max(2,min(5,round(.6/meters_per_pixel)))
    offsets=cv2.dilate(lines,np.ones((lineweight,lineweight),np.uint8))
    alpha=np.maximum(alpha,(offsets.astype(np.float32)*.92).astype(np.uint8))
    alpha[edge]=235
    rgb=np.array((224,83,69) if role=='cut' else (56,183,93),np.uint8)
    color=np.broadcast_to(rgb,(h,w,3)).copy()
    color[edge]=np.array((110,40,33) if role=='cut' else (24,89,45),np.uint8)
    return color,alpha

def natural_style(mask, lines, role, meters_per_pixel):
    """1.16: talude com aparência de terreno (corte: solo exposto; aterro: grama), com contorno fino na cor do tipo.
    A textura (grão do solo e da grama) é aplicada no quadro, ancorada em metros."""
    h,w=mask.shape
    alpha=np.where(mask>0,200,0).astype(np.uint8)
    boundary=cv2.morphologyEx(mask,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8));edge=(boundary>0)&(mask>0)
    lineweight=max(1,min(3,round(.35/meters_per_pixel)))
    offsets=cv2.dilate(lines,np.ones((lineweight,lineweight),np.uint8))>0
    rgb=np.array((156,124,92) if role=='cut' else (92,124,66),np.uint8)
    color=np.broadcast_to(rgb,(h,w,3)).copy()
    line=np.array((176,72,60) if role=='cut' else (40,120,62),np.uint8)
    color[offsets]=line;alpha[offsets&(mask>0)]=np.maximum(alpha[offsets&(mask>0)],150)
    color[edge]=line;alpha[edge]=230
    return color,alpha
