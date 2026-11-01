"""1.42.39: barreira final anti-conflito do simulador de tráfego (usa a geometria OBB/SAT + grelha espacial de app.microsim).

Princípio: NÃO substitui nenhum cálculo. Roda depois de todas as barreiras existentes (IDM, reservas por polígono,
separação longitudinal) e antes de o quadro ser gravado/validado. Se nenhum par de corpos (com a folga lateral do
aplicativo) se sobrepõe, não toca em nada, portanto o resultado de projetos sem conflito é idêntico ao anterior.
Se há sobreposição, o veículo de TRÁS (pela projeção sobre o rumo do outro) volta ao estado do passo anterior e fica
parado neste passo (congelamento longitudinal); repete até 4 vezes e, em último caso, também o da frente.
Antes, esse caso interrompia o vídeo com 'Reserva lateral insuficiente'; agora é resolvido e contabilizado."""
import math
import numpy as np
from shapely.geometry import Polygon
from .microsim.geometry import OBB,SpatialHash,separation
from .vehicle_motion import PROFILES
from .vehicle_safety import LATERAL_BUFFER,body

MAX_PASSES=4


def snapshot(v):
    lc=v.get('lc')
    return (v['p'],v['s'],v['v'],dict(lc) if lc is not None else None,v.get('lc_cooldown'),v.get('li',0),v.get('_previous_s'))


def restore(v,snap):
    v['p'],v['s'],v['v'],lc,v['lc_cooldown'],v['li'],ps=snap
    v['lc']=dict(lc) if lc is not None else None
    if ps is not None:v['_previous_s']=ps


class ConflictGuard:
    def __init__(self,sim):
        self.sim=sim;self.interventions=0;self.passes=0;self.full_reverts=0;self.unresolved=0;self.pairs_seen=0;self.enabled=True

    def _box(self,v):
        c,h=self.sim.polygon_safety.pose(v);L,Bw,_,_=PROFILES.get(v.get('t','car'),PROFILES['car'])
        return OBB(float(c[0]),float(c[1]),math.atan2(float(h[1]),float(h[0])),L+2*LATERAL_BUFFER,Bw+2*LATERAL_BUFFER),(c,h,L,Bw)

    def _conflicts(self,V):
        boxes={};raw={};grid=SpatialHash(20.);byid={}
        for v in V:
            if v['id'] in byid:continue
            o,r=self._box(v);boxes[v['id']]=o;raw[v['id']]=r;byid[v['id']]=v;grid.insert(v['id'],o)
        out=[];ps=self.sim.polygon_safety
        for a,b in grid.pairs():
            if separation(boxes[a],boxes[b])>=-1e-6:continue
            va,vb=byid[a],byid[b];la,lb=ps.level(va),ps.level(vb)
            if la is not None and lb is not None and la!=lb:continue
            ca,ha,L1,W1=raw[a];cb,hb,L2,W2=raw[b]       # confirmação exata com a mesma regra de check() (área > 1e-7)
            if body(ca,ha,L1,W1,LATERAL_BUFFER).intersection(body(cb,hb,L2,W2,LATERAL_BUFFER)).area<=1e-7:continue
            out.append((va,vb,raw[a],raw[b]))
        return out

    @staticmethod
    def _rear(va,vb,ra,rb):
        h=np.asarray(ra[1],float);d=float(np.dot(np.asarray(rb[0],float)-np.asarray(ra[0],float),h))      # >0: b à frente de a
        if abs(d)<.25*min(ra[2],rb[2]):return va if va['id']>vb['id'] else vb
        return va if d>0 else vb

    def apply(self,V):
        if not self.enabled or len(V)<2:return 0
        fixed=0
        for it in range(MAX_PASSES):
            pairs=self._conflicts(V)
            if not pairs:return fixed
            self.pairs_seen+=len(pairs);self.passes+=1
            for va,vb,ra,rb in pairs:
                targets=[self._rear(va,vb,ra,rb)] if it<2 else [va,vb]
                for w in targets:
                    snap=w.get('_snap')
                    if snap is None:continue
                    if w['p']==snap[0] and snap[1]!=w['s']:
                        for link,a,b in self.sim.link_of[w['p']]:
                            if link[0]=='c' and snap[1]<b<=w['s'] and self.sim.node_transfers.get((link[1],link[2]),0)>0:self.sim.node_transfers[(link[1],link[2])]-=1
                    restore(w,snap);w['v']=0.;w['_risk_stop']=True;self.interventions+=1;fixed+=1
        left=self._conflicts(V)
        if left:
            for va,vb,_,_ in left:
                for w in (va,vb):
                    if w.get('_snap') is not None:restore(w,w['_snap']);w['v']=0.
            self.full_reverts+=1
            if self._conflicts(V):self.unresolved+=1
        return fixed

    def report(self):
        return {'engine':'app.microsim OBB/SAT + grelha espacial','interventions':self.interventions,'conflicting_pairs_seen':self.pairs_seen,
                'passes':self.passes,'full_reverts':self.full_reverts,'unresolved':self.unresolved,
                'scope':'Só atua se dois corpos (com a folga lateral) se sobrepõem; sem conflito não altera nenhum resultado.'}
