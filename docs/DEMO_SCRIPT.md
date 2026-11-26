# PLANTPULSE Demonstration Script for Challenge Evaluators

**Target Audience**: L'Oréal Sustainability Challenge Jury, Plant Energy Managers, Electrical Maintenance Leads.  
**Demonstration Time**: 5–8 minutes.

---

## 1. Opening: Context & Honesty Statement (1 min)

1. Open the application at `http://127.0.0.1:8000`.
2. Point out the persistent status banner across the top:
   > `"PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET"`  
   > `"All savings are ESTIMATED from SIMULATED data."`
3. Emphasize the core thesis: We chose **Option 03 — Less Waste, Smarter Resource Use**, specifically targeting **Avoidable Idle Electricity** in auxiliary equipment.
4. Point out the primary application theme: **Clean, high-contrast pure white background** on every page, with restrained green sustainability accents and explicit data provenance badges on every numerical figure.

---

## 2. Page 1 (Dashboard) — Executive Overview (1 min)

1. Read the **Operational Headline Sentence**:
   > *"X of 8 equipment currently idle; Z kWh avoidable idle energy identified in selected period — SIMULATED"*
2. Review the primary indicator cards: Active Power ($\text{kW}$), Cumulative Shift Energy ($\text{kWh}$), Avoidable Idle Energy, and Idle Share $\%$.
3. Click **"View Engineering Calculation"** on any card to demonstrate progressive disclosure: shows exact physical formula, inputs, unit, provenance, and assumptions.
4. Note the sparkline chart showing the continuous separation between total load and avoidable idle energy.

---

## 3. Page 2 (Equipment Monitoring) & Page 3 (Idle Analysis) (1.5 mins)

1. Navigate to **Page 2: Equipment Monitoring**:
   * Show the 8 connected equipment items (2 critical, 6 non-critical).
   * Point out the **Lock icon** next to `Main Process Extruder Motor` and `Cooling Tower Circulation Pump`. Note: *"These assets are permanently locked as CRITICAL and can never be shut down."*
   * Click on `Assembly Infeed Conveyor Motor` to show its live active power and line current profile.
2. Navigate to **Page 3: Idle Analysis**:
   * Answer **Track Question 1 ("Where does the loss occur?")**:
   * Show the visual ranked bar chart and ranking table: avoidable idle energy is concentrated in the auxiliary conveyor, exhaust fan, and air compressor during shift pauses.
   * Review the qualifying idle periods log ($t \ge t_{\text{delay}}$).

---

## 4. Page 4 (Optimisation) & Page 5 (Control & Safety) (2 mins)

1. Navigate to **Page 4: Optimisation & Recommendations**:
   * Inspect the **8-Step Logical Flow Stepper**:
     * Step 1: Input Acquisition
     * Step 2: Electrical Parameter Validation
     * Step 3: Real-Time Power Monitoring
     * Step 4: Operating-State Detection
     * Step 5: Idle Condition Identification
     * Step 6: Idle Duration Verification
     * Step 7: Check Equipment Eligibility & Safety Interlocks
     * Step 8: Decision
   * Select `eq_conveyor_motor` (sustained idle qualifying for shutdown recommendation).
   * Select `eq_cooling_water_pump` to demonstrate **Step 7 exclusion**: *"Stopped at Step 7: Critical load — permanent automated shutdown exclusion enforced."*
   * Scroll down to **Trade-off Checklist** (answers Track Question 3: motor inrush thermal stress, restart limits, process lag).
2. Navigate to **Page 5: Control & Safety (Simulated)**:
   * Notice the clear notice: *"NO REAL EQUIPMENT CONTROLLED — SIMULATED COMMANDS ONLY"*.
   * In the top banner, select role **OPERATOR**.
   * In the Approvals Queue, click **"Approve Shutdown"** for an asset.
   * Watch the command appear instantly in the **Simulated Contactor Command Audit Log** tagged with label `SIMULATED COMMAND`.

---

## 5. Scenario Switching Demonstration (1 min)

1. Use the Scenario dropdown in the top navigation bar:
   * Select **"Scenario 3: Intermittent Short Idle"**: Show that brief 30–60s pauses do NOT trigger shutdown recommendations because $t < t_{\text{delay}}$.
   * Select **"Scenario 5: Interlock Blocked"**: Show that an active E-stop or thermal overload halts the pipeline at Step 7 (`BLOCKED_INTERLOCK`).
   * Select **"Scenario 6: Sensor / Data Fault"**: Show that voltage swells or frequency instability fail at Step 2 (`REJECTED_INPUT_FAULT`).
   * Return to **"Scenario 2: Heavy Idle (Baseline)"** and then switch to **"Scenario 7: Optimised Run"**.

---

## 6. Page 6 (Savings) & Page 8 (Reports & Pilot Plan) (1.5 mins)

1. Navigate to **Page 6: Savings & Baseline**:
   * Review the controlled before/after comparison under identical seed ($202$) and identical load schedule.
   * Show the net $\text{kWh}$ saved, estimated cost savings, and emissions reduction with transparent reference rates.
2. Navigate to **Page 8: Reports & Pilot Plan**:
   * Show the dynamic assessment compiled from live database values.
   * Highlight the **Pilot Plan section**: 4-step methodology and 6-stage roadmap (Stage 1 marked `IN PROGRESS`, Stages 2–6 marked `PLANNED / NOT IMPLEMENTED`).
   * Highlight the **Measures Block** and the explicit scope notice: *"Water use / material loss / waste generated: Not in scope of current prototype (energy only)"*.
   * Click **"Print / PDF"** to demonstrate the print-optimized view.
