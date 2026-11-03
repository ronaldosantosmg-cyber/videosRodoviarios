import json
import pytest
import ezdxf

from app.encoding import ffmpeg_exe, validate_mp4
from app.models import Settings
from app.render import render


@pytest.mark.parametrize('lighting',['off','night'])
def test_mp4_hd_com_eixo_autorizado_decodifica_todos_os_quadros(tmp_path,lighting):
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
                        render_profile='rapido', render_workers=1, encoder='cpu',day_night=lighting)
    output = render(tmp_path, settings)
    check = validate_mp4(ffmpeg_exe(), output, 72, 1280, 720, 24)
    assert check['ok'], check
    assert check['frames_decoded'] == 72

    metadata=json.loads((tmp_path/'video.json').read_text())
    assert set(metadata['stage_seconds'])=={'scene','detail_images','traffic','render_and_encode','validation'}
    assert metadata['motion_audit']['initialization']['warmup_seconds']==0.
    assert metadata['motion_audit']['flow_balance']['conserved']
    assert not metadata['motion_audit']['gold_rule']['violations']
