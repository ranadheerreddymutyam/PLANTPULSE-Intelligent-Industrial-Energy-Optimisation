# PLANTPULSE Engineering Methodology & Mathematical Formulas

All mathematical functions in PlantPulse are strictly deterministic, physical, and rule-based. No neural networks, predictive models, or black-box algorithms are used.

All calculations reside in a single centralized module: `backend/app/engineering/calculations.py`. The frontend never duplicates or reimplements any calculation.

---

## 1. 3-Phase AC Power Fundamentals

All calculations assume a balanced 3-phase AC supply where:
* $V$ is line-to-line RMS voltage (nominal 415.0 V in European/IEC industrial distribution)
* $I$ is line RMS current in Amperes
* $\sqrt{3} \approx 1.7320508075688772$

### 1.1 Apparent Power ($S$)
$$S = \frac{\sqrt{3} \times V_{\text{LL}} \times I_{\text{line}}}{1000} \quad [\text{kVA}]$$
* **Provenance**: `DERIVED`
* **Guards**: If $V < 0$ or $I < 0$ or missing, returns $0.0\text{ kVA}$.

### 1.2 Active Power ($P$)
$$P = \frac{\sqrt{3} \times V_{\text{LL}} \times I_{\text{line}} \times PF}{1000} \quad [\text{kW}]$$
Or taken directly from imported/metered active power if provided by physical PQ logger:
$$P = P_{\text{metered}} \quad [\text{kW}]$$
* **Provenance**: `DERIVED` or `IMPORTED`

### 1.3 Power Factor ($PF$)
$$PF = \frac{P}{S} \quad [\text{dimensionless}]$$
* **Provenance**: `DERIVED`
* **Guards**: If $S \le 10^{-6}\text{ kVA}$, returns $1.0$ if $P > 0$ else $0.0$; clamps within $[0.0, 1.0]$.

### 1.4 Reactive Power ($Q$)
$$Q = \sqrt{\max\left(0.0, \, S^2 - P^2\right)} \quad [\text{kvar}]$$
* **Provenance**: `DERIVED`

---

## 2. Energy Accumulation via Trapezoidal Numerical Integration

Energy is computed strictly via numerical integration over discrete timestamped telemetry samples:
$$E = \int_{t_0}^{t_n} P(t) \, dt \approx \sum_{i=1}^{n} \frac{P_{i-1} + P_i}{2} \times \frac{t_i - t_{i-1}}{3600} \quad [\text{kWh}]$$
* **Guards**: If $\Delta t = t_i - t_{i-1} \le 0$ (non-monotonic or duplicated timestamps), the interval is skipped to preserve physical validity.
* **Provenance**: `DERIVED`

---

## 3. Idle Detection & Avoidable Energy Quantification

### 3.1 Idle Condition
An instantaneous telemetry sample at timestamp $t$ is identified as idle if and only if:
$$\text{idle}(t) = \left(P(t) < P_{\text{idle}}\right) \land \left(\text{state}(t) \in \{\text{RUNNING}, \text{IDLE}\}\right)$$
* **Note**: When an asset is stopped intentionally ($\text{state} = \text{STOPPED}$), $P \approx 0$ is not counted as active idle loss.

### 3.2 Idle Duration Verification (Qualifying Period)
A continuous idle period $[t_{\text{start}}, t_{\text{end}}]$ qualifies as an actionable idle condition if and only if:
$$\Delta t_{\text{idle}} = t_{\text{end}} - t_{\text{start}} \ge t_{\text{delay}}$$
* Where $t_{\text{delay}}$ is a configured engineering reference buffer (typically 90s to 240s) designed to prevent false trips during transient process pauses.

### 3.3 Avoidable Idle Energy ($E_{\text{avoid}}$)
The avoidable idle energy represents the active energy consumed **strictly after the configured delay has elapsed**, for eligible equipment only:
$$E_{\text{avoid}} = \begin{cases}
\int_{t_{\text{start}} + t_{\text{delay}}}^{t_{\text{end}}} P(t) \, dt & \text{if equipment is NON-CRITICAL and ELIGIBLE} \\
0.0 & \text{if equipment is CRITICAL or INELIGIBLE}
\end{cases}$$
* **Provenance**: `ESTIMATED`

---

## 4. Economic, Carbon, and Baseline Savings

### 4.1 Net Energy Savings ($E_{\text{save}}$)
$$E_{\text{save}} = \max\left(0.0, \, E_{\text{avoid}} - E_{\text{restart\_allowance}}\right) \quad [\text{kWh}]$$
* Where $E_{\text{restart\_allowance}}$ is a configured reference accounting for motor inrush energy losses during restart.

### 4.2 Cost Savings
$$\text{Cost Savings} = E_{\text{save}} \times \text{Tariff} \quad [\text{Currency}]$$

### 4.3 Emissions Reduction
$$\text{Emissions Reduction} = E_{\text{save}} \times \text{Emission Factor} \quad [\text{kg CO}_2\text{e}]$$
* Explicitly labelled as a demonstration reference rate, not an official regulatory factor.

### 4.4 Before/After Comparison Fairness Guarantee
$$\text{Saving Percentage} = \frac{E_{\text{baseline}} - E_{\text{after}}}{E_{\text{baseline}}} \times 100 \quad [\%]$$
* **Fairness Rule**: Before/after comparisons are computed **strictly between two runs sharing the exact same random seed, operational load schedule, and runtime duration**.
