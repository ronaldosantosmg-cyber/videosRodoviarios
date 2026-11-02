from videos_rodoviarios.core.models import GeometryEntity
from videos_rodoviarios.geometry.selection import pick_entity, rank_entities


def entity(handle: str, y: float, layer: str = "0") -> GeometryEntity:
    return GeometryEntity(
        handle=handle,
        dxftype="LINE",
        layer=layer,
        category="other",
        points=[(0.0, y), (100.0, y)],
    )


def test_pick_entity_uses_nearest_segment():
    entities = [entity("A", 0.0), entity("B", 5.0)]
    hit = pick_entity(entities, (50.0, 4.6), tolerance=2.0)
    assert hit is not None
    assert hit.entity.handle == "B"
    assert abs(hit.distance - 0.4) < 1e-9


def test_rank_and_cycle_overlapping_entities():
    entities = [entity("A", 0.0, "L1"), entity("B", 0.0, "L2")]
    hits = rank_entities(entities, (20.0, 0.1), tolerance=1.0)
    assert [hit.entity.handle for hit in hits] == ["A", "B"]
    assert pick_entity(entities, (20.0, 0.1), tolerance=1.0, cycle_index=1).entity.handle == "B"


def test_pick_entity_respects_category_filter():
    a = entity("A", 0.0)
    b = entity("B", 1.0)
    a.category = "edge"
    b.category = "center"
    hit = pick_entity([a, b], (20.0, 0.1), tolerance=5.0, selectable_categories={"center"})
    assert hit is not None
    assert hit.entity.handle == "B"
