import pytest
from pydantic import ValidationError
from app.models import Settings
from app.dependencies import geometry_cache_key,revisions


def test_internal_final_resolution_preserves_geometry_and_editor_cache(tmp_path):
    public=Settings(width=1920,render_profile='final')
    internal=public.model_copy(update={'width':2880})
    assert geometry_cache_key(tmp_path,public)==geometry_cache_key(tmp_path,internal)
    a=revisions(tmp_path,public);b=revisions(tmp_path,internal)
    assert a['geometry']==b['geometry'] and a['editor']==b['editor']
    assert a['video']!=b['video']


def test_external_invalid_resolution_is_still_rejected(tmp_path):
    with pytest.raises(ValidationError):geometry_cache_key(tmp_path,{'width':2880})
    with pytest.raises(ValidationError):revisions(tmp_path,{'width':2880})


def test_final_full_hd_export_keeps_supersampling_and_decodes(tmp_path):
    import json
    from app.render import render
    from test_traffic_pipeline import project
    settings=project(tmp_path).model_copy(update={'width':1920,'duration_s':3.,'render_profile':'final'})
    output=render(tmp_path,settings)
    metadata=json.loads((tmp_path/'video.json').read_text())
    assert output.is_file()
    assert metadata['validation']['frames_decoded']==72
    assert metadata['validation']['width']==1920 and metadata['validation']['height']==1080
