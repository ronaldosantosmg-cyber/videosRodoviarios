from __future__ import annotations
from dataclasses import asdict,dataclass,field
from typing import Any
from videos_rodoviarios.core.scene import SceneObject,TrafficFlow
Point=tuple[float,float]
@dataclass(slots=True)
class GeometryEntity:
 handle:str;dxftype:str;layer:str;category:str;points:list[Point];closed:bool=False;source:str="dxf";visible:bool=True;layer_off:bool=False;layer_frozen:bool=False;user_hidden:bool=False;output_frozen:bool=False;video_hidden:bool=False
 @property
 def visible_in_viewport(self)->bool:return self.visible and not self.layer_off and not self.layer_frozen and not self.user_hidden
 @property
 def visible_in_output(self)->bool:return self.visible_in_viewport and not self.output_frozen and not self.video_hidden
 def to_dict(self)->dict[str,Any]:return asdict(self)
@dataclass(slots=True)
class TextEntity:
 handle:str;layer:str;text:str;x:float;y:float;visible:bool=True;layer_off:bool=False;layer_frozen:bool=False;user_hidden:bool=False;output_frozen:bool=False;video_hidden:bool=False
 @property
 def visible_in_viewport(self)->bool:return self.visible and not self.layer_off and not self.layer_frozen and not self.user_hidden
 @property
 def visible_in_output(self)->bool:return self.visible_in_viewport and not self.output_frozen and not self.video_hidden
@dataclass(slots=True)
class OffsetInfo:
 handle:str;layer:str;category:str;side:str;min_m:float;median_m:float;max_m:float;length_m:float
@dataclass(slots=True)
class KmlContext:
 path:str;names:list[str]=field(default_factory=list);coordinates:list[tuple[float,float,float|None]]=field(default_factory=list);centroid_lon:float|None=None;centroid_lat:float|None=None;utm_zone:int|None=None;hemisphere:str|None=None;datum:str="WGS84";geographic_epsg:int=4326;projected_epsg:int|None=None;crs_source:str="kml_wgs84";station_values_m:list[float]=field(default_factory=list)
@dataclass(slots=True)
class RoadAnalysis:
 dxf_path:str;kmz_path:str|None;entities:list[GeometryEntity];texts:list[TextEntity];main_centerline_handle:str|None;extension_m:float;km_start_m:float|None;km_end_m:float|None;station_delta_m:float|None;category_counts:dict[str,int];layer_counts:dict[str,int];offsets:list[OffsetInfo];warnings:list[str]=field(default_factory=list);kml_context:KmlContext|None=None;scene_objects:list[SceneObject]=field(default_factory=list);traffic_flows:list[TrafficFlow]=field(default_factory=list)
 def to_dict(self)->dict[str,Any]:return asdict(self)
