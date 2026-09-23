"""
Bloch-Sphere / Qubit-Inspired Quantum Particle Swarm Optimization (Bloch-QPSO).
Uses quantum bits (qubits) represented on the Bloch sphere, with quantum rotation gates
to guide exploration and phase collapse to candidate routes.
"""

from typing import List, Dict, Tuple, Optional, Callable
import time
import math
import numpy as np

from .base import BaseMetaheuristic
from ..models.vrp import VRPInstance, Route, OptimizationResult, IterationMetric


class BlochQPSO(BaseMetaheuristic):
    """
    Qubit-Inspired Particle Swarm Optimization.
    Each dimension is represented by a qubit state parameterized by phase angle theta:
        |psi> = cos(theta)|0> + sin(theta)|1>
    Particles update phase angles using quantum rotation gates:
        theta_{id}(t+1) = theta_{id}(t) + Delta_theta_{id}(t+1)
    where Delta_theta_{id} is determined by quantum rotation angles directed toward P_best and G_best.
    """

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray,
                 node_idx_map: Dict[int, int], num_particles: int = 40, max_iterations: int = 100):
        super().__init__(instance, dist_matrix, time_matrix, node_idx_map)
        self.num_particles = num_particles
        self.max_iterations = max_iterations

    def optimize(self, callback: Optional[Callable[[IterationMetric], None]] = None) -> OptimizationResult:
        start_time = time.time()
        D = self.num_customers
        M = self.num_particles

        # Quantum phase angles theta in [0, 2*pi]
        theta = np.random.uniform(0.0, 2.0 * np.pi, size=(M, D))
        # Quantum angular velocity delta_theta
        delta_theta = np.random.uniform(-0.1 * np.pi, 0.1 * np.pi, size=(M, D))

        P_best_theta = np.copy(theta)
        P_best_fitness = np.full(M, float('inf'))
        P_best_routes: List[List[Route]] = [[] for _ in range(M)]

        G_best_theta = np.zeros(D)
        G_best_fitness = float('inf')
        G_best_routes: List[Route] = []

        # Initial evaluation: observe/collapse qubit state to continuous coordinates
        # Position X = cos(2 * theta)
        for i in range(M):
            X_i = np.cos(2.0 * theta[i])
            perm = self.decode_continuous_to_permutation(X_i)
            cost, routes = self.evaluate_solution(perm)
            P_best_fitness[i] = cost
            P_best_routes[i] = routes
            if cost < G_best_fitness:
                G_best_fitness = cost
                G_best_theta = np.copy(theta[i])
                G_best_routes = routes

        convergence_history: List[IterationMetric] = []

        for it in range(1, self.max_iterations + 1):
            # Dynamic quantum rotation step size
            step_size = 0.05 * np.pi * (1.0 - 0.8 * (it / self.max_iterations))

            for i in range(M):
                r1 = np.random.rand(D)
                r2 = np.random.rand(D)

                # Quantum rotation gate: delta_theta updated towards P_best and G_best
                delta_theta[i] = (
                    0.5 * delta_theta[i] +
                    step_size * r1 * np.sin(P_best_theta[i] - theta[i]) +
                    step_size * r2 * np.sin(G_best_theta - theta[i])
                )
                # Bound rotation speed to prevent erratic oscillations
                delta_theta[i] = np.clip(delta_theta[i], -0.2 * np.pi, 0.2 * np.pi)

                # Phase update
                theta[i] = (theta[i] + delta_theta[i]) % (2.0 * np.pi)

                # Quantum observation / collapse
                X_i = np.cos(2.0 * theta[i]) + 0.1 * np.sin(theta[i])
                perm = self.decode_continuous_to_permutation(X_i)
                cost, routes = self.evaluate_solution(perm)

                if cost < P_best_fitness[i]:
                    P_best_fitness[i] = cost
                    P_best_theta[i] = np.copy(theta[i])
                    P_best_routes[i] = routes

                    if cost < G_best_fitness:
                        G_best_fitness = cost
                        G_best_theta = np.copy(theta[i])
                        G_best_routes = routes

            best_travel_time = sum(r.total_travel_time for r in G_best_routes)
            best_distance = sum(r.total_distance for r in G_best_routes)

            metric = IterationMetric(
                iteration=it,
                best_fitness=float(G_best_fitness),
                mean_fitness=float(np.mean(P_best_fitness)),
                best_cost=float(G_best_fitness),
                best_travel_time=float(best_travel_time),
                best_distance=float(best_distance),
                quantum_parameter=float(step_size)
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
            algorithm_name="Bloch-Sphere Qubit PSO (BQPSO)",
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
