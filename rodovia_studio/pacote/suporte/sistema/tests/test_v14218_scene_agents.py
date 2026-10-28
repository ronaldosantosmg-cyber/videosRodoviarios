import json
import numpy as np
from test_v1425_scene3d import project
from app.scene3d import build
from app.models import Settings
from app import store


def test_real_scene_contains_shared_pedestrian_tracks_bridge_and_smoke_configuration(tmp_path):
    d,s=project(tmp_path)
    data=s.model_dump();data.update(duration_s=12,pedestrians=True,traffic_density=1,pedestrian_paths=[dict(id='walk',points=[dict(x=500100,y=7800025),dict(x=500400,y=7800025)],people_per_100m=5)],pois=[dict(id='bridge',title='Passarela',kind='passarela',x=500250,y=7800000,bridge_span_m=50)],railways=[dict(id='rail',points=[dict(x=500050,y=7799700),dict(x=500050,y=7800300)],start_s=0,speed_kmh=40,min_wagons=5,max_wagons=5)])
    s=Settings.model_validate(data);store.write_json(d/'config.json',s.model_dump());scene=build(d,s)
    assert scene['pedestrians'] and scene['pedestrian_report']['admitted']>0 and scene['rail_smoke']
    assert any(m['role']=='passarela' for m in scene['meshes'])
    assert any(v['type']=='rail_locomotive' and isinstance(v['smoke_seed'],int) for v in scene['vehicles'])
    assert all(len(row)==7 and np.isfinite(row).all() for p in scene['pedestrians'] for row in p['samples'])
    json.dumps(scene,allow_nan=False)
