# Figma Design System Specification: Quantum Traffic Route Optimization (Q-TRO)

**Project**: Quantum-Inspired Intelligent Traffic Route Optimization in Transportation Systems Using Metaheuristic Optimization  
**Organization**: Egreen Quanta  
**Vertical**: Quantum Technology Vertical (SIH 2026)  
**Theme**: OLED Midnight / Quantum Cyber-Minimalism  

---

## 1. Design Principles & Aesthetic Direction

The Q-TRO interface is designed according to **Figma-grade Design Standards**:
1. **Clarity & Spatial Rhythm**: Strict 8px spacing system (`4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`).
2. **Cognitive Hierarchy**: High-contrast OLED midnight surfaces (`#050510`) with vibrant quantum accents (`#00FFFF` Cyan, `#7B61FF` Purple, `#FF00FF` Magenta) that guide operator attention to live traffic states without visual clutter.
3. **No Emoji as Structural Icons**: Pure vector SVG icons (Phosphor / FontAwesome / Heroicons) for platform consistency.
4. **Information Density**: Tabbed navigation (`nav-tabs`) dividing spatial routing, quantum convergence dynamics, and comparative benchmarking into focused views.

---

## 2. Figma Tokens & Styles

All tokens are provided in machine-readable format in [`frontend/figma-tokens.json`](file:///Users/psryogeshwar/Downloads/MASHI/frontend/figma-tokens.json) and can be directly loaded into Figma using the **Tokens Studio for Figma** plugin.

### 2.1 Color Palette
| Token Name | Value | Role / Usage |
|---|---|---|
| `color.background.canvas` | `#050510` | Full page canvas background |
| `color.background.surface` | `#0C0D1B` | Primary cards, panels, and tables |
| `color.background.surface-elevated` | `#141628` | Modals, floating map controls, tooltips |
| `color.background.surface-hover` | `#1D2038` | Interactive hover states |
| `color.brand.quantum-cyan` | `#00FFFF` | Primary quantum accent, active tabs, buttons |
| `color.brand.quantum-purple` | `#7B61FF` | Secondary quantum interference gradient |
| `color.brand.quantum-magenta` | `#FF00FF` | Highlight badges, alerts, vehicle route 2 |
| `color.text.primary` | `#E0E0FF` | Primary headers, data metrics |
| `color.text.secondary` | `#9CA3C9` | Secondary labels, descriptions |
| `color.text.muted` | `#5F6588` | Table headers, timestamps, inactive states |
| `color.border.subtle` | `#1F2238` | Subtle card dividers |
| `color.border.default` | `#33334E` | Form borders, card strokes |
| `color.border.focus` | `#00FFFF` | 2px focus ring on inputs and buttons |

### 2.2 Dynamic Traffic Status Tokens
| Token Name | Value | Condition / Semantics |
|---|---|---|
| `color.traffic.free-flow` | `#10B981` | Edge volume ratio $V/C < 0.6$ (Green) |
| `color.traffic.moderate` | `#F59E0B` | Edge volume ratio $0.6 \le V/C \le 1.0$ (Yellow) |
| `color.traffic.congested` | `#EF4444` | Edge volume ratio $V/C > 1.0$ (Red) |
| `color.traffic.disruption` | `#DC2626` | Incident / Complete road closure |

---

## 3. Figma Component Architecture & Auto-Layout

### 3.1 Header Component (`AppHeader`)
- **Frame Type**: Horizontal Auto-Layout (`padding: 12px 24px`, `justify: space-between`, `align: center`).
- **Left**: Logo icon (`40x40px`, gradient `#3B82F6` $\to$ `#7B61FF`, `radius: 10px`) + Title (`Inter 18px Bold`) + Subtitle (`Inter 12px Regular`).
- **Right**: Badge group (`Auto-Layout horizontal gap 8px`):
  - `QPSO Engine Active`: Pill badge with glowing cyan border.
  - `System Status`: Pill badge with pulse dot.

### 3.2 Navigation Tabs (`NavTabs`)
- **Frame Type**: Horizontal Auto-Layout (`gap: 4px`, `background: #0C0D1B`, `padding: 4px`, `radius: 8px`, `border: 1px solid #1F2238`).
- **Tab Variants**:
  - `Default`: Text `#9CA3C9`, transparent background, `padding: 8px 16px`.
  - `Active`: Text `#00FFFF`, background `#141628`, `border: 1px solid #00FFFF33`, `shadow: 0 0 10px #00FFFF22`.

### 3.3 Metric Card (`MetricCard`)
- **Frame Type**: Vertical Auto-Layout (`padding: 12px 16px`, `gap: 4px`, `radius: 10px`, `background: #0C0D1B`, `border: 1px solid #1F2238`).
- **Top**: Label (`Inter 11px Medium`, uppercase, `#5F6588`, tracking: `0.05em`).
- **Bottom**: Value (`JetBrains Mono 20px Bold`, `#E0E0FF`).

### 3.4 Floating Map Toolbar (`MapToolbar`)
- **Frame Type**: Horizontal Auto-Layout (`padding: 6px 12px`, `gap: 8px`, `background: rgba(12, 13, 27, 0.9)`, `backdrop-blur: 12px`, `border: 1px solid #33334E`, `radius: 8px`).
- **Items**: Layer switches (Traffic Heatmap, Vehicle Routes, Incident Markers).

---

## 4. How to Import Tokens into Figma

1. In Figma, install the **Tokens Studio for Figma** plugin (formerly Figma Tokens).
2. Open the plugin and click **Settings** $\to$ **Load from File**.
3. Select [`frontend/figma-tokens.json`](file:///Users/psryogeshwar/Downloads/MASHI/frontend/figma-tokens.json).
4. The plugin will automatically create all Color Styles, Text Styles, and Spacing Tokens in your Figma document.
