"""OBB, SAT e grelha espacial (camada redundante anti-sobreposição)."""
import math
from collections import defaultdict


class OBB:
    __slots__=('cx','cy','hl','hw','ux','uy','vx','vy','ex','ey')

    def __init__(self,cx,cy,heading,length,width):
        c,s=math.cos(heading),math.sin(heading)
        self.cx,self.cy=cx,cy;self.hl,self.hw=length/2,width/2
        self.ux,self.uy=c,s            # eixo longitudinal
        self.vx,self.vy=-s,c           # eixo lateral (esquerda)
        self.ex=self.hl*abs(c)+self.hw*abs(s);self.ey=self.hl*abs(s)+self.hw*abs(c)   # meia-extensão do AABB

    def corners(self):
        return [(self.cx+a*self.hl*self.ux+b*self.hw*self.vx,self.cy+a*self.hl*self.uy+b*self.hw*self.vy) for a,b in((1,1),(1,-1),(-1,-1),(-1,1))]


def separation(a,b):
    """Maior separação ao longo dos 4 eixos do SAT. >0: caixas afastadas (limite inferior da distância real);
    <0: sobrepostas (|valor| = penetração mínima)."""
    dx,dy=b.cx-a.cx,b.cy-a.cy;best=-1e9
    for ax,ay in((a.ux,a.uy),(a.vx,a.vy),(b.ux,b.uy),(b.vx,b.vy)):
        ra=a.hl*abs(a.ux*ax+a.uy*ay)+a.hw*abs(a.vx*ax+a.vy*ay)
        rb=b.hl*abs(b.ux*ax+b.uy*ay)+b.hw*abs(b.vx*ax+b.vy*ay)
        sep=abs(dx*ax+dy*ay)-ra-rb
        if sep>best:best=sep
    return best


def conflicts(a,b,margin=0.):
    """True se a folga entre as caixas é menor que `margin` (margin=0 → sobreposição)."""
    return separation(a,b)<margin


class SpatialHash:
    """Grelha uniforme: inserção O(1); os pares candidatos são apenas os que dividem célula."""
    def __init__(self,cell=15.):
        self.cell=float(cell);self.cells=defaultdict(list)

    def insert(self,key,o,pad=0.):
        c=self.cell
        for i in range(int((o.cx-o.ex-pad)//c),int((o.cx+o.ex+pad)//c)+1):
            for j in range(int((o.cy-o.ey-pad)//c),int((o.cy+o.ey+pad)//c)+1):self.cells[(i,j)].append(key)

    def pairs(self):
        seen=set()
        for items in self.cells.values():
            n=len(items)
            for i in range(n):
                for j in range(i+1,n):
                    p=(items[i],items[j]) if items[i]<items[j] else (items[j],items[i])
                    if p not in seen:seen.add(p);yield p

    def near(self,o,pad=0.):
        c=self.cell;out=set()
        for i in range(int((o.cx-o.ex-pad)//c),int((o.cx+o.ex+pad)//c)+1):
            for j in range(int((o.cy-o.ey-pad)//c),int((o.cy+o.ey+pad)//c)+1):out.update(self.cells.get((i,j),()))
        return out
