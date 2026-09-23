"""
Pydantic models for API request bodies and responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .graph import Node, Edge, TrafficIncident
from .vrp import OptimizationResult, Route


class OptimizationRequest(BaseModel):
    """Request to solve a routing problem with specified algorithm and parameters."""
    network_id: str = Field("noida_sector126", description="Network preset name (e.g. noida_sector126, solomon_c101, synthetic_grid)")
    algorithm: str = Field("qpso", description="Algorithm: qpso, bloch_qpso, pso, ga, sa, exact")
    num_particles: int = Field(50, ge=10, le=500, description="Swarm / population size")
    max_iterations: int = Field(100, ge=5, le=1000, description="Max iterations")
    num_vehicles: int = Field(5, ge=1, le=50, description="Fleet size available")
    vehicle_capacity: float = Field(100.0, ge=1.0, description="Vehicle payload capacity")
    # QPSO-specific parameters
    alpha_ce_start: float = Field(1.0, description="Initial contraction-expansion coefficient (QPSO)")
    alpha_ce_end: float = Field(0.5, description="Final contraction-expansion coefficient (QPSO)")
    # Traffic modifiers
    traffic_surge: float = Field(1.0, ge=0.5, le=5.0, description="Global traffic volume multiplier")
    incidents: List[TrafficIncident] = Field(default_factory=list)


class BenchmarkRequest(BaseModel):
    """Request to benchmark multiple algorithms side-by-side."""
    network_id: str = "noida_sector126"
    algorithms: List[str] = Field(default_factory=lambda: ["qpso", "bloch_qpso", "pso", "ga", "sa", "exact"])
    num_particles: int = 40
    max_iterations: int = 80
    num_vehicles: int = 5
    vehicle_capacity: float = 100.0
    runs_per_algorithm: int = 1


class BenchmarkResponse(BaseModel):
    """Response containing comparative metrics for all benchmarked algorithms."""
    instance_name: str
    network_nodes: int
    network_edges: int
    results: List[OptimizationResult]
    summary_table: List[Dict[str, Any]]
    fastest_algorithm: str
    best_solution_algorithm: str
    quantum_speedup_vs_pso: float  # Percentage improvement or speedup
    quantum_cost_reduction_vs_pso: float


class TrafficUpdateRequest(BaseModel):
    """Request to dynamically update traffic or inject an incident."""
    network_id: str = "noida_sector126"
    source: int
    target: int
    severity: float = 2.5
    is_closure: bool = False
    description: str = "Traffic incident"
