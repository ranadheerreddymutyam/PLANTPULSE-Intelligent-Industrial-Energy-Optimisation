# PLANTPULSE Pilot Plan & Implementation Roadmap

**Track Requirement Deliverable 3**: Comprehensive pilot implementation plan for industrial validation.  
**Honesty Statement**: `PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET`

---

## 1. Six-Stage Implementation Roadmap

| Stage Gate | Name | Current Status | Description & Deliverables |
| :---: | :--- | :---: | :--- |
| **Stage 1** | **System Design** | **IN PROGRESS** | Algorithmic state machine, database schema, centralized calculation layer, and UI platform (delivered in this codebase). |
| **Stage 2** | **Component Selection** | **PLANNED / NOT IMPLEMENTED** | Finalizing split-core CTs, potential transformers, metering ICs (ADE9000), and industrial relay modules. |
| **Stage 3** | **Hardware Prototype Development** | **PLANNED / NOT IMPLEMENTED** | Building DIN-rail mounted retrofit edge enclosure with hardware safety interlock relays. |
| **Stage 4** | **Functional Testing in Test Cell** | **PLANNED / NOT IMPLEMENTED** | Bench testing against 415 V motor test bench under artificial load and simulated safety trips. |
| **Stage 5** | **Industrial Pilot Validation** | **PLANNED / NOT IMPLEMENTED** | Single-line pilot deployment at a participating manufacturing facility under controlled conditions. |
| **Stage 6** | **Multi-Site Industrial Deployment** | **PLANNED / NOT IMPLEMENTED** | Plant-wide scaling across packaging and process lines. |

---

## 2. Four-Step Pilot Execution Methodology

```
+---------------------------------------------------------------------------------+
| STEP 1: Baseline Energy Measurement (2-4 Weeks Non-Intrusive)                   |
| - Connect CTs/VTs without actuating any control relays                           |
| - Establish unmitigated shift energy profile, shift handover idle, and baselines |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| STEP 2: Idle-Period Monitoring & Signature Calibration                          |
| - Calibrate individual P_idle (kW) and t_delay (s) for each motor/fan/pump      |
| - Validate false-trip rejection during normal short production pauses           |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| STEP 3: Controlled Before-and-After Comparison                                  |
| - Enable operator-approved simulated or real contactor shutdowns                 |
| - Maintain identical shift duration, batch sizes, and operating conditions      |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| STEP 4: Verification Under Comparable Conditions                                |
| - Normalize kWh reduction against ambient temperature and product output         |
| - Audit motor winding temperatures to verify no inrush thermal degradation      |
+---------------------------------------------------------------------------------+
```

---

## 3. Scope Boundaries & Exclusions

* **In Scope**: Avoidable idle electrical consumption ($\text{kWh}$), electrical signature characterization ($V, I, P, Q, PF$), operator-approved controlled shutdown simulation, and safe-restart limiter.
* **Explicitly Out of Scope for Current Prototype**: Water consumption, material scrap reduction, wastewater chemical load, and steam/boiler thermodynamics. These are designated as *"Not in scope of current prototype (energy only)"*.
