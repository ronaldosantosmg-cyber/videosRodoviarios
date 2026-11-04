import json
import os
from pathlib import Path
import pytest
from app.quarantine import move,restore,purge,DAY
from app.maintenance import clean_categories,duplicate_videos


def test_cleanup_moves_then_restores_without_overwriting(tmp_path):
    project=tmp_path/('a'*32);project.mkdir();(project/'render_tmp').mkdir();(project/'render_tmp/frame.png').write_bytes(b'frame')
    (project/'input.dxf').write_bytes(b'original');(project/'config.json').write_text('{}')
    result=clean_categories(tmp_path,['temporarios']);token=result['quarantine'][0]
    assert result['retention_days']==30 and not (project/'render_tmp').exists()
    assert (project/'input.dxf').read_bytes()==b'original'
    restore(tmp_path/'_quarentena',token,[tmp_path])
    assert (project/'render_tmp/frame.png').read_bytes()==b'frame'
    with pytest.raises(ValueError):restore(tmp_path/'_quarentena',token,[tmp_path])


def test_retention_uses_quarantine_entry_time_not_file_age(tmp_path):
    f=tmp_path/'old.tmp';f.write_bytes(b'old');os.utime(f,(0,0));now=1700000000
    token=move(f,tmp_path/'_quarentena',now=now)
    assert not purge(tmp_path/'_quarentena',now=now+29*DAY,execute=True)['removed']
    assert (tmp_path/'_quarentena'/token/'data').exists()
    assert purge(tmp_path/'_quarentena',now=now+30*DAY,execute=True)['removed']==[token]
    assert not (tmp_path/'_quarentena'/token).exists()


def test_same_names_are_distinct_and_links_not_followed(tmp_path):
    q=tmp_path/'_quarentena'
    for name in ('a','b'):
        p=tmp_path/name;p.mkdir();(p/'x.tmp').write_text(name)
    tokens=[move(tmp_path/name/'x.tmp',q) for name in ('a','b')]
    assert tokens[0]!=tokens[1]
    for name,token in zip(('a','b'),tokens):restore(q,token,[tmp_path]);assert (tmp_path/name/'x.tmp').read_text()==name
    outside=tmp_path/'real';outside.write_text('keep');link=tmp_path/'link';link.symlink_to(outside)
    with pytest.raises(ValueError):move(link,q)
    assert outside.read_text()=='keep'


def test_full_hash_dedup_preserves_referenced_and_unique_videos(tmp_path):
    root=tmp_path/'projects';project=root/('a'*32);project.mkdir(parents=True)
    videos=tmp_path/'videos';videos.mkdir();a=videos/'a.mp4';b=videos/'b.mp4';unique=videos/'unique.mp4'
    a.write_bytes(b'abc123');b.write_bytes(b'abc123');unique.write_bytes(b'abc124')
    (project/'video.json').write_text(json.dumps({'pasta_videos':str(videos),'arquivo':'b.mp4'}))
    assert duplicate_videos(root,videos)==[a]
    result=clean_categories(root,['duplicados'],videos=videos)
    assert result['items']==1 and b.exists() and unique.exists() and not a.exists()
    restore(root/'_quarentena',result['quarantine'][0],[root,videos])
    assert a.read_bytes()==b.read_bytes()
