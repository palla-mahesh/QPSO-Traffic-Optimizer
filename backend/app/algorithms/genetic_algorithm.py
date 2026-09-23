"""
Genetic Algorithm (GA) baseline for Vehicle Routing.
Implements:
1. Order Crossover (OX) for permutation chromosomes.
2. Inversion and Swap mutations.
3. Tournament selection and elitism.
"""

from typing import List, Dict, Tuple, Optional, Callable
import time
import random
import numpy as np

from .base import BaseMetaheuristic
from ..models.vrp import VRPInstance, Route, OptimizationResult, IterationMetric


class GeneticAlgorithm(BaseMetaheuristic):
    """
    Standard Genetic Algorithm baseline for comparative benchmarking.
    """

    def __init__(self, instance: VRPInstance, dist_matrix: np.ndarray, time_matrix: np.ndarray,
                 node_idx_map: Dict[int, int], population_size: int = 50, max_generations: int = 100,
                 crossover_rate: float = 0.85, mutation_rate: float = 0.2, tournament_size: int = 3):
        super().__init__(instance, dist_matrix, time_matrix, node_idx_map)
        self.pop_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size

    def _order_crossover(self, p1: List[int], p2: List[int]) -> Tuple[List[int], List[int]]:
        """Order Crossover (OX) for permutation chromosomes."""
        size = len(p1)
        if size <= 2:
            return list(p1), list(p2)

        cx1, cx2 = sorted(random.sample(range(size), 2))

        def make_child(parent_a, parent_b):
            child = [None] * size
            # Copy slice from parent_a
            child[cx1:cx2+1] = parent_a[cx1:cx2+1]
            # Fill remaining from parent_b in order
            b_elements = [x for x in parent_b if x not in child[cx1:cx2+1]]
            fill_idx = (cx2 + 1) % size
            for item in b_elements:
                while child[fill_idx] is not None:
                    fill_idx = (fill_idx + 1) % size
                child[fill_idx] = item
            return child

        c1 = make_child(p1, p2)
        c2 = make_child(p2, p1)
        return c1, c2

    def _mutate(self, chromosome: List[int]) -> List[int]:
        """Applies swap or inversion mutation."""
        c = list(chromosome)
        if len(c) < 2:
            return c

        if random.random() < 0.5:
            # Swap mutation
            i, j = random.sample(range(len(c)), 2)
            c[i], c[j] = c[j], c[i]
        else:
            # Inversion mutation
            i, j = sorted(random.sample(range(len(c)), 2))
            c[i:j+1] = c[i:j+1][::-1]
        return c

    def optimize(self, callback: Optional[Callable[[IterationMetric], None]] = None) -> OptimizationResult:
        start_time = time.time()
        base_permutation = list(self.customer_ids)

        # 1. Initialize population
        population: List[List[int]] = []
        fitnesses: List[float] = []
        routes_pop: List[List[Route]] = []

        for _ in range(self.pop_size):
            perm = list(base_permutation)
            random.shuffle(perm)
            cost, routes = self.evaluate_solution(perm)
            population.append(perm)
            fitnesses.append(cost)
            routes_pop.append(routes)

        best_idx = int(np.argmin(fitnesses))
        best_cost = fitnesses[best_idx]
        best_routes = routes_pop[best_idx]
        best_chromosome = list(population[best_idx])

        convergence_history: List[IterationMetric] = []

        # 2. Generational Loop
        for gen in range(1, self.max_generations + 1):
            new_population: List[List[int]] = []
            new_fitnesses: List[float] = []
            new_routes_pop: List[List[Route]] = []

            # Elitism: retain best individual
            new_population.append(list(best_chromosome))
            new_fitnesses.append(best_cost)
            new_routes_pop.append(best_routes)

            # Tournament Selection and Offspring Generation
            while len(new_population) < self.pop_size:
                # Tournament 1
                cand1 = random.sample(range(self.pop_size), self.tournament_size)
                p1 = population[min(cand1, key=lambda i: fitnesses[i])]

                # Tournament 2
                cand2 = random.sample(range(self.pop_size), self.tournament_size)
                p2 = population[min(cand2, key=lambda i: fitnesses[i])]

                if random.random() < self.crossover_rate:
                    c1, c2 = self._order_crossover(p1, p2)
                else:
                    c1, c2 = list(p1), list(p2)

                if random.random() < self.mutation_rate:
                    c1 = self._mutate(c1)
                if random.random() < self.mutation_rate:
                    c2 = self._mutate(c2)

                for c in [c1, c2]:
                    if len(new_population) < self.pop_size:
                        cost, routes = self.evaluate_solution(c)
                        new_population.append(c)
                        new_fitnesses.append(cost)
                        new_routes_pop.append(routes)
                        if cost < best_cost:
                            best_cost = cost
                            best_routes = routes
                            best_chromosome = list(c)

            population = new_population
            fitnesses = new_fitnesses
            routes_pop = new_routes_pop

            best_travel_time = sum(r.total_travel_time for r in best_routes)
            best_distance = sum(r.total_distance for r in best_routes)

            metric = IterationMetric(
                iteration=gen,
                best_fitness=float(best_cost),
                mean_fitness=float(np.mean(fitnesses)),
                best_cost=float(best_cost),
                best_travel_time=float(best_travel_time),
                best_distance=float(best_distance)
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
            algorithm_name="Genetic Algorithm (GA)",
            instance_name=self.instance.name,
            routes=final_routes,
            total_cost=float(final_cost),
            total_travel_time=float(total_time),
            total_distance=float(total_dist),
            total_tardiness=float(total_delay),
            vehicles_used=len(final_routes),
            execution_time_ms=float(elapsed_ms),
            iterations_run=self.max_generations,
            convergence_history=convergence_history,
            is_feasible=is_feasible,
            constraint_violations=violations
        )
