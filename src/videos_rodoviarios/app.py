from __future__ import annotations
import json, os, subprocess, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from videos_rodoviarios.core.scene import SceneObject, TrafficFlow
from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.export.geojson_export import write_geojson
from videos_rodoviarios.export.json_export import write_analysis_json
from videos_rodoviarios.export.svg_preview import write_svg_preview
from videos_rodoviarios.paths import SAVED_DIR, ensure_app_dirs, settings_path
from videos_rodoviarios.render.video_renderer import render_video
APP_NAME="Vídeos Rodoviários · REV03"; SETTINGS=settings_path(); QMS_PROVIDER_CHOICES={"Esri World Imagery (satélite)":"esri_world_imagery","OpenStreetMap":"osm_standard","Carto Light":"carto_light"}
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
  ensure_app_dirs();super().__init__();self.title(APP_NAME);self.geometry("1180x820");self.cfg=load_settings();self.analysis=None;self._build()
 def _build(self):
  root=ttk.Frame(self,padding=12);root.pack(fill="both",expand=True);ttk.Label(root,text="Vídeos Rodoviários · REV03",font=("Segoe UI",20,"bold")).pack(anchor="w");ttk.Label(root,text="DXF + KMZ → modelo automático → elementos manuais → preview → QHD").pack(anchor="w")
  f=ttk.LabelFrame(root,text="1 · Arquivos",padding=8);f.pack(fill="x",pady=8);f.columnconfigure(1,weight=1);self.dxf=tk.StringVar(value=self.cfg.get("dxf",""));self.kmz=tk.StringVar(value=self.cfg.get("kmz",""));self.out=tk.StringVar(value=self.cfg.get("output",str(SAVED_DIR)))
  for r,(lab,var,cmd) in enumerate([("DXF",self.dxf,self._pick_dxf),("KMZ/KML",self.kmz,self._pick_kmz),("Saída",self.out,self._pick_out)]):ttk.Label(f,text=lab).grid(row=r,column=0,sticky="w");ttk.Entry(f,textvariable=var).grid(row=r,column=1,sticky="ew",padx=6);ttk.Button(f,text="Selecionar",command=cmd).grid(row=r,column=2)
  self.provider=tk.StringVar(value="Esri World Imagery (satélite)");self.imagery=tk.BooleanVar(value=True);r=ttk.Frame(root);r.pack(fill="x");ttk.Checkbutton(r,text="Imagem aérea",variable=self.imagery).pack(side="left");ttk.Combobox(r,textvariable=self.provider,values=tuple(QMS_PROVIDER_CHOICES),state="readonly",width=28).pack(side="left",padx=8);self.analyze_btn=ttk.Button(r,text="1 · ANALISAR",command=self.start_analysis);self.analyze_btn.pack(side="left",fill="x",expand=True,padx=3);self.preview_btn=ttk.Button(r,text="2 · PREVIEW 720p",command=lambda:self.start_video(True));self.preview_btn.pack(side="left",fill="x",expand=True,padx=3);self.video_btn=ttk.Button(r,text="3 · FINAL QHD",command=lambda:self.start_video(False));self.video_btn.pack(side="left",fill="x",expand=True,padx=3)
  ed=ttk.LabelFrame(root,text="Elementos adicionados · preservados separadamente do DXF",padding=8);ed.pack(fill="x",pady=8);self.objlist=tk.Listbox(ed,height=5);self.objlist.pack(side="left",fill="both",expand=True);buttons=ttk.Frame(ed);buttons.pack(side="left",padx=8)
  for text,cmd in [("OAE · 4 vértices",self.add_oae),("Passarela",lambda:self.add_linear("footbridge","Passarela")),("Pórtico",lambda:self.add_linear("gantry","Pórtico")),("Semipórtico",lambda:self.add_linear("semi_gantry","Semipórtico")),("Poste",self.add_pole),("Fluxo no eixo",self.add_flow),("Excluir selecionado",self.delete_selected)]:ttk.Button(buttons,text=text,command=cmd,width=20).pack(fill="x",pady=1)
  self.progress=ttk.Progressbar(root,maximum=100);self.progress.pack(fill="x");self.status=tk.StringVar(value="Importe DXF/KMZ e clique em ANALISAR.");ttk.Label(root,textvariable=self.status).pack(anchor="w");self.details=tk.Text(root,height=13,wrap="word",font=("Consolas",10));self.details.pack(fill="both",expand=True,pady=6);foot=ttk.Frame(root);foot.pack(fill="x");ttk.Button(foot,text="Abrir pasta",command=self.open_folder).pack(side="left");ttk.Button(foot,text="Abrir vídeo",command=self.open_video).pack(side="left",padx=5)
 def _pick_dxf(self):
  p=filedialog.askopenfilename(filetypes=[("DXF","*.dxf")]);
  if p:self.dxf.set(p);self.analysis=None;self.refresh_objects()
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
 def _busy(self,t):
  for b in (self.analyze_btn,self.preview_btn,self.video_btn):b.configure(state="disabled")
  self.status.set(t);self.progress["value"]=0
 def _free(self):
  for b in (self.analyze_btn,self.preview_btn,self.video_btn):b.configure(state="normal")
 def _analyze(self,d,k,o):
  a=analyze_road(d,k,curve_tolerance_m=.10);o.mkdir(parents=True,exist_ok=True);write_analysis_json(a,o/"analise.json");write_geojson(a,o/"geometrias_dxf.geojson");write_svg_preview(a,o/"preview.svg");self.analysis=a;return a
 def start_analysis(self):
  v=self.validate_inputs()
  if not v:return
  self._busy("Analisando projeto...");threading.Thread(target=self._analysis_worker,args=v,daemon=True).start()
 def _analysis_worker(self,d,k,o):
  try:a=self._analyze(d,k,o);self.after(0,lambda:self.analysis_done(a))
  except Exception as e:self.after(0,lambda:self.failed(str(e)))
 def analysis_done(self,a):
  self._free();self.progress["value"]=100;self.status.set("Modelo automático pronto. Adicione elementos ou gere preview.");lines=[f"Extensão: {a.extension_m/1000:.3f} km",f"Eixo: {a.main_centerline_handle or 'automático'}",f"Corte: {a.category_counts.get('cut',0)} | Aterro: {a.category_counts.get('fill',0)} | OAE DXF: {a.category_counts.get('oae',0)}","","Layers:",*sorted(a.layer_counts,key=str.casefold)];self.details.delete("1.0","end");self.details.insert("1.0","\n".join(lines));self.refresh_objects()
 def require_analysis(self):
  if self.analysis is None:messagebox.showwarning(APP_NAME,"Clique em ANALISAR antes de inserir elementos.");return False
  return True
 def ask_point(self,title,n):
  pts=[]
  for i in range(n):
   s=simpledialog.askstring(title,f"Vértice {i+1} — informe X,Y:")
   if not s:return None
   try:x,y=(float(v.strip().replace(",",".")) for v in s.replace(";",",").split(",",1));pts.append((x,y))
   except Exception:messagebox.showerror(APP_NAME,"Coordenada inválida. Use X,Y.");return None
  return pts
 def add_oae(self):
  if not self.require_analysis():return
  pts=self.ask_point("OAE por 4 vértices",4)
  if pts:self.analysis.scene_objects.append(SceneObject.oae_from_four_vertices(pts,material="concrete",deck_thickness_m=1.8));self.refresh_objects()
 def add_linear(self,kind,name):
  if not self.require_analysis():return
  pts=self.ask_point(name,2)
  if pts:self.analysis.scene_objects.append(SceneObject(kind=kind,points=pts,name=name));self.refresh_objects()
 def add_pole(self):
  if not self.require_analysis():return
  pts=self.ask_point("Poste",1)
  if pts:self.analysis.scene_objects.append(SceneObject(kind="light_pole",points=pts,name="Poste de iluminação"));self.refresh_objects()
 def add_flow(self):
  if not self.require_analysis():return
  path=list(self.analysis.centerline)
  if len(path)<2:messagebox.showerror(APP_NAME,"Eixo sem geometria suficiente.");return
  direction="reverse" if messagebox.askyesno(APP_NAME,"Fluxo no sentido decrescente/reverso?") else "forward";speed=simpledialog.askfloat("Fluxo","Velocidade km/h:",initialvalue=70,minvalue=1,maxvalue=160) or 70;density=simpledialog.askinteger("Fluxo","Quantidade/densidade de veículos:",initialvalue=8,minvalue=1,maxvalue=80) or 8;self.analysis.traffic_flows.append(TrafficFlow(path=path,direction=direction,speed_kmh=speed,density=density));self.refresh_objects()
 def refresh_objects(self):
  if not hasattr(self,"objlist"):return
  self.objlist.delete(0,"end")
  if not self.analysis:return
  for o in self.analysis.scene_objects:self.objlist.insert("end",f"OBJ · {o.name or o.kind} · {o.id[:6]}")
  for f in self.analysis.traffic_flows:self.objlist.insert("end",f"FLUXO · {f.direction} · {f.speed_kmh:.0f} km/h · {f.id[:6]}")
 def delete_selected(self):
  if not self.analysis:return
  s=self.objlist.curselection()
  if not s:return
  i=s[0];n=len(self.analysis.scene_objects)
  if i<n:self.analysis.scene_objects.pop(i)
  else:self.analysis.traffic_flows.pop(i-n)
  self.refresh_objects()
 def start_video(self,preview=False):
  v=self.validate_inputs()
  if not v:return
  self._busy("Gerando preview..." if preview else "Gerando QHD...");threading.Thread(target=self._video_worker,args=(*v,preview),daemon=True).start()
 def _video_worker(self,d,k,o,preview):
  try:
   a=self.analysis if self.analysis is not None else self._analyze(d,k,o);os.environ["VIDEOS_RODOVIARIOS_TILE_PROVIDER"]=QMS_PROVIDER_CHOICES.get(self.provider.get(),"esri_world_imagery");target=o/("preview_rev03.mp4" if preview else "video_rodoviario_qhd.mp4");w,h,fps,dur=(1280,720,24,15) if preview else (2560,1440,30,90)
   def prog(v,t):self.after(0,lambda:self._progress(v,t))
   render_video(a,target,width=w,height=h,fps=fps,duration_s=dur,zoom=17,imagery=bool(self.imagery.get()),progress=prog);self.after(0,lambda:self.video_done(target,preview))
  except Exception as e:self.after(0,lambda:self.failed(str(e)))
 def _progress(self,v,t):self.progress["value"]=v*100;self.status.set(t)
 def video_done(self,t,p):self._free();self.progress["value"]=100;self.status.set("Preview pronto." if p else "QHD pronto.");messagebox.showinfo(APP_NAME,f"Gerado:\n{t}")
 def failed(self,m):self._free();self.status.set("Falha.");messagebox.showerror(APP_NAME,m)
 def output_dir(self):return Path(self.out.get().strip() or SAVED_DIR)
 def open_folder(self):
  p=self.output_dir();
  if p.exists():open_path(p)
 def open_video(self):
  for n in ("video_rodoviario_qhd.mp4","preview_rev03.mp4"):
   p=self.output_dir()/n
   if p.exists():open_path(p);return
  messagebox.showwarning(APP_NAME,"Nenhum vídeo gerado.")
 def persist(self):save_settings({"dxf":self.dxf.get(),"kmz":self.kmz.get(),"output":self.out.get()})
 def destroy(self):self.persist();super().destroy()
def main():RoadVideoApp().mainloop()
if __name__=="__main__":main()
