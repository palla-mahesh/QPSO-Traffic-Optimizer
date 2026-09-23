"""
Classical Particle Swarm Optimization (PSO) baseline.
Implements the standard velocity and position update equations:
    V(t+1) = w * V(t) + c1 * r1 * (P_best - X(t)) + c2 * r2 * (G_best - X(t))
    X(t+1) = X(t) + V(t+1)
"""

from typing import List, Dict, Tuple, Optional, Callable
import time
import numpy as np

from .base import BaseMetaheuristic
from ..models.vrp import VRPInstance, Route, OptimizationResult, IterationMetric


class ClassicalPSO(BaseMetaheuristic):
    """
    Standard Classical PSO baseline for comparative benchmarking.
    """

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray,
                 node_idx_map: Dict[int, int], num_particles: int = 50, max_iterations: int = 100,
                 w: float = 0.7298, c1: float = 1.49618, c2: float = 1.49618):
        super().__init__(instance, dist_matrix, time_matrix, node_idx_map)
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2

    def optimize(self, callback: Optional[Callable[[IterationMetric], None]] = None) -> OptimizationResult:
        start_time = time.time()
        D = self.num_customers
        M = self.num_particles

        # Positions and velocities
        X = np.random.uniform(-5.0, 5.0, size=(M, D))
        V = np.random.uniform(-2.0, 2.0, size=(M, D))
        v_max = 4.0

        P_best = np.copy(X)
        P_best_fitness = np.full(M, float('inf'))
        P_best_routes: List[List[Route]] = [[] for _ in range(M)]

        G_best = np.zeros(D)
        G_best_fitness = float('inf')
        G_best_routes: List[Route] = []

        # Evaluate initial swarm
        for i in range(M):
            perm = self.decode_continuous_to_permutation(X[i])
            cost, routes = self.evaluate_solution(perm)
            P_best_fitness[i] = cost
            P_best_routes[i] = routes
            if cost < G_best_fitness:
                G_best_fitness = cost
                G_best = np.copy(X[i])
                G_best_routes = routes

        convergence_history: List[IterationMetric] = []

        for it in range(1, self.max_iterations + 1):
            for i in range(M):
                r1 = np.random.rand(D)
                r2 = np.random.rand(D)

                # Classical velocity update
                V[i] = (
                    self.w * V[i] +
                    self.c1 * r1 * (P_best[i] - X[i]) +
                    self.c2 * r2 * (G_best - X[i])
                )
                V[i] = np.clip(V[i], -v_max, v_max)

                # Position update
                X[i] = X[i] + V[i]

                # Evaluate new position
                perm = self.decode_continuous_to_permutation(X[i])
                cost, routes = self.evaluate_solution(perm)

                if cost < P_best_fitness[i]:
                    P_best_fitness[i] = cost
                    P_best[i] = np.copy(X[i])
                    P_best_routes[i] = routes

                    if cost < G_best_fitness:
                        G_best_fitness = cost
                        G_best = np.copy(X[i])
                        G_best_routes = routes

            best_travel_time = sum(r.total_travel_time for r in G_best_routes)
            best_distance = sum(r.total_distance for r in G_best_routes)

            metric = IterationMetric(
                iteration=it,
                best_fitness=float(G_best_fitness),
                mean_fitness=float(np.mean(P_best_fitness)),
                best_cost=float(G_best_fitness),
                best_travel_time=float(best_travel_time),
                best_distance=float(best_distance)
            )
            convergence_history.append(metric)

            if callback is not None:
                callback(metric)

        refined_routes = self.refine_routes(G_best_routes)
        refined_cost = sum(r.cost for r in refined_routes)
        if refined_cost < G_best_fitness:
            final_routes = refined_routes
            final_cost = refined_cost
        else:
            final_routes = G_best_routes
            final_cost = G_best_fitness

        elapsed_ms = (time.time() - start_time) * 1000.0

        total_time = sum(r.total_travel_time for r in final_routes)
        total_dist = sum(r.total_distance for r in final_routes)
        total_delay = sum(r.total_delay for r in final_routes)
        is_feasible, violations = self.formulation.validate_solution(final_routes)

        return OptimizationResult(
            algorithm_name="Classical PSO",
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
