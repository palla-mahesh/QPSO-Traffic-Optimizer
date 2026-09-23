"""
Graph-based Network Model for Urban Transportation Networks.
Implements weighted directed graph with dynamic traffic congestion calculation
governed by the Bureau of Public Roads (BPR) formulation.
"""

from typing import Dict, List, Tuple, Optional, Any
import math
import networkx as nx
import numpy as np

from ..models.graph import Node, Edge, TrafficIncident


class TransportationNetwork:
    """
    Weighted directed graph modeling a road network.
    Maintains nodes (intersections/depots/customers) and edges (road segments).
    Supports dynamic travel time recalculation and all-pairs shortest path caching.
    """

    def __init__(self, name: str = "transportation_network"):
        self.name = name
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[Tuple[int, int], Edge] = {}
        self.incidents: Dict[str, TrafficIncident] = {}
        self.graph = nx.DiGraph()
        self._distance_matrix: Optional[np.ndarray] = None
        self._travel_time_matrix: Optional[np.ndarray] = None
        self._node_id_to_idx: Dict[int, int] = {}
        self._idx_to_node_id: Dict[int, int] = {}
        self._is_matrix_dirty: bool = True

    def add_node(self, node: Node) -> None:
        """Add or update a node in the network."""
        self.nodes[node.id] = node
        self.graph.add_node(
            node.id,
            x=node.x,
            y=node.y,
            is_depot=node.is_depot,
            demand=node.demand,
            service_time=node.service_time,
            ready_time=node.ready_time,
            due_time=node.due_time,
            name=node.name
        )
        self._is_matrix_dirty = True

    def add_edge(self, edge: Edge) -> None:
        """Add or update a directed edge."""
        self.edges[(edge.source, edge.target)] = edge
        travel_time = edge.compute_travel_time()
        self.graph.add_edge(
            edge.source,
            edge.target,
            distance=edge.distance,
            free_flow_speed=edge.free_flow_speed,
            capacity=edge.capacity,
            current_volume=edge.current_volume,
            alpha_bpr=edge.alpha_bpr,
            beta_bpr=edge.beta_bpr,
            congestion_factor=edge.congestion_factor,
            is_closed=edge.is_closed,
            weight=travel_time  # default weight for routing is travel time
        )
        self._is_matrix_dirty = True

    def update_traffic(self, source: int, target: int, volume: Optional[float] = None,
                       congestion_factor: Optional[float] = None, is_closed: Optional[bool] = None) -> None:
        """Dynamically update traffic volume or congestion on an edge."""
        key = (source, target)
        if key in self.edges:
            edge = self.edges[key]
            if volume is not None:
                edge.current_volume = volume
            if congestion_factor is not None:
                edge.congestion_factor = congestion_factor
            if is_closed is not None:
                edge.is_closed = is_closed
            
            new_tt = edge.compute_travel_time()
            self.graph[source][target]['weight'] = new_tt
            self.graph[source][target]['current_volume'] = edge.current_volume
            self.graph[source][target]['congestion_factor'] = edge.congestion_factor
            self.graph[source][target]['is_closed'] = edge.is_closed
            self._is_matrix_dirty = True

    def add_incident(self, incident: TrafficIncident) -> None:
        """Inject an incident causing a localized traffic disruption or closure."""
        self.incidents[incident.id] = incident
        self.update_traffic(
            incident.source,
            incident.target,
            congestion_factor=incident.severity,
            is_closed=incident.is_closure
        )

    def remove_incident(self, incident_id: str) -> None:
        """Clear an incident and restore normal conditions."""
        if incident_id in self.incidents:
            inc = self.incidents.pop(incident_id)
            self.update_traffic(
                inc.source,
                inc.target,
                congestion_factor=1.0,
                is_closed=False
            )

    def apply_global_surge(self, surge_multiplier: float) -> None:
        """Scale traffic volume across the entire network by a surge factor (e.g. 1.8 for rush hour)."""
        for (u, v), edge in self.edges.items():
            edge.current_volume *= surge_multiplier
            new_tt = edge.compute_travel_time()
            self.graph[u][v]['weight'] = new_tt
            self.graph[u][v]['current_volume'] = edge.current_volume
        self._is_matrix_dirty = True

    def compute_matrices(self) -> Tuple[np.ndarray, np.ndarray, Dict[int, int]]:
        """
        Compute all-pairs shortest paths for distance and dynamic travel time.
        Returns:
            (distance_matrix, travel_time_matrix, node_id_to_idx)
        """
        if not self._is_matrix_dirty and self._distance_matrix is not None:
            return self._distance_matrix, self._travel_time_matrix, self._node_id_to_idx

        node_ids = sorted(list(self.nodes.keys()))
        n = len(node_ids)
        self._node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        self._idx_to_node_id = {i: nid for i, nid in enumerate(node_ids)}

        dist_matrix = np.full((n, n), float('inf'), dtype=np.float64)
        time_matrix = np.full((n, n), float('inf'), dtype=np.float64)
        np.fill_diagonal(dist_matrix, 0.0)
        np.fill_diagonal(time_matrix, 0.0)

        # 1. Travel time all-pairs shortest path via Dijkstra on graph with weight='weight' (travel time)
        try:
            time_lengths = dict(nx.all_pairs_dijkstra_path_length(self.graph, weight='weight'))
            for u, targets in time_lengths.items():
                if u in self._node_id_to_idx:
                    i = self._node_id_to_idx[u]
                    for v, length in targets.items():
                        if v in self._node_id_to_idx:
                            j = self._node_id_to_idx[v]
                            time_matrix[i, j] = length
        except Exception:
            pass

        # 2. Distance all-pairs shortest path via Dijkstra with weight='distance'
        try:
            dist_lengths = dict(nx.all_pairs_dijkstra_path_length(self.graph, weight='distance'))
            for u, targets in dist_lengths.items():
                if u in self._node_id_to_idx:
                    i = self._node_id_to_idx[u]
                    for v, length in targets.items():
                        if v in self._node_id_to_idx:
                            j = self._node_id_to_idx[v]
                            dist_matrix[i, j] = length
        except Exception:
            pass

        # Fallback Euclidean if graph is disconnected or for virtual edges
        for i, uid in enumerate(node_ids):
            u_node = self.nodes[uid]
            for j, vid in enumerate(node_ids):
                if dist_matrix[i, j] == float('inf'):
                    v_node = self.nodes[vid]
                    eucl = math.hypot(u_node.x - v_node.x, u_node.y - v_node.y)
                    dist_matrix[i, j] = eucl
                    # Free-flow time assuming 40 km/h (11.11 m/s)
                    if time_matrix[i, j] == float('inf'):
                        time_matrix[i, j] = eucl / 11.11

        self._distance_matrix = dist_matrix
        self._travel_time_matrix = time_matrix
        self._is_matrix_dirty = False
        return self._distance_matrix, self._travel_time_matrix, self._node_id_to_idx

    def get_shortest_path_nodes(self, source: int, target: int, weight: str = 'weight') -> List[int]:
        """Find the exact path of nodes from source to target."""
        try:
            return nx.shortest_path(self.graph, source=source, target=target, weight=weight)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [source, target]

    def to_dict(self) -> Dict[str, Any]:
        """Export network data as serializable dictionary for API/UI."""
        return {
            "name": self.name,
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "nodes": [node.model_dump() for node in self.nodes.values()],
            "edges": [
                {
                    **edge.model_dump(),
                    "travel_time": edge.compute_travel_time(),
                    "free_flow_time": edge.free_flow_time,
                    "congestion_ratio": edge.current_volume / max(1.0, edge.capacity)
                }
                for edge in self.edges.values()
            ],
            "incidents": [inc.model_dump() for inc in self.incidents.values()]
        }
