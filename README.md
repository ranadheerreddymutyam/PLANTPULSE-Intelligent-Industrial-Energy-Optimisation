# PLANTPULSE — Intelligent Industrial Energy Optimisation for Sustainable Manufacturing

**Challenge Track**: L'Oréal Sustainability Challenge, Option 03 — *"Less Waste, Smarter Resource Use"*  
**Challenge Target**: AVOIDABLE IDLE ELECTRICITY of industrial motors, pumps, fans, and auxiliary manufacturing equipment.  
**Project Status**: `PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET`  
**Data Provenance**: `SIMULATED / DEMONSTRATION DATA` (All savings and reductions are estimated from deterministic physical models; never presented as field-measured).

---

## 1. Executive Summary & Core Logic

In manufacturing plants, auxiliary machinery (conveyors, exhaust fans, utility compressors, slurry agitators, washdown pumps) frequently remains powered on during scheduled breaks, shift handovers, and line pauses—drawing continuous active power while producing zero useful manufacturing output.

**PlantPulse** is a non-AI, non-ML, simulation-based engineering decision-support platform built on one straightforward physical principle:
> **Idle operation has an unmistakable electrical signature: low active power ($P < P_{\text{idle}}$) sustained beyond a calibrated time delay ($t \ge t_{\text{delay}}$). Measured against a rigorous baseline, hidden idle kilowatt-hours become a quantified, actionable sustainability opportunity.**

PlantPulse converts raw 3-phase electrical data ($V, I, \text{kW}, \text{kWh}, \text{PF}$) into real-time idle detection, avoidable-energy quantification, actionable recommendations, and operator-approved simulated controlled shutdown of eligible non-critical loads. It is designed as a retrofit layer that **complements, rather than replaces**, existing feeders, motor control centers (MCC), protection relays, and plant control systems.

---

## 2. Track Deliverables Mapping

| Required Deliverable | Platform Implementation | Application Location |
| :--- | :--- | :--- |
| **(1) Baseline Data Needed** | 3-Phase $V_{\text{LL}}$, line current $I$, active power $P$, power factor $PF$, frequency $f$, operating status, and safety interlock circuits. | **Page 8: Reports** & **Page 1: Dashboard** |
| **(2) Proposed Solution** | Deterministic 8-step logical flow engine; rule-based $P_{\text{idle}}$ and $t_{\text{delay}}$ qualification; operator-approved simulated contactor/VFD shutdown. | **Page 4: Optimisation** & **Page 5: Control** |
| **(3) Pilot Plan** | 4-step pilot methodology (Baseline Measurement $\to$ Idle Monitoring $\to$ Before/After Comparison $\to$ Verification) + 6-stage roadmap. | **Page 8: Reports (Pilot Plan)** |
| **(4) Measures Block** | Energy use ($\text{kWh}$), idle $\text{kWh}$, avoidable $\text{kWh}$, estimated cost & emissions savings. Water and material waste explicitly declared out of scope. | **Page 1: Dashboard** & **Page 8: Reports** |

### Three Consideration Questions Answered:
1. **Where does the loss occur?** Answered on **Page 3 (Idle Analysis)** via the ranked avoidable $\text{kWh}$ table and breakdown. Losses occur predominantly in auxiliary fans, compressors, and conveyors during shift handovers.
2. **Can process, equipment, planning, or employee practices reduce it?** Answered on **Page 4 & 8**. Through batch-aligned auxiliary runtime planning, VFD/standby retrofits, and operator-approved one-click pause workflows.
3. **What trade-offs should be checked?** Answered on **Page 4 (Trade-off Checklist)**: motor inrush thermal stress (mitigated by max restarts/hour limits), process restart lag (mitigated by pre-shift alerts), and critical load protection (mitigated by permanent hardware/software lock).

---

## 3. Strict Engineering Safeguards (Hard Boundaries)

* **Zero AI/ML**: No neural networks, random forests, or black-box classifiers. Every calculation uses pure classical physical equations ($S = \sqrt{3}VI$, $P = \sqrt{3}VI\cdot PF$, $Q = \sqrt{S^2-P^2}$, $E = \int P dt$).
* **Permanent Critical Load Exclusion**: Critical assets (e.g. Main Extruder Motor, Cooling Water Circulation Pump) are permanently locked against automated shutdown. This rule cannot be overridden from the UI or API.
* **Operator Approval Workflow**: Controlled shutdown is never autonomous. It requires explicit operator sign-off with audit logging.
* **Simulated Contactor Layer**: Every command is tagged `SIMULATED COMMAND`. No physical relays or field equipment are actuated.
* **Data Provenance Badges**: Every visual number displays an explicit provenance badge (`[SIMULATED]`, `[DERIVED]`, `[ESTIMATED]`, `[CONFIGURED]`, `[IMPORTED]`).

---

## 4. Architecture Overview (L1–L7 Layers)

* **L1 Inputs**: 3-Phase 415 V (line-to-line RMS), 50 Hz balanced AC supply feeding 8 industrial equipment items.
* **L2 Acquisition & Processing**: Deterministic synthetic scenario engine + CSV/JSON import boundary.
* **L3 Energy Analysis Layer**: Centralized `/engineering/calculations.py` computing $S, P, Q, PF, E$, idle duration, and avoidable $\text{kWh}$.
* **L4 Optimisation Engine**: 8-Step state machine generating explainable decision traces.
* **L5 Control & Safety Layer**: Simulated contactor/VFD adapter, interlock monitoring (E-stop, overload, permissive), and restart cooldown limiter.
* **L6 Outputs & UI**: High-contrast, pure white primary background UI built with React + TypeScript + Tailwind CSS across 10 dedicated pages.
* **L7 Governance**: Role-based access control (Operator, Energy Manager, Maintenance, Admin) with complete audit logging.

---

## 5. Quickstart & Installation

### Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 1. Initialize & Seed Backend
```bash
cd backend
python -m app.services.seed
```

### 2. Run Test Suite
```bash
python -m pytest tests/ -v
```

### 3. Start Backend Server
```bash
python run_server.py
# Server runs at http://127.0.0.1:8000 (serves both API and built React frontend)
# OpenAPI documentation available at http://127.0.0.1:8000/docs
```

### 4. Run Frontend in Development (Optional)
```bash
cd ../frontend
npm run dev
# Vite dev server runs at http://localhost:5173
```
