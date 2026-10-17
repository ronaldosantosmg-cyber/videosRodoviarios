from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.export.geojson_export import write_geojson
from videos_rodoviarios.export.json_export import write_analysis_json
from videos_rodoviarios.export.svg_preview import write_svg_preview
from videos_rodoviarios.geometry.stationing import format_station
from videos_rodoviarios.render.video_renderer import render_video

APP_NAME = "Vídeos Rodoviários"
SETTINGS_PATH = Path.home() / ".videos_rodoviarios.json"


def _load() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _open(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1040x790")
        self.minsize(920, 720)
        self.settings = _load()
        self.analysis = None
        self._style()
        self._ui()

    def _style(self):
        s = ttk.Style(self)
        if "vista" in s.theme_names():
            s.theme_use("vista")
        s.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        s.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        s.configure("Metric.TLabel", font=("Segoe UI", 17, "bold"))

    def _ui(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Vídeos Rodoviários", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="DXF + KMZ/KML → análise técnica → imagem aérea → vídeo MP4").pack(anchor="w", pady=(0, 12))

        files = ttk.LabelFrame(root, text="1 · Arquivos", padding=10)
        files.pack(fill="x")
        files.columnconfigure(1, weight=1)
        self.dxf = tk.StringVar(value=self.settings.get("dxf", ""))
        self.kmz = tk.StringVar(value=self.settings.get("kmz", ""))
        self.out = tk.StringVar(value=self.settings.get("output", ""))
        for r, (label, var, cmd, text) in enumerate([
            ("DXF", self.dxf, self._pick_dxf, "Selecionar DXF"),
            ("KMZ/KML", self.kmz, self._pick_kmz, "Selecionar KMZ/KML"),
            ("Saída", self.out, self._pick_out, "Escolher pasta"),
        ]):
            ttk.Label(files, text=label).grid(row=r, column=0, sticky="w", pady=4)
            ttk.Entry(files, textvariable=var).grid(row=r, column=1, sticky="ew", padx=8, pady=4)
            ttk.Button(files, text=text, command=cmd).grid(row=r, column=2, pady=4)

        opts = ttk.LabelFrame(root, text="2 · Vídeo", padding=10)
        opts.pack(fill="x", pady=10)
        self.res = tk.StringVar(value=self.settings.get("resolution", "1280x720"))
        self.fps = tk.StringVar(value=self.settings.get("fps", "24"))
        self.duration = tk.StringVar(value=self.settings.get("duration", "45"))
        self.zoom = tk.StringVar(value=self.settings.get("zoom", "17"))
        self.imagery = tk.BooleanVar(value=self.settings.get("imagery", True))
        for text, var, values in [
            ("Resolução", self.res, ("1280x720", "1920x1080")),
            ("FPS", self.fps, ("24", "30")),
            ("Duração", self.duration, ("30", "45", "60", "90")),
            ("Zoom aéreo", self.zoom, ("16", "17", "18")),
        ]:
            box = ttk.Frame(opts)
            box.pack(side="left", padx=(0, 16))
            ttk.Label(box, text=text).pack(anchor="w")
            ttk.Combobox(box, textvariable=var, values=values, width=11, state="readonly").pack()
        ttk.Checkbutton(opts, text="Imagem aérea Esri", variable=self.imagery).pack(side="left", padx=8)

        buttons = ttk.Frame(root)
        buttons.pack(fill="x")
        buttons.columnconfigure((0, 1), weight=1)
        self.an_btn = ttk.Button(buttons, text="ANALISAR PROJETO", style="Primary.TButton", command=self._start_analysis)
        self.an_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.video_btn = ttk.Button(buttons, text="GERAR VÍDEO MP4", style="Primary.TButton", command=self._start_video)
        self.video_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(10, 2))
        self.status = tk.StringVar(value="Pronto.")
        ttk.Label(root, textvariable=self.status).pack(anchor="w")

        metrics = ttk.Frame(root)
        metrics.pack(fill="x", pady=10)
        self.m_ext = tk.StringVar(value="—")
        self.m_cut = tk.StringVar(value="—")
        self.m_fill = tk.StringVar(value="—")
        self.m_mark = tk.StringVar(value="—")
        for i, (t, v) in enumerate([("Extensão", self.m_ext), ("Corte", self.m_cut), ("Aterro", self.m_fill), ("Sinalização", self.m_mark)]):
            c = ttk.LabelFrame(metrics, text=t, padding=8)
            c.grid(row=0, column=i, sticky="nsew", padx=3)
            metrics.columnconfigure(i, weight=1)
            ttk.Label(c, textvariable=v, style="Metric.TLabel").pack()

        self.details = tk.Text(root, height=13, wrap="word", font=("Consolas", 10))
        self.details.pack(fill="both", expand=True)
        self.details.insert("1.0", "Selecione DXF e KMZ/KML. O botão GERAR VÍDEO também executa a análise automaticamente.")
        self.details.configure(state="disabled")

        foot = ttk.Frame(root)
        foot.pack(fill="x", pady=(8, 0))
        ttk.Button(foot, text="Ver prévia", command=self._preview).pack(side="left")
        ttk.Button(foot, text="Abrir pasta", command=self._folder).pack(side="left", padx=6)
        ttk.Button(foot, text="Abrir vídeo", command=self._open_video).pack(side="left")

    def _pick_dxf(self):
        p = filedialog.askopenfilename(filetypes=[("DXF", "*.dxf")])
        if p:
            self.dxf.set(p)
            if not self.out.get():
                self.out.set(str(Path(p).parent / "resultado_video_rodoviario"))

    def _pick_kmz(self):
        p = filedialog.askopenfilename(filetypes=[("KMZ/KML", "*.kmz *.kml")])
        if p:
            self.kmz.set(p)

    def _pick_out(self):
        p = filedialog.askdirectory()
        if p:
            self.out.set(p)

    def _validate(self):
        dxf = Path(self.dxf.get().strip())
        kmz = Path(self.kmz.get().strip()) if self.kmz.get().strip() else None
        out = Path(self.out.get().strip() or (dxf.parent / "resultado_video_rodoviario"))
        if not dxf.exists() or dxf.suffix.lower() != ".dxf":
            messagebox.showerror(APP_NAME, "Selecione um DXF válido.")
            return None
        if kmz and (not kmz.exists() or kmz.suffix.lower() not in {".kmz", ".kml"}):
            messagebox.showerror(APP_NAME, "Selecione um KMZ/KML válido.")
            return None
        return dxf, kmz, out

    def _busy(self, text):
        self.an_btn.configure(state="disabled")
        self.video_btn.configure(state="disabled")
        self.status.set(text)
        self.progress["value"] = 0

    def _free(self):
        self.an_btn.configure(state="normal")
        self.video_btn.configure(state="normal")

    def _start_analysis(self):
        v = self._validate()
        if not v:
            return
        self._busy("Analisando projeto...")
        threading.Thread(target=self._do_analysis, args=v, daemon=True).start()

    def _do_analysis(self, dxf, kmz, out):
        try:
            analysis = analyze_road(dxf, kmz, curve_tolerance_m=0.10)
            out.mkdir(parents=True, exist_ok=True)
            write_analysis_json(analysis, out / "analise.json")
            write_geojson(analysis, out / "geometrias_dxf.geojson")
            if analysis.kml_context and analysis.kml_context.utm_zone:
                try:
                    write_geojson(analysis, out / "geometrias_wgs84.geojson", to_wgs84=True)
                except Exception:
                    pass
            write_svg_preview(analysis, out / "preview.svg")
            self.analysis = analysis
            self.after(0, lambda: self._analysis_done(analysis, out))
        except Exception as exc:
            self.after(0, lambda: self._failed(str(exc)))

    def _analysis_done(self, a, out):
        self._free()
        self.progress["value"] = 100
        self.status.set("Análise concluída.")
        self.m_ext.set(f"{a.extension_m/1000:.3f} km")
        self.m_cut.set(str(a.category_counts.get("cut", 0)))
        self.m_fill.set(str(a.category_counts.get("fill", 0)))
        self.m_mark.set(str(a.category_counts.get("marking", 0)))
        lines = [f"Extensão: {a.extension_m/1000:.3f} km"]
        if a.km_start_m is not None:
            lines += [f"Km inicial: {format_station(a.km_start_m)}", f"Km final: {format_station(a.km_end_m)}"]
        lines += ["", "OFFSETS DE CORTE / ATERRO"]
        lines += [f"{o.category.upper():<6} {o.side:<12} mediana {o.median_m:7.2f} m | min {o.min_m:7.2f} | max {o.max_m:7.2f} | {o.layer}" for o in a.offsets]
        if a.warnings:
            lines += ["", "ATENÇÕES"] + [f"• {w}" for w in a.warnings]
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")
        self._persist()

    def _start_video(self):
        v = self._validate()
        if not v:
            return
        self._busy("Preparando vídeo...")
        threading.Thread(target=self._do_video, args=v, daemon=True).start()

    def _do_video(self, dxf, kmz, out):
        try:
            a = self.analysis
            if a is None or Path(a.dxf_path) != dxf:
                a = analyze_road(dxf, kmz, curve_tolerance_m=0.10)
                out.mkdir(parents=True, exist_ok=True)
                write_analysis_json(a, out / "analise.json")
                write_svg_preview(a, out / "preview.svg")
                self.analysis = a
            w, h = (int(x) for x in self.res.get().split("x"))
            target = out / "video_rodoviario.mp4"
            def progress(p, text):
                self.after(0, lambda: (self.progress.configure(value=p * 100), self.status.set(text)))
            render_video(
                a,
                target,
                width=w,
                height=h,
                fps=int(self.fps.get()),
                duration_s=int(self.duration.get()),
                zoom=int(self.zoom.get()),
                imagery=bool(self.imagery.get()),
                progress=progress,
            )
            self.after(0, lambda: self._video_done(target, a, out))
        except Exception as exc:
            self.after(0, lambda: self._failed(str(exc)))

    def _video_done(self, target, a, out):
        self._analysis_done(a, out)
        self.status.set("Vídeo MP4 concluído.")
        self.progress["value"] = 100
        messagebox.showinfo(APP_NAME, f"Vídeo gerado com sucesso:\n{target}")

    def _failed(self, msg):
        self._free()
        self.status.set("Falha.")
        messagebox.showerror(APP_NAME, msg)

    def _preview(self):
        p = Path(self.out.get()) / "preview.svg"
        if p.exists():
            webbrowser.open(p.resolve().as_uri())

    def _folder(self):
        p = Path(self.out.get())
        if p.exists():
            _open(p)

    def _open_video(self):
        p = Path(self.out.get()) / "video_rodoviario.mp4"
        if p.exists():
            _open(p)
        else:
            messagebox.showwarning(APP_NAME, "O vídeo ainda não foi gerado.")

    def _persist(self):
        _save({
            "dxf": self.dxf.get(), "kmz": self.kmz.get(), "output": self.out.get(),
            "resolution": self.res.get(), "fps": self.fps.get(), "duration": self.duration.get(),
            "zoom": self.zoom.get(), "imagery": self.imagery.get(),
        })

    def destroy(self):
        self._persist()
        super().destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
