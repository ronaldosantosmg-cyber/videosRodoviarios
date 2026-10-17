from __future__ import annotations

from videos_rodoviarios import app
from videos_rodoviarios.render.final_renderer import render_video


def main() -> None:
    app.render_video = render_video
    app.main()


if __name__ == "__main__":
    main()
