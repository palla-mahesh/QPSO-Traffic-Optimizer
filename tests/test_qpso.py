"""
Unit tests for Quantum-Inspired Particle Swarm Optimization (QPSO & Bloch-QPSO).
"""

import pytest
from backend.app.network.osm_loader import build_noida_sector126_network
from backend.app.algorithms.qpso import QPSO
from backend.app.algorithms.bloch_qpso import BlochQPSO


def test_qpso_execution_and_convergence():
    net, instance = build_noida_sector126_network()
    dist_mat, time_mat, idx_map = net.compute_matrices()

    callback_iterations = []

    def on_iteration(metric):
        callback_iterations.append(metric.iteration)

    qpso = QPSO(
        instance=instance,
        dist_matrix=dist_mat,
        time_matrix=time_mat,
        node_idx_map=idx_map,
        num_particles=25,
        max_iterations=20,
        beta_start=1.0,
        beta_end=0.5
    )

    result = qpso.optimize(callback=on_iteration)

    assert result.algorithm_name == "Quantum-Inspired PSO (QPSO)"
    assert result.is_feasible
    assert len(result.constraint_violations) == 0
    assert result.total_cost > 0
    assert result.total_travel_time > 0
    assert result.total_distance > 0
    assert len(result.routes) > 0
    assert len(result.convergence_history) == 20
    assert len(callback_iterations) == 20

    # Ensure best fitness monotonically improves or stays equal
    for i in range(len(result.convergence_history) - 1):
        assert result.convergence_history[i + 1].best_fitness <= result.convergence_history[i].best_fitness + 1e-6


def test_bloch_qpso_execution():
    net, instance = build_noida_sector126_network()
    dist_mat, time_mat, idx_map = net.compute_matrices()

    bqpso = BlochQPSO(
        instance=instance,
        dist_matrix=dist_mat,
        time_matrix=time_mat,
        node_idx_map=idx_map,
        num_particles=20,
        max_iterations=15
    )

    result = bqpso.optimize()
    assert result.is_feasible
    assert result.total_cost > 0
    assert len(result.convergence_history) == 15
