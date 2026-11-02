"""Vehicle Micro-Simulation Engine (autônomo: não depende do resto do aplicativo)."""
from .params import IDMParams,MobilParams,VehicleParams,EngineParams
from .network import BoundaryKind,LayerRules,Lane,TrafficSignal,StopLine,LaneClosure,RoadNetwork,parallel_lanes
from .vehicle import Vehicle,Phase
from .engine import Simulation
from .geometry import OBB,SpatialHash,separation,conflicts
from .idm import idm_accel
