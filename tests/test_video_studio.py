import ezdxf

from app.encoding import ffmpeg_exe, validate_mp4
from app.models import Settings
from app.render import render


def test_mp4_hd_com_eixo_autorizado_decodifica_todos_os_quadros(tmp_path):
    document = ezdxf.new()
    document.layers.new('EIXO')
    document.layers.new('PAVIMENTO')
    model = document.modelspace()
    model.add_lwpolyline([(500000, 7800000), (500600, 7800000)], dxfattribs={'layer': 'EIXO'})
    hatch = model.add_hatch(dxfattribs={'layer': 'PAVIMENTO'})
    hatch.paths.add_polyline_path([(500000, 7799990), (500600, 7799990), (500600, 7800010), (500000, 7800010)], is_closed=True)
    document.saveas(tmp_path / 'input.dxf')
    settings = Settings(width=1280, fps=24, duration_s=3, imagery='neutral', hydrography=False,
                        coordinates_confirmed=True, route_directions={'layer:EIXO': 'forward'},
                        render_profile='rapido', render_workers=1, encoder='cpu')
    output = render(tmp_path, settings)
    check = validate_mp4(ffmpeg_exe(), output, 72, 1280, 720, 24)
    assert check['ok'], check
    assert check['frames_decoded'] == 72
