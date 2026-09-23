"""
Simulated Annealing (SA) baseline for Vehicle Routing.
Implements:
1. Metropolis acceptance criterion: P = exp(-Delta_E / T)
2. Geometric cooling schedule: T_{k+1} = alpha * T_k
3. Multi-operator neighborhood generation (swap, relocate, 2-opt inversion).
"""

from typing import List, Dict, Tuple, Optional, Callable
import time
import math
import random
import numpy as np

from .base import BaseMetaheuristic
from ..models.vrp import VRPInstance, Route, OptimizationResult, IterationMetric


class SimulatedAnnealing(BaseMetaheuristic):
    """
    Simulated Annealing baseline for comparative benchmarking.
    """

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray,
                 node_idx_map: Dict[int, int], max_iterations: int = 100,
                 initial_temp: float = 1000.0, cooling_rate: float = 0.95,
                 steps_per_temp: int = 50):
        super().__init__(instance, dist_matrix, time_matrix, node_idx_map)
        self.max_iterations = max_iterations
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.steps_per_temp = steps_per_temp

    def _neighbor(self, permutation: List[int]) -> List[int]:
        """Generates a neighboring permutation via swap, relocate, or 2-opt inversion."""
        c = list(permutation)
        if len(c) < 2:
            return c

        move_type = random.choice(["swap", "relocate", "invert"])
        if move_type == "swap":
            i, j = random.sample(range(len(c)), 2)
            c[i], c[j] = c[j], c[i]
        elif move_type == "relocate":
            i = random.randrange(len(c))
            item = c.pop(i)
            j = random.randrange(len(c) + 1)
            c.insert(j, item)
        else:
            i, j = sorted(random.sample(range(len(c)), 2))
            c[i:j+1] = c[i:j+1][::-1]
        return c

    def optimize(self, callback: Optional[Callable[[IterationMetric], None]] = None) -> OptimizationResult:
        start_time = time.time()
        curr_permutation = list(self.customer_ids)
        random.shuffle(curr_permutation)

        curr_cost, curr_routes = self.evaluate_solution(curr_permutation)
        best_permutation = list(curr_permutation)
        best_cost = curr_cost
        best_routes = curr_routes

        T = self.initial_temp
        convergence_history: List[IterationMetric] = []

        for it in range(1, self.max_iterations + 1):
            for _ in range(self.steps_per_temp):
                neighbor_perm = self._neighbor(curr_permutation)
                neighbor_cost, neighbor_routes = self.evaluate_solution(neighbor_perm)

                delta = neighbor_cost - curr_cost

                # Metropolis acceptance criterion
                if delta < 0 or (T > 1e-6 and random.random() < math.exp(-delta / T)):
                    curr_permutation = neighbor_perm
                    curr_cost = neighbor_cost
                    curr_routes = neighbor_routes

                    if curr_cost < best_cost:
                        best_cost = curr_cost
                        best_routes = curr_routes
                        best_permutation = list(curr_permutation)

            # Cool down
            T = max(1e-4, T * self.cooling_rate)

            best_travel_time = sum(r.total_travel_time for r in best_routes)
            best_distance = sum(r.total_distance for r in best_routes)

            metric = IterationMetric(
                iteration=it,
                best_fitness=float(best_cost),
                mean_fitness=float(curr_cost),
                best_cost=float(best_cost),
                best_travel_time=float(best_travel_time),
                best_distance=float(best_distance),
                quantum_parameter=float(T)
            )
            convergence_history.append(metric)

            if callback is not None:
                callback(metric)

        refined_routes = self.refine_routes(best_routes)
        refined_cost = sum(r.cost for r in refined_routes)
        if refined_cost < best_cost:
            final_routes = refined_routes
            final_cost = refined_cost
        else:
            final_routes = best_routes
            final_cost = best_cost

        elapsed_ms = (time.time() - start_time) * 1000.0

        total_time = sum(r.total_travel_time for r in final_routes)
        total_dist = sum(r.total_distance for r in final_routes)
        total_delay = sum(r.total_delay for r in final_routes)
        is_feasible, violations = self.formulation.validate_solution(final_routes)

        return OptimizationResult(
            algorithm_name="Simulated Annealing (SA)",
            instance_name=self.instance.name,
            routes=final_routes,
            total_cost=float(final_cost),
            total_travel_time=float(total_time),
            total_distance=float(total_dist),
            total_tardiness=float(total_delay),
            vehicles_used=len(final_routes),
            execution_time_ms=float(elapsed_ms),
            iterations_run=self.max_iterations,
            convergence_history=convergence_history,
            is_feasible=is_feasible,
            constraint_violations=violations
        )
