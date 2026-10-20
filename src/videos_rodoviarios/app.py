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
from videos_rodoviarios.io.local_imagery import prepare_local_imagery
from videos_rodoviarios.paths import SAVED_DIR, ensure_app_dirs, settings_path
from videos_rodoviarios.render.video_renderer import render_video

APP_NAME = "Vídeos Rodoviários"
SETTINGS = settings_path()


def load_settings() -> dict:
    ensure_app_dirs()
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    ensure_app_dirs()
    try:
        SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class RoadVideoApp(tk.Tk):
    def __init__(self) -> None:
        ensure_app_dirs()
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1100x820")
        self.minsize(940, 740)
        self.cfg = load_settings()
        self.analysis = None
        self.selected_centerline_handle: str | None = self.cfg.get("centerline_handle") or None
        self.local_imagery_path: Path | None = None
        saved_image = self.cfg.get("local_imagery", "")
        if saved_image and Path(saved_image).exists():
            self.local_imagery_path = Path(saved_image)
        self._style()
        self._build()

    def _style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Metric.TLabel", font=("Segoe UI", 17, "bold"))

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Vídeos Rodoviários", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="DXF + KMZ/KML + imagem local → análise → visualização → MP4").pack(anchor="w", pady=(0, 12))

        files = ttk.LabelFrame(root, text="1 · Arquivos", padding=10)
        files.pack(fill="x")
        files.columnconfigure(1, weight=1)
        self.dxf = tk.StringVar(value=self.cfg.get("dxf", ""))
        self.kmz = tk.StringVar(value=self.cfg.get("kmz", ""))
        self.local_image = tk.StringVar(value=self.cfg.get("local_imagery", ""))
        self.out = tk.StringVar(value=self.cfg.get("output", str(SAVED_DIR)))
        rows = [
            ("DXF", self.dxf, self._pick_dxf, "Selecionar DXF"),
            ("KMZ/KML", self.kmz, self._pick_kmz, "Selecionar KMZ/KML"),
            ("Imagem local", self.local_image, self._pick_local_image, "Selecionar imagem"),
            ("Saída", self.out, self._pick_out, "Escolher pasta"),
        ]
        for row, (label, var, action, caption) in enumerate(rows):
            ttk.Label(files, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(files, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
            ttk.Button(files, text=caption, command=action).grid(row=row, column=2, pady=4)

        opts = ttk.LabelFrame(root, text="2 · Configuração do vídeo", padding=10)
        opts.pack(fill="x", pady=10)
        self.res = tk.StringVar(value=self.cfg.get("resolution", "1280x720"))
        self.fps = tk.StringVar(value=self.cfg.get("fps", "24"))
        self.duration = tk.StringVar(value=self.cfg.get("duration", "45"))
        self.zoom = tk.StringVar(value=self.cfg.get("zoom", "17"))
        self.imagery = tk.BooleanVar(value=self.cfg.get("imagery", True))
        for label, var, values in [
            ("Resolução", self.res, ("1280x720", "1920x1080")),
            ("FPS", self.fps, ("24", "30")),
            ("Duração (s)", self.duration, ("30", "45", "60", "90")),
            ("Zoom", self.zoom, ("16", "17", "18")),
        ]:
            frame = ttk.Frame(opts)
            frame.pack(side="left", padx=(0, 16))
            ttk.Label(frame, text=label).pack(anchor="w")
            ttk.Combobox(frame, textvariable=var, values=values, width=11, state="readonly").pack()
        ttk.Checkbutton(opts, text="Imagem aérea Esri", variable=self.imagery).pack(side="left", padx=8)

        buttons = ttk.Frame(root)
        buttons.pack(fill="x")
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        self.analyze_btn = ttk.Button(buttons, text="ANALISAR PROJETO", style="Primary.TButton", command=self.start_analysis)
        self.analyze_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.video_btn = ttk.Button(buttons, text="GERAR VÍDEO MP4", style="Primary.TButton", command=self.start_video)
        self.video_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(10, 2))
        self.status = tk.StringVar(value="Pronto.")
        ttk.Label(root, textvariable=self.status).pack(anchor="w")

        metrics = ttk.Frame(root)
        metrics.pack(fill="x", pady=10)
        self.metrics = {key: tk.StringVar(value="—") for key in ("ext", "cut", "fill", "mark")}
        for col, (title, key) in enumerate([
            ("Extensão", "ext"),
            ("Corte", "cut"),
            ("Aterro", "fill"),
            ("Sinalização", "mark"),
        ]):
            metrics.columnconfigure(col, weight=1)
            card = ttk.LabelFrame(metrics, text=title, padding=8)
            card.grid(row=0, column=col, sticky="nsew", padx=3)
            ttk.Label(card, textvariable=self.metrics[key], style="Metric.TLabel").pack()

        self.details = tk.Text(root, height=13, wrap="word", font=("Consolas", 10))
        self.details.pack(fill="both", expand=True)
        self.details.insert("1.0", "Selecione os arquivos e clique em GERAR VÍDEO MP4. A análise é automática.")
        self.details.configure(state="disabled")

        footer = ttk.Frame(root)
        footer.pack(fill="x", pady=(8, 0))
        ttk.Button(footer, text="Ver prévia", command=self.open_preview).pack(side="left")
        ttk.Button(footer, text="Abrir pasta", command=self.open_folder).pack(side="left", padx=6)
        ttk.Button(footer, text="Abrir vídeo", command=self.open_video).pack(side="left")

    def set_selected_centerline(self, handle: str | None) -> None:
        self.selected_centerline_handle = handle or None
        self.analysis = None
        if self.selected_centerline_handle:
            self.status.set(f"Eixo selecionado: {self.selected_centerline_handle}")
            cad = getattr(self, "cad", None)
            if cad is not None:
                cad.write(f"Eixo ativo: entidade {self.selected_centerline_handle}.")
        else:
            self.status.set("Eixo automático.")

    def _pick_dxf(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("DXF", "*.dxf")])
        if path:
            self.dxf.set(path)
            self.set_selected_centerline(None)

    def _pick_kmz(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("KMZ/KML", "*.kmz *.kml")])
        if path:
            self.kmz.set(path)

    def _pick_local_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a imagem georreferenciada",
            filetypes=[
                ("Imagens georreferenciadas", "*.ecw *.tif *.tiff *.png *.jpg *.jpeg"),
                ("ECW", "*.ecw"),
                ("GeoTIFF", "*.tif *.tiff"),
                ("Imagens", "*.png *.jpg *.jpeg"),
            ],
        )
        if not path:
            return
        self.status.set("Preparando imagem local...")
        try:
            cache_dir = SAVED_DIR / "cache_imagens"
            result = prepare_local_imagery(path, cache_dir)
            self.local_imagery_path = result.usable_path
            self.local_image.set(str(result.usable_path))
            if result.converted:
                self.status.set(f"ECW convertido para GeoTIFF: {result.usable_path.name}")
            else:
                self.status.set(f"Imagem local preparada: {result.usable_path.name}")
            self.persist()
        except Exception as exc:
            self.local_imagery_path = None
            self.status.set("Falha ao preparar imagem local.")
            messagebox.showerror(APP_NAME, str(exc))

    def _pick_out(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.out.set(path)

    def validate_inputs(self):
        dxf = Path(self.dxf.get().strip())
        kmz = Path(self.kmz.get().strip()) if self.kmz.get().strip() else None
        out = Path(self.out.get().strip() or SAVED_DIR)
        if not dxf.exists() or dxf.suffix.lower() != ".dxf":
            messagebox.showerror(APP_NAME, "Selecione um DXF válido.")
            return None
        if kmz and (not kmz.exists() or kmz.suffix.lower() not in {".kmz", ".kml"}):
            messagebox.showerror(APP_NAME, "Selecione um KMZ/KML válido.")
            return None
        return dxf, kmz, out

    def set_busy(self, text: str) -> None:
        self.analyze_btn.configure(state="disabled")
        self.video_btn.configure(state="disabled")
        self.status.set(text)
        self.progress["value"] = 0

    def set_free(self) -> None:
        self.analyze_btn.configure(state="normal")
        self.video_btn.configure(state="normal")

    def start_analysis(self) -> None:
        values = self.validate_inputs()
        if not values:
            return
        self.set_busy("Analisando projeto...")
        threading.Thread(target=self._analyze_worker, args=values, daemon=True).start()

    def _analyze_worker(self, dxf: Path, kmz: Path | None, out: Path) -> None:
        try:
            analysis = self._analyze(dxf, kmz, out)
            self.after(0, lambda a=analysis, o=out: self.analysis_done(a, o))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda msg=message: self.failed(msg))

    def _analyze(self, dxf: Path, kmz: Path | None, out: Path):
        analysis = analyze_road(
            dxf,
            kmz,
            curve_tolerance_m=0.10,
            centerline_handle=self.selected_centerline_handle,
        )
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
        return analysis

    def analysis_done(self, analysis, out: Path) -> None:
        self.set_free()
        self.progress["value"] = 100
        self.status.set("Análise concluída.")
        self.metrics["ext"].set(f"{analysis.extension_m / 1000:.3f} km")
        self.metrics["cut"].set(str(analysis.category_counts.get("cut", 0)))
        self.metrics["fill"].set(str(analysis.category_counts.get("fill", 0)))
        self.metrics["mark"].set(str(analysis.category_counts.get("marking", 0)))
        lines = [f"Extensão: {analysis.extension_m / 1000:.3f} km"]
        if analysis.main_centerline_handle:
            lines.append(f"Eixo ativo: entidade {analysis.main_centerline_handle}")
        if self.local_imagery_path:
            lines.append(f"Imagem local: {self.local_imagery_path}")
        if analysis.km_start_m is not None:
            lines.extend([
                f"Km inicial: {format_station(analysis.km_start_m)}",
                f"Km final: {format_station(analysis.km_end_m)}",
            ])
        lines.extend(["", "OFFSETS DE CORTE / ATERRO"])
        lines.extend(
            f"{item.category.upper():<6} {item.side:<12} mediana {item.median_m:7.2f} m | "
            f"min {item.min_m:7.2f} | max {item.max_m:7.2f} | {item.layer}"
            for item in analysis.offsets
        )
        if analysis.warnings:
            lines.extend(["", "ATENÇÕES"])
            lines.extend(f"• {warning}" for warning in analysis.warnings)
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")
        self.persist()

    def start_video(self) -> None:
        values = self.validate_inputs()
        if not values:
            return
        self.set_busy("Preparando vídeo...")
        threading.Thread(target=self._video_worker, args=values, daemon=True).start()

    def _video_worker(self, dxf: Path, kmz: Path | None, out: Path) -> None:
        try:
            analysis = self.analysis
            selected_changed = bool(
                self.selected_centerline_handle
                and analysis is not None
                and analysis.main_centerline_handle != self.selected_centerline_handle
            )
            if analysis is None or Path(analysis.dxf_path) != dxf or selected_changed:
                analysis = self._analyze(dxf, kmz, out)
            width, height = (int(value) for value in self.res.get().split("x"))
            target = out / "video_rodoviario.mp4"

            def progress(value: float, text: str) -> None:
                self.after(0, lambda v=value, t=text: self._set_progress(v, t))

            render_video(
                analysis,
                target,
                width=width,
                height=height,
                fps=int(self.fps.get()),
                duration_s=int(self.duration.get()),
                zoom=int(self.zoom.get()),
                imagery=bool(self.imagery.get()),
                progress=progress,
            )
            self.after(0, lambda a=analysis, o=out, t=target: self.video_done(a, o, t))
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda msg=message: self.failed(msg))

    def _set_progress(self, value: float, text: str) -> None:
        self.progress["value"] = value * 100
        self.status.set(text)

    def video_done(self, analysis, out: Path, target: Path) -> None:
        self.analysis_done(analysis, out)
        self.progress["value"] = 100
        self.status.set("Vídeo MP4 concluído.")
        messagebox.showinfo(APP_NAME, f"Vídeo gerado com sucesso:\n{target}")

    def failed(self, message: str) -> None:
        self.set_free()
        self.status.set("Falha.")
        messagebox.showerror(APP_NAME, message)

    def output_dir(self) -> Path:
        return Path(self.out.get().strip() or SAVED_DIR)

    def open_preview(self) -> None:
        path = self.output_dir() / "preview.svg"
        if path.exists():
            webbrowser.open(path.resolve().as_uri())

    def open_folder(self) -> None:
        path = self.output_dir()
        if path.exists():
            open_path(path)

    def open_video(self) -> None:
        path = self.output_dir() / "video_rodoviario.mp4"
        if path.exists():
            open_path(path)
        else:
            messagebox.showwarning(APP_NAME, "O vídeo ainda não foi gerado.")

    def persist(self) -> None:
        save_settings({
            "dxf": self.dxf.get(),
            "kmz": self.kmz.get(),
            "local_imagery": self.local_image.get(),
            "output": self.out.get(),
            "resolution": self.res.get(),
            "fps": self.fps.get(),
            "duration": self.duration.get(),
            "zoom": self.zoom.get(),
            "imagery": self.imagery.get(),
            "centerline_handle": self.selected_centerline_handle,
        })

    def destroy(self) -> None:
        self.persist()
        super().destroy()


def main() -> None:
    RoadVideoApp().mainloop()


if __name__ == "__main__":
    main()
