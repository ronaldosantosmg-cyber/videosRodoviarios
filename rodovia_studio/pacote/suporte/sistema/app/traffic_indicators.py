"""Setas e alerta visíveis na apresentação 2D, sem linhas de diagnóstico."""
import math
import cv2
import numpy as np
from .vehicle_motion import PROFILES

def draw(scene,image,t,cam,width):
    sim=getattr(scene,'_sim',None)
    if sim is None or math.floor(t*2.5)%2:return
    signals=sim.indicators(t)
    for center,heading,vid,_,_ in sim.vehicles_ex(t):
        code=signals.get(int(vid),0)
        if not code:continue
        L,B,_,_=PROFILES.get(sim.info[vid][1],PROFILES['car']);normal=np.array([-heading[1],heading[0]])
        for side in [-1,1]:
            if code==1 and side<0 or code==2 and side>0:continue
            for tip in [-1,1]:
                point=center+heading*(L*.44*tip)+normal*(B*.46*side);q=scene.screen(point[None],cam,width)[0]
                if np.isfinite(q).all() and -10<q[0]<scene.W+10 and -10<q[1]<scene.H+10:cv2.circle(image,tuple(q.astype(int)),max(2,min(6,round(.22*scene.W/width))),(255,178,35),-1,cv2.LINE_AA)
