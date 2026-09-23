"""
Dynamic Traffic Simulator.
Simulates time-of-day congestion waves (morning/evening rush hour)
and injects random or user-triggered incidents (road blocks, accidents).
"""

from typing import Dict, List, Optional
import math
import random
import time

from .graph_model import TransportationNetwork
from ..models.graph import TrafficIncident


class TrafficSimulator:
    """
    Manages dynamic traffic variations on a TransportationNetwork.
    Calculates time-dependent volume multipliers based on hour of day:
        M(t) = base + rush_amplitude * [peak_morning(t) + peak_evening(t)]
    """

    def __init__(self, network: TransportationNetwork):
        self.network = network
        self.simulation_time_seconds: float = 8.0 * 3600.0  # Default 8:00 AM (start of morning rush)
        self.time_compression_factor: float = 60.0  # 1 real sec = 60 sim seconds
        self._last_tick_time: float = time.time()

    def get_time_of_day_multiplier(self, time_seconds: Optional[float] = None) -> float:
        """
        Calculate traffic volume multiplier based on time of day (0 to 86400s).
        Features two Gaussian rush-hour peaks:
          1. Morning peak: centered at 8:30 AM (8.5h), sigma = 1.2h
          2. Evening peak: centered at 6:00 PM (18.0h), sigma = 1.5h
        """
        t_sec = time_seconds if time_seconds is not None else self.simulation_time_seconds
        hour = (t_sec % 86400.0) / 3600.0

        # Morning rush (8:30 AM)
        m_peak = math.exp(-((hour - 8.5) ** 2) / (2 * (1.2 ** 2)))
        # Evening rush (6:00 PM)
        e_peak = math.exp(-((hour - 18.0) ** 2) / (2 * (1.5 ** 2)))
        
        # Base multiplier is 0.5 (off-peak), up to 2.2 during peak rush
        multiplier = 0.5 + 1.4 * m_peak + 1.2 * e_peak
        return multiplier

    def tick(self, dt_real_seconds: float = 1.0) -> None:
        """Advance simulation clock and update network edge volumes."""
        self.simulation_time_seconds += dt_real_seconds * self.time_compression_factor
        multiplier = self.get_time_of_day_multiplier(self.simulation_time_seconds)

        for (u, v), edge in self.network.edges.items():
            # Apply base volume scaled by time of day + small random fluctuation (+- 5%)
            fluctuation = random.uniform(0.95, 1.05)
            # base volume is roughly 50% of capacity
            base_vol = edge.capacity * 0.45
            edge.current_volume = base_vol * multiplier * fluctuation
            new_tt = edge.compute_travel_time()
            self.network.graph[u][v]['weight'] = new_tt
            self.network.graph[u][v]['current_volume'] = edge.current_volume
            
        self.network._is_matrix_dirty = True

    def trigger_accident(self, source: int, target: int, severity: float = 3.0, is_closure: bool = False,
                         description: str = "Multi-vehicle collision") -> TrafficIncident:
        """Simulate a sudden traffic accident causing major congestion or lane closure."""
        inc_id = f"inc_{source}_{target}_{int(time.time())}"
        incident = TrafficIncident(
            id=inc_id,
            source=source,
            target=target,
            severity=severity,
            is_closure=is_closure,
            description=description,
            duration_seconds=1800.0
        )
        self.network.add_incident(incident)
        return incident

    def trigger_rush_hour_surge(self, surge_factor: float = 2.0) -> None:
        """Simulate an abrupt city-wide traffic surge."""
        self.network.apply_global_surge(surge_factor)
