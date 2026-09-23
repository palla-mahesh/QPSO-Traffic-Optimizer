# Quantum-Inspired Intelligent Traffic Route Optimization (Q-TRO)

**Problem Statement ID**: 26137  
**Organization**: Egreen Quanta  
**Theme**: Transportation & Logistics  
**Vertical**: Quantum Technology Vertical (SIH 2026)  

[![CI/CD Pipeline](https://github.com/psryogeshwar-14/quantum-traffic-optimization/actions/workflows/ci.yml/badge.svg)](https://github.com/psryogeshwar-14/quantum-traffic-optimization/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg)](https://github.com/psryogeshwar-14/quantum-traffic-optimization/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

Modern urban transportation networks face severe challenges of traffic congestion, non-linear travel delays, and escalating operational costs. Classical Vehicle Routing Problems (VRP) and dynamic shortest-path optimization are NP-hard combinatorial problems that quickly become computationally intractable for large-scale smart-city logistics. While pure quantum hardware (QPU) is currently constrained by qubit noise and NISQ limitations, **Quantum-Inspired Metaheuristics** embed quantum-mechanical concepts into classical computation to deliver superior global exploration, quantum tunneling through local minima, and faster convergence.

This platform provides a complete, production-ready system implementing **Quantum Particle Swarm Optimization (QPSO)** and **Bloch-Sphere Qubit PSO (BQPSO)** for dynamic vehicle routing and traffic optimization under simulated and real-world road congestion.

---

## Key Features & Deliverables

| S.No | Deliverable | Implementation Details |
|---|---|---|
| **1** | **Graph-based Network Model** | Weighted directed multigraph with nodes (intersections, depots, customers) and edges with physical distances, speed limits, and dynamic travel times modeled via the **Bureau of Public Roads (BPR)** congestion formula: $t(V) = t_0 [1 + \alpha (V/C)^\beta] \cdot \gamma$. |
| **2** | **Mathematical Formulation** | Mixed Integer Linear Programming (MILP) formulation of Capacitated Vehicle Routing with Time Windows and Traffic Congestion (**CVRPTW-TC**), including flow conservation, capacity limits, MTZ subtour elimination, and time-window tardiness penalties. |
| **3** | **Quantum-Inspired Algorithms** | **QPSO** using Sun et al.'s Delta-Potential Well wave collapse model and Mean Best Position ($mbest$), alongside **Bloch-Sphere Qubit PSO (BQPSO)** with quantum rotation gates. Benchmarked against Classical PSO, Genetic Algorithm (GA), Simulated Annealing (SA), and Exact MILP (CBC). |
| **4** | **Software Platform / Prototype** | Interactive web dashboard powered by **FastAPI** and **Leaflet.js**, featuring live traffic congestion heatmaps, animated multi-vehicle routes, real-time Chart.js convergence dynamics via WebSockets, and dynamic traffic disruption controls. |
| **5** | **Demonstration & Real-Scale Scenarios** | Evaluated on real-world **Noida Sector 126 Network** (Egreen Quanta HQ / Expressway corridor), standard **Solomon Academic Benchmarks (C101, R101)**, and scalable synthetic urban grids up to 500+ nodes. |

---

## Quick Start Guide

### 1. Clone & Environment Setup
```bash
# Clone the repository
git clone https://github.com/psryogeshwar-14/quantum-traffic-optimization.git
cd quantum-traffic-optimization

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Run Automated Test Suite
```bash
pytest tests/ -v
```
*(All 12 unit & integration tests verify API endpoints, network BPR graphs, VRP formulation feasibility, and QPSO/Bloch-QPSO convergence).*

### 3. Run Benchmark Suite (CLI)
```bash
python3 -m backend.app.benchmark.benchmark_suite
```

### 4. Launch Interactive Web Platform
```bash
./start.sh
# or directly with uvicorn:
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at **`http://localhost:8000`**.

---

## Free 24/7 Live Cloud Hosting (Zero-Cost Deployment)

This repository is pre-configured with free deployment manifests:

### Option A: Render.com (100% Free, Auto-Deploy on Git Push)
1. Sign in to [Render Dashboard](https://dashboard.render.com/) with GitHub.
2. Click **New +** $\to$ **Blueprint** (or **Web Service**).
3. Connect `psryogeshwar-14/quantum-traffic-optimization`.
4. Render automatically reads [`render.yaml`](render.yaml) and provisions the service with free HTTPS.

### Option B: Hugging Face Spaces (100% Free, 16 GB RAM + 2 vCPUs)
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) $\to$ **Create new Space**.
2. Select **Docker** $\to$ Blank $\to$ **Free Tier (16 GB RAM)**.
3. Connect this repository to launch an AI/Optimization demo space.

### Option C: Instant Public Tunnel (No Signup / Zero Install)
To share your local running instance with judges instantly:
```bash
ssh -R 80:localhost:8000 localhost.run
```
*(Generates a direct public `https://...lhr.life` link immediately).*

---

## Platform Architecture

```
quantum-traffic-optimization/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Automated GitHub Actions test pipeline
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI server (REST & WebSockets)
│   │   ├── models/                    # Pydantic data schemas
│   │   │   ├── graph.py               # Node, Edge, TrafficIncident
│   │   │   ├── vrp.py                 # Vehicle, VRPInstance, Route, OptimizationResult
│   │   │   └── api_models.py          # Request & response schemas
│   │   ├── network/                   # Graph & Traffic Simulation
│   │   │   ├── graph_model.py         # TransportationNetwork with BPR function
│   │   │   ├── traffic_simulator.py   # Rush hour waves & incident injection
│   │   │   └── osm_loader.py          # Noida Sec 126, Solomon C101/R101, Grid
│   │   ├── formulation/               # Mathematical Formulation & Exact Methods
│   │   │   ├── vrp_formulation.py     # Formal CVRPTW-TC model & validator
│   │   │   └── exact_solver.py        # PuLP MILP Branch-and-Bound solver
│   │   ├── algorithms/                # Metaheuristic Optimization Engine
│   │   │   ├── base.py                # Base class, SPV decoding, Prins' split, 2-opt
│   │   │   ├── qpso.py                # Quantum PSO (Delta Potential Well)
│   │   │   ├── bloch_qpso.py          # Bloch-Sphere Qubit PSO
│   │   │   ├── classical_pso.py       # Classical PSO baseline
│   │   │   ├── genetic_algorithm.py   # GA (Order Crossover & Inversion)
│   │   │   └── simulated_annealing.py # SA (Metropolis cooling & 2-opt)
│   │   └── benchmark/                 # Automated Benchmarking
│   │       └── benchmark_suite.py     # Multi-algorithm comparative benchmark
│   └── requirements.txt
├── frontend/                          # Interactive Web UI
│   ├── index.html                     # Dashboard HTML (Midnight OLED theme)
│   ├── css/style.css                  # Cyber-dark glassmorphism styling
│   ├── figma-tokens.json              # Figma Tokens Studio integration tokens
│   └── js/
│       ├── app.js                     # Main UI controller & WebSocket handler
│       ├── map_view.js                # Leaflet map rendering & route paths
│       ├── charts.js                  # Real-time Chart.js convergence curves
│       └── traffic_sim.js             # Traffic disruption controls
├── tests/                             # Pytest automated test suite (12 tests)
├── docs/                              # Technical & Mathematical Documentation
│   ├── mathematical_formulation.md    # Rigorous LaTeX formulation
│   ├── technical_report.md            # Comprehensive project report
│   ├── deployment_guide.md            # Production deployment walkthrough
│   └── figma_design_system.md         # UI/UX & Figma design specification
├── Dockerfile                         # Production multi-stage Docker build
├── docker-compose.yml                 # Local container orchestration
├── render.yaml                        # 1-click cloud blueprint
├── Procfile                           # Cloud dyno entrypoint
└── start.sh                           # Unified self-bootstrapping launcher
```

---

## Mathematical Highlights: QPSO

In QPSO, a particle's state is described by a wave function $\psi(X)$ centered at a stochastic local attractor:
$$p_{id}(t) = \phi_{id} P_{id,best}(t) + (1 - \phi_{id}) G_{d,best}(t), \quad \phi_{id} \sim U(0, 1)$$

The particle's position is updated by collapsing the wave function:
$$X_{id}(t+1) = p_{id}(t) \pm \beta(t) \cdot |mbest_d(t) - X_{id}(t)| \cdot \ln\left( \frac{1}{u_{id}} \right), \quad u_{id} \sim U(0, 1)$$

where:
- $mbest(t) = \frac{1}{M} \sum_{i=1}^M P_{i,best}(t)$ is the **Mean Best Position** of the swarm.
- $\beta(t) = \beta_{\max} - \frac{t}{T_{\max}} (\beta_{\max} - \beta_{\min})$ is the **Contraction-Expansion (CE) parameter** controlling the quantum potential well width.

---

## API Endpoints

- `GET /api/network?network_id=noida_sector126`: Retrieve road graph, nodes, and live BPR traffic status.
- `POST /api/optimize`: Run routing optimization using QPSO, BQPSO, PSO, GA, SA, or Exact MILP.
- `POST /api/benchmark`: Execute multi-algorithm benchmark with comparative metrics.
- `POST /api/traffic/disrupt`: Simulate traffic incidents (accidents, rush-hour volume surges, closures).
- `POST /api/traffic/clear`: Reset network to baseline free-flow conditions.
- `WS /ws/optimize`: Stream live iteration-by-iteration convergence metrics to client.
- `GET /health` & `GET /api/health`: Health status endpoint for cloud load balancers.

---

## Authors & Acknowledgments

- **Team**: MASHI
- **Organization**: Egreen Quanta
- **Event**: AICTE Smart India Hackathon (SIH) 2026
- **Vertical**: Quantum Technology Vertical
