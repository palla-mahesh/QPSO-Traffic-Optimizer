"""
Systematic Benchmarking Suite for Traffic Routing Optimization.
Benchmarks Quantum-Inspired Metaheuristics (QPSO, Bloch-QPSO) against
Classical Metaheuristics (PSO, GA, SA) and Exact MILP solver.
Computes solution quality, convergence speed, runtime, and relative percentage deviation (RPD).
"""

from typing import List, Dict, Any, Optional
import time
import numpy as np

from ..network.osm_loader import get_network_by_id
from ..network.graph_model import TransportationNetwork
from ..models.vrp import VRPInstance, OptimizationResult
from ..models.api_models import BenchmarkResponse
from ..algorithms.qpso import QPSO
from ..algorithms.bloch_qpso import BlochQPSO
from ..algorithms.classical_pso import ClassicalPSO
from ..algorithms.genetic_algorithm import GeneticAlgorithm
from ..algorithms.simulated_annealing import SimulatedAnnealing
from ..formulation.exact_solver import ExactMILPSolver


class BenchmarkSuite:
    """Automated benchmark runner."""

    @staticmethod
    def run_benchmark(
        network_id: str = "noida_sector126",
        algorithms: Optional[List[str]] = None,
        num_particles: int = 40,
        max_iterations: int = 80,
        traffic_surge: float = 1.0
    ) -> BenchmarkResponse:
        """
        Executes a comprehensive benchmark comparing specified algorithms on a chosen network.
        """
        if algorithms is None:
            algorithms = ["qpso", "bloch_qpso", "pso", "ga", "sa", "exact"]

        net, instance = get_network_by_id(network_id)
        if traffic_surge != 1.0:
            net.apply_global_surge(traffic_surge)

        dist_matrix, time_matrix, node_idx_map = net.compute_matrices()

        results: List[OptimizationResult] = []

        for algo_name in algorithms:
            algo_key = algo_name.lower().strip()
            result: Optional[OptimizationResult] = None

            if algo_key == "qpso":
                solver = QPSO(
                    instance=instance,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    node_idx_map=node_idx_map,
                    num_particles=num_particles,
                    max_iterations=max_iterations,
                    beta_start=1.0,
                    beta_end=0.5
                )
                result = solver.optimize()

            elif algo_key in ["bloch_qpso", "bqpso"]:
                solver = BlochQPSO(
                    instance=instance,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    node_idx_map=node_idx_map,
                    num_particles=num_particles,
                    max_iterations=max_iterations
                )
                result = solver.optimize()

            elif algo_key == "pso":
                solver = ClassicalPSO(
                    instance=instance,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    node_idx_map=node_idx_map,
                    num_particles=num_particles,
                    max_iterations=max_iterations
                )
                result = solver.optimize()

            elif algo_key == "ga":
                solver = GeneticAlgorithm(
                    instance=instance,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    node_idx_map=node_idx_map,
                    population_size=num_particles,
                    max_generations=max_iterations
                )
                result = solver.optimize()

            elif algo_key == "sa":
                solver = SimulatedAnnealing(
                    instance=instance,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    node_idx_map=node_idx_map,
                    max_iterations=max_iterations,
                    steps_per_temp=30
                )
                result = solver.optimize()

            elif algo_key in ["exact", "milp"]:
                solver = ExactMILPSolver(
                    instance=instance,
                    dist_matrix=dist_matrix,
                    time_matrix=time_matrix,
                    node_idx_map=node_idx_map,
                    max_runtime_seconds=15.0
                )
                result = solver.solve()

            if result:
                results.append(result)

        # Comparative Summary Table & Metrics
        best_cost = min(r.total_cost for r in results) if results else 1.0
        fastest_time = min(r.execution_time_ms for r in results) if results else 1.0

        summary_table = []
        qpso_cost = None
        pso_cost = None
        qpso_time = None
        pso_time = None

        for r in results:
            rpd = ((r.total_cost - best_cost) / max(1e-6, best_cost)) * 100.0
            row = {
                "algorithm": r.algorithm_name,
                "cost": round(r.total_cost, 2),
                "travel_time_sec": round(r.total_travel_time, 1),
                "distance_km": round(r.total_distance / 1000.0, 2),
                "vehicles_used": r.vehicles_used,
                "runtime_ms": round(r.execution_time_ms, 1),
                "rpd_percent": round(rpd, 2),
                "is_feasible": r.is_feasible
            }
            summary_table.append(row)

            if "QPSO" in r.algorithm_name:
                qpso_cost = r.total_cost
                qpso_time = r.execution_time_ms
            elif "Classical PSO" in r.algorithm_name:
                pso_cost = r.total_cost
                pso_time = r.execution_time_ms

        best_algo = min(results, key=lambda r: r.total_cost).algorithm_name if results else "N/A"
        fastest_algo = min(results, key=lambda r: r.execution_time_ms).algorithm_name if results else "N/A"

        # Improvements
        cost_reduction = 0.0
        speedup = 0.0
        if qpso_cost and pso_cost and pso_cost > 0:
            cost_reduction = max(0.0, ((pso_cost - qpso_cost) / pso_cost) * 100.0)
        if qpso_time and pso_time and pso_time > 0:
            speedup = (pso_time / max(1e-6, qpso_time))

        return BenchmarkResponse(
            instance_name=instance.name,
            network_nodes=len(net.nodes),
            network_edges=len(net.edges),
            results=results,
            summary_table=summary_table,
            fastest_algorithm=fastest_algo,
            best_solution_algorithm=best_algo,
            quantum_speedup_vs_pso=round(speedup, 2),
            quantum_cost_reduction_vs_pso=round(cost_reduction, 2)
        )


if __name__ == "__main__":
    print("Executing Benchmark on Noida Sector 126 Network...")
    resp = BenchmarkSuite.run_benchmark(network_id="noida_sector126", max_iterations=60)
    print("\n--- BENCHMARK RESULTS ---")
    for row in resp.summary_table:
        print(f"{row['algorithm']:<30} Cost: {row['cost']:<10} Time(s): {row['travel_time_sec']:<10} Runtime(ms): {row['runtime_ms']:<10} RPD(%): {row['rpd_percent']}")
    print(f"\nBest Solution Algorithm: {resp.best_solution_algorithm}")
    print(f"Quantum Cost Reduction vs PSO: {resp.quantum_cost_reduction_vs_pso}%")
