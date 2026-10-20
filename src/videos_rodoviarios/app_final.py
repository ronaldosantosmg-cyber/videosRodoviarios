from __future__ import annotations

from videos_rodoviarios import app
from videos_rodoviarios.cad_interaction import install_cad_interactions
from videos_rodoviarios.render.router import render_video


def main() -> None:
    app.render_video = render_video
    window = app.RoadVideoApp()
    install_cad_interactions(window)
    window.mainloop()


if __name__ == "__main__":
    main()
