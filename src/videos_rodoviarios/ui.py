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

APP_NAME = "Vídeos Rodoviários"
SETTINGS_PATH = Path.home() / ".videos_rodoviarios.json"


def default_output_for(dxf: str) -> str:
    if not dxf:
        return str(Path.home() / "VideosRodoviarios_Output")
    return str(Path(dxf).resolve().parent / "resultado_video_rodoviario")


def load_settings() -> dict[str, str]:
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data: dict[str, str]) -> None:
    try:
        SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
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
        super().__init__()
        self.title(APP_NAME)
        self.geometry("980x720")
        self.minsize(860, 650)
        self.analysis = None
        self.settings = load_settings()
        self._build_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Metric.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("TButton", padding=7)
        style.configure("TEntry", padding=5)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Vídeos Rodoviários", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Análise automática de DXF + KMZ/KML com extensão, curvas, offsets de corte/aterro e sinalização horizontal.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 14))

        inputs = ttk.LabelFrame(root, text="1 · Arquivos do projeto", padding=12)
        inputs.pack(fill="x")
        inputs.columnconfigure(1, weight=1)

        self.dxf_var = tk.StringVar(value=self.settings.get("dxf", ""))
        self.kmz_var = tk.StringVar(value=self.settings.get("kmz", ""))
        self.out_var = tk.StringVar(value=self.settings.get("output", default_output_for(self.dxf_var.get())))

        ttk.Label(inputs, text="Projeto DXF").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(inputs, textvariable=self.dxf_var).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(inputs, text="Selecionar DXF", command=self._select_dxf).grid(row=0, column=2, padx=(8, 0), pady=5)

        ttk.Label(inputs, text="Referência KMZ/KML").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(inputs, textvariable=self.kmz_var).grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(inputs, text="Selecionar KMZ/KML", command=self._select_kmz).grid(row=1, column=2, padx=(8, 0), pady=5)

        ttk.Label(inputs, text="Pasta de saída").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(inputs, textvariable=self.out_var).grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Button(inputs, text="Escolher pasta", command=self._select_output).grid(row=2, column=2, padx=(8, 0), pady=5)

        controls = ttk.LabelFrame(root, text="2 · Processamento", padding=12)
        controls.pack(fill="x", pady=12)
        controls.columnconfigure(0, weight=1)

        row = ttk.Frame(controls)
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)
        self.analyze_btn = ttk.Button(row, text="ANALISAR PROJETO", style="Primary.TButton", command=self._start_analysis)
        self.analyze_btn.grid(row=0, column=0, sticky="ew")

        options = ttk.Frame(controls)
        options.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(options, text="Precisão das curvas:").pack(side="left")
        self.tol_var = tk.StringVar(value=self.settings.get("tolerance", "0.10"))
        ttk.Combobox(
            options,
            textvariable=self.tol_var,
            state="readonly",
            width=10,
            values=("0.50", "0.20", "0.10", "0.05", "0.02"),
        ).pack(side="left", padx=(6, 14))
        ttk.Label(options, text="m · menor valor = curva mais suave").pack(side="left")

        self.progress = ttk.Progressbar(controls, mode="indeterminate")
        self.progress.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.status_var = tk.StringVar(value="Aguardando arquivos.")
        ttk.Label(controls, textvariable=self.status_var).grid(row=3, column=0, sticky="w", pady=(5, 0))

        results = ttk.LabelFrame(root, text="3 · Resultado", padding=12)
        results.pack(fill="both", expand=True)

        metrics = ttk.Frame(results)
        metrics.pack(fill="x")
        for i in range(4):
            metrics.columnconfigure(i, weight=1)
        self.metric_vars = {
            "ext": tk.StringVar(value="—"),
            "cut": tk.StringVar(value="—"),
            "fill": tk.StringVar(value="—"),
            "mark": tk.StringVar(value="—"),
        }
        self._metric(metrics, 0, "Extensão", self.metric_vars["ext"])
        self._metric(metrics, 1, "Corte", self.metric_vars["cut"])
        self._metric(metrics, 2, "Aterro", self.metric_vars["fill"])
        self._metric(metrics, 3, "Sinalização", self.metric_vars["mark"])

        self.details = tk.Text(results, height=12, wrap="word", font=("Consolas", 10))
        self.details.pack(fill="both", expand=True, pady=(12, 10))
        self.details.insert("1.0", "Os detalhes técnicos aparecerão aqui após a análise.")
        self.details.configure(state="disabled")

        actions = ttk.Frame(results)
        actions.pack(fill="x")
        self.preview_btn = ttk.Button(actions, text="Ver prévia", command=self._open_preview, state="disabled")
        self.preview_btn.pack(side="left")
        self.folder_btn = ttk.Button(actions, text="Abrir pasta de resultados", command=self._open_output, state="disabled")
        self.folder_btn.pack(side="left", padx=8)
        self.json_btn = ttk.Button(actions, text="Abrir relatório JSON", command=self._open_json, state="disabled")
        self.json_btn.pack(side="left")

    def _metric(self, parent: ttk.Frame, col: int, title: str, var: tk.StringVar) -> None:
        box = ttk.Frame(parent, padding=8)
        box.grid(row=0, column=col, sticky="nsew", padx=4)
        ttk.Label(box, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(box, textvariable=var, style="Metric.TLabel").pack(anchor="w")

    def _select_dxf(self) -> None:
        path = filedialog.askopenfilename(title="Selecione o DXF", filetypes=[("DXF", "*.dxf")])
        if path:
            self.dxf_var.set(path)
            if not self.out_var.get() or self.out_var.get().endswith("VideosRodoviarios_Output"):
                self.out_var.set(default_output_for(path))

    def _select_kmz(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o KMZ/KML",
            filetypes=[("KMZ/KML", "*.kmz *.kml"), ("KMZ", "*.kmz"), ("KML", "*.kml")],
        )
        if path:
            self.kmz_var.set(path)

    def _select_output(self) -> None:
        path = filedialog.askdirectory(title="Selecione a pasta de saída")
        if path:
            self.out_var.set(path)

    def _validate(self) -> tuple[Path, Path | None, Path, float] | None:
        dxf = Path(self.dxf_var.get().strip())
        kmz_text = self.kmz_var.get().strip()
        kmz = Path(kmz_text) if kmz_text else None
        output = Path(self.out_var.get().strip() or default_output_for(str(dxf)))
        try:
            tol = float(self.tol_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror(APP_NAME, "A precisão das curvas é inválida.")
            return None
        if not dxf.exists() or dxf.suffix.lower() != ".dxf":
            messagebox.showerror(APP_NAME, "Selecione um arquivo DXF válido.")
            return None
        if kmz and (not kmz.exists() or kmz.suffix.lower() not in {".kmz", ".kml"}):
            messagebox.showerror(APP_NAME, "Selecione um arquivo KMZ/KML válido ou deixe o campo vazio.")
            return None
        return dxf, kmz, output, tol

    def _start_analysis(self) -> None:
        validated = self._validate()
        if not validated:
            return
        self.analyze_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        self.folder_btn.configure(state="disabled")
        self.json_btn.configure(state="disabled")
        self.status_var.set("Analisando geometrias, curvas, offsets e sinalização...")
        self.progress.start(12)
        threading.Thread(target=self._run_analysis, args=validated, daemon=True).start()

    def _run_analysis(self, dxf: Path, kmz: Path | None, output: Path, tol: float) -> None:
        try:
            analysis = analyze_road(dxf, kmz, curve_tolerance_m=tol)
            output.mkdir(parents=True, exist_ok=True)
            write_analysis_json(analysis, output / "analise.json")
            write_geojson(analysis, output / "geometrias_dxf.geojson")
            try:
                if analysis.kml_context and analysis.kml_context.utm_zone:
                    write_geojson(analysis, output / "geometrias_wgs84.geojson", to_wgs84=True)
            except Exception:
                pass
            write_svg_preview(analysis, output / "preview.svg")
            self.analysis = analysis
            self.after(0, lambda a=analysis, o=output: self._analysis_done(a, o))
        except Exception as exc:
            error_message = str(exc)
            self.after(0, lambda msg=error_message: self._analysis_failed(msg))

    def _analysis_done(self, analysis, output: Path) -> None:
        self.progress.stop()
        self.analyze_btn.configure(state="normal")
        self.preview_btn.configure(state="normal")
        self.folder_btn.configure(state="normal")
        self.json_btn.configure(state="normal")
        self.status_var.set("Análise concluída com sucesso.")
        self.metric_vars["ext"].set(f"{analysis.extension_m / 1000:.3f} km")
        self.metric_vars["cut"].set(str(analysis.category_counts.get("cut", 0)))
        self.metric_vars["fill"].set(str(analysis.category_counts.get("fill", 0)))
        self.metric_vars["mark"].set(str(analysis.category_counts.get("marking", 0)))

        lines = [f"Extensão geométrica do eixo: {analysis.extension_m / 1000:.3f} km"]
        if analysis.km_start_m is not None:
            lines.append(f"Km inicial: {format_station(analysis.km_start_m)}")
            lines.append(f"Km final:   {format_station(analysis.km_end_m)}")
        lines.append("")
        lines.append("OFFSETS DE CORTE / ATERRO")
        if analysis.offsets:
            for item in analysis.offsets:
                lines.append(
                    f"{item.category.upper():<7} | {item.side:<12} | mediana {item.median_m:7.2f} m | "
                    f"mín {item.min_m:7.2f} | máx {item.max_m:7.2f} | {item.layer}"
                )
        else:
            lines.append("Nenhum offset de corte/aterro foi reconhecido.")
        if analysis.warnings:
            lines.append("")
            lines.append("ATENÇÕES")
            lines.extend(f"• {warning}" for warning in analysis.warnings)

        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")
        save_settings(
            {
                "dxf": self.dxf_var.get(),
                "kmz": self.kmz_var.get(),
                "output": self.out_var.get(),
                "tolerance": self.tol_var.get(),
            }
        )
        messagebox.showinfo(APP_NAME, f"Análise concluída.\n\nResultados em:\n{output}")

    def _analysis_failed(self, message: str) -> None:
        self.progress.stop()
        self.analyze_btn.configure(state="normal")
        self.status_var.set("Falha na análise.")
        messagebox.showerror(APP_NAME, f"Não foi possível concluir a análise:\n\n{message}")

    def _output_path(self) -> Path:
        return Path(self.out_var.get().strip() or default_output_for(self.dxf_var.get()))

    def _open_preview(self) -> None:
        path = self._output_path() / "preview.svg"
        if path.exists():
            webbrowser.open(path.resolve().as_uri())
        else:
            messagebox.showwarning(APP_NAME, "A prévia ainda não foi gerada.")

    def _open_output(self) -> None:
        path = self._output_path()
        if path.exists():
            open_path(path)

    def _open_json(self) -> None:
        path = self._output_path() / "analise.json"
        if path.exists():
            open_path(path)

    def _on_close(self) -> None:
        save_settings(
            {
                "dxf": self.dxf_var.get(),
                "kmz": self.kmz_var.get(),
                "output": self.out_var.get(),
                "tolerance": self.tol_var.get(),
            }
        )
        self.destroy()


def main() -> None:
    RoadVideoApp().mainloop()


if __name__ == "__main__":
    main()
