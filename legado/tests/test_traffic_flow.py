from videos_rodoviarios.core.models import GeometryEntity
from videos_rodoviarios.geometry.traffic_flow import TrafficFlowModel, flow_from_arrow


def _road() -> GeometryEntity:
    return GeometryEntity(
        handle="ROAD1",
        dxftype="LWPOLYLINE",
        layer="EIXO",
        category="center",
        points=[(0.0, 0.0), (20.0, 0.0), (40.0, 0.0)],
    )


def test_arrow_builds_forward_flow_on_nearest_segment():
    segment = flow_from_arrow((10.0, 1.0), (14.0, 1.0), [_road()], tolerance_m=3.0)
    assert segment.entity_handle == "ROAD1"
    assert segment.forward is True
    assert segment.start == (0.0, 0.0)
    assert segment.end == (20.0, 0.0)


def test_arrow_builds_reverse_flow():
    segment = flow_from_arrow((10.0, -1.0), (6.0, -1.0), [_road()], tolerance_m=3.0)
    assert segment.forward is False


def test_successive_arrows_form_progressive_flow():
    road = _road()
    model = TrafficFlowModel()
    first = flow_from_arrow((10.0, 0.5), (14.0, 0.5), [road], tolerance_m=2.0)
    second = flow_from_arrow((30.0, 0.5), (34.0, 0.5), [road], tolerance_m=2.0)
    model.set_segment_direction(first)
    model.set_segment_direction(second)
    assert len(model.segments) == 2
    assert all(item.forward for item in model.segments)


def test_latest_arrow_replaces_direction_for_same_segment():
    road = _road()
    model = TrafficFlowModel()
    model.set_segment_direction(flow_from_arrow((10.0, 0.5), (14.0, 0.5), [road], tolerance_m=2.0))
    model.set_segment_direction(flow_from_arrow((10.0, 0.5), (6.0, 0.5), [road], tolerance_m=2.0))
    assert len(model.segments) == 1
    assert model.segments[0].forward is False
