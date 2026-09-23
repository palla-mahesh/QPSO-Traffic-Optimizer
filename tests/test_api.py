"""
Integration tests for FastAPI REST endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_api_get_network():
    res = client.get("/api/network?network_id=noida_sector126")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "noida_sector126"
    assert data["num_nodes"] == 16
    assert data["num_edges"] > 0
    assert len(data["nodes"]) == 16


def test_api_optimize_qpso():
    payload = {
        "network_id": "noida_sector126",
        "algorithm": "qpso",
        "num_particles": 20,
        "max_iterations": 15,
        "num_vehicles": 5,
        "vehicle_capacity": 80.0,
        "alpha_ce_start": 1.0,
        "alpha_ce_end": 0.5,
        "traffic_surge": 1.0,
        "incidents": []
    }
    res = client.post("/api/optimize", json=payload)
    assert res.status_code == 200
    result = res.json()
    assert result["algorithm_name"] == "Quantum-Inspired PSO (QPSO)"
    assert result["is_feasible"]
    assert len(result["routes"]) > 0
    assert result["total_cost"] > 0


def test_api_traffic_disrupt_and_clear():
    # 1. Trigger accident
    res = client.post("/api/traffic/disrupt?network_id=noida_sector126&disruption_type=accident")
    assert res.status_code == 200
    assert res.json()["disruption"] == "accident"

    # Verify incident is in network
    net_res = client.get("/api/network?network_id=noida_sector126")
    assert len(net_res.json()["incidents"]) > 0

    # 2. Clear traffic
    clear_res = client.post("/api/traffic/clear?network_id=noida_sector126")
    assert clear_res.status_code == 200

    # Verify cleared
    net_res2 = client.get("/api/network?network_id=noida_sector126")
    assert len(net_res2.json()["incidents"]) == 0
