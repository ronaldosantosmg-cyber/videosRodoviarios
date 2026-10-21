from __future__ import annotations
import math,os,random,urllib.request
from io import BytesIO
from pathlib import Path
from typing import Callable
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
from pyproj import CRS,Transformer
from shapely.geometry import LineString
from videos_rodoviarios.core.models import RoadAnalysis
from videos_rodoviarios.geometry.stationing import format_station
from videos_rodoviarios.paths import SUPPORT_DIR
Progress=Callable[[float,str],None];TILE_SIZE=256
QMS_PROVIDERS={"esri_world_imagery":"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}","osm_standard":"https://tile.openstreetmap.org/{z}/{x}/{y}.png","carto_light":"https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"};DEFAULT_PROVIDER="esri_world_imagery"
def _font(s,bold=False):
 for p in (["C:/Windows/Fonts/segoeuib.ttf","C:/Windows/Fonts/arialbd.ttf"] if bold else ["C:/Windows/Fonts/segoeui.ttf","C:/Windows/Fonts/arial.ttf"]):
  try:return ImageFont.truetype(p,s)
  except OSError:pass
 return ImageFont.load_default()
def _utm_transformer(a):
 c=a.kml_context
 if not c or not c.utm_zone or not c.hemisphere:return None
 return Transformer.from_crs(CRS.from_dict({"proj":"utm","zone":c.utm_zone,"south":c.hemisphere.lower().startswith("s"),"datum":"WGS84","units":"m"}),"EPSG:4326",always_xy=True)
def _lonlat_to_world_px(lon,lat,z):
 lat=max(-85.05112878,min(85.05112878,lat));s=256*(2**z);q=math.sin(math.radians(lat));return ((lon+180)/360*s,(.5-math.log((1+q)/(1-q))/(4*math.pi))*s)
def _to_world(points,t,z):return [(x*.8,-y*.8) for x,y in points] if t is None else [_lonlat_to_world_px(*t.transform(x,y),z) for x,y in points]
def _screen(points,cx,cy,w,h):return [(x-cx+w/2,y-cy+h/2) for x,y in points]
class TileCache:
 def __init__(self):
  p=os.environ.get("VIDEOS_RODOVIARIOS_TILE_PROVIDER",DEFAULT_PROVIDER);self.provider=p if p in QMS_PROVIDERS else DEFAULT_PROVIDER;self.url_template=QMS_PROVIDERS[self.provider];self.memory={};self.root=SUPPORT_DIR/"cache_tiles"/self.provider;self.root.mkdir(parents=True,exist_ok=True)
 def get(self,z,x,y):
  n=2**z;x%=n
  if y<0 or y>=n:return Image.new("RGB",(256,256),(64,69,73))
  k=(z,x,y)
  if k in self.memory:return self.memory[k]
  path=self.root/str(z)/str(x)/f"{y}.jpg"
  try:
   if path.exists():im=Image.open(path).convert("RGB")
   else:
    req=urllib.request.Request(self.url_template.format(z=z,x=x,y=y),headers={"User-Agent":"VideosRodoviarios/REV03"});im=Image.open(BytesIO(urllib.request.urlopen(req,timeout=15).read())).convert("RGB");path.parent.mkdir(parents=True,exist_ok=True);im.save(path,"JPEG",quality=92)
  except Exception:im=Image.new("RGB",(256,256),(72,78,82))
  self.memory[k]=im;return im
def _background(cache,cx,cy,w,h,z,imagery):
 if not imagery:return Image.new("RGB",(w,h),(47,54,58))
 left,top=cx-w/2,cy-h/2;tx0,ty0=int(left//256),int(top//256);tx1,ty1=int((cx+w/2)//256),int((cy+h/2)//256);m=Image.new("RGB",((tx1-tx0+1)*256,(ty1-ty0+1)*256))
 for yy,ty in enumerate(range(ty0,ty1+1)):
  for xx,tx in enumerate(range(tx0,tx1+1)):m.paste(cache.get(z,tx,ty),(xx*256,yy*256))
 return m.crop((int(left-tx0*256),int(top-ty0*256),int(left-tx0*256)+w,int(top-ty0*256)+h)).resize((w,h),Image.Resampling.BICUBIC)
def _find_centerline(a):
 if a.main_centerline_handle:
  for e in a.entities:
   if e.handle==a.main_centerline_handle:return e
 return max(a.entities,key=lambda e:LineString(e.points).length if len(e.points)>=2 else 0)
def _sample(points,n):
 l=LineString(points);return [(l.interpolate(l.length*i/max(1,n-1)).x,l.interpolate(l.length*i/max(1,n-1)).y) for i in range(n)]
def _line(d,p,cx,cy,w,h,fill,lw):
 q=_screen(p,cx,cy,w,h)
 if len(q)>1:d.line(q,fill=fill,width=lw,joint="curve")
def _polygon(d,p,cx,cy,w,h,fill,outline=None,lw=1):
 q=_screen(p,cx,cy,w,h)
 if len(q)>=3:d.polygon(q,fill=fill);outline and d.line(q+[q[0]],fill=outline,width=lw,joint="curve")
def _oae(d,pts,cx,cy,w,h):
 """Deck, sombra projetada, barreiras laterais e juntas de dilatação nas extremidades."""
 q=_screen(pts,cx,cy,w,h)
 if len(q)<4:return
 shadow=[(x+7,y+9) for x,y in q];d.polygon(shadow,fill=(0,0,0,105));d.polygon(q,fill=(177,174,165,255),outline=(225,221,210,255))
 # bordas/barreiras: usa as duas arestas longitudinais mais longas do polígono
 edges=[(math.hypot(q[(i+1)%len(q)][0]-q[i][0],q[(i+1)%len(q)][1]-q[i][1]),q[i],q[(i+1)%len(q)]) for i in range(len(q))];edges.sort(reverse=True,key=lambda x:x[0])
 for _,a,b in edges[:2]:d.line([(a[0]+4,a[1]+5),(b[0]+4,b[1]+5)],fill=(0,0,0,90),width=8);d.line([a,b],fill=(210,207,198,255),width=6);d.line([a,b],fill=(242,239,230,255),width=2)
 # juntas: duas arestas restantes, linha escura + sombra curta
 used={(a,b) for _,a,b in edges[:2]}
 for _,a,b in edges[2:]:d.line([(a[0]+2,a[1]+3),(b[0]+2,b[1]+3)],fill=(0,0,0,100),width=5);d.line([a,b],fill=(55,56,55,245),width=3)
def _draw_vehicle(d,line,phase,cx,cy,w,h,truck=False):
 if line.length<=0:return
 dist=(phase%1)*line.length;p=line.interpolate(dist);p2=line.interpolate(min(line.length,dist+max(1,line.length*.002)));ang=math.atan2(p2.y-p.y,p2.x-p.x);x=p.x-cx+w/2;y=p.y-cy+h/2;L=18 if truck else 12;W=7 if truck else 6;ca,sa=math.cos(ang),math.sin(ang);poly=[(x+a*ca-b*sa,y+a*sa+b*ca) for a,b in [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]];d.polygon(poly,fill=(235,175,65,245) if truck else (238,238,235,245),outline=(25,28,30,255))
def _draw_scene(frame,a,center,entities,road,scene,flows,i,total):
 w,h=frame.size;cx,cy=center;d=ImageDraw.Draw(frame,"RGBA");d.rectangle((0,0,w,h),fill=(0,0,0,18));_line(d,road,cx,cy,w,h,(38,41,43,245),42);_line(d,road,cx,cy,w,h,(83,86,88,245),34);_line(d,road,cx,cy,w,h,(205,205,198,180),2)
 for e,pts in entities:
  cat=(e.category or "").lower();layer=(e.layer or "").lower()
  if cat in {"cut","fill"}:_line(d,pts,cx,cy,w,h,(139,103,68,150) if cat=="cut" else (86,132,72,145),18)
  elif cat=="oae":
   if e.closed and len(pts)>=4:_oae(d,pts,cx,cy,w,h)
   else:_line(d,pts,cx,cy,w,h,(173,169,158,240),14)
  elif cat in {"marking","edge"}:_line(d,pts,cx,cy,w,h,(250,250,244,245),3)
  elif cat=="domain":_line(d,pts,cx,cy,w,h,(255,202,56,210),2)
  if "rigid" in cat or "rigid" in layer or "concret" in layer:_line(d,pts,cx,cy,w,h,(184,183,174,235),30)
 for obj,pts in scene:
  if not obj.visible:continue
  if obj.kind=="oae":_oae(d,pts,cx,cy,w,h)
  elif obj.kind=="footbridge":_line(d,pts,cx,cy,w,h,(210,205,190,250),10);_line(d,pts,cx,cy,w,h,(245,240,225,255),2)
  elif obj.kind in {"gantry","semi_gantry"}:_line(d,pts,cx,cy,w,h,(195,200,202,250),6)
  elif obj.kind=="light_pole":
   for x,y in _screen(pts,cx,cy,w,h):d.ellipse((x-4,y-4,x+4,y+4),fill=(245,220,130,250),outline=(40,40,40,250))
 for flow,pts in flows:
  if not flow.visible:continue
  line=LineString(pts[::-1] if flow.direction=="reverse" else pts)
  for k in range(flow.density):_draw_vehicle(d,line,(i/max(1,total)+k/flow.density)*(.45+flow.speed_kmh/140),cx,cy,w,h,"truck" in flow.vehicle_mix and k%4==3)
 d.rectangle((0,0,w,64),fill=(9,17,24,226));d.text((22,10),"VÍDEOS RODOVIÁRIOS · REV03",font=_font(24,True),fill="white");d.text((22,39),f"{format_station(a.km_start_m) or 'início'} → {format_station(a.km_end_m) or 'fim'} | {a.extension_m/1000:.3f} km",font=_font(15),fill=(215,224,231,255));p=i/max(1,total-1);d.rectangle((0,h-8,w,h),fill=(10,15,20,220));d.rectangle((0,h-8,int(w*p),h),fill=(255,205,40,245))
def render_video(analysis,output_path,*,width=1280,height=720,fps=24,duration_s=45,zoom=17,imagery=True,progress=None):
 output=Path(output_path);output.parent.mkdir(parents=True,exist_ok=True);width+=width%2;height+=height%2;cl=_find_centerline(analysis);t=_utm_transformer(analysis);imagery=imagery and t is not None;road=_to_world(cl.points,t,zoom);entities=[(e,_to_world(e.points,t,zoom)) for e in analysis.entities if e.visible_in_output];scene=[(o,_to_world(o.points,t,zoom)) for o in getattr(analysis,"scene_objects",[]) if o.points];flows=[(f,_to_world(f.path,t,zoom)) for f in getattr(analysis,"traffic_flows",[])];total=max(2,int(fps*duration_s));route=_sample(road,total);cache=TileCache();writer=imageio_ffmpeg.write_frames(str(output),(width,height),pix_fmt_in="rgb24",pix_fmt_out="yuv420p",fps=fps,codec="libx264",quality=7,macro_block_size=2,ffmpeg_log_level="error",output_params=["-movflags","+faststart"]);writer.send(None)
 try:
  for i,(cx,cy) in enumerate(route):
   frame=_background(cache,cx,cy,width,height,zoom,imagery);_draw_scene(frame,analysis,(cx,cy),entities,road,scene,flows,i,total);writer.send(frame.tobytes())
   if progress and (i%max(1,fps//2)==0 or i==total-1):progress((i+1)/total,f"Renderizando REV03: {int((i+1)*100/total)}%")
 finally:writer.close()
 if not output.exists() or output.stat().st_size<1000:raise RuntimeError("O codificador não produziu um MP4 válido.")
 if progress:progress(1.0,f"Vídeo REV03 concluído: {output.name}")
 return output
