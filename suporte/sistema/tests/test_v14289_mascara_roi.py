"""2.59: a máscara por retângulo é idêntica à por matriz inteira (polígonos fora, na borda, com furo)."""
import numpy as np,cv2
def _antigo(n,polys):
    mask=np.zeros((n,n),np.uint8)
    for q,holes in polys:
        t=np.zeros_like(mask);cv2.fillPoly(t,[q],255)
        for h in holes:cv2.fillPoly(t,[h],0)
        mask=cv2.bitwise_or(mask,t)
    return mask
def _novo(n,polys):
    mask=np.zeros((n,n),np.uint8)
    for q,holes in polys:
        x0,y0=max(0,int(q[:,0].min())),max(0,int(q[:,1].min()));x1,y1=min(n,int(q[:,0].max())+1),min(n,int(q[:,1].max())+1)
        if x1>x0 and y1>y0:
            t=np.zeros((y1-y0,x1-x0),np.uint8);off=(-x0,-y0);cv2.fillPoly(t,[q],255,offset=off)
            for h in holes:cv2.fillPoly(t,[h],0,offset=off)
            np.bitwise_or(mask[y0:y1,x0:x1],t,out=mask[y0:y1,x0:x1])
    return mask
def test_identico():
    rng=np.random.default_rng(1);n=500;polys=[]
    for _ in range(60):
        c=rng.integers(-100,600,2);r=rng.integers(5,120);ang=np.sort(rng.uniform(0,6.28,7));q=(c+np.stack([np.cos(ang),np.sin(ang)],1)*r).astype(np.int32)
        holes=[(c+np.stack([np.cos(ang),np.sin(ang)],1)*(r*.4)).astype(np.int32)] if rng.random()<.4 else []
        polys.append((q,holes))
    polys.append((np.array([[-50,-50],[-10,-60],[-20,-5]],np.int32),[]))                       # totalmente fora
    polys.append((np.array([[490,490],[900,495],[800,900]],np.int32),[]))                      # cruza a borda
    assert np.array_equal(_antigo(n,polys),_novo(n,polys))
