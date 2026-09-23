"""
Mathematical formulation of the Capacitated Vehicle Routing Problem
with Time Windows and Traffic Congestion (CVRPTW-TC).
Provides formal constraint definitions and a solution feasibility evaluator.
"""

from typing import List, Dict, Tuple, Any
import numpy as np

from ..models.vrp import VRPInstance, Route, OptimizationResult
from ..models.graph import Node


class VRPFormulation:
    """
    Mathematical Formulation for CVRPTW-TC.
    
    Sets:
      V: Set of all vertices {0, 1, ..., n}, where 0 is the depot
      C: Set of customer vertices {1, ..., n}
      K: Set of available vehicles {1, ..., m}
      E: Set of directed edges {(i, j) : i, j in V, i != j}
      
    Parameters:
      d_ij: Distance between node i and node j (meters)
      t_ij(s): Dynamic travel time from i to j starting at departure time s (seconds, BPR)
      q_i: Demand of customer i
      Q_k: Capacity of vehicle k
      [a_i, b_i]: Ready time and due time (time window) for node i
      s_i: Service duration at node i
      f_k: Fixed dispatch cost for vehicle k
      c_d: Variable cost per meter traveled
      c_t: Variable cost per second of travel time
      p_delay: Penalty cost per second of tardiness (exceeding b_i)
      
    Decision Variables:
      x_ijk in {0, 1}: 1 if vehicle k traverses edge (i, j); 0 otherwise
      S_ik >= 0: Time at which vehicle k begins service at node i
      L_ik >= 0: Cumulative load carried by vehicle k immediately after visiting node i
      u_k in {0, 1}: 1 if vehicle k is dispatched; 0 otherwise
      
    Objective Function:
      Minimize:
        Z = sum_{k in K} f_k * u_k
          + sum_{k in K} sum_{(i,j) in E} (c_d * d_ij + c_t * t_ij) * x_ijk
          + sum_{k in K} sum_{i in C} p_delay * max(0, S_ik - b_i)
          
    Subject to:
      1. Every customer visited exactly once:
         sum_{k in K} sum_{j in V, j != i} x_ijk = 1,   forall i in C
         
      2. Vehicle departure from depot:
         sum_{j in C} x_0jk = u_k,   forall k in K
         
      3. Flow conservation at each node:
         sum_{i in V, i != p} x_ipk - sum_{j in V, j != p} x_pjk = 0,   forall p in C, k in K
         
      4. Vehicle return to depot:
         sum_{i in C} x_i0k = u_k,   forall k in K
         
      5. Capacity constraint (Load accumulation & Subtour elimination):
         L_jk >= L_ik + q_j - M * (1 - x_ijk),   forall i in V, j in C, i != j, k in K
         q_i <= L_ik <= Q_k,                     forall i in C, k in K
         L_0k = 0,                               forall k in K
         
      6. Time window & travel time propagation:
         S_jk >= S_ik + s_i + t_ij(S_ik + s_i) - M * (1 - x_ijk),  forall i, j in V, k in K
         S_ik >= a_i,                             forall i in V, k in K
         S_ik <= b_i + Tardiness_ik,              forall i in V, k in K
    """

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray, node_idx_map: Dict[int, int]):
        self.instance = instance
        self.dist_matrix = dist_matrix
        self.time_matrix = time_matrix
        self.node_idx_map = node_idx_map
        self.nodes_by_id = {node.id: node for node in instance.nodes}

    def evaluate_route(self, node_sequence: List[int], vehicle_id: int = 0) -> Route:
        """
        Calculates distance, travel time, arrival/departure schedules,
        waiting times, tardiness, and objective cost for a given vehicle route.
        """
        route = Route(vehicle_id=vehicle_id, node_sequence=node_sequence)
        if len(node_sequence) <= 2:
            return route  # empty route [0, 0]

        total_dist = 0.0
        total_time = 0.0
        total_wait = 0.0
        total_delay = 0.0
        total_load = 0.0

        current_time = 0.0
        arrival_times: Dict[int, float] = {node_sequence[0]: 0.0}
        departure_times: Dict[int, float] = {node_sequence[0]: 0.0}

        veh = self.instance.vehicles[vehicle_id % len(self.instance.vehicles)]

        for idx in range(len(node_sequence) - 1):
            u_id = node_sequence[idx]
            v_id = node_sequence[idx + 1]
            u_idx = self.node_idx_map[u_id]
            v_idx = self.node_idx_map[v_id]

            # Travel distance and dynamic travel time
            d_uv = self.dist_matrix[u_idx, v_idx]
            t_uv = self.time_matrix[u_idx, v_idx]
            total_dist += d_uv
            total_time += t_uv

            # Time when vehicle reaches node v
            arrival_at_v = current_time + t_uv
            arrival_times[v_id] = arrival_at_v

            v_node = self.nodes_by_id[v_id]
            total_load += v_node.demand

            # Time window handling:
            # If vehicle arrives before ready_time, it must wait
            wait_time = max(0.0, v_node.ready_time - arrival_at_v)
            service_start = arrival_at_v + wait_time
            total_wait += wait_time

            # If vehicle arrives after due_time, calculate tardiness
            tardiness = max(0.0, service_start - v_node.due_time)
            total_delay += tardiness

            # Departure after service
            departure_from_v = service_start + v_node.service_time
            departure_times[v_id] = departure_from_v
            current_time = departure_from_v

        # Compute cost
        cost = (
            veh.fixed_cost +
            veh.cost_per_meter * total_dist +
            veh.cost_per_second * total_time +
            self.instance.tardiness_penalty_per_sec * total_delay
        )

        route.total_distance = total_dist
        route.total_travel_time = total_time
        route.total_waiting_time = total_wait
        route.total_delay = total_delay
        route.total_load = total_load
        route.cost = cost
        route.arrival_times = arrival_times
        route.departure_times = departure_times
        return route

    def validate_solution(self, routes: List[Route]) -> Tuple[bool, List[str]]:
        """
        Validates whether a set of routes satisfies all mathematical constraints.
        Returns:
            (is_feasible, list_of_violation_messages)
        """
        violations = []
        visited_customers = []
        depot_id = self.instance.depot_id

        for r_idx, route in enumerate(routes):
            seq = route.node_sequence
            if len(seq) <= 2:
                continue

            # Constraint: Route must start and end at depot
            if seq[0] != depot_id or seq[-1] != depot_id:
                violations.append(f"Route {r_idx} does not start or end at depot {depot_id}: {seq}")

            # Constraint: Vehicle capacity
            veh = self.instance.vehicles[route.vehicle_id % len(self.instance.vehicles)]
            if route.total_load > veh.capacity:
                violations.append(f"Route {r_idx} exceeds capacity: {route.total_load} > {veh.capacity}")

            # Constraint: Strict time window check (if enabled)
            if self.instance.time_window_strict and route.total_delay > 1e-4:
                violations.append(f"Route {r_idx} violates strict time windows with total delay {route.total_delay:.1f}s")

            for node_id in seq[1:-1]:
                visited_customers.append(node_id)

        # Constraint: Every customer visited exactly once
        customer_ids = [n.id for n in self.instance.nodes if not n.is_depot]
        for cid in customer_ids:
            count = visited_customers.count(cid)
            if count == 0:
                violations.append(f"Customer {cid} was never visited.")
            elif count > 1:
                violations.append(f"Customer {cid} was visited {count} times (must be exactly 1).")

        return len(violations) == 0, violations
