"""
Unit tests for TransportationNetwork, Edge BPR travel time, and dynamic congestion.
"""

import pytest
import numpy as np

from backend.app.models.graph import Node, Edge, TrafficIncident
from backend.app.network.graph_model import TransportationNetwork
from backend.app.network.osm_loader import build_noida_sector126_network, build_solomon_benchmark


def test_edge_bpr_travel_time():
    """Verify BPR formula t = t0 * (1 + alpha * (V/C)^beta) * incident."""
    dist = 1000.0  # 1 km
    speed = 20.0   # 20 m/s -> t0 = 50s
    cap = 1000.0
    vol = 1000.0   # V/C = 1.0
    alpha = 0.15
    beta = 4.0

    edge = Edge(
        source=1,
        target=2,
        distance=dist,
        free_flow_speed=speed,
        capacity=cap,
        current_volume=vol,
        alpha_bpr=alpha,
        beta_bpr=beta,
        congestion_factor=1.0
    )

    expected_tt = 50.0 * (1.0 + 0.15 * (1.0 ** 4.0))  # 50 * 1.15 = 57.5s
    assert abs(edge.compute_travel_time() - expected_tt) < 1e-3

    # With 2.0x incident severity
    edge.congestion_factor = 2.0
    assert abs(edge.compute_travel_time() - (expected_tt * 2.0)) < 1e-3

    # Road closure
    edge.is_closed = True
    assert edge.compute_travel_time() == float('inf')


def test_transportation_network_matrices():
    """Verify matrix calculation and shortest path Dijkstra."""
    net, instance = build_noida_sector126_network()
    dist_mat, time_mat, idx_map = net.compute_matrices()

    assert dist_mat.shape[0] == len(net.nodes)
    assert time_mat.shape[0] == len(net.nodes)
    assert np.all(np.diag(dist_mat) == 0.0)
    assert np.all(np.diag(time_mat) == 0.0)
    assert np.all(dist_mat >= 0.0)
    assert np.all(time_mat >= 0.0)


def test_dynamic_traffic_incident():
    """Verify incident injection updates travel time and matrices."""
    net, _ = build_noida_sector126_network()
    _, orig_time, _ = net.compute_matrices()
    orig_val = orig_time[net._node_id_to_idx[3], net._node_id_to_idx[7]]

    # Inject incident on 3 -> 7
    inc = TrafficIncident(
        id="test_inc",
        source=3,
        target=7,
        severity=3.0,
        description="Test incident"
    )
    net.add_incident(inc)
    _, new_time, _ = net.compute_matrices()
    new_val = new_time[net._node_id_to_idx[3], net._node_id_to_idx[7]]

    assert new_val > orig_val

    # Remove incident
    net.remove_incident("test_inc")
    _, restored_time, _ = net.compute_matrices()
    restored_val = restored_time[net._node_id_to_idx[3], net._node_id_to_idx[7]]
    assert abs(restored_val - orig_val) < 1e-3
