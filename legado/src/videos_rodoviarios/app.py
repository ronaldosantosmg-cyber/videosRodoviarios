from __future__ import annotations
import json,os,subprocess,sys,threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox,simpledialog,ttk
from videos_rodoviarios.cad_interaction import install_cad_interactions
from videos_rodoviarios.core.scene import SceneObject,TrafficFlow
from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.paths import SAVED_DIR,ensure_app_dirs,settings_path
from videos_rodoviarios.render.video_renderer import render_video
APP_NAME="Vídeos Rodoviários · REV03";SETTINGS=settings_path();QMS_PROVIDER_CHOICES={"Esri World Imagery (satélite)":"esri_world_imagery","OpenStreetMap":"osm_standard","Carto Light":"carto_light"}
def load_settings():
 ensure_app_dirs()
 try:return json.loads(SETTINGS.read_text(encoding="utf-8"))
 except Exception:return {}
def save_settings(d):
 try:SETTINGS.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
 except Exception:pass
def open_path(p):
 if sys.platform.startswith("win"):os.startfile(p)
 elif sys.platform=="darwin":subprocess.Popen(["open",str(p)])
 else:subprocess.Popen(["xdg-open",str(p)])
class RoadVideoApp(tk.Tk):
 def __init__(self):
  ensure_app_dirs();super().__init__();self.title(APP_NAME);self.geometry("1320x920");self.cfg=load_settings();self.analysis=None;self.pick_points=[];self.pick_mode=None;self._build();install_cad_interactions(self)
 def _build(self):
  root=ttk.Frame(self,padding=8);root.pack(fill="both",expand=True);ttk.Label(root,text="Vídeos Rodoviários · REV03",font=("Segoe UI",19,"bold")).pack(anchor="w");ttk.Label(root,text="DXF fiel → controle de layers → máscara → preview → QHD").pack(anchor="w")
  f=ttk.LabelFrame(root,text="1 · Arquivos",padding=5);f.pack(fill="x",pady=4);f.columnconfigure(1,weight=1);self.dxf=tk.StringVar(value=self.cfg.get("dxf",""));self.kmz=tk.StringVar(value=self.cfg.get("kmz",""));self.out=tk.StringVar(value=self.cfg.get("output",str(SAVED_DIR)))
  for r,(lab,var,cmd) in enumerate([("DXF",self.dxf,self._pick_dxf),("KMZ/KML",self.kmz,self._pick_kmz),("Saída",self.out,self._pick_out)]):ttk.Label(f,text=lab).grid(row=r,column=0,sticky="w");ttk.Entry(f,textvariable=var).grid(row=r,column=1,sticky="ew",padx=5);ttk.Button(f,text="Selecionar",command=cmd).grid(row=r,column=2)
  bar=ttk.Frame(root);bar.pack(fill="x");self.provider=tk.StringVar(value="Esri World Imagery (satélite)");self.imagery=tk.BooleanVar(value=True);ttk.Checkbutton(bar,text="Imagem aérea",variable=self.imagery).pack(side="left");ttk.Combobox(bar,textvariable=self.provider,values=tuple(QMS_PROVIDER_CHOICES),state="readonly",width=25).pack(side="left",padx=5);self.analyze_btn=ttk.Button(bar,text="1 · ANALISAR",command=self.start_analysis);self.analyze_btn.pack(side="left",expand=True,fill="x");self.preview_btn=ttk.Button(bar,text="2 · PREVIEW 720p",command=lambda:self.start_video(True));self.preview_btn.pack(side="left",expand=True,fill="x",padx=4);self.video_btn=ttk.Button(bar,text="3 · FINAL QHD",command=lambda:self.start_video(False));self.video_btn.pack(side="left",expand=True,fill="x")
  work=ttk.Frame(root);work.pack(fill="both",expand=True,pady=5);left=ttk.LabelFrame(work,text="Vista DXF",padding=3);left.pack(side="left",fill="both",expand=True);self.canvas=tk.Canvas(left,bg="#20262b",height=430,cursor="crosshair");self.canvas.pack(fill="both",expand=True);self.canvas.bind("<Button-1>",self.canvas_click);self.canvas.bind("<Motion>",self.canvas_motion)
  side=ttk.Frame(work);side.pack(side="left",fill="y",padx=(5,0));layers=ttk.LabelFrame(side,text="Layers · ordem alfabética",padding=4);layers.pack(fill="both",expand=True);self.layer_tree=ttk.Treeview(layers,columns=("view","video"),show="tree headings",height=13);self.layer_tree.heading("#0",text="Layer");self.layer_tree.heading("view",text="Vista");self.layer_tree.heading("video",text="Vídeo");self.layer_tree.column("#0",width=210);self.layer_tree.column("view",width=85,anchor="center");self.layer_tree.column("video",width=85,anchor="center");self.layer_tree.pack(fill="both",expand=True);self.layer_tree.bind("<Double-1>",self.layer_double_click);lb=ttk.Frame(layers);lb.pack(fill="x");ttk.Button(lb,text="Congelar/Descongelar",command=self.toggle_layer_freeze).pack(side="left",expand=True,fill="x");ttk.Button(lb,text="Vídeo ON/OFF",command=self.toggle_layer_video).pack(side="left",expand=True,fill="x",padx=(3,0))
  ed=ttk.LabelFrame(side,text="Elementos adicionados",padding=4);ed.pack(fill="x",pady=(4,0));self.objlist=tk.Listbox(ed,width=39,height=6);self.objlist.pack(fill="x");
  for text,cmd in [("OAE · 4+ pontos",self.add_oae),("Passarela",lambda:self.add_linear("footbridge","Passarela")),("Fluxo no eixo",self.add_flow),("Excluir",self.delete_selected)]:ttk.Button(ed,text=text,command=cmd).pack(fill="x",pady=1)
  self.progress=ttk.Progressbar(root,maximum=100);self.progress.pack(fill="x");self.status=tk.StringVar(value="Importe DXF/KMZ e clique em ANALISAR.");ttk.Label(root,textvariable=self.status).pack(anchor="w")
 def _pick_dxf(self):
  p=filedialog.askopenfilename(filetypes=[("DXF","*.dxf")]);
  if p:self.dxf.set(p);self.analysis=None;self.redraw_canvas()
 def _pick_kmz(self):
  p=filedialog.askopenfilename(filetypes=[("KMZ/KML","*.kmz *.kml")]);
  if p:self.kmz.set(p);self.analysis=None
 def _pick_out(self):
  p=filedialog.askdirectory();
  if p:self.out.set(p)
 def validate_inputs(self):
  d=Path(self.dxf.get().strip());k=Path(self.kmz.get().strip()) if self.kmz.get().strip() else None;o=Path(self.out.get().strip() or SAVED_DIR)
  if not d.exists():messagebox.showerror(APP_NAME,"Selecione um DXF válido.");return None
  if k and not k.exists():messagebox.showerror(APP_NAME,"Selecione um KMZ/KML válido.");return None
  return d,k,o
 def start_analysis(self):
  v=self.validate_inputs()
  if not v:return
  self.status.set("Lendo DXF, layers e hachuras...");threading.Thread(target=self._analysis_worker,args=v,daemon=True).start()
 def _analysis_worker(self,d,k,o):
  try:a=analyze_road(d,k,curve_tolerance_m=.10);self.analysis=a;self.after(0,lambda:self.analysis_done(a))
  except Exception as e:
   msg=str(e);self.after(0,lambda m=msg:self.failed(m))
 def analysis_done(self,a):self.progress["value"]=100;self.status.set("DXF carregado. Controle Vista e Vídeo independentemente por layer.");self.refresh_layers();self.refresh_objects();self.redraw_canvas()
 def layer_entities(self,name):return [e for e in self.analysis.entities if e.layer==name] if self.analysis else []
 def refresh_layers(self):
  self.layer_tree.delete(*self.layer_tree.get_children())
  if not self.analysis:return
  for name in sorted(self.analysis.layer_counts,key=str.casefold):
   es=self.layer_entities(name);frozen=bool(es) and all(e.user_hidden for e in es);video_off=bool(es) and all(e.video_hidden for e in es);self.layer_tree.insert("", "end",iid=name,text=name,values=("CONGELADA" if frozen else "ATIVA","OFF" if video_off else "ON"))
 def selected_layer(self):
  s=self.layer_tree.selection();return s[0] if s else None
 def toggle_layer_freeze(self):
  name=self.selected_layer()
  if not name:return
  es=self.layer_entities(name);new=not all(e.user_hidden for e in es)
  for e in es:e.user_hidden=new
  for t in self.analysis.texts:
   if t.layer==name:t.user_hidden=new
  self.refresh_layers();self.redraw_canvas();self.status.set(f"Layer {name}: {'congelada na vista' if new else 'ativa na vista'}.")
 def toggle_layer_video(self):
  name=self.selected_layer()
  if not name:return
  es=self.layer_entities(name);new=not all(e.video_hidden for e in es)
  for e in es:e.video_hidden=new
  for t in self.analysis.texts:
   if t.layer==name:t.video_hidden=new
  self.refresh_layers();self.status.set(f"Layer {name}: vídeo {'OFF' if new else 'ON'}; a vista não foi alterada.")
 def layer_double_click(self,event):
  region=self.layer_tree.identify_region(event.x,event.y);col=self.layer_tree.identify_column(event.x)
  if region=="cell" and col=="#1":self.toggle_layer_freeze()
  elif region=="cell" and col=="#2":self.toggle_layer_video()
 def bounds(self):
  pts=[p for e in self.analysis.entities for p in e.points] if self.analysis else []
  if not pts:return(0,0,1,1)
  xs=[p[0] for p in pts];ys=[p[1] for p in pts];return min(xs),min(ys),max(xs),max(ys)
 def world_to_canvas(self,p):
  x0,y0,x1,y1=self.bounds();w=max(100,self.canvas.winfo_width());h=max(100,self.canvas.winfo_height());s=min((w-30)/max(1,x1-x0),(h-30)/max(1,y1-y0));return(15+(p[0]-x0)*s,h-15-(p[1]-y0)*s)
 def canvas_to_world(self,x,y):
  x0,y0,x1,y1=self.bounds();w=max(100,self.canvas.winfo_width());h=max(100,self.canvas.winfo_height());s=min((w-30)/max(1,x1-x0),(h-30)/max(1,y1-y0));return(x0+(x-15)/s,y0+(h-15-y)/s)
 def redraw_canvas(self):
  if not hasattr(self,"canvas"):return
  self.canvas.delete("all")
  if not self.analysis:return
  for e in self.analysis.entities:
   if not e.visible_in_viewport:continue
   q=[self.world_to_canvas(p) for p in e.points]
   if len(q)<2:continue
   col="#9aa0a6";cat=(e.category or "").lower()
   if cat.startswith("pavement_"):col="#66696b" if "flexible" in cat else "#b8b5aa"
   elif cat=="cut":col="#c65342"
   elif cat=="fill":col="#5e9b55"
   elif cat in {"grass","median_grass"}:col="#69a95f"
   elif cat=="oae":col="#e1c890"
   self.canvas.create_polygon(q,fill=col,outline=col) if e.closed and len(q)>=3 else self.canvas.create_line(q,fill=col,width=1,smooth=True)
  for o in self.analysis.scene_objects:
   q=[self.world_to_canvas(p) for p in o.points]
   if len(q)>=3:self.canvas.create_polygon(q,outline="#ffd54f",fill="",width=3)
  self._draw_pick()
 def _draw_pick(self,mouse=None):
  self.canvas.delete("pick")
  if not self.pick_points:return
  q=[self.world_to_canvas(p) for p in self.pick_points]
  for x,y in q:self.canvas.create_oval(x-4,y-4,x+4,y+4,fill="#ffeb3b",outline="#111",tags="pick")
  line=q+([mouse] if mouse else [])
  if len(line)>1:self.canvas.create_line(line,fill="#ffeb3b",width=2,dash=(5,3),tags="pick")
 def canvas_click(self,event):
  if self.pick_mode=="oae":self.pick_points.append(self.canvas_to_world(event.x,event.y));self._draw_pick();self.status.set(f"OAE: {len(self.pick_points)} pontos · Enter conclui · Esc cancela")
 def canvas_motion(self,event):
  if self.pick_mode=="oae" and self.pick_points:self._draw_pick((event.x,event.y))
 def require_analysis(self):
  if not self.analysis:messagebox.showwarning(APP_NAME,"Analise o DXF primeiro.");return False
  return True
 def add_oae(self):
  if not self.require_analysis():return
  self.pick_mode="oae";self.pick_points=[];self.cad.begin("OAE","Clique 4+ pontos · Enter conclui · Esc cancela",on_confirm=lambda _:self.finish_oae(),on_cancel=self.cancel_pick,focus=False)
 def finish_oae(self):
  if len(self.pick_points)<4:self.cad.begin("OAE","Mínimo 4 pontos · continue clicando",on_confirm=lambda _:self.finish_oae(),on_cancel=self.cancel_pick,focus=False);return
  self.analysis.scene_objects.append(SceneObject.oae_from_vertices(self.pick_points,material="concrete"));self.pick_mode=None;self.pick_points=[];self.refresh_objects();self.redraw_canvas()
 def cancel_pick(self):self.pick_mode=None;self.pick_points=[];self.redraw_canvas()
 def ask_point(self,title,n):
  pts=[]
  for i in range(n):
   s=simpledialog.askstring(title,f"Ponto {i+1} — X;Y:")
   if not s:return None
   try:x,y=[float(v.strip().replace(",",".")) for v in s.split(";",1)];pts.append((x,y))
   except Exception:return None
  return pts
 def add_linear(self,k,n):
  if not self.require_analysis():return
  p=self.ask_point(n,2)
  if p:self.analysis.scene_objects.append(SceneObject(kind=k,points=p,name=n));self.refresh_objects();self.redraw_canvas()
 def add_flow(self):
  if not self.require_analysis():return
  c=next((e for e in self.analysis.entities if e.handle==self.analysis.main_centerline_handle),None)
  if not c:return
  self.analysis.traffic_flows.append(TrafficFlow(path=list(c.points)));self.refresh_objects()
 def refresh_objects(self):
  self.objlist.delete(0,"end")
  if not self.analysis:return
  for o in self.analysis.scene_objects:self.objlist.insert("end",f"OBJ · {o.name or o.kind}")
  for f in self.analysis.traffic_flows:self.objlist.insert("end",f"FLUXO · {f.direction}")
 def delete_selected(self):
  s=self.objlist.curselection()
  if not s or not self.analysis:return
  i=s[0];n=len(self.analysis.scene_objects);self.analysis.scene_objects.pop(i) if i<n else self.analysis.traffic_flows.pop(i-n);self.refresh_objects();self.redraw_canvas()
 def start_video(self,preview=False):
  v=self.validate_inputs()
  if not v:return
  threading.Thread(target=self._video_worker,args=(*v,preview),daemon=True).start()
 def _video_worker(self,d,k,o,preview):
  try:
   a=self.analysis or analyze_road(d,k,curve_tolerance_m=.10);o.mkdir(parents=True,exist_ok=True);os.environ["VIDEOS_RODOVIARIOS_TILE_PROVIDER"]=QMS_PROVIDER_CHOICES.get(self.provider.get(),"esri_world_imagery");target=o/("preview_rev03.mp4" if preview else "video_rodoviario_qhd.mp4");w,h,fps,dur=(1280,720,24,15) if preview else (2560,1440,30,90);render_video(a,target,width=w,height=h,fps=fps,duration_s=dur,zoom=17,imagery=bool(self.imagery.get()),progress=lambda v,t:self.after(0,lambda:self._progress(v,t)));self.after(0,lambda:self.video_done(target,preview))
  except Exception as e:
   msg=str(e);self.after(0,lambda m=msg:self.failed(m))
 def _progress(self,v,t):self.progress["value"]=v*100;self.status.set(t)
 def video_done(self,t,p):self.progress["value"]=100;self.status.set("Preview pronto." if p else "QHD pronto.");messagebox.showinfo(APP_NAME,f"Gerado:\n{t}")
 def failed(self,m):self.status.set("Falha.");messagebox.showerror(APP_NAME,m)
 def persist(self):save_settings({"dxf":self.dxf.get(),"kmz":self.kmz.get(),"output":self.out.get()})
 def destroy(self):self.persist();super().destroy()
def main():RoadVideoApp().mainloop()
if __name__=="__main__":main()
