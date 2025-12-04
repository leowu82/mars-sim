from config import MCSimConfig
from simulation import MarsColony
import pandas as pd
import visualization

# ==========================================
# MONTE CARLO SIMULATION
# ==========================================

def run_experiment(experiment_mode, n_simulations=1000):
    print(f"\n--- Starting Experiment: {experiment_mode} ---")

    summary_results = []
    all_histories = []
    success_count = 0
    death_causes = {}
    
    cfg = MCSimConfig(experiment_mode)
    
    for i in range(n_simulations):
        colony = MarsColony(cfg)
        alive, cause, history = colony.run_mission()

        if alive: success_count += 1
        else: death_causes[cause] = death_causes.get(cause, 0) + 1
        
        # Save summary of this specific run
        summary_results.append({
            "Experiment": experiment_mode,
            "Run_ID": i,
            "Survived": alive,
            "Cause": cause,
            "Day_Ended": len(history)
        })
        
        # Save the daily trace (Resources over time)
        # We convert to DataFrame immediately for easier plotting later
        df_history = pd.DataFrame(history)
        df_history['Run_ID'] = i
        all_histories.append(df_history)

    # Summarize Results
    success_rate = (success_count / n_simulations) * 100
    print(f"Simulations: {n_simulations}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Failure Causes: {death_causes}")

    return pd.DataFrame(summary_results), all_histories


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    print("==============================")
    print("=== Mars Colony Simulation ===")
    print("==============================")

    # --- 1. Run Simulations ---
    print("Gathering Data...")
    
    # Number of simulations per experiment
    n_simulations = 1000
    
    # Run Control
    control_summary, control_histories = run_experiment("CONTROL", n_simulations=n_simulations)
    
    # Run Hypothesis 1 (Oxygenator Redundancy)
    oxy_summary, oxy_histories = run_experiment("OXYGENATOR_REDUNDANCY_TEST", n_simulations=n_simulations)
    
    # Run Hypothesis 2 (Battery Buffer)
    battery_summary, battery_histories = run_experiment("BATTERY_TEST", n_simulations=n_simulations)

    # --- 2. Combine Results ---
    df_all = pd.concat([control_summary, oxy_summary, battery_summary], ignore_index=True)
    # Order by "Control", "Oxygenator Redundancy", "Battery Test"
    df_all['Experiment'] = pd.Categorical(df_all['Experiment'], categories=["CONTROL", "OXYGENATOR_REDUNDANCY_TEST", "BATTERY_TEST"], ordered=True)

    # --- 3. Visualizations ---
    print("\n\nGenerating Visualizations...")
    visualization.plot_survival_curves(df_all)
    visualization.plot_failure_analysis(df_all)
    visualization.plot_redundancy_validation(control_histories, oxy_histories)
    visualization.plot_battery_stability(control_histories, battery_histories)