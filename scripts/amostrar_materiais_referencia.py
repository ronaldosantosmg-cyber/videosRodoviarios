"""Amostras dos shaders do aplicativo; sem fotos ou geometria de projetos privados."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'suporte/sistema'))
from app.pavement import paint_rigid,JointField
from app.render import font
from app import visual


def main():
    h,w=420,600;mask=np.ones((h,w),bool)
    transform=np.array([[.02,0,730000],[0,-.02,7830000.]])
    field=JointField([np.array([[730000.,7829980.],[730000.,7830010.]])])
    concrete=paint_rigid(np.full((h,w,3),190,np.uint8),mask,'pavement',730000,7830000,.02,field,5,artistic=True)
    visual.shade_surface(concrete,np.full((h,w),3,np.uint8),transform,.02,mask,arte=True)
    rock=np.empty((h,w,3),np.uint8);rock[:]=[138,135,129]
    visual.shade_rock(rock,np.full((h,w),visual.ROCK_SURF,np.uint8),transform,.02,mask)
    canvas=Image.new('RGB',(1240,500),(245,245,242));canvas.paste(Image.fromarray(concrete),(10,55));canvas.paste(Image.fromarray(rock),(630,55))
    draw=ImageDraw.Draw(canvas)
    draw.text((15,15),'Concreto - placas claras e juntas',font=font(23),fill=(30,35,38))
    draw.text((635,15),'Rocha exposta - cinza-bege e fraturas',font=font(23),fill=(30,35,38))
    output=ROOT/'proveniencia/visuais-3.13/concreto-rocha.png';output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output)
    print(output)


if __name__=='__main__':main()
