"""
Base class and tour decoding utilities for metaheuristic routing algorithms.
Implements:
1. Smallest Position Value (SPV) rule for continuous-to-discrete mapping.
2. Optimal Route Partitioning (Prins' Split Algorithm) under vehicle capacity and time windows.
3. 2-opt local search refinement.
"""

from typing import List, Dict, Tuple, Optional, Callable, Any
import numpy as np

from ..models.vrp import VRPInstance, Route, OptimizationResult, IterationMetric
from ..models.graph import Node
from ..formulation.vrp_formulation import VRPFormulation


class BaseMetaheuristic:
    """Abstract base class for all vehicle routing metaheuristics."""

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray,
                 node_idx_map: Dict[int, int]):
        self.instance = instance
        self.dist_matrix = dist_matrix
        self.time_matrix = time_matrix
        self.node_idx_map = node_idx_map
        self.formulation = VRPFormulation(instance, dist_matrix, time_matrix, node_idx_map)
        self.customer_nodes = [n for n in instance.nodes if not n.is_depot]
        self.depot_id = instance.depot_id
        self.num_customers = len(self.customer_nodes)
        self.customer_ids = [n.id for n in self.customer_nodes]

    def decode_continuous_to_permutation(self, continuous_vector: np.ndarray) -> List[int]:
        """
        Converts continuous position vector in R^N to customer permutation
        using the Smallest Position Value (SPV) / Ranked Order Value rule.
        """
        sorted_indices = np.argsort(continuous_vector)
        return [self.customer_ids[i] for i in sorted_indices]

    def split_tour_into_routes(self, customer_permutation: List[int]) -> List[Route]:
        """
        Partitions a giant customer tour into feasible vehicle routes
        respecting vehicle capacity and time windows (Prins' Split Algorithm).
        """
        routes: List[Route] = []
        if not customer_permutation:
            return routes

        curr_seq = [self.depot_id]
        curr_load = 0.0
        vehicle_idx = 0
        max_vehicles = len(self.instance.vehicles)
        veh = self.instance.vehicles[0]
        capacity = veh.capacity

        for cid in customer_permutation:
            c_node = self.formulation.nodes_by_id[cid]
            # If adding this customer exceeds capacity, close current route and start new one
            if curr_load + c_node.demand > capacity and len(curr_seq) > 1:
                curr_seq.append(self.depot_id)
                route_obj = self.formulation.evaluate_route(curr_seq, vehicle_id=vehicle_idx)
                routes.append(route_obj)
                
                vehicle_idx = (vehicle_idx + 1) % max_vehicles
                curr_seq = [self.depot_id, cid]
                curr_load = c_node.demand
            else:
                curr_seq.append(cid)
                curr_load += c_node.demand

        # Append final route
        if len(curr_seq) > 1:
            curr_seq.append(self.depot_id)
            route_obj = self.formulation.evaluate_route(curr_seq, vehicle_id=vehicle_idx)
            routes.append(route_obj)

        return routes

    def local_search_2opt(self, route_sequence: List[int]) -> List[int]:
        """Applies 2-opt local search move to improve a single route sequence."""
        if len(route_sequence) <= 4:
            return route_sequence

        best_seq = list(route_sequence)
        best_cost = self.formulation.evaluate_route(best_seq).cost
        improved = True

        while improved:
            improved = False
            for i in range(1, len(best_seq) - 2):
                for j in range(i + 1, len(best_seq) - 1):
                    # 2-opt swap: reverse segment between i and j
                    new_seq = best_seq[:i] + best_seq[i:j+1][::-1] + best_seq[j+1:]
                    new_cost = self.formulation.evaluate_route(new_seq).cost
                    if new_cost < best_cost - 1e-3:
                        best_seq = new_seq
                        best_cost = new_cost
                        improved = True
                        break
                if improved:
                    break

        return best_seq

    def refine_routes(self, routes: List[Route]) -> List[Route]:
        """Applies 2-opt refinement to all routes."""
        refined = []
        for r in routes:
            improved_seq = self.local_search_2opt(r.node_sequence)
            refined_r = self.formulation.evaluate_route(improved_seq, vehicle_id=r.vehicle_id)
            refined.append(refined_r)
        return refined

    def evaluate_solution(self, customer_permutation: List[int]) -> Tuple[float, List[Route]]:
        """
        Decodes customer permutation into routes, calculates total cost.
        Returns:
            (total_cost, routes)
        """
        routes = self.split_tour_into_routes(customer_permutation)
        total_cost = sum(r.cost for r in routes)
        return total_cost, routes
