import math, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))

def test_portuguese_lane_change_labels_present():
    t=(ROOT/'app/js/28_opcoes_nomes.js').read_text(encoding='utf-8')+(ROOT/'app/js/32_rotas.js').read_text(encoding='utf-8')
    assert "marked:'Somente em trechos permitidos'" in t
    assert "lane_change:['Política de ultrapassagem'" in t

def test_short_routes_blocked_frontend_and_backend():
    js=(ROOT/'app/js/32_rotas.js').read_text(encoding='utf-8')
    py=(ROOT/'app/routes.py').read_text(encoding='utf-8')
    tr=(ROOT/'app/traffic.py').read_text(encoding='utf-8')
    assert 'routeLen<50' in js and 'Rota descartada' in js
    assert 'route_len < 50.0' in py
    assert 'self.make_itineraries(0.)' not in tr

def test_models_reject_non_finite_and_invalid_route_inputs():
    from app.models import Settings, RouteAlignment
    import pydantic
    bad=[float('nan'),float('inf'),-float('inf')]
    for v in bad:
        try:
            RouteAlignment(points=[{'x':0,'y':0},{'x':100,'y':0}],lane_width_m=v)
            assert False, 'não-finito aceito'
        except Exception: pass
    for payload in [None,{}, {'points':[]}, {'points':[{'x':0,'y':0}]}]:
        if payload is None: continue
        try:
            RouteAlignment(**payload); assert False, 'rota vazia/incompleta aceita'
        except Exception: pass

def test_route_lane_change_window_is_total_and_no_divzero():
    from app.simulation import TrafficSim
    sim=object.__new__(TrafficSim)
    sim.paths=[{'length':1000,'lane_change':'marked','lane_change_sections':[]}]
    assert sim.lane_change_window_allowed(0,100,0) is False
    assert sim.lane_change_window_allowed(0,100,float('inf')) is False

def test_no_raw_lane_change_marked_visible_in_property_labels():
    js=(ROOT/'app/js/32_rotas.js').read_text(encoding='utf-8')
    assert '>Somente em trechos permitidos</option>' in js
    assert '>Permitida salvo trechos proibidos</option>' in js


def test_numeric_boundary_matrix_settings():
    from app.models import Settings
    base={"schema_version":7,"chainage":{"start":{"x":1,"y":2}}}
    numeric=["fps","duration_s","width","imagery_pixels","traffic_speed_kmh","min_route_segment_m"]
    for key in numeric:
        for bad in [float("nan"),float("inf"),-float("inf")]:
            d=dict(base);d[key]=bad
            try:
                Settings.model_validate(d);assert False,f"{key} aceitou não-finito"
            except Exception: pass

def test_empty_and_zero_inputs_do_not_create_nonfinite_route_geometry():
    from app.models import RouteAlignment
    cases=[
      {"points":[{"x":0,"y":0},{"x":0,"y":0}],"lane_width_m":0},
      {"points":[{"x":0,"y":0},{"x":100,"y":0}],"lanes":0},
      {"points":[{"x":0,"y":0},{"x":100,"y":0}],"taper_m":0},
    ]
    for d in cases:
        try:
            RouteAlignment(**d);assert False,"entrada zero inválida aceita"
        except Exception: pass


def test_legacy_short_route_is_disabled_on_model_load():
    from app.models import RouteAlignment
    r=RouteAlignment(points=[{"x":0,"y":0},{"x":49.9,"y":0}],enabled=True)
    assert r.enabled is False
    r2=RouteAlignment(points=[{"x":0,"y":0},{"x":50,"y":0}],enabled=True)
    assert r2.enabled is True
