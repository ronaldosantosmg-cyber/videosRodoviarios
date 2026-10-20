from __future__ import annotations

from dataclasses import dataclass

from videos_rodoviarios.core.models import GeometryEntity, TextEntity


CLEAN_CATEGORIES = {"center", "edge", "marking", "cut", "fill", "oae"}


@dataclass(slots=True)
class LayerVisibility:
    name: str
    visible: bool
    source_off: bool = False
    source_frozen: bool = False


def collect_layer_visibility(
    entities: list[GeometryEntity],
    texts: list[TextEntity] | None = None,
) -> dict[str, LayerVisibility]:
    result: dict[str, LayerVisibility] = {}
    for item in [*entities, *(texts or [])]:
        current = result.get(item.layer)
        visible = bool(getattr(item, "visible", True))
        source_off = bool(getattr(item, "layer_off", False))
        source_frozen = bool(getattr(item, "layer_frozen", False))
        if current is None:
            result[item.layer] = LayerVisibility(
                name=item.layer,
                visible=visible,
                source_off=source_off,
                source_frozen=source_frozen,
            )
        else:
            current.visible = current.visible or visible
            current.source_off = current.source_off or source_off
            current.source_frozen = current.source_frozen or source_frozen
    return result


def apply_clean_view(
    entities: list[GeometryEntity],
    *,
    keep_source_hidden: bool = True,
) -> None:
    """Reduce visual clutter without changing the original DXF file.

    Keeps engineering layers commonly needed for road review. Source OFF/FROZEN
    layers remain hidden by default, but their entities stay loaded so a UI layer
    panel can re-enable them explicitly later.
    """
    for entity in entities:
        if keep_source_hidden and (entity.layer_off or entity.layer_frozen):
            entity.visible = False
        else:
            entity.visible = entity.category in CLEAN_CATEGORIES


def set_layer_visible(
    layer_name: str,
    visible: bool,
    entities: list[GeometryEntity],
    texts: list[TextEntity] | None = None,
) -> None:
    for entity in entities:
        if entity.layer == layer_name:
            entity.visible = visible
    for text in texts or []:
        if text.layer == layer_name:
            text.visible = visible


def visible_entities(entities: list[GeometryEntity]) -> list[GeometryEntity]:
    return [entity for entity in entities if entity.visible]


def visible_texts(texts: list[TextEntity]) -> list[TextEntity]:
    return [text for text in texts if text.visible]
