"""
Unit tests for the Benchmarking Suite comparing QPSO, PSO, GA, SA, and Exact solver.
"""

import pytest
from backend.app.benchmark.benchmark_suite import BenchmarkSuite


def test_benchmark_suite_execution():
    """Runs a quick benchmark across all algorithms on Noida network."""
    resp = BenchmarkSuite.run_benchmark(
        network_id="noida_sector126",
        algorithms=["qpso", "bloch_qpso", "pso", "ga", "sa", "exact"],
        num_particles=15,
        max_iterations=10
    )

    assert len(resp.results) == 6
    assert len(resp.summary_table) == 6
    assert resp.network_nodes == 16
    assert resp.best_solution_algorithm != ""
    assert resp.fastest_algorithm != ""

    for row in resp.summary_table:
        assert row["cost"] > 0
        assert row["runtime_ms"] >= 0
        assert row["rpd_percent"] >= 0
