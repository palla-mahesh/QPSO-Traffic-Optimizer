# Mathematical Formulation: Quantum-Inspired Intelligent Traffic Route Optimization (CVRPTW-TC)

**Problem Statement ID**: 26137  
**Organization**: Egreen Quanta  
**Vertical**: Quantum Technology Vertical (SIH 2026)  

---

## 1. Introduction and Network Model

The transportation network is modeled as a weighted directed multigraph $G = (V, E)$, where:
- $V = \{0\} \cup C$: The set of vertices. Vertex $0$ denotes the central fleet depot (e.g., Egreen Quanta Headquarters, NASSCOM Campus, Sector 126, Noida), and $C = \{1, 2, \dots, n\}$ denotes the set of customer delivery locations or demand nodes.
- $E = \{(i, j) : i, j \in V, i \ne j\}$: The set of directed road segments.
- $K = \{1, 2, \dots, m\}$: The homogeneous or heterogeneous fleet of vehicles with payload capacities $Q_k$.

### 1.1 Dynamic Congestion Modeling (BPR Function)
For each road segment $(i, j) \in E$, the physical length is denoted by $d_{ij}$ and the free-flow speed by $v_{ij}^0$. The free-flow travel time is:
$$t_{ij}^0 = \frac{d_{ij}}{v_{ij}^0}$$

To capture real-time dynamic congestion, we employ the standard **Bureau of Public Roads (BPR)** link performance function:
$$t_{ij}(V_{ij}) = t_{ij}^0 \left[ 1 + \alpha_{BPR} \left( \frac{V_{ij}}{C_{ij}} \right)^{\beta_{BPR}} \right] \cdot \gamma_{ij}$$

where:
- $V_{ij}$: Current traffic volume on edge $(i, j)$ (vehicles per hour).
- $C_{ij}$: Practical traffic capacity of the road segment (vehicles per hour).
- $\alpha_{BPR} \ge 0, \beta_{BPR} \ge 1$: Calibrated BPR parameters (standard values: $\alpha_{BPR} = 0.15, \beta_{BPR} = 4.0$).
- $\gamma_{ij} \ge 1.0$: Dynamic incident/disruption multiplier ($\gamma_{ij} = 1.0$ for normal flow, $\gamma_{ij} > 2.0$ for accidents or severe bottlenecks, $\gamma_{ij} = \infty$ for complete road closures).

---

## 2. Mixed Integer Linear Programming (MILP) Formulation

### 2.1 Parameters
| Symbol | Description |
|---|---|
| $d_{ij}$ | Physical distance of edge $(i, j)$ (meters) |
| $t_{ij}(s)$ | Time-dependent dynamic travel time from $i$ to $j$ departing at time $s$ (seconds) |
| $q_i$ | Demand of customer $i \in C$ ($q_0 = 0$) |
| $Q_k$ | Maximum payload capacity of vehicle $k \in K$ |
| $[a_i, b_i]$ | Earliest ready time $a_i$ and latest due time $b_i$ for node $i \in V$ |
| $s_i$ | Service / unloading duration at customer $i \in C$ |
| $f_k$ | Fixed deployment cost for activating vehicle $k$ |
| $c_d$ | Variable cost per unit distance traveled |
| $c_t$ | Variable cost per unit travel time |
| $p_{\text{delay}}$ | Penalty cost per unit time of customer tardiness |

### 2.2 Decision Variables
- $x_{ijk} \in \{0, 1\}$: Binary variable equal to $1$ if vehicle $k \in K$ traverses directed edge $(i, j) \in E$; $0$ otherwise.
- $S_{ik} \ge 0$: Continuous variable indicating the service start time of vehicle $k$ at node $i \in V$.
- $L_{ik} \ge 0$: Cumulative load of vehicle $k$ immediately upon departing node $i \in V$.
- $u_k \in \{0, 1\}$: Binary variable equal to $1$ if vehicle $k$ is utilized; $0$ otherwise.
- $T_{ik} \ge 0$: Tardiness of vehicle $k$ at customer $i$ ($T_{ik} = \max(0, S_{ik} - b_i)$).

### 2.3 Objective Function
$$\min Z = \sum_{k \in K} f_k u_k + \sum_{k \in K} \sum_{(i,j) \in E} \left( c_d d_{ij} + c_t t_{ij}(S_{ik} + s_i) \right) x_{ijk} + \sum_{k \in K} \sum_{i \in C} p_{\text{delay}} T_{ik}$$

The objective minimizes the weighted sum of vehicle activation fixed costs, total distance traveled, total dynamic congestion-adjusted travel time, and time-window tardiness penalties.

### 2.4 Mathematical Constraints

#### 1. Exact Customer Visit Constraint
Every customer must be visited exactly once by exactly one vehicle:
$$\sum_{k \in K} \sum_{j \in V, j \ne i} x_{ijk} = 1, \quad \forall i \in C$$

#### 2. Fleet Depot Departures and Arrivals
Each vehicle $k$ departs from and returns to the depot if and only if it is active:
$$\sum_{j \in C} x_{0jk} = u_k, \quad \forall k \in K$$
$$\sum_{i \in C} x_{i0k} = u_k, \quad \forall k \in K$$

#### 3. Flow Conservation
At every customer node, inflow equals outflow for any vehicle $k$:
$$\sum_{i \in V, i \ne p} x_{ipk} - \sum_{j \in V, j \ne p} x_{pjk} = 0, \quad \forall p \in C, \forall k \in K$$

#### 4. Vehicle Capacity & Subtour Elimination (MTZ Formulation)
Load accumulates along the route and prevents sub-tours:
$$L_{jk} \ge L_{ik} + q_j - M (1 - x_{ijk}), \quad \forall i \in V, \forall j \in C, i \ne j, \forall k \in K$$
$$q_i \le L_{ik} \le Q_k, \quad \forall i \in C, \forall k \in K$$
$$L_{0k} = 0, \quad \forall k \in K$$

#### 5. Time Window & Travel Time Propagation
$$S_{jk} \ge S_{ik} + s_i + t_{ij}(S_{ik} + s_i) - M (1 - x_{ijk}), \quad \forall i, j \in V, \forall k \in K$$
$$S_{ik} \ge a_i, \quad \forall i \in V, \forall k \in K$$
$$T_{ik} \ge S_{ik} - b_i, \quad \forall i \in C, \forall k \in K$$
$$T_{ik} \ge 0, \quad \forall i \in C, \forall k \in K$$

---

## 3. Quantum-Inspired Metaheuristic: QPSO Mechanics

Classical Particle Swarm Optimization (PSO) updates particles using Newtonian velocity vectors:
$$V_i(t+1) = w V_i(t) + c_1 r_1 (P_{i,best} - X_i(t)) + c_2 r_2 (G_{best} - X_i(t))$$
$$X_i(t+1) = X_i(t) + V_i(t+1)$$

In classical PSO, particles are bounded by Newtonian trajectories and frequently become trapped in local optima when $V_i(t) \to 0$.

### 3.1 Quantum Delta-Potential Well Model
In **Quantum Particle Swarm Optimization (QPSO)**, particles exist in a quantum space governed by the Schrödinger equation. Particles have no deterministic velocity; instead, their state is characterized by a wave function $\psi(X)$.

Solving the time-independent Schrödinger equation for a one-dimensional delta-potential well centered at the local attractor $p$:
$$-\frac{\hbar^2}{2m} \frac{d^2 \psi(y)}{dy^2} - \gamma \delta(y) \psi(y) = E \psi(y), \quad y = X - p$$

yields the normalized bound-state wave function:
$$\psi(y) = \frac{1}{\sqrt{L}} \exp\left( -\frac{|y|}{L} \right)$$
where $L = \frac{\hbar^2}{m \gamma}$ is the characteristic width of the quantum potential well.

The probability density of observing particle $i$ at position $X$ is:
$$Q(X) = |\psi(X)|^2 = \frac{1}{L} \exp\left( -\frac{2|X - p|}{L} \right)$$

Using Monte Carlo inverse cumulative distribution sampling:
$$s = \int_{-\infty}^X Q(z) dz = \begin{cases} \frac{1}{2} \exp\left(\frac{2(X-p)}{L}\right), & X < p \\ 1 - \frac{1}{2} \exp\left(-\frac{2(X-p)}{L}\right), & X \ge p \end{cases}$$

Letting $u \sim U(0, 1)$, the quantum position collapse equation is derived:
$$X(t+1) = p \pm \frac{L}{2} \ln\left( \frac{1}{u} \right)$$

### 3.2 Mean Best Position ($mbest$) and Stochastic Attractor
To provide cooperative collective intelligence, Sun et al. introduced the **Mean Best Position** ($mbest$):
$$mbest(t) = \frac{1}{M} \sum_{i=1}^M P_{i,best}(t) = \left( \frac{1}{M}\sum_{i=1}^M P_{i,1}, \dots, \frac{1}{M}\sum_{i=1}^M P_{i,D} \right)$$

The characteristic well length is dynamically scaled as:
$$L_{id}(t) = 2 \beta(t) |mbest_d(t) - X_{id}(t)|$$

where $\beta(t)$ is the **Contraction-Expansion (CE) parameter**.

The stochastic local attractor $p_{id}$ balances cognitive and social information:
$$p_{id}(t) = \phi_{id}(t) P_{id,best}(t) + (1 - \phi_{id}(t)) G_{d,best}(t), \quad \phi_{id} \sim U(0, 1)$$

### 3.3 Quantum Update Rule
$$X_{id}(t+1) = p_{id}(t) \pm \beta(t) \cdot |mbest_d(t) - X_{id}(t)| \cdot \ln\left( \frac{1}{u_{id}(t)} \right), \quad u_{id} \sim U(0, 1)$$

The $\pm$ sign is chosen with equal probability ($0.5$).

### 3.4 Contraction-Expansion Scheduling
To balance global exploration in early iterations and local exploitation near convergence, $\beta$ is scheduled dynamically:
$$\beta(t) = \beta_{\max} - \frac{t}{T_{\max}} (\beta_{\max} - \beta_{\min})$$
where $\beta_{\max} = 1.0$ and $\beta_{\min} = 0.5$.

### 3.5 Quantum Tunneling Effect
Because the quantum wave function $|\psi(X)|^2 > 0$ for all $X \in (-\infty, \infty)$, a QPSO particle has a strictly non-zero probability of appearing outside any barrier or local basin, allowing it to escape local minima that permanently trap classical PSO.
