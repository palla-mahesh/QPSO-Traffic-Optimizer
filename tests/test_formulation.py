"""
Unit tests for mathematical formulation and constraint verification.
"""

import pytest
from backend.app.network.osm_loader import build_noida_sector126_network
from backend.app.formulation.vrp_formulation import VRPFormulation
from backend.app.models.vrp import Route


def test_vrp_formulation_route_evaluation():
    net, instance = build_noida_sector126_network()
    dist_mat, time_mat, idx_map = net.compute_matrices()
    formulation = VRPFormulation(instance, dist_mat, time_mat, idx_map)

    # Route: Depot(0) -> Customer(1) -> Customer(2) -> Depot(0)
    route_seq = [0, 1, 2, 0]
    route = formulation.evaluate_route(route_seq, vehicle_id=0)

    assert route.total_distance > 0
    assert route.total_travel_time > 0
    assert route.total_load == (instance.nodes[1].demand + instance.nodes[2].demand)
    assert route.cost > 0
    assert len(route.arrival_times) == len(set(route_seq))


def test_vrp_formulation_feasibility_check():
    net, instance = build_noida_sector126_network()
    dist_mat, time_mat, idx_map = net.compute_matrices()
    formulation = VRPFormulation(instance, dist_mat, time_mat, idx_map)

    customers = [n.id for n in instance.nodes if not n.is_depot]
    
    # 1. Infeasible: missing customers
    partial_route = formulation.evaluate_route([0, customers[0], 0], vehicle_id=0)
    is_feas, violations = formulation.validate_solution([partial_route])
    assert not is_feas
    assert any("never visited" in v for v in violations)

    # 2. Infeasible: customer visited twice
    dup_route_1 = formulation.evaluate_route([0, customers[0], customers[1], 0], vehicle_id=0)
    dup_route_2 = formulation.evaluate_route([0, customers[0], 0] + customers[2:] + [0], vehicle_id=1)
    is_feas, violations = formulation.validate_solution([dup_route_1, dup_route_2])
    assert not is_feas
    assert any("visited 2 times" in v for v in violations)

    # 3. Infeasible: does not start/end at depot
    bad_route = Route(vehicle_id=0, node_sequence=[customers[0], customers[1], 0], total_load=10.0)
    is_feas, violations = formulation.validate_solution([bad_route])
    assert not is_feas
    assert any("does not start or end at depot" in v for v in violations)
