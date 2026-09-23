/**
 * Dynamic Traffic Simulation Controller.
 * Handles triggering accidents, rush hour surges, closures, and resets.
 */

class TrafficSimulationController {
  constructor(app) {
    this.app = app;
    this.bindEvents();
  }

  bindEvents() {
    const accidentBtn = document.getElementById('btn-disrupt-accident');
    if (accidentBtn) {
      accidentBtn.addEventListener('click', (e) => this.triggerDisruption('accident', e.currentTarget));
    }

    const rushBtn = document.getElementById('btn-disrupt-rush');
    if (rushBtn) {
      rushBtn.addEventListener('click', (e) => this.triggerDisruption('rush_hour', e.currentTarget));
    }

    const closureBtn = document.getElementById('btn-disrupt-closure');
    if (closureBtn) {
      closureBtn.addEventListener('click', (e) => this.triggerDisruption('road_closure', e.currentTarget));
    }

    const clearBtn = document.getElementById('btn-clear-traffic');
    if (clearBtn) {
      clearBtn.addEventListener('click', (e) => this.clearTraffic(e.currentTarget));
    }
  }

  async triggerDisruption(type, btnElement) {
    const networkId = document.getElementById('network-select').value;
    const originalHtml = btnElement ? btnElement.innerHTML : '';
    if (btnElement) {
      btnElement.disabled = true;
      btnElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Applying...';
    }

    try {
      this.app.setStatus(`Simulating ${type}...`, 'warning');
      const res = await fetch(`/api/traffic/disrupt?network_id=${networkId}&disruption_type=${type}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      console.log('Traffic disruption applied:', data);

      await this.app.loadNetwork();
      this.app.setStatus(`Disruption active: ${type}. Quantum re-routing...`, 'warning');
      await this.app.runOptimization();
      this.app.setStatus(`Dynamic re-routing completed for ${type}`, 'success');
    } catch (err) {
      console.error('Failed to trigger disruption:', err);
      this.app.setStatus('Disruption failed', 'error');
    } finally {
      if (btnElement) {
        btnElement.disabled = false;
        btnElement.innerHTML = originalHtml;
      }
    }
  }

  async clearTraffic(btnElement) {
    const networkId = document.getElementById('network-select').value;
    const originalHtml = btnElement ? btnElement.innerHTML : '';
    if (btnElement) {
      btnElement.disabled = true;
      btnElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Resetting...';
    }

    try {
      this.app.setStatus('Clearing traffic conditions...', 'info');
      const res = await fetch(`/api/traffic/clear?network_id=${networkId}`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await this.app.loadNetwork();
      this.app.setStatus('Traffic reset to normal baseline', 'success');
      await this.app.runOptimization();
    } catch (err) {
      console.error('Failed to clear traffic:', err);
      this.app.setStatus('Reset failed', 'error');
    } finally {
      if (btnElement) {
        btnElement.disabled = false;
        btnElement.innerHTML = originalHtml;
      }
    }
  }
}

window.TrafficSimulationController = TrafficSimulationController;
