from __future__ import annotations

from videos_rodoviarios import __revision__, __revision_name__, app
from videos_rodoviarios.cad_interaction import install_cad_interactions
from videos_rodoviarios.paths import SAVED_DIR, ensure_app_dirs, settings_path
from videos_rodoviarios.render.router import render_video


def main() -> None:
    ensure_app_dirs()
    app.SETTINGS = settings_path()
    app.render_video = render_video
    window = app.RoadVideoApp()
    window.title(f"Vídeos Rodoviários · {__revision__} · {__revision_name__}")
    if not window.out.get().strip():
        window.out.set(str(SAVED_DIR))
    install_cad_interactions(window)
    window.mainloop()


if __name__ == "__main__":
    main()
