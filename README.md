# Reliability Analysis of a Closed-Loop Martian Life Support System

**Author**: Zong-Hua Wu

**NetID**: zonghua2


## Overview

A Monte Carlo simulation project designed to model the survivability of a 6-person Martian colony over a 500-day mission.

Unlike standard resource management games, this project models the complex dependencies between electrical power, life support (ECLSS), and biological systems. It tests whether a colony is better served by Engineering Redundancy (spare machines) or Resource Buffering (larger batteries) when facing stochastic risks like dust storms and mechanical failures.


## Inspiration

This project was originally inspired by the mechanics of Fallout Shelter, but pivoted to focus on the constraints of real-world spaceflight. Instead of optimizing for "happiness," Project Ares optimizes for mass efficiency and reliability, utilizing data from NASA's Environmental Control and Life Support Systems (ECLSS).


## Phase 1: The Model

The simulation tracks the daily status of Oxygen, Water, Food, and Power. It utilizes a Closed-Loop System where waste water is recycled, and power generation drives life support.

### Deterministic Variables
- Mission Members: 6 crew members
- Mission Duration: 500 days
- Consumption: Based on NASA "Baseline Values for Human Space Flight"
- Power Load: for oxygenator, water reclaimer, and other base systems

### Stochastic Variables (The Risks)

| Variable | Model Used | Description |
| :- | :- | :- |
| Mechanical Failure | Exponential Distribution | Modeled using Mean Time Between Failures (MTBF). |
Repair Time | Log-Normal Distribution | Repairs are usually fast, but have a "long tail" representing catastrophic diagnostics. |
Martian Weather | Beer-Lambert / Markov | Simulates Solar Longitude (Ls) to create "Clear" and "Dusty" seasons, plus stochastic Global Dust Storms. |
Crop Yield | Normal Distribution | Simulates biological variability in hydroponic food and oxygen output. |


## Phase 2: Experiments & Hypotheses

Ran 1000 Monte Carlo simulations for three distinct experiments.

### The Control Group (Baseline)
- **Setup**: 1 Large Oxygenator, Standard Battery, Standard Solar.
- **Purpose**: Baseline for failure rates under normal Martian conditions.

### Hypothesis 1: The Redundancy Test
- **Question**: Is it safer to have one high-output machine or three lower-output machines?
- **Hypothesis**: The distributed system (3 units) will result in higher survival because it avoids "Zero-Production Days."
- **Implementation**: Replaced 1 Large Oxygenator with 3 Small ones (total capacity matched).

### Hypothesis 2: The Battery Test
- **Question**: Given a fixed mass budget, is it better to maximize Solar Power (Generation) or Battery Buffer (Storage)?
- **Hypothesis**: Due to the stochastic nature of storms, Storage > Generation. Bringing more batteries will yield higher survival rates than more solar panels.
- **Implementation**: Reduced Solar Capacity to fund a massive Battery Bank increase.


## Phase 3: Results & Conclusions

Here's a sample run of 1,000 Monte Carlo simulations for three experiment types:

```terminal
--- Starting Experiment: CONTROL ---
Simulations: 1000
Success Rate: 49.70%
Failure Causes: {'Power Failure': 333, 'Suffocation': 162, 'Dehydration': 8}

--- Starting Experiment: OXYGENATOR_REDUNDANCY_TEST ---
Simulations: 1000
Success Rate: 62.50%
Failure Causes: {'Power Failure': 370, 'Dehydration': 5}

--- Starting Experiment: BATTERY_TEST ---
Simulations: 1000
Success Rate: 66.70%
Failure Causes: {'Power Failure': 178, 'Suffocation': 152, 'Dehydration': 3}
```

### Conclusion 1: Redundancy Eliminates "Sudden Death"
Hypothesis Supported. In the Control group, a single point failure often led to death before repairs could be finished (Suffocation). In the Redundancy Test, Suffocation deaths dropped to nearly zero. The redundancy architecture successfully converted fatal single point failures into manageable stress events, allowing the colony to limp along until repairs were made.

### Conclusion 2: Buffers Beat Generation
Hypothesis Supported. The Control group frequently died during dust storms lasting >6 days. The Battery Test group, despite having lower daily power generation, survived storms lasting up to 12 days. The data suggests that endurance (batteries) is more valuable than peak capacity (solar panels) due to the stochastic nature of storms.

### Visualizations

**Colony Survival Rate Over Time**

![Colony Survival Rate Over Time](results/plot_survival_curves.png)

**Failure Mode Analysis (Cause of Death)**

![Failure Mode Analysis (Cause of Death)](results/plot_failure_modes.png)

**Oxygen Buffer Stability**

![Oxygen Buffer Stability](results/plot_o2_redundancy.png)

**Battery Buffer Stability During Storms**

![Battery Buffer Stability During Storms](results/plot_battery_traces.png)

