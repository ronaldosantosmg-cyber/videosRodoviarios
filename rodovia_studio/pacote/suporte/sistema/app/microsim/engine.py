"""Motor de microssimulação: IDM + MOBIL + setas + transição suave + caixas OBB com camada anti-sobreposição.

Passo (O(n log n) com grelha espacial): sinais → índice por faixa → acelerações IDM (líderes reais e virtuais)
→ decisões laterais → cessão lateral → integração → resolução de conflitos (SAT) com congelamento do veículo de trás.
"""
from ..seguro import sdiv as _sdiv
import math
from bisect import bisect_left,bisect_right
from collections import Counter
from .geometry import OBB,SpatialHash,separation
from .idm import idm_accel
from .mobil import evaluate
from .params import EngineParams,T_PREP_MIN
from .vehicle import LaneChange,Overtake,Phase,Vehicle,smoothstep,smoothstep_rate
import numpy as np

LEFT,RIGHT=1,-1


class Simulation:
    def __init__(self,network,params=None):
        self.net=network;self.p=params or EngineParams();self.t=0.;self.vehicles={};self.events=[];self.stats=Counter()
        self.preds=network.predecessors();self._lane_entries={};self._signal_state={}
        self._obst={k:[] for k in network.lanes}
        for sl in network.stop_lines:self._obst[sl.lane_id].append((sl.s,'stop',sl))
        for c in network.closures:self._obst[c.lane_id].append((c.s_start,'closure',c))
        for k in self._obst:self._obst[k].sort(key=lambda x:x[0])

    # ------------------------------------------------------------------ entrada
    def add_vehicle(self,veh):
        if veh.id in self.vehicles:raise ValueError('Veículo duplicado: '+veh.id)
        if veh.lane_id not in self.net.lanes:raise ValueError('Faixa inexistente: '+veh.lane_id)
        self._pose(veh)
        o=OBB(veh.x,veh.y,veh.heading,veh.length,veh.width)
        for w in self.vehicles.values():
            if separation(o,OBB(w.x,w.y,w.heading,w.length,w.width))<self.p.clearance:
                raise ValueError(f'Veículo {veh.id} nasce sobreposto/colado a {w.id}.')
        self.vehicles[veh.id]=veh;return veh

    def _event(self,kind,veh,**kw):
        self.events.append(dict(t=round(self.t,3),kind=kind,id=veh.id,**kw))
        if len(self.events)>5000:del self.events[:1000]

    # ------------------------------------------------------------------ pose
    def _pose(self,v):
        lane=self.net.lanes[v.lane_id];p,h=lane.poses([v.s]);self._place(v,lane,p[0],float(h[0]))

    def _place(self,v,lane,p,h):
        nx,ny=-math.sin(h),math.cos(h);v.x=float(p[0])+nx*v.lat;v.y=float(p[1])+ny*v.lat;v.heading=h
        if v.phase is Phase.CHANGING and v.lc:
            rate=-v.lc.off0*smoothstep_rate(v.lc.t/v.lc.T)/v.lc.T          # d(lat)/dt
            v.heading=h+math.atan2(rate,max(v.v,.5))                        # carroceria alinhada ao vetor de direção

    def _poses_all(self):
        by={}
        for v in self.vehicles.values():by.setdefault(v.lane_id,[]).append(v)
        for lid,vs in by.items():
            lane=self.net.lanes[lid];p,h=lane.poses([x.s for x in vs])
            for i,x in enumerate(vs):self._place(x,lane,p[i],float(h[i]))

    # ------------------------------------------------------------------ sinais e índice por faixa
    def _update_signals(self):
        self._signal_state={k:s.state(self.t) for k,s in self.net.signals.items()}

    def _index(self):
        ent={k:[] for k in self.net.lanes}
        for v in self.vehicles.values():
            ent[v.lane_id].append((v.s,v,False))
            if v.phase is Phase.CHANGING and v.lc and v.lc.t/v.lc.T<.8:          # "fantasma" na faixa de origem
                if v.lc.from_lane in ent:ent[v.lc.from_lane].append((v.s-v.lc.s_delta,v,True))
        self._lane_entries={}
        for k,l in ent.items():
            l.sort(key=lambda e:e[0]);self._lane_entries[k]=([e[0] for e in l],l)

    def _stop_active(self,kind,obj,gap_line,v,veh):
        if kind=='closure':return obj.active
        if obj.signal_id is None:return True
        st=self._signal_state.get(obj.signal_id,'green')
        if st=='red':return True
        if st=='yellow':return gap_line>=v*v/(2*1.5*veh.params.idm.b)      # dilema: para só se der para frear com conforto
        return False

    # ------------------------------------------------------------------ vizinhança
    def _leader(self,veh,lane_id,s,exclude=(),depth=0,v=None):
        """(gap líquido, v_líder, objeto|None) do líder mais próximo na faixa (reais, fantasmas e virtuais)."""
        v=veh.v if v is None else v;L=veh.length;lane=self.net.lanes[lane_id];best=None
        arr,ent=self._lane_entries[lane_id];i=bisect_right(arr,s+1e-9)
        while i<len(ent):
            sv,w,ghost=ent[i]
            if w is not veh and w.id not in exclude:
                g=sv-s-.5*(w.length+L);best=(g,w.v,w);break
            i+=1
        for so,kind,obj in self._obst[lane_id]:
            if so<s+.5*L-1e-6:continue
            g=so-s-.5*L
            if best and g>=best[0]:break
            if self._stop_active(kind,obj,g,v,veh):best=(g,0.,obj);break
        if lane.dead_end_stops and not lane.successors:
            g=lane.length-s-.5*L
            if best is None or g<best[0]:best=(g,0.,None)
        if best is None and depth<2:
            nid=veh.next_lane(lane)
            if nid and nid in self.net.lanes:
                r=self._leader(veh,nid,s-lane.length,exclude,depth+1,v)
                if r:best=r
        if best and best[0]>self.p.horizon:return None
        return best

    def _follower(self,veh,lane_id,s,exclude=(),depth=0):
        arr,ent=self._lane_entries[lane_id];i=bisect_left(arr,s-1e-9)-1
        while i>=0:
            sv,w,ghost=ent[i]
            if w is not veh and w.id not in exclude:return (s-sv-.5*(w.length+veh.length),w)
            i-=1
        if depth<1:
            for pid in self.preds.get(lane_id,[]):
                r=self._follower(veh,pid,s+self.net.lanes[pid].length,exclude,depth+1)
                if r:return r
        return None

    def _v0(self,veh,lane_id):return self.net.lanes[lane_id].v0*veh.params.v0_factor

    def _accel(self,veh,lane_id,s,v=None,exclude=()):
        v=veh.v if v is None else v;ld=self._leader(veh,lane_id,s,exclude,v=v)
        gap,dv=(None,0.) if ld is None else (ld[0],v-ld[1])
        return idm_accel(v,self._v0(veh,lane_id),gap,dv,veh.params.idm),ld

    # ------------------------------------------------------------------ acelerações
    def _compute_accels(self):
        intents={}
        for v in self.vehicles.values():
            if v.phase is Phase.PREPARING and v.lc and v.lc.mandatory and self.p.courtesy:
                lane=self.net.lanes[v.lc.to_lane];intents.setdefault(v.lc.to_lane,[]).append((lane.project((v.x,v.y)),v))
        for v in self.vehicles.values():
            a,ld=self._accel(v,v.lane_id,v.s);v.leader_id=ld[2].id if ld and isinstance(ld[2],Vehicle) else None
            for si,m in intents.get(v.lane_id,()):                          # cortesia: abre brecha para quem vai entrar
                if m is v or si<=v.s:continue
                g=si-v.s-.5*(m.length+v.length)
                if 0<g<60:
                    ac=idm_accel(v.v,self._v0(v,v.lane_id),g,v.v-m.v,v.params.idm);a=min(a,max(ac,-v.params.idm.b))
            v.a=a

    # ------------------------------------------------------------------ troca de faixa
    def _closure_ahead(self,lane_id,s,L):
        for so,kind,obj in self._obst[lane_id]:
            if kind=='closure' and obj.active and so>=s+.5*L-1e-6:return so-s-.5*L,obj
        return None

    def _target_ok(self,v,side):
        lane=self.net.lanes[v.lane_id];nid=lane.neighbor(side)
        if not nid or nid not in self.net.lanes or lane.boundary(side).value!='open':return None
        s_to=self.net.lanes[nid].project((v.x,v.y));h=.5*v.length
        for so,kind,obj in self._obst[nid]:                                  # nunca entrar num trecho interditado
            if kind=='closure' and obj.active and so-h<=s_to<=obj.s_end+h:return None
        return nid

    def _lc_eval(self,v,side,nid,mandatory,reason):
        """Avalia a troca para `nid` com o MOBIL; devolve (resultado, s_destino)."""
        tl=self.net.lanes[nid];s_to=tl.project((v.x,v.y));idm=v.params.idm
        a_new,ld=self._accel(v,nid,s_to);fol=self._follower(v,nid,s_to)
        gap_front_ok=ld is None or ld[0]>=idm.s0
        gap_rear_ok=fol is None or fol[0]>=idm.s0+max(0.,(fol[1].v-v.v))*.5
        if fol:
            f=fol[1];a_nb,_=self._accel(f,nid,f.s);gf=fol[0]
            a_na=idm_accel(f.v,self._v0(f,nid),gf,f.v-v.v,f.params.idm)
        else:a_nb=a_na=0.
        of=self._follower(v,v.lane_id,v.s,exclude=())
        if of:
            o=of[1];a_ob,_=self._accel(o,v.lane_id,o.s)
            a_oa,_=self._accel(o,v.lane_id,o.s,exclude={v.id})
        else:a_ob=a_oa=0.
        r=evaluate(v.params.mobil,a_self=v.a,a_self_new=a_new,a_new_follower_after=a_na,a_new_follower_before=a_nb,
                   a_old_follower_after=a_oa,a_old_follower_before=a_ob,gap_front_ok=gap_front_ok,gap_rear_ok=gap_rear_ok,
                   toward_right=side<0,mandatory=mandatory)
        return r,s_to

    def _start_prep(self,v,side,nid,reason,mandatory):
        v.phase=Phase.PREPARING;v.indicator='left' if side>0 else 'right'
        v.lc=LaneChange(side=side,to_lane=nid,from_lane=v.lane_id,reason=reason,mandatory=mandatory)
        self._event('indicator_on',v,side=v.indicator,reason=reason)

    def _cancel(self,v,why):
        self._event('lane_change_cancel',v,why=why);v.phase=Phase.IDLE;v.indicator='off';v.lc=None;v.cooldown=self.p.lc_cooldown

    def _commit(self,v,s_to):
        lc=v.lc;tl=self.net.lanes[lc.to_lane];p,h=tl.poses([s_to]);nx,ny=-math.sin(h[0]),math.cos(h[0])
        off0=(v.x-p[0][0])*nx+(v.y-p[0][1])*ny
        lc.off0=float(off0);lc.s_delta=s_to-v.s;lc.T=max(v.params.mobil.t_change_min,1.5*abs(off0)/v.params.mobil.v_lat_max);lc.t=0.
        v.lane_id=lc.to_lane;v.s=s_to;v.lat=lc.off0;v.phase=Phase.CHANGING
        self._event('lane_change_start',v,to=lc.to_lane,T=round(lc.T,2));self.stats['lane_changes']+=1

    def _lateral_decisions(self,dt):
        for v in self.vehicles.values():
            m=v.params.mobil;v.cooldown=max(0.,v.cooldown-dt)
            if v.phase is Phase.CHANGING:continue
            if v.phase is Phase.PREPARING:
                lc=v.lc;lc.prep+=dt;lc.wait+=dt
                nid=lc.to_lane
                if nid not in self.net.lanes or self.net.lanes[v.lane_id].neighbor(lc.side)!=nid:self._cancel(v,'faixa mudou');continue
                if lc.prep>=max(m.t_prep,T_PREP_MIN):
                    r,s_to=self._lc_eval(v,lc.side,nid,lc.mandatory,lc.reason)
                    ok=r.safe if lc.mandatory or lc.reason=='return' else r.ok
                    if ok:self._commit(v,s_to)
                    elif not lc.mandatory and lc.wait>self.p.prep_timeout:self._cancel(v,'sem brecha')
                continue
            if self.t<v.next_decision or v.cooldown>0 or v.v<1.:continue
            v.next_decision=self.t+self.p.decision_interval
            L=v.length;lane=self.net.lanes[v.lane_id]
            cl=self._closure_ahead(v.lane_id,v.s,L)
            if cl and cl[0]<=self.p.closure_d_min+v.v*self.p.closure_t_ant:           # merge obrigatório (zíper) antecipado
                for side in(LEFT,RIGHT):
                    nid=self._target_ok(v,side)
                    if nid and not self._closure_ahead(nid,self.net.lanes[nid].project((v.x,v.y)),L):
                        self._start_prep(v,side,nid,'closure',True);break
                continue
            if v.overtake:
                ot=v.overtake;home=ot.home_lane;side=-ot.side
                passed=self.vehicles.get(ot.passed_id)
                if lane.neighbor(side)==home and self._target_ok(v,side)==home:
                    if passed is None or not passed.alive or passed.lane_id!=home:
                        d_ok=True
                    else:
                        d=v.s-passed.s-.5*(v.length+passed.length)
                        d_ok=d>=max(m.return_gap_min,v.v*m.return_gap_time)       # distância segura do ultrapassado
                    if d_ok:
                        r,_=self._lc_eval(v,side,home,False,'return')
                        if r.safe:self._start_prep(v,side,home,'return',False);continue
                elif lane.neighbor(side)!=home:v.overtake=None
                continue
            ld=self._leader(v,v.lane_id,v.s)
            if ld is None or ld[0]>80:continue
            best=None
            for side in(LEFT,RIGHT):
                nid=self._target_ok(v,side)
                if not nid:continue
                r,_=self._lc_eval(v,side,nid,False,'mobil')
                if r.ok and (best is None or r.incentive>best[0]):best=(r.incentive,side,nid)
            if best:
                self._start_prep(v,best[1],best[2],'mobil',False)
                if isinstance(ld[2],Vehicle) and v.overtake is None:v.overtake=Overtake(v.lane_id,ld[2].id,best[1])

    # ------------------------------------------------------------------ cessão lateral (estreitamentos)
    def _yield_pass(self):
        vs=list(self.vehicles.values());boxes={v.id:OBB(v.x,v.y,v.heading,v.length,v.width) for v in vs};h=SpatialHash(self.p.cell)
        for v in vs:h.insert(v.id,boxes[v.id],self.p.yield_margin)
        for ia,ib in h.pairs():
            a,b=self.vehicles[ia],self.vehicles[ib]
            if a.lane_id==b.lane_id and a.phase is Phase.IDLE and b.phase is Phase.IDLE:continue      # mesma faixa: IDM cuida
            if separation(boxes[ia],boxes[ib])>=self.p.yield_margin:continue
            rear=self._rear(a,b);rear.a=min(rear.a,-rear.params.idm.b);self.stats['yields']+=1

    @staticmethod
    def _rear(a,b):
        ux,uy=math.cos(a.heading),math.sin(a.heading);d=(b.x-a.x)*ux+(b.y-a.y)*uy      # >0: b à frente de a
        if abs(d)<.25*min(a.length,b.length):return a if a.id>b.id else b
        return a if d>0 else b

    # ------------------------------------------------------------------ integração
    def _integrate(self,dt):
        for v in list(self.vehicles.values()):
            a=v.a;v0=v.v
            if v0+a*dt<0:ds=v0*v0/(2*-a) if a<0 else 0.;v.v=0.
            else:v.v=v0+a*dt;ds=.5*(v0+v.v)*dt
            v.s+=ds;v.frozen=False
            if v.phase is Phase.CHANGING and v.lc:
                lc=v.lc;lc.t+=dt;v.lat=lc.off0*(1-smoothstep(lc.t/lc.T))
                if lc.t>=lc.T:
                    v.lat=0.;v.phase=Phase.IDLE;v.indicator='off';v.cooldown=self.p.lc_cooldown;v.lc=None
                    self._event('lane_change_end',v,lane=v.lane_id)
            lane=self.net.lanes[v.lane_id]
            while v.s>lane.length:
                nid=v.next_lane(lane)
                if nid and nid in self.net.lanes:
                    v.s-=lane.length;v.lane_id=nid;lane=self.net.lanes[nid]
                    if v.lc:v.lc.from_lane=None if v.phase is Phase.CHANGING else v.lc.from_lane
                    if v.phase is Phase.PREPARING:self._cancel(v,'fim da faixa')
                else:
                    if lane.dead_end_stops:v.s=lane.length;v.v=0.
                    else:v.alive=False;self._event('exit',v)
                    break
        for k in [k for k,v in self.vehicles.items() if not v.alive]:del self.vehicles[k]

    # ------------------------------------------------------------------ fail-safe anti-sobreposição
    def _conflict_pairs(self):
        vs=list(self.vehicles.values());boxes={v.id:OBB(v.x,v.y,v.heading,v.length,v.width) for v in vs};h=SpatialHash(self.p.cell)
        for v in vs:h.insert(v.id,boxes[v.id],self.p.clearance)
        return [(ia,ib) for ia,ib in h.pairs() if separation(boxes[ia],boxes[ib])<self.p.clearance]

    def _resolve(self,saved):
        for it in range(4):
            pairs=self._conflict_pairs()
            if not pairs:return
            for ia,ib in pairs:
                a,b=self.vehicles[ia],self.vehicles[ib];targets=[self._rear(a,b)] if it<2 else [a,b]
                for w in targets:
                    if w.id in saved:
                        w.restore(saved[w.id]);w.v=0.;w.a=0.;w.frozen=True;self.stats['frozen']+=1;self._event('frozen',w,other=(b if w is a else a).id)
        if self._conflict_pairs():                                          # último recurso: todos voltam ao estado anterior
            for w in self.vehicles.values():
                if w.id in saved:w.restore(saved[w.id]);w.v=0.;w.a=0.;w.frozen=True
            self.stats['full_revert']+=1

    # ------------------------------------------------------------------ passo
    def step(self,dt=None):
        dt=dt or self.p.dt;self.stats['steps']+=1
        self._update_signals();self._index();self._compute_accels();self._lateral_decisions(dt);self._yield_pass()
        saved={k:v.save() for k,v in self.vehicles.items()}
        self._integrate(dt);self._poses_all();self._resolve(saved);self.t+=dt

    def run(self,duration,callback=None):
        n=int(round((_sdiv(duration, self.p.dt))))
        for _ in range(n):
            self.step()
            if callback:callback(self)

    def snapshot(self):
        return [dict(id=v.id,x=v.x,y=v.y,heading=v.heading,v=v.v,a=v.a,indicator=v.indicator,lane=v.lane_id,lat=v.lat,
                     length=v.length,width=v.width,phase=v.phase.value,frozen=v.frozen) for v in self.vehicles.values()]

    def overlaps(self):
        """Verificação independente (força bruta) para testes: pares com caixas sobrepostas."""
        vs=list(self.vehicles.values());out=[]
        for i in range(len(vs)):
            for j in range(i+1,len(vs)):
                if separation(OBB(vs[i].x,vs[i].y,vs[i].heading,vs[i].length,vs[i].width),OBB(vs[j].x,vs[j].y,vs[j].heading,vs[j].length,vs[j].width))<0:out.append((vs[i].id,vs[j].id))
        return out
