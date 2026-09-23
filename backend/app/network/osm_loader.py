"""
Urban network and benchmark loaders.
Includes:
1. Real-world Noida Sector 126 / Expressway Network (Egreen Quanta headquarters).
2. Standard Solomon VRP Academic Benchmarks (C101 Clustered, R101 Random, RC101 Mixed).
3. Scalable Synthetic Urban Grid generator for large-scale stress testing.
"""

from typing import Dict, List, Tuple
import math
import random

from .graph_model import TransportationNetwork
from ..models.graph import Node, Edge
from ..models.vrp import VRPInstance, Vehicle


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in meters between two GPS coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def build_noida_sector126_network() -> Tuple[TransportationNetwork, VRPInstance]:
    """
    Constructs a realistic urban network representing Sector 126, Noida and surroundings
    (Egreen Quanta HQ, NASSCOM Campus, Amity University, Noida-Greater Noida Expressway,
    Sector 125, Sector 127, Sector 93, Kalindi Kunj, Botanical Garden).
    """
    net = TransportationNetwork(name="noida_sector126")

    # Real locations with realistic lat, lon coordinates
    locations = [
        # Depot: Egreen Quanta / NASSCOM Campus
        {"id": 0, "name": "Egreen Quanta (Depot)", "lat": 28.5442, "lon": 77.3325, "is_depot": True, "demand": 0.0, "service": 0.0, "ready": 0.0, "due": 86400.0},
        # Customer deliveries & key intersections in Noida Sector 124-128 / Expressway
        {"id": 1, "name": "Amity University Gate 2", "lat": 28.5458, "lon": 77.3341, "demand": 15.0, "service": 300.0, "ready": 1800.0, "due": 14400.0},
        {"id": 2, "name": "HCL Technologies Hub", "lat": 28.5412, "lon": 77.3365, "demand": 22.0, "service": 360.0, "ready": 3600.0, "due": 18000.0},
        {"id": 3, "name": "Tech Boulevard Sec 127", "lat": 28.5375, "lon": 77.3410, "demand": 18.0, "service": 240.0, "ready": 1800.0, "due": 12600.0},
        {"id": 4, "name": "Advant Navis Business Park", "lat": 28.5028, "lon": 77.4085, "demand": 30.0, "service": 480.0, "ready": 7200.0, "due": 25200.0},
        {"id": 5, "name": "Jaypee Hospital Sec 128", "lat": 28.5178, "lon": 77.3752, "demand": 25.0, "service": 400.0, "ready": 3600.0, "due": 21600.0},
        {"id": 6, "name": "Logix Techno Park Sec 127", "lat": 28.5390, "lon": 77.3450, "demand": 12.0, "service": 200.0, "ready": 1800.0, "due": 10800.0},
        {"id": 7, "name": "Noida-Gr Noida Expressway Toll", "lat": 28.5280, "lon": 77.3590, "demand": 8.0, "service": 180.0, "ready": 0.0, "due": 18000.0},
        {"id": 8, "name": "Sector 125 IT Zone", "lat": 28.5475, "lon": 77.3250, "demand": 14.0, "service": 240.0, "ready": 5400.0, "due": 16200.0},
        {"id": 9, "name": "Okhla Bird Sanctuary Gate", "lat": 28.5520, "lon": 77.3190, "demand": 16.0, "service": 300.0, "ready": 7200.0, "due": 19800.0},
        {"id": 10, "name": "Kalindi Kunj Border", "lat": 28.5450, "lon": 77.3110, "demand": 20.0, "service": 360.0, "ready": 1800.0, "due": 14400.0},
        {"id": 11, "name": "Sector 93 Grand Omaxe", "lat": 28.5130, "lon": 77.3780, "demand": 17.0, "service": 300.0, "ready": 9000.0, "due": 28800.0},
        {"id": 12, "name": "Sector 108 Police HQ", "lat": 28.5240, "lon": 77.3680, "demand": 10.0, "service": 180.0, "ready": 3600.0, "due": 14400.0},
        {"id": 13, "name": "Sector 132 Genesis School", "lat": 28.5080, "lon": 77.3870, "demand": 19.0, "service": 300.0, "ready": 7200.0, "due": 21600.0},
        {"id": 14, "name": "Sector 135 Express Trade Towers", "lat": 28.4980, "lon": 77.4010, "demand": 28.0, "service": 420.0, "ready": 10800.0, "due": 32400.0},
        {"id": 15, "name": "Sector 94 Supernova Tower", "lat": 28.5510, "lon": 77.3270, "demand": 24.0, "service": 360.0, "ready": 3600.0, "due": 18000.0},
    ]

    nodes_list: List[Node] = []
    for loc in locations:
        node = Node(
            id=loc["id"],
            name=loc["name"],
            x=loc["lon"],  # lon for X
            y=loc["lat"],  # lat for Y
            is_depot=loc.get("is_depot", False),
            demand=loc["demand"],
            service_time=loc["service"],
            ready_time=loc["ready"],
            due_time=loc["due"]
        )
        net.add_node(node)
        nodes_list.append(node)

    # Connect road network: Expressway corridors + Arterial connectors
    # Expressway connects: 0 <-> 1 <-> 8 <-> 15 <-> 9
    # Expressway corridor: 0 <-> 6 <-> 3 <-> 7 <-> 12 <-> 5 <-> 11 <-> 13 <-> 14 <-> 4
    # Cross connections: 8 <-> 10, 15 <-> 10, 1 <-> 2, 2 <-> 3, 2 <-> 6, 7 <-> 8
    road_links = [
        (0, 1, 60.0, 1800.0), (1, 0, 60.0, 1800.0),
        (0, 8, 50.0, 1400.0), (8, 0, 50.0, 1400.0),
        (1, 2, 40.0, 1000.0), (2, 1, 40.0, 1000.0),
        (2, 3, 45.0, 1200.0), (3, 2, 45.0, 1200.0),
        (2, 6, 45.0, 1100.0), (6, 2, 45.0, 1100.0),
        (0, 6, 50.0, 1300.0), (6, 0, 50.0, 1300.0),
        (6, 3, 50.0, 1400.0), (3, 6, 50.0, 1400.0),
        (3, 7, 70.0, 2200.0), (7, 3, 70.0, 2200.0),
        (7, 12, 70.0, 2400.0), (12, 7, 70.0, 2400.0),
        (12, 5, 60.0, 1800.0), (5, 12, 60.0, 1800.0),
        (5, 11, 50.0, 1400.0), (11, 5, 50.0, 1400.0),
        (11, 13, 60.0, 1700.0), (13, 11, 60.0, 1700.0),
        (13, 14, 70.0, 2300.0), (14, 13, 70.0, 2300.0),
        (14, 4, 70.0, 2500.0), (4, 14, 70.0, 2500.0),
        (8, 15, 50.0, 1200.0), (15, 8, 50.0, 1200.0),
        (15, 9, 50.0, 1300.0), (9, 15, 50.0, 1300.0),
        (8, 10, 50.0, 1500.0), (10, 8, 50.0, 1500.0),
        (10, 9, 45.0, 1100.0), (9, 10, 45.0, 1100.0),
        (15, 1, 45.0, 1200.0), (1, 15, 45.0, 1200.0),
        (7, 8, 55.0, 1600.0), (8, 7, 55.0, 1600.0),
        (12, 11, 50.0, 1500.0), (11, 12, 50.0, 1500.0),
        (5, 13, 50.0, 1400.0), (13, 5, 50.0, 1400.0),
        (7, 5, 65.0, 2000.0), (5, 7, 65.0, 2000.0),
    ]

    for u, v, speed_kmh, capacity in road_links:
        u_loc = locations[u]
        v_loc = locations[v]
        dist = haversine_distance(u_loc["lat"], u_loc["lon"], v_loc["lat"], v_loc["lon"])
        speed_ms = speed_kmh / 3.6
        edge = Edge(
            source=u,
            target=v,
            distance=dist,
            free_flow_speed=speed_ms,
            capacity=capacity,
            current_volume=capacity * 0.4,  # 40% initial load
            alpha_bpr=0.15,
            beta_bpr=4.0,
            congestion_factor=1.0
        )
        net.add_edge(edge)

    # Create VRP fleet
    vehicles = [
        Vehicle(id=i, capacity=80.0, fixed_cost=15.0, cost_per_meter=0.0012, cost_per_second=0.015)
        for i in range(5)
    ]

    vrp_inst = VRPInstance(
        name="noida_sector126",
        nodes=nodes_list,
        depot_id=0,
        vehicles=vehicles,
        vehicle_capacity=80.0,
        num_vehicles=5,
        tardiness_penalty_per_sec=0.08
    )

    return net, vrp_inst


def build_solomon_benchmark(instance_type: str = "C101", num_customers: int = 25) -> Tuple[TransportationNetwork, VRPInstance]:
    """
    Standard Solomon benchmark instance generator (C101 Clustered, R101 Random, RC101 Mixed).
    Generates academic benchmark coordinates, demands, and time windows.
    """
    net = TransportationNetwork(name=f"solomon_{instance_type.lower()}")
    random.seed(42)

    # Depot at center (40, 50)
    depot_node = Node(
        id=0,
        name="Central Depot",
        x=40.0,
        y=50.0,
        is_depot=True,
        demand=0.0,
        service_time=0.0,
        ready_time=0.0,
        due_time=1236.0
    )
    net.add_node(depot_node)
    nodes_list = [depot_node]

    # Generate customer nodes based on Solomon characteristics
    clusters = [
        (25.0, 30.0), (30.0, 75.0), (60.0, 70.0), (65.0, 35.0)
    ] if "C" in instance_type.upper() else None

    for i in range(1, num_customers + 1):
        if clusters:
            # Clustered distribution
            cx, cy = clusters[(i - 1) % len(clusters)]
            x = cx + random.gauss(0, 6.0)
            y = cy + random.gauss(0, 6.0)
        elif "R" in instance_type.upper():
            # Uniform random distribution
            x = random.uniform(5.0, 95.0)
            y = random.uniform(5.0, 95.0)
        else:
            # RC mixed
            if i % 2 == 0:
                x = random.uniform(10.0, 90.0)
                y = random.uniform(10.0, 90.0)
            else:
                x = 35.0 + random.gauss(0, 8.0)
                y = 55.0 + random.gauss(0, 8.0)

        demand = random.choice([10.0, 20.0, 15.0, 25.0, 30.0])
        ready = random.uniform(50.0, 600.0)
        due = ready + random.uniform(120.0, 400.0)

        node = Node(
            id=i,
            name=f"Customer {i}",
            x=x,
            y=y,
            is_depot=False,
            demand=demand,
            service_time=90.0,
            ready_time=ready,
            due_time=due
        )
        net.add_node(node)
        nodes_list.append(node)

    # Fully connected or k-nearest neighbor road mesh
    for i in range(len(nodes_list)):
        u = nodes_list[i]
        for j in range(len(nodes_list)):
            if i != j:
                v = nodes_list[j]
                dist = math.hypot(u.x - v.x, u.y - v.y) * 100.0  # scaled to meters
                speed = 13.89  # 50 km/h
                edge = Edge(
                    source=u.id,
                    target=v.id,
                    distance=dist,
                    free_flow_speed=speed,
                    capacity=800.0,
                    current_volume=300.0,
                    alpha_bpr=0.15,
                    beta_bpr=4.0
                )
                net.add_edge(edge)

    vehicles = [
        Vehicle(id=k, capacity=200.0, fixed_cost=50.0, cost_per_meter=0.001, cost_per_second=0.02)
        for k in range(5)
    ]

    vrp_inst = VRPInstance(
        name=f"solomon_{instance_type.lower()}_{num_customers}",
        nodes=nodes_list,
        depot_id=0,
        vehicles=vehicles,
        vehicle_capacity=200.0,
        num_vehicles=5,
        tardiness_penalty_per_sec=0.1
    )

    return net, vrp_inst


def build_synthetic_grid_network(rows: int = 5, cols: int = 5) -> Tuple[TransportationNetwork, VRPInstance]:
    """
    Generates a scalable Manhattan-style urban grid with (rows x cols) intersections.
    Ideal for testing algorithm scalability up to hundreds of nodes.
    """
    net = TransportationNetwork(name=f"synthetic_grid_{rows}x{cols}")
    nodes_list = []
    node_id = 0

    grid: Dict[Tuple[int, int], int] = {}
    base_lat = 28.5000
    base_lon = 77.3000
    for r in range(rows):
        for c in range(cols):
            is_depot = (r == 0 and c == 0)
            demand = 0.0 if is_depot else random.choice([10.0, 15.0, 20.0, 25.0])
            # 0.009 degrees latitude is approx 1000 meters
            lat = base_lat + r * 0.009
            lon = base_lon + c * 0.010
            node = Node(
                id=node_id,
                name=f"Depot" if is_depot else f"Intersection ({r},{c})",
                x=lon,
                y=lat,
                is_depot=is_depot,
                demand=demand,
                service_time=0.0 if is_depot else 180.0,
                ready_time=0.0,
                due_time=28800.0
            )
            net.add_node(node)
            nodes_list.append(node)
            grid[(r, c)] = node_id
            node_id += 1

    # Connect adjacent grid nodes (bidirectional)
    for r in range(rows):
        for c in range(cols):
            u_id = grid[(r, c)]
            # Right neighbor
            if c + 1 < cols:
                v_id = grid[(r, c + 1)]
                net.add_edge(Edge(source=u_id, target=v_id, distance=1000.0, free_flow_speed=13.89, capacity=1000.0, current_volume=400.0))
                net.add_edge(Edge(source=v_id, target=u_id, distance=1000.0, free_flow_speed=13.89, capacity=1000.0, current_volume=400.0))
            # Down neighbor
            if r + 1 < rows:
                v_id = grid[(r + 1, c)]
                net.add_edge(Edge(source=u_id, target=v_id, distance=1000.0, free_flow_speed=13.89, capacity=1000.0, current_volume=400.0))
                net.add_edge(Edge(source=v_id, target=u_id, distance=1000.0, free_flow_speed=13.89, capacity=1000.0, current_volume=400.0))

    vehicles = [
        Vehicle(id=k, capacity=150.0, fixed_cost=20.0, cost_per_meter=0.001, cost_per_second=0.01)
        for k in range(max(3, (rows * cols) // 5))
    ]

    vrp_inst = VRPInstance(
        name=f"synthetic_grid_{rows}x{cols}",
        nodes=nodes_list,
        depot_id=0,
        vehicles=vehicles,
        vehicle_capacity=150.0,
        num_vehicles=len(vehicles)
    )

    return net, vrp_inst


def get_network_by_id(network_id: str) -> Tuple[TransportationNetwork, VRPInstance]:
    """Factory helper to fetch network by identifier."""
    nid = network_id.lower()
    if "noida" in nid:
        return build_noida_sector126_network()
    elif "c101" in nid:
        return build_solomon_benchmark("C101", 25)
    elif "r101" in nid:
        return build_solomon_benchmark("R101", 25)
    elif "rc101" in nid:
        return build_solomon_benchmark("RC101", 25)
    elif "grid" in nid:
        return build_synthetic_grid_network(5, 5)
    else:
        # Default to Noida Sector 126
        return build_noida_sector126_network()
