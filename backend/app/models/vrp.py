"""
Data models for the Vehicle Routing Problem (VRP), vehicle definitions,
routes, optimization convergence metrics, and solutions.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .graph import Node


class Vehicle(BaseModel):
    """Represents a fleet vehicle."""
    id: int
    capacity: float = Field(100.0, description="Maximum payload capacity")
    fixed_cost: float = Field(10.0, description="Fixed dispatch cost per vehicle used")
    cost_per_meter: float = Field(0.001, description="Variable cost per meter")
    cost_per_second: float = Field(0.01, description="Variable cost per second of travel time")
    max_travel_time: float = Field(86400.0, description="Max route duration in seconds")


class VRPInstance(BaseModel):
    """Represents a full VRP instance problem definition."""
    name: str
    nodes: List[Node]
    depot_id: int
    vehicles: List[Vehicle]
    vehicle_capacity: float = 100.0
    num_vehicles: int = 5
    tardiness_penalty_per_sec: float = 0.05
    time_window_strict: bool = False  # If True, tardiness is not allowed


class Route(BaseModel):
    """Represents an optimized route for a single vehicle."""
    vehicle_id: int
    node_sequence: List[int] = Field(..., description="Ordered list of node IDs visited, starting and ending at depot")
    total_distance: float = 0.0
    total_travel_time: float = 0.0
    total_waiting_time: float = 0.0
    total_delay: float = 0.0
    total_load: float = 0.0
    cost: float = 0.0
    arrival_times: Dict[int, float] = {}
    departure_times: Dict[int, float] = {}


class IterationMetric(BaseModel):
    """Represents metrics captured at each iteration of optimization."""
    iteration: int
    best_fitness: float
    mean_fitness: float
    best_cost: float
    best_travel_time: float
    best_distance: float
    diversity_metric: Optional[float] = None
    quantum_parameter: Optional[float] = None  # e.g., alpha / beta CE coefficient


class OptimizationResult(BaseModel):
    """Complete output returned by an optimization algorithm."""
    algorithm_name: str
    instance_name: str
    routes: List[Route]
    total_cost: float
    total_travel_time: float
    total_distance: float
    total_tardiness: float
    vehicles_used: int
    execution_time_ms: float
    iterations_run: int
    convergence_history: List[IterationMetric] = []
    is_feasible: bool = True
    constraint_violations: List[str] = []
