from app.maintenance import clean

def test_cleanup_preserves_originals_and_exports(tmp_path):
    project=tmp_path/'project';project.mkdir()
    for name in ['input.dxf','input.kmz','config.json','video.mp4','preview.png']:(project/name).write_bytes(b'KEEP')
    for name in ['cache_geometria','imagery','hidrografia']:
        p=project/name;p.mkdir();(p/'cache.bin').write_bytes(b'x'*100)
    (project/'video.partial.mp4').write_bytes(b'x'*20)
    assert clean(tmp_path)['bytes']==320
    assert (project/'video.partial.mp4').exists()
    result=clean(tmp_path,True);assert result['bytes']==320 and not result['errors']
    for name in ['input.dxf','input.kmz','config.json','video.mp4','preview.png']:assert (project/name).read_bytes()==b'KEEP'
    assert clean(tmp_path)['bytes']==0
