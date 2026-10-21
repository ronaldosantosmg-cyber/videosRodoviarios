from __future__ import annotations

import json, os, subprocess, sys, threading, webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.export.geojson_export import write_geojson
from videos_rodoviarios.export.json_export import write_analysis_json
from videos_rodoviarios.export.svg_preview import write_svg_preview
from videos_rodoviarios.geometry.stationing import format_station
from videos_rodoviarios.paths import SAVED_DIR, ensure_app_dirs, settings_path
from videos_rodoviarios.render.video_renderer import render_video

APP_NAME="Vídeos Rodoviários · REV03"
SETTINGS=settings_path()
QMS_PROVIDER_CHOICES={"Esri World Imagery (satélite)":"esri_world_imagery","OpenStreetMap (mapa)":"osm_standard","Carto Light (mapa claro)":"carto_light"}


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
        ensure_app_dirs();super().__init__();self.title(APP_NAME);self.geometry("1060x760");self.minsize(900,680);self.cfg=load_settings();self.analysis=None;self.selected_centerline_handle=self.cfg.get("centerline_handle") or None;self._build()
    def _build(self):
        root=ttk.Frame(self,padding=16);root.pack(fill="both",expand=True);ttk.Label(root,text="Vídeos Rodoviários · REV03",font=("Segoe UI",20,"bold")).pack(anchor="w");ttk.Label(root,text="Fluxo rápido: DXF + KMZ → analisar → preview 720p → vídeo final QHD").pack(anchor="w",pady=(0,12))
        f=ttk.LabelFrame(root,text="1 · Arquivos",padding=10);f.pack(fill="x");f.columnconfigure(1,weight=1);self.dxf=tk.StringVar(value=self.cfg.get("dxf",""));self.kmz=tk.StringVar(value=self.cfg.get("kmz",""));self.out=tk.StringVar(value=self.cfg.get("output",str(SAVED_DIR)))
        for r,(lab,var,cmd,cap) in enumerate([("DXF",self.dxf,self._pick_dxf,"Selecionar DXF"),("KMZ/KML",self.kmz,self._pick_kmz,"Selecionar KMZ/KML"),("Saída",self.out,self._pick_out,"Escolher pasta")]):ttk.Label(f,text=lab).grid(row=r,column=0,sticky="w");ttk.Entry(f,textvariable=var).grid(row=r,column=1,sticky="ew",padx=8,pady=4);ttk.Button(f,text=cap,command=cmd).grid(row=r,column=2)
        o=ttk.LabelFrame(root,text="2 · Renderização",padding=10);o.pack(fill="x",pady=10);self.provider=tk.StringVar(value="Esri World Imagery (satélite)");self.imagery=tk.BooleanVar(value=True);ttk.Checkbutton(o,text="Imagem aérea",variable=self.imagery).pack(side="left");ttk.Combobox(o,textvariable=self.provider,values=tuple(QMS_PROVIDER_CHOICES),state="readonly",width=30).pack(side="left",padx=10);ttk.Label(o,text="Preview: 1280×720 / 15 s · Final: 2560×1440 / 30 fps").pack(side="left")
        b=ttk.Frame(root);b.pack(fill="x");[b.columnconfigure(i,weight=1) for i in range(3)];self.analyze_btn=ttk.Button(b,text="1 · ANALISAR",command=self.start_analysis);self.analyze_btn.grid(row=0,column=0,sticky="ew",padx=3);self.preview_btn=ttk.Button(b,text="2 · PREVIEW 720p",command=lambda:self.start_video(True));self.preview_btn.grid(row=0,column=1,sticky="ew",padx=3);self.video_btn=ttk.Button(b,text="3 · FINAL QHD",command=lambda:self.start_video(False));self.video_btn.grid(row=0,column=2,sticky="ew",padx=3)
        self.progress=ttk.Progressbar(root,mode="determinate",maximum=100);self.progress.pack(fill="x",pady=(12,3));self.status=tk.StringVar(value="Pronto para importar DXF e KMZ.");ttk.Label(root,textvariable=self.status).pack(anchor="w");self.details=tk.Text(root,height=18,wrap="word",font=("Consolas",10));self.details.pack(fill="both",expand=True,pady=10);self.details.insert("1.0","REV03 operacional. Faça primeiro o preview curto; só depois inicie o QHD.");self.details.configure(state="disabled");foot=ttk.Frame(root);foot.pack(fill="x");ttk.Button(foot,text="Abrir pasta",command=self.open_folder).pack(side="left");ttk.Button(foot,text="Abrir último vídeo",command=self.open_video).pack(side="left",padx=6)
    def _pick_dxf(self):
        p=filedialog.askopenfilename(filetypes=[("DXF","*.dxf")]);
        if p:self.dxf.set(p);self.analysis=None
    def _pick_kmz(self):
        p=filedialog.askopenfilename(filetypes=[("KMZ/KML","*.kmz *.kml")]);
        if p:self.kmz.set(p);self.analysis=None
    def _pick_out(self):
        p=filedialog.askdirectory();
        if p:self.out.set(p)
    def validate_inputs(self):
        d=Path(self.dxf.get().strip());k=Path(self.kmz.get().strip()) if self.kmz.get().strip() else None;o=Path(self.out.get().strip() or SAVED_DIR)
        if not d.exists() or d.suffix.lower()!=".dxf":messagebox.showerror(APP_NAME,"Selecione um DXF válido.");return None
        if k and (not k.exists() or k.suffix.lower() not in {".kmz",".kml"}):messagebox.showerror(APP_NAME,"Selecione um KMZ/KML válido.");return None
        return d,k,o
    def _busy(self,text):
        for x in (self.analyze_btn,self.preview_btn,self.video_btn):x.configure(state="disabled")
        self.status.set(text);self.progress["value"]=0
    def _free(self):
        for x in (self.analyze_btn,self.preview_btn,self.video_btn):x.configure(state="normal")
    def _analyze(self,d,k,o):
        a=analyze_road(d,k,curve_tolerance_m=.10,centerline_handle=self.selected_centerline_handle);o.mkdir(parents=True,exist_ok=True);write_analysis_json(a,o/"analise.json");write_geojson(a,o/"geometrias_dxf.geojson");write_svg_preview(a,o/"preview.svg");self.analysis=a;return a
    def start_analysis(self):
        v=self.validate_inputs()
        if not v:return
        self._busy("Analisando layers, eixo, pavimentos, OAEs e taludes...");threading.Thread(target=self._analysis_worker,args=v,daemon=True).start()
    def _analysis_worker(self,d,k,o):
        try:a=self._analyze(d,k,o);self.after(0,lambda:self.analysis_done(a))
        except Exception as e:self.after(0,lambda:self.failed(str(e)))
    def analysis_done(self,a):
        self._free();self.progress["value"]=100;self.status.set("Análise concluída. Gere o preview 720p.");lines=[f"Extensão: {a.extension_m/1000:.3f} km",f"Eixo: {a.main_centerline_handle or 'automático'}",f"Layers: {len(a.layer_counts)}",f"Corte: {a.category_counts.get('cut',0)} | Aterro: {a.category_counts.get('fill',0)} | OAE: {a.category_counts.get('oae',0)} | Sinalização: {a.category_counts.get('marking',0)}","","Layers reconhecidos:",*sorted(a.layer_counts,key=str.casefold)];self.details.configure(state="normal");self.details.delete("1.0","end");self.details.insert("1.0","\n".join(lines));self.details.configure(state="disabled");self.persist()
    def start_video(self,preview=False):
        v=self.validate_inputs()
        if not v:return
        self._busy("Gerando preview rápido..." if preview else "Gerando vídeo final QHD...");threading.Thread(target=self._video_worker,args=(*v,preview),daemon=True).start()
    def _video_worker(self,d,k,o,preview):
        try:
            a=self.analysis if self.analysis is not None and Path(self.analysis.dxf_path)==d else self._analyze(d,k,o);os.environ["VIDEOS_RODOVIARIOS_TILE_PROVIDER"]=QMS_PROVIDER_CHOICES.get(self.provider.get(),"esri_world_imagery");target=o/("preview_rev03.mp4" if preview else "video_rodoviario_qhd.mp4");w,h,fps,dur=(1280,720,24,15) if preview else (2560,1440,30,90)
            def prog(v,t):self.after(0,lambda:self._progress(v,t))
            render_video(a,target,width=w,height=h,fps=fps,duration_s=dur,zoom=17,imagery=bool(self.imagery.get()),progress=prog);self.after(0,lambda:self.video_done(target,preview))
        except Exception as e:self.after(0,lambda:self.failed(str(e)))
    def _progress(self,v,t):self.progress["value"]=v*100;self.status.set(t)
    def video_done(self,target,preview):self._free();self.progress["value"]=100;self.status.set("Preview concluído; confira antes do QHD." if preview else "Vídeo final QHD concluído.");messagebox.showinfo(APP_NAME,f"Arquivo gerado:\n{target}")
    def failed(self,msg):self._free();self.status.set("Falha. Veja a mensagem e corrija antes do render final.");messagebox.showerror(APP_NAME,msg)
    def output_dir(self):return Path(self.out.get().strip() or SAVED_DIR)
    def open_folder(self):
        p=self.output_dir();
        if p.exists():open_path(p)
    def open_video(self):
        for name in ("video_rodoviario_qhd.mp4","preview_rev03.mp4"):
            p=self.output_dir()/name
            if p.exists():open_path(p);return
        messagebox.showwarning(APP_NAME,"Nenhum vídeo REV03 foi gerado ainda.")
    def persist(self):save_settings({"dxf":self.dxf.get(),"kmz":self.kmz.get(),"output":self.out.get(),"centerline_handle":self.selected_centerline_handle})
    def destroy(self):self.persist();super().destroy()

def main():RoadVideoApp().mainloop()
if __name__=="__main__":main()
