# PROPOSED HARDWARE ARCHITECTURE — IMPLEMENTATION PENDING

**Project Status**: `PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET`  
**Prototype Scope Notice**: The software platform released in this repository operates strictly in simulation and software test mode. No physical hardware, microcontrollers, serial connections, or contactor coils are actuated in this software prototype. This document specifies the proposed physical retrofit architecture for subsequent pilot validation.

---

## 1. Physical Retrofit Design Overview

PlantPulse is engineered as a non-invasive retrofit layer that connects to existing motor control centers (MCCs) and distribution switchboards without altering protective circuit breakers or primary thermal overload trips.

```
       [ 3-Phase 415 V (Line-to-Line) 50 Hz Feeder Bus ]
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
     [ VT / PT Sensing ]                  [ CT Sensing ]
   (415 V LL -> 110 V / 3.3 V)          (Split-core 100:5A)
            |                                     |
            +------------------+------------------+
                               |
                               v
               +-------------------------------+
               |     DEDICATED METERING IC     |
               | (ADE9000 / ATM90E36A 24-bit)  |
               +-------------------------------+
                               | SPI / Isolated UART
                               v
               +-------------------------------+
               |    EDGE EMBEDDED CONTROLLER   |
               |     (ARM Cortex-M4 / Linux)   |
               +-------------------------------+
                     |                   |
 (Simulated Telemetry Pipeline)          | (Simulated Contactor/VFD Interface)
                     v                   v
           +-------------------+  +--------------------------------+
           | PLANTPULSE CLOUD/ |  | SAFETY INTERLOCK INTERFACE     |
           | LOCAL EDGE SERVER |  | - Emergency Stop Loop          |
           | - 8-Step Engine   |  | - Overload Relay Contacts 95/96|
           | - Operator Signoff|  | - Process Permissive Relay     |
           +-------------------+  | - Manual Maintenance Bypass    |
                                  +--------------------------------+
                                                 |
                                                 v
                                  [ Contactor Auxiliary Trip / VFD Standby ]
```

---

## 2. Hardware Subsystem Specifications

### 2.1 Voltage Sensing (VT/PT)
* **Input**: 3-Phase 415 V AC line-to-line RMS, 240 V line-to-neutral.
* **Component**: Precision potential divider or 415V/110V potential transformer (Class 0.2 accuracy).
* **Protection**: In-line fast-acting fuses (2A 500V HBC).

### 2.2 Current Sensing (CT)
* **Component**: Split-core current transformers (Class 0.5S) sized to equipment full-load current (e.g. 50:5A to 200:5A).
* **Advantage**: Retrofit installation without disconnecting primary busbars or motor leads.

### 2.3 Metering Analog Front-End (AFE)
* **Component**: Dedicated multi-phase power metering IC (e.g., Analog Devices ADE9000 or Microchip ATM90E36A).
* **Capability**: True RMS calculation of voltage, current, active power, reactive power, displacement power factor, and line frequency at 4 kHz sample rate.

### 2.4 Contactor & VFD Interface
* **Direct-On-Line (DOL) Contactor**: Interfaced via dry relay contacts in series with the contactor coil circuit, downstream of plant safety loops.
* **VFD Controlled Drives**: Interfaced via digital standby/enable inputs (e.g., Safe Torque Off or Run/Stop auxiliary input) to command controlled deceleration without cutting bus power.

### 2.5 Hardware Interlock Verification Loop
To guarantee process and personnel safety, the hardware adapter incorporates hard-wired series interlocks:
1. **Emergency Stop (E-Stop)**: If engaged, isolates the automated control adapter immediately.
2. **Thermal Overload Relay (95/96)**: If tripped, automated restart commands are physically inhibited.
3. **Upstream Process Permissive**: Connected to PLC dry contacts ensuring downstream conveyors/pumps do not stop while upstream tanks or hoppers are discharging.
4. **Local Manual Bypass Switch**: Mounted on the motor control panel allowing technicians to override automated control during maintenance.
