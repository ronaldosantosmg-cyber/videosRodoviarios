from PIL import Image

from videos_rodoviarios.render.video_renderer import DEFAULT_PROVIDER, QMS_PROVIDERS, TileCache, _background


def test_qms_catalog_has_default_provider(tmp_path, monkeypatch):
    assert DEFAULT_PROVIDER in QMS_PROVIDERS
    monkeypatch.setattr("videos_rodoviarios.render.video_renderer.SUPPORT_DIR", tmp_path)
    cache = TileCache("provedor_inexistente")
    assert cache.provider == DEFAULT_PROVIDER


def test_background_without_imagery_has_exact_size(tmp_path, monkeypatch):
    monkeypatch.setattr("videos_rodoviarios.render.video_renderer.SUPPORT_DIR", tmp_path)
    cache = TileCache()
    image = _background(cache, 1000.5, 2000.5, 640, 360, 17, False)
    assert isinstance(image, Image.Image)
    assert image.size == (640, 360)
