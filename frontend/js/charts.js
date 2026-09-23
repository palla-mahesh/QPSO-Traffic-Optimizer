/**
 * Chart Controller for Real-Time Convergence Dynamics.
 * Plots fitness / cost vs. iteration for Quantum and Classical algorithms.
 */

class ConvergenceChartController {
  constructor(canvasId = 'convergenceChart') {
    this.canvasId = canvasId;
    this.chart = null;
    this.initChart();
  }

  initChart() {
    const ctx = document.getElementById(this.canvasId).getContext('2d');
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Best Fitness (Cost)',
            data: [],
            borderColor: '#06b6d4', // Cyan
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.25,
            pointRadius: 0,
            pointHoverRadius: 4
          },
          {
            label: 'Mean Swarm Fitness',
            data: [],
            borderColor: 'rgba(156, 163, 175, 0.5)',
            borderWidth: 1.5,
            borderDash: [4, 4],
            fill: false,
            tension: 0.25,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 150
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Iteration / Generation',
              color: '#9ca3af',
              font: { family: 'Inter', size: 11 }
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#6b7280',
              font: { family: 'JetBrains Mono', size: 10 }
            }
          },
          y: {
            title: {
              display: true,
              text: 'Objective Function Value (Z)',
              color: '#9ca3af',
              font: { family: 'Inter', size: 11 }
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#6b7280',
              font: { family: 'JetBrains Mono', size: 10 }
            }
          }
        },
        plugins: {
          legend: {
            labels: {
              color: '#d1d5db',
              font: { family: 'Inter', size: 11 }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            titleColor: '#06b6d4',
            bodyColor: '#f9fafb',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1
          }
        }
      }
    });
  }

  reset(algoName = 'Optimization') {
    this.chart.data.labels = [];
    this.chart.data.datasets[0].data = [];
    this.chart.data.datasets[0].label = `${algoName} Best Fitness`;
    this.chart.data.datasets[1].data = [];
    this.chart.update('none');
  }

  addIteration(metric) {
    this.chart.data.labels.push(metric.iteration);
    this.chart.data.datasets[0].data.push(metric.best_fitness);
    this.chart.data.datasets[1].data.push(metric.mean_fitness);
    this.chart.update('none');
  }

  loadFullHistory(history, algoName = 'Optimization') {
    this.reset(algoName);
    history.forEach(m => {
      this.chart.data.labels.push(m.iteration);
      this.chart.data.datasets[0].data.push(m.best_fitness);
      this.chart.data.datasets[1].data.push(m.mean_fitness);
    });
    this.chart.update();
  }
}

window.ConvergenceChartController = ConvergenceChartController;
