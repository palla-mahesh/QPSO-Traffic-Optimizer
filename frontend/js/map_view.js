/**
 * Leaflet Map View Controller for Quantum Traffic Route Optimization.
 * Renders nodes, road edges with BPR congestion levels, and multi-vehicle routes.
 */

class MapViewController {
  constructor(containerId = 'map-container') {
    this.containerId = containerId;
    this.map = null;
    this.nodeLayer = null;
    this.edgeLayer = null;
    this.routeLayer = null;
    this.incidentLayer = null;

    // Route colors for distinct vehicles
    this.routeColors = [
      '#06b6d4', // Cyan
      '#ec4899', // Pink
      '#10b981', // Emerald
      '#f59e0b', // Amber
      '#8b5cf6', // Violet
      '#3b82f6', // Blue
      '#14b8a6', // Teal
      '#f43f5e'  // Rose
    ];

    this.initMap();
  }

  initMap() {
    // Default center at Noida Sector 126 (28.544, 77.332)
    this.map = L.map(this.containerId, {
      zoomControl: true,
      attributionControl: false
    }).setView([28.544, 77.332], 13);

    // Dark theme tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd'
    }).addTo(this.map);

    this.edgeLayer = L.layerGroup().addTo(this.map);
    this.routeLayer = L.layerGroup().addTo(this.map);
    this.incidentLayer = L.layerGroup().addTo(this.map);
    this.nodeLayer = L.layerGroup().addTo(this.map);

    window.addEventListener('resize', () => {
      if (this.map) {
        this.map.invalidateSize();
      }
    });
  }

  renderNetwork(networkData) {
    this.edgeLayer.clearLayers();
    this.nodeLayer.clearLayers();
    this.incidentLayer.clearLayers();

    const nodes = networkData.nodes || [];
    const edges = networkData.edges || [];
    const incidents = networkData.incidents || [];
    const nodeMap = {};

    const bounds = [];

    // 1. Render Nodes
    nodes.forEach(node => {
      nodeMap[node.id] = node;
      const lat = node.y;
      const lon = node.x;
      bounds.push([lat, lon]);

      let marker;
      if (node.is_depot) {
        // Gold Depot Marker
        marker = L.circleMarker([lat, lon], {
          radius: 10,
          fillColor: '#facc15',
          color: '#ffffff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.95
        });
        marker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 12px; color: #111;">
            <strong>${node.name} (DEPOT)</strong><br>
            Time Window: 00:00 - 24:00<br>
            Fleet Depot
          </div>
        `);
      } else {
        // Customer Marker
        marker = L.circleMarker([lat, lon], {
          radius: 6,
          fillColor: '#38bdf8',
          color: '#ffffff',
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.8
        });
        const readyH = (node.ready_time / 3600).toFixed(1);
        const dueH = (node.due_time / 3600).toFixed(1);
        marker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 12px; color: #111;">
            <strong>${node.name}</strong><br>
            Demand: ${node.demand} units<br>
            Window: ${readyH}h - ${dueH}h<br>
            Service: ${node.service_time}s
          </div>
        `);
      }
      this.nodeLayer.addLayer(marker);
    });

    // 2. Render Road Edges with BPR Congestion Color
    edges.forEach(edge => {
      const u = nodeMap[edge.source];
      const v = nodeMap[edge.target];
      if (!u || !v) return;

      const ratio = edge.congestion_ratio || (edge.current_volume / Math.max(1, edge.capacity));
      let edgeColor = '#10b981'; // Green: free flow
      let weight = 2.5;

      if (edge.is_closed) {
        edgeColor = '#7f1d1d'; // Dark Red
        weight = 3;
      } else if (ratio >= 1.2) {
        edgeColor = '#ef4444'; // Red: Heavy congestion
        weight = 3.5;
      } else if (ratio >= 0.7) {
        edgeColor = '#f59e0b'; // Yellow: Moderate
        weight = 3;
      }

      const polyline = L.polyline([[u.y, u.x], [v.y, v.x]], {
        color: edgeColor,
        weight: weight,
        opacity: 0.65,
        smoothFactor: 1
      });

      polyline.bindTooltip(`
        <strong>${u.name} &rarr; ${v.name}</strong><br>
        Speed: ${(edge.free_flow_speed * 3.6).toFixed(0)} km/h<br>
        Travel Time: ${(edge.travel_time || 0).toFixed(1)}s<br>
        Congestion: ${(ratio * 100).toFixed(0)}%
      `, { sticky: true });

      this.edgeLayer.addLayer(polyline);
    });

    // 3. Render Incidents
    incidents.forEach(inc => {
      const u = nodeMap[inc.source];
      const v = nodeMap[inc.target];
      if (u && v) {
        const midLat = (u.y + v.y) / 2.0;
        const midLon = (u.x + v.x) / 2.0;
        const incMarker = L.circleMarker([midLat, midLon], {
          radius: 8,
          fillColor: '#dc2626',
          color: '#ffffff',
          weight: 2,
          fillOpacity: 1
        });
        incMarker.bindPopup(`<strong>Incident:</strong> ${inc.description}<br>Severity: ${inc.severity}x`);
        this.incidentLayer.addLayer(incMarker);
      }
    });

    if (bounds.length > 0) {
      this.map.fitBounds(bounds, { padding: [30, 30] });
    }
  }

  renderRoutes(routes, networkData) {
    this.routeLayer.clearLayers();
    if (!routes || routes.length === 0) return;

    const nodeMap = {};
    (networkData.nodes || []).forEach(n => { nodeMap[n.id] = n; });

    routes.forEach((route, idx) => {
      const color = this.routeColors[idx % this.routeColors.length];
      const latlngs = [];

      route.node_sequence.forEach(nid => {
        const n = nodeMap[nid];
        if (n) {
          latlngs.push([n.y, n.x]);
        }
      });

      if (latlngs.length > 1) {
        // Glow effect line
        const glowLine = L.polyline(latlngs, {
          color: color,
          weight: 6,
          opacity: 0.35,
          smoothFactor: 1
        });
        this.routeLayer.addLayer(glowLine);

        // Main sharp route line
        const mainLine = L.polyline(latlngs, {
          color: color,
          weight: 3.5,
          opacity: 0.95,
          dashArray: '8, 6',
          smoothFactor: 1
        });

        mainLine.bindPopup(`
          <div style="font-family: sans-serif; font-size: 12px; color: #111;">
            <strong>Vehicle ${route.vehicle_id + 1} Route</strong><br>
            Stops: ${route.node_sequence.length}<br>
            Distance: ${(route.total_distance / 1000).toFixed(2)} km<br>
            Travel Time: ${(route.total_travel_time).toFixed(1)} s<br>
            Payload Load: ${route.total_load.toFixed(1)} units<br>
            Cost: ${route.cost.toFixed(2)}
          </div>
        `);

        this.routeLayer.addLayer(mainLine);
      }
    });
  }
}

window.MapViewController = MapViewController;
