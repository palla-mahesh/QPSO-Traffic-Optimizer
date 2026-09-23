"""
Graph data models representing nodes (intersections/depots) and edges (roads)
with dynamic congestion attributes based on the Bureau of Public Roads (BPR) model.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class Node(BaseModel):
    """Represents a transportation network node (intersection, depot, or delivery location)."""
    id: int
    name: str = ""
    x: float = Field(..., description="X coordinate (meters) or Longitude")
    y: float = Field(..., description="Y coordinate (meters) or Latitude")
    is_depot: bool = False
    demand: float = Field(0.0, description="Customer demand (e.g. package weight/volume)")
    service_time: float = Field(0.0, description="Service / unloading time at this location (seconds)")
    ready_time: float = Field(0.0, description="Earliest time window start (seconds from t=0)")
    due_time: float = Field(86400.0, description="Latest time window end (seconds from t=0)")


class Edge(BaseModel):
    """
    Represents a directed road segment connecting two nodes.
    Travel time is dynamically computed using the BPR function:
        t(V) = t0 * [1 + alpha * (V / C)^beta]
    """
    source: int
    target: int
    distance: float = Field(..., description="Physical road length in meters")
    free_flow_speed: float = Field(13.89, description="Free-flow speed limit in m/s (default 50 km/h)")
    capacity: float = Field(1000.0, description="Practical hourly capacity (vehicles/hour)")
    current_volume: float = Field(200.0, description="Current vehicle traffic volume (vehicles/hour)")
    alpha_bpr: float = Field(0.15, description="BPR standard coefficient alpha")
    beta_bpr: float = Field(4.0, description="BPR standard exponent beta")
    congestion_factor: float = Field(1.0, description="Disruption / incident multiplier (1.0 = normal, 2.5 = heavy jam)")
    is_closed: bool = Field(False, description="Whether the road is closed due to incident/construction")

    @property
    def free_flow_time(self) -> float:
        """Free-flow travel time in seconds."""
        if self.free_flow_speed <= 0:
            return float('inf')
        return self.distance / self.free_flow_speed

    def compute_travel_time(self, volume: Optional[float] = None, incident_multiplier: Optional[float] = None) -> float:
        """
        Compute dynamic travel time in seconds using the BPR function.
        """
        if self.is_closed:
            return float('inf')
        
        v = volume if volume is not None else self.current_volume
        inc = incident_multiplier if incident_multiplier is not None else self.congestion_factor
        t0 = self.free_flow_time
        
        if self.capacity <= 0:
            return t0 * inc
            
        v_c_ratio = max(0.0, v / self.capacity)
        # BPR formula: t = t0 * (1 + alpha * (V/C)^beta) * incident_multiplier
        t = t0 * (1.0 + self.alpha_bpr * (v_c_ratio ** self.beta_bpr)) * inc
        return t


class TrafficIncident(BaseModel):
    """Represents a dynamic road incident (accident, roadblock, rush hour spike)."""
    id: str
    source: int
    target: int
    severity: float = Field(2.0, description="Congestion multiplier (e.g. 2.0 = 2x travel time)")
    description: str = ""
    is_closure: bool = False
    duration_seconds: float = 3600.0
