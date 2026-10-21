from __future__ import annotations

import math
import os
import random
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from pyproj import CRS, Transformer
from shapely.geometry import LineString

from videos_rodoviarios.core.models import GeometryEntity, RoadAnalysis
from videos_rodoviarios.geometry.stationing import format_station
from videos_rodoviarios.paths import SUPPORT_DIR

Progress = Callable[[float, str], None]
TILE_SIZE = 256
QMS_PROVIDERS = {"esri_world_imagery":"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}","osm_standard":"https://tile.openstreetmap.org/{z}/{x}/{y}.png","carto_light":"https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"}
DEFAULT_PROVIDER = "esri_world_imagery"


def _font(size:int,bold:bool=False):
    for p in (["C:/Windows/Fonts/segoeuib.ttf","C:/Windows/Fonts/arialbd.ttf"] if bold else ["C:/Windows/Fonts/segoeui.ttf","C:/Windows/Fonts/arial.ttf"]):
        try:return ImageFont.truetype(p,size)
        except OSError:pass
    return ImageFont.load_default()


def _utm_transformer(a:RoadAnalysis):
    c=a.kml_context
    if not c or not c.utm_zone or not c.hemisphere:return None
    crs=CRS.from_dict({"proj":"utm","zone":c.utm_zone,"south":c.hemisphere.lower().startswith("s"),"datum":"WGS84","units":"m"})
    return Transformer.from_crs(crs,"EPSG:4326",always_xy=True)


def _lonlat_to_world_px(lon,lat,z):
    lat=max(-85.05112878,min(85.05112878,lat)); s=TILE_SIZE*(2**z); x=(lon+180)/360*s; q=math.sin(math.radians(lat)); y=(.5-math.log((1+q)/(1-q))/(4*math.pi))*s
    return x,y


def _to_world(points,t,z):
    if t is None:return [(x*.8,-y*.8) for x,y in points]
    return [_lonlat_to_world_px(*t.transform(x,y),z) for x,y in points]


def _screen(points,cx,cy,w,h):return [(x-cx+w/2,y-cy+h/2) for x,y in points]


class TileCache:
    def __init__(self,provider=None):
        p=provider or os.environ.get("VIDEOS_RODOVIARIOS_TILE_PROVIDER",DEFAULT_PROVIDER); self.provider=p if p in QMS_PROVIDERS else DEFAULT_PROVIDER; self.url_template=QMS_PROVIDERS[self.provider]; self.memory={}; self.root=SUPPORT_DIR/"cache_tiles"/self.provider; self.root.mkdir(parents=True,exist_ok=True)
    def get(self,z,x,y):
        n=2**z;x%=n
        if y<0 or y>=n:return Image.new("RGB",(256,256),(64,69,73))
        k=(z,x,y)
        if k in self.memory:return self.memory[k]
        path=self.root/str(z)/str(x)/f"{y}.jpg"
        try:
            if path.exists(): im=Image.open(path).convert("RGB")
            else:
                req=urllib.request.Request(self.url_template.format(z=z,x=x,y=y),headers={"User-Agent":"VideosRodoviarios/REV03"}); im=Image.open(BytesIO(urllib.request.urlopen(req,timeout=15).read())).convert("RGB"); path.parent.mkdir(parents=True,exist_ok=True); im.save(path,"JPEG",quality=92)
        except Exception:im=Image.new("RGB",(256,256),(72,78,82))
        self.memory[k]=im
        return im


def _background(cache,cx,cy,w,h,z,imagery):
    if not imagery:return Image.new("RGB",(w,h),(47,54,58))
    left,top=cx-w/2,cy-h/2; tx0,ty0=int(math.floor(left/256)),int(math.floor(top/256)); tx1,ty1=int(math.floor((cx+w/2)/256)),int(math.floor((cy+h/2)/256)); m=Image.new("RGB",((tx1-tx0+1)*256,(ty1-ty0+1)*256))
    for yy,ty in enumerate(range(ty0,ty1+1)):
        for xx,tx in enumerate(range(tx0,tx1+1)):m.paste(cache.get(z,tx,ty),(xx*256,yy*256))
    ox=int(left-tx0*256);oy=int(top-ty0*256);return m.crop((ox,oy,ox+w,oy+h)).resize((w,h),Image.Resampling.BICUBIC)


def _find_centerline(a):
    if a.main_centerline_handle:
        for e in a.entities:
            if e.handle==a.main_centerline_handle:return e
    return max(a.entities,key=lambda e:LineString(e.points).length if len(e.points)>=2 else 0)


def _sample(points,n):
    l=LineString(points)
    return [(l.interpolate(l.length*i/max(1,n-1)).x,l.interpolate(l.length*i/max(1,n-1)).y) for i in range(n)]


def _line(draw,pts,cx,cy,w,h,fill,lw):
    p=_screen(pts,cx,cy,w,h)
    if len(p)>1:draw.line(p,fill=fill,width=lw,joint="curve")


def _polygon(draw,pts,cx,cy,w,h,fill,outline=None,lw=1):
    p=_screen(pts,cx,cy,w,h)
    if len(p)>=3:draw.polygon(p,fill=fill); outline and draw.line(p+[p[0]],fill=outline,width=lw,joint="curve")


def _draw_vehicle(draw,line,phase,cx,cy,w,h,truck=False):
    if line.length<=0:return
    d=(phase%1)*line.length; p=line.interpolate(d); p2=line.interpolate(min(line.length,d+max(1,line.length*.002))); ang=math.atan2(p2.y-p.y,p2.x-p.x); x=p.x-cx+w/2;y=p.y-cy+h/2; L=18 if truck else 12;W=7 if truck else 6; ca,sa=math.cos(ang),math.sin(ang); poly=[]
    for a,b in [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]:poly.append((x+a*ca-b*sa,y+a*sa+b*ca))
    draw.polygon(poly,fill=(238,238,235,245) if not truck else (235,175,65,245),outline=(25,28,30,255))


def _draw_scene(frame,a,center,entities,road,scene_world,flow_world,i,total):
    w,h=frame.size;cx,cy=center;d=ImageDraw.Draw(frame,"RGBA");d.rectangle((0,0,w,h),fill=(0,0,0,18))
    # Pavimento flexível: base asfáltica em duas camadas + granulação sutil e bordas.
    _line(d,road,cx,cy,w,h,(38,41,43,245),42);_line(d,road,cx,cy,w,h,(83,86,88,245),34);_line(d,road,cx,cy,w,h,(205,205,198,180),2)
    rng=random.Random(731)
    for _ in range(180):
        x=rng.randrange(w);y=rng.randrange(h);d.point((x,y),fill=(220,220,215,18))
    for e,pts in entities:
        cat=(e.category or "").lower(); layer=(e.layer or "").lower()
        if cat in {"cut","fill"}:
            col=(139,103,68,150) if cat=="cut" else (86,132,72,145); _line(d,pts,cx,cy,w,h,col,18); _line(d,pts,cx,cy,w,h,(80,70,55,160),2)
        elif cat=="oae":
            if e.closed and len(pts)>=3:_polygon(d,pts,cx,cy,w,h,(173,169,158,235),(235,230,215,245),3)
            else:_line(d,pts,cx,cy,w,h,(173,169,158,240),14)
        elif cat in {"marking","edge"}:_line(d,pts,cx,cy,w,h,(250,250,244,245),3)
        elif cat=="domain":_line(d,pts,cx,cy,w,h,(255,202,56,210),2)
        # Pavimento rígido identificado por categoria/layer recebe concreto e juntas.
        if "rigid" in cat or "rigid" in layer or "concret" in layer:
            _line(d,pts,cx,cy,w,h,(184,183,174,235),30); p=_screen(pts,cx,cy,w,h)
            for j in range(1,len(p),2):d.ellipse((p[j][0]-2,p[j][1]-2,p[j][0]+2,p[j][1]+2),fill=(100,100,95,180))
    # Objetos manuais: OAE de quatro vértices e biblioteca básica.
    for obj,pts in scene_world:
        if not obj.visible:continue
        if obj.kind=="oae":
            _polygon(d,[(x+4,y+4) for x,y in pts],cx,cy,w,h,(0,0,0,85));_polygon(d,pts,cx,cy,w,h,(180,176,165,245),(245,240,225,255),3)
        elif obj.kind=="footbridge":_line(d,pts,cx,cy,w,h,(210,205,190,250),10);_line(d,pts,cx,cy,w,h,(245,240,225,255),2)
        elif obj.kind in {"gantry","semi_gantry"}:_line(d,pts,cx,cy,w,h,(195,200,202,250),6)
        elif obj.kind=="light_pole":
            for x,y in _screen(pts,cx,cy,w,h):d.ellipse((x-4,y-4,x+4,y+4),fill=(245,220,130,250),outline=(40,40,40,250))
    for flow,pts in flow_world:
        if not flow.visible:continue
        line=LineString(pts[::-1] if flow.direction=="reverse" else pts)
        for k in range(flow.density):_draw_vehicle(d,line,(i/max(1,total)+k/flow.density)*(.45+flow.speed_kmh/140),cx,cy,w,h,"truck" in flow.vehicle_mix and k%4==3)
    d.rectangle((0,0,w,64),fill=(9,17,24,226));km0=format_station(a.km_start_m) or "início";km1=format_station(a.km_end_m) or "fim";d.text((22,10),"VÍDEOS RODOVIÁRIOS · REV03",font=_font(24,True),fill="white");d.text((22,39),f"{km0} → {km1} | {a.extension_m/1000:.3f} km | modelagem artística",font=_font(15),fill=(215,224,231,255));p=i/max(1,total-1);d.rectangle((0,h-8,w,h),fill=(10,15,20,220));d.rectangle((0,h-8,int(w*p),h),fill=(255,205,40,245))


def render_video(analysis,output_path,*,width=1280,height=720,fps=24,duration_s=45,zoom=17,imagery=True,progress=None):
    output=Path(output_path);output.parent.mkdir(parents=True,exist_ok=True);width+=width%2;height+=height%2;cl=_find_centerline(analysis);t=_utm_transformer(analysis)
    if imagery and t is None:imagery=False
    road=_to_world(cl.points,t,zoom);entities=[(e,_to_world(e.points,t,zoom)) for e in analysis.entities if e.visible_in_output];scene=[(o,_to_world(o.points,t,zoom)) for o in analysis.scene_objects if o.points];flows=[(f,_to_world(f.path,t,zoom)) for f in analysis.traffic_flows]
    total=max(2,int(fps*duration_s));route=_sample(road,total);cache=TileCache();writer=imageio_ffmpeg.write_frames(str(output),(width,height),pix_fmt_in="rgb24",pix_fmt_out="yuv420p",fps=fps,codec="libx264",quality=7,macro_block_size=2,ffmpeg_log_level="error",output_params=["-movflags","+faststart"]);writer.send(None)
    try:
        for i,(cx,cy) in enumerate(route):
            frame=_background(cache,cx,cy,width,height,zoom,imagery);_draw_scene(frame,analysis,(cx,cy),entities,road,scene,flows,i,total);writer.send(frame.tobytes())
            if progress and (i%max(1,fps//2)==0 or i==total-1):progress((i+1)/total,f"Renderizando REV03: {int((i+1)*100/total)}%")
    finally:writer.close()
    if not output.exists() or output.stat().st_size<1000:raise RuntimeError("O codificador não produziu um MP4 válido.")
    if progress:progress(1.0,f"Vídeo REV03 concluído: {output.name}")
    return output
