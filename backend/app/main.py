"""
FastAPI application for Quantum-Inspired Intelligent Traffic Route Optimization.
Provides REST and WebSocket endpoints for network querying, optimization,
real-time iteration streaming, benchmarking, and dynamic traffic simulation.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from .models.api_models import (
    OptimizationRequest,
    BenchmarkRequest,
    BenchmarkResponse,
    TrafficUpdateRequest
)
from .models.vrp import OptimizationResult, IterationMetric
from .network.osm_loader import get_network_by_id, build_noida_sector126_network
from .network.graph_model import TransportationNetwork
from .network.traffic_simulator import TrafficSimulator
from .algorithms.qpso import QPSO
from .algorithms.bloch_qpso import BlochQPSO
from .algorithms.classical_pso import ClassicalPSO
from .algorithms.genetic_algorithm import GeneticAlgorithm
from .algorithms.simulated_annealing import SimulatedAnnealing
from .formulation.exact_solver import ExactMILPSolver
from .benchmark.benchmark_suite import BenchmarkSuite

app = FastAPI(
    title="Quantum-Inspired Intelligent Traffic Route Optimization",
    description="Egreen Quanta (SIH 2026 - Quantum Technology Vertical) Optimization Platform",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory network cache
ACTIVE_NETWORKS: Dict[str, TransportationNetwork] = {}
ACTIVE_SIMULATORS: Dict[str, TrafficSimulator] = {}


def get_or_load_network(network_id: str) -> TransportationNetwork:
    """Retrieve or initialize network instance."""
    nid = network_id.lower()
    if nid not in ACTIVE_NETWORKS:
        net, _ = get_network_by_id(nid)
        ACTIVE_NETWORKS[nid] = net
        ACTIVE_SIMULATORS[nid] = TrafficSimulator(net)
    return ACTIVE_NETWORKS[nid]


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "platform": "Quantum-Inspired Traffic Route Optimization (Q-TRO)"}


@app.get("/favicon.ico", include_in_schema=False)
@app.head("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/api/network")
async def get_network(network_id: str = Query("noida_sector126")):
    """Get the network graph structure, nodes, edges, and congestion status."""
    net = get_or_load_network(network_id)
    return net.to_dict()


@app.post("/api/optimize", response_model=OptimizationResult)
async def optimize_route(req: OptimizationRequest):
    """Run optimization with selected algorithm and return final routes and metrics."""
    net = get_or_load_network(req.network_id)
    _, instance = get_network_by_id(req.network_id)

    # Apply surge if requested
    if req.traffic_surge != 1.0:
        net.apply_global_surge(req.traffic_surge)

    # Inject incidents if any
    for inc in req.incidents:
        net.add_incident(inc)

    dist_matrix, time_matrix, node_idx_map = net.compute_matrices()
    algo_name = req.algorithm.lower().strip()

    if algo_name == "qpso":
        solver = QPSO(
            instance=instance,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            node_idx_map=node_idx_map,
            num_particles=req.num_particles,
            max_iterations=req.max_iterations,
            beta_start=req.alpha_ce_start,
            beta_end=req.alpha_ce_end
        )
        return solver.optimize()

    elif algo_name in ["bloch_qpso", "bqpso"]:
        solver = BlochQPSO(
            instance=instance,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            node_idx_map=node_idx_map,
            num_particles=req.num_particles,
            max_iterations=req.max_iterations
        )
        return solver.optimize()

    elif algo_name == "pso":
        solver = ClassicalPSO(
            instance=instance,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            node_idx_map=node_idx_map,
            num_particles=req.num_particles,
            max_iterations=req.max_iterations
        )
        return solver.optimize()

    elif algo_name == "ga":
        solver = GeneticAlgorithm(
            instance=instance,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            node_idx_map=node_idx_map,
            population_size=req.num_particles,
            max_generations=req.max_iterations
        )
        return solver.optimize()

    elif algo_name == "sa":
        solver = SimulatedAnnealing(
            instance=instance,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            node_idx_map=node_idx_map,
            max_iterations=req.max_iterations
        )
        return solver.optimize()

    elif algo_name in ["exact", "milp"]:
        solver = ExactMILPSolver(
            instance=instance,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            node_idx_map=node_idx_map
        )
        return solver.solve()

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {req.algorithm}")


@app.post("/api/benchmark", response_model=BenchmarkResponse)
async def run_benchmark(req: BenchmarkRequest):
    """Run systematic benchmark comparing algorithms."""
    resp = BenchmarkSuite.run_benchmark(
        network_id=req.network_id,
        algorithms=req.algorithms,
        num_particles=req.num_particles,
        max_iterations=req.max_iterations
    )
    return resp


@app.post("/api/traffic/update")
async def update_traffic(req: TrafficUpdateRequest):
    """Update dynamic traffic volume or inject an incident on an edge."""
    net = get_or_load_network(req.network_id)
    net.update_traffic(
        req.source,
        req.target,
        congestion_factor=req.severity,
        is_closed=req.is_closure
    )
    return {"status": "updated", "edge": (req.source, req.target), "severity": req.severity}


@app.post("/api/traffic/disrupt")
async def trigger_disruption(
    network_id: str = Query("noida_sector126"),
    disruption_type: str = Query("accident", description="accident, rush_hour, road_closure")
):
    """Trigger preset traffic disruption event."""
    net = get_or_load_network(network_id)
    sim = ACTIVE_SIMULATORS.get(network_id.lower(), TrafficSimulator(net))

    if disruption_type == "accident":
        # Accident on key expressway segment (e.g. 7 -> 12 or 3 -> 7)
        inc = sim.trigger_accident(3, 7, severity=3.5, description="Major collision on Expressway")
        return {"disruption": "accident", "incident": inc.model_dump()}
    elif disruption_type == "rush_hour":
        sim.trigger_rush_hour_surge(surge_factor=2.2)
        return {"disruption": "rush_hour", "surge": 2.2}
    elif disruption_type == "road_closure":
        inc = sim.trigger_accident(7, 12, severity=10.0, is_closure=True, description="Complete lane closure")
        return {"disruption": "road_closure", "incident": inc.model_dump()}
    else:
        raise HTTPException(status_code=400, detail="Invalid disruption type")


@app.post("/api/traffic/clear")
async def clear_traffic(network_id: str = Query("noida_sector126")):
    """Reset network to normal baseline conditions."""
    net, _ = get_network_by_id(network_id)
    ACTIVE_NETWORKS[network_id.lower()] = net
    ACTIVE_SIMULATORS[network_id.lower()] = TrafficSimulator(net)
    return {"status": "cleared"}


@app.websocket("/ws/optimize")
async def websocket_optimize(websocket: WebSocket):
    """
    WebSocket endpoint streaming iteration-by-iteration optimization progress
    in real time for animated convergence plotting on the frontend.
    """
    await websocket.accept()
    try:
        raw_msg = await websocket.receive_text()
        data = json.loads(raw_msg)
        req = OptimizationRequest(**data)

        net = get_or_load_network(req.network_id)
        _, instance = get_network_by_id(req.network_id)
        dist_matrix, time_matrix, node_idx_map = net.compute_matrices()

        loop = asyncio.get_event_loop()

        # Thread-safe callback for streaming
        def iteration_callback(metric: IterationMetric):
            msg = {
                "type": "iteration",
                "data": metric.model_dump()
            }
            # Schedule async send on event loop
            asyncio.run_coroutine_threadsafe(websocket.send_text(json.dumps(msg)), loop)

        # Run solver in thread pool so it does not block the async event loop
        algo_name = req.algorithm.lower().strip()
        if algo_name == "qpso":
            solver = QPSO(
                instance=instance,
                dist_matrix=dist_matrix,
                time_matrix=time_matrix,
                node_idx_map=node_idx_map,
                num_particles=req.num_particles,
                max_iterations=req.max_iterations,
                beta_start=req.alpha_ce_start,
                beta_end=req.alpha_ce_end
            )
        elif algo_name in ["bloch_qpso", "bqpso"]:
            solver = BlochQPSO(
                instance=instance,
                dist_matrix=dist_matrix,
                time_matrix=time_matrix,
                node_idx_map=node_idx_map,
                num_particles=req.num_particles,
                max_iterations=req.max_iterations
            )
        elif algo_name == "pso":
            solver = ClassicalPSO(
                instance=instance,
                dist_matrix=dist_matrix,
                time_matrix=time_matrix,
                node_idx_map=node_idx_map,
                num_particles=req.num_particles,
                max_iterations=req.max_iterations
            )
        elif algo_name == "ga":
            solver = GeneticAlgorithm(
                instance=instance,
                dist_matrix=dist_matrix,
                time_matrix=time_matrix,
                node_idx_map=node_idx_map,
                population_size=req.num_particles,
                max_generations=req.max_iterations
            )
        elif algo_name == "sa":
            solver = SimulatedAnnealing(
                instance=instance,
                dist_matrix=dist_matrix,
                time_matrix=time_matrix,
                node_idx_map=node_idx_map,
                max_iterations=req.max_iterations
            )
        else:
            solver = ExactMILPSolver(
                instance=instance,
                dist_matrix=dist_matrix,
                time_matrix=time_matrix,
                node_idx_map=node_idx_map
            )

        result = await loop.run_in_executor(None, solver.optimize if hasattr(solver, "optimize") else solver.solve, iteration_callback if hasattr(solver, "optimize") else None)

        final_msg = {
            "type": "completed",
            "result": result.model_dump()
        }
        await websocket.send_text(json.dumps(final_msg))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))
        except Exception:
            pass


# Mount frontend static directory if exists
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.head("/", include_in_schema=False)
    async def serve_index_head():
        return Response(status_code=200, headers={"content-type": "text/html; charset=utf-8"})
