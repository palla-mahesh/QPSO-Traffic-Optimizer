"""
Quantum-Inspired Particle Swarm Optimization (QPSO).
Based on the Delta-Potential Well Quantum Model (Sun et al., 2004).
Implements:
1. Mean best position (mbest) attractor.
2. Quantum wave function collapse and stochastic local attractor.
3. Adaptive Contraction-Expansion (CE) parameter scheduling.
4. Quantum tunneling mechanics to escape local optima.
"""

from typing import List, Dict, Tuple, Optional, Callable
import time
import numpy as np

from .base import BaseMetaheuristic
from ..models.vrp import VRPInstance, Route, OptimizationResult, IterationMetric


class QPSO(BaseMetaheuristic):
    """
    Quantum Particle Swarm Optimization for Vehicle Routing.
    
    In QPSO, particles have no classical velocity vectors. Instead, their state
    is determined by a wave function in a delta-potential well. The probability
    of finding a particle at position X is given by the square of the wave function:
        |psi(x)|^2 = (1 / L) * exp(-2 * |x - p| / L)
    where p is the local attractor and L is the characteristic length of the well.
    """

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray,
                 node_idx_map: Dict[int, int], num_particles: int = 50, max_iterations: int = 100,
                 beta_start: float = 1.0, beta_end: float = 0.5):
        super().__init__(instance, dist_matrix, time_matrix, node_idx_map)
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.beta_start = beta_start
        self.beta_end = beta_end

    def optimize(self, callback: Optional[Callable[[IterationMetric], None]] = None) -> OptimizationResult:
        """
        Executes the QPSO algorithm.
        Returns:
            OptimizationResult containing best routes, convergence history, and performance stats.
        """
        start_time = time.time()
        D = self.num_customers
        M = self.num_particles

        # 1. Initialize swarm positions in continuous domain [-5.0, 5.0]
        X = np.random.uniform(-5.0, 5.0, size=(M, D))
        
        # 2. Personal best positions and fitnesses
        P_best = np.copy(X)
        P_best_fitness = np.full(M, float('inf'))
        P_best_routes: List[List[Route]] = [[] for _ in range(M)]

        # Global best
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

        # 3. Main Quantum Optimization Loop
        for it in range(1, self.max_iterations + 1):
            # Dynamic Contraction-Expansion (CE) parameter beta
            beta = self.beta_start - (it / self.max_iterations) * (self.beta_start - self.beta_end)

            # Compute Mean Best Position (mbest)
            # mbest_d = (1 / M) * sum_{i=1}^M P_{i,best,d}
            mbest = np.mean(P_best, axis=0)

            # Update each particle using Quantum Delta-Potential equation
            for i in range(M):
                # Random weights for local attractor
                phi = np.random.uniform(0.0, 1.0, size=D)
                # Stochastic local attractor p_i
                p = phi * P_best[i] + (1.0 - phi) * G_best

                # Quantum displacement: delta = beta * |mbest - X_i| * ln(1 / u)
                u = np.random.uniform(1e-7, 1.0, size=D)
                displacement = beta * np.abs(mbest - X[i]) * np.log(1.0 / u)

                # Random sign (+ or - with 50% probability)
                sign = np.where(np.random.rand(D) < 0.5, 1.0, -1.0)
                X[i] = p + sign * displacement

                # Evaluate new position
                perm = self.decode_continuous_to_permutation(X[i])
                cost, routes = self.evaluate_solution(perm)

                # Update Personal Best
                if cost < P_best_fitness[i]:
                    P_best_fitness[i] = cost
                    P_best[i] = np.copy(X[i])
                    P_best_routes[i] = routes

                    # Update Global Best
                    if cost < G_best_fitness:
                        G_best_fitness = cost
                        G_best = np.copy(X[i])
                        G_best_routes = routes

            # Swarm diversity metric
            swarm_mean = np.mean(X, axis=0)
            diversity = np.mean(np.abs(X - swarm_mean))

            # Best routes metrics
            best_travel_time = sum(r.total_travel_time for r in G_best_routes)
            best_distance = sum(r.total_distance for r in G_best_routes)

            metric = IterationMetric(
                iteration=it,
                best_fitness=float(G_best_fitness),
                mean_fitness=float(np.mean(P_best_fitness)),
                best_cost=float(G_best_fitness),
                best_travel_time=float(best_travel_time),
                best_distance=float(best_distance),
                diversity_metric=float(diversity),
                quantum_parameter=float(beta)
            )
            convergence_history.append(metric)

            if callback is not None:
                callback(metric)

        # 4. Post-optimization local search refinement (2-opt on best routes)
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
            algorithm_name="Quantum-Inspired PSO (QPSO)",
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
