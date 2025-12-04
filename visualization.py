import matplotlib.pyplot as plt
import pandas as pd

def plot_survival_curves(df_results):
    """
    Shows the % of colonies still alive at each day (0-500).
    Shows 'When' they die, not just 'If' they die.
    """
    plt.figure(figsize=(10, 6))
    
    experiments = df_results['Experiment'].unique()
    
    for exp in experiments:
        subset = df_results[df_results['Experiment'] == exp]
        
        # Sort by day ended to calculate drop-off
        dead_days = subset[subset['Survived'] == False]['Day_Ended'].sort_values()
        
        # Create X (Days) and Y (Survival %) coordinates
        x_vals = range(501)
        y_vals = []
        
        total_runs = len(subset)
        current_alive = total_runs
        
        for day in x_vals:
            # Subtract deaths that happened on this specific day
            deaths_today = (dead_days == day).sum()
            current_alive -= deaths_today
            y_vals.append((current_alive / total_runs) * 100)
            
        plt.plot(x_vals, y_vals, label=exp, linewidth=2.5)

    plt.title("Colony Survival Rate Over Time", fontsize=14)
    plt.xlabel("Mission Day")
    plt.ylabel("Survival Probability (%)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("plot_survival_curves.png")
    print("Saved: plot_survival_curves.png")


def plot_failure_analysis(df_results):
    """
    Stacked Bar Chart of Failure Causes
    Shows breakdown of 'How' colonies died per experiment.
    """
    # Pivot data to get counts of each Cause per Experiment
    breakdown = df_results.groupby(['Experiment', 'Cause'], observed=True).size().unstack(fill_value=0)
    
    # Convert to percentages for fair comparison
    breakdown_pct = breakdown.div(breakdown.sum(axis=1), axis=0) * 100
    
    # Plot
    breakdown_pct.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='viridis')
    
    plt.title("Failure Mode Analysis (Cause of Death)", fontsize=14)
    plt.ylabel("Percentage of Runs (%)")
    plt.xlabel("Experiment Configuration")
    plt.legend(title="Cause", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("plot_failure_modes.png")
    print("Saved: plot_failure_modes.png")


def plot_battery_stability(control_traces, battery_traces):
    """
    Resource Trace (The 'Spaghetti' Plot)
    Overlays 10 random runs of Control vs Battery Test.
    Visualizes how the 'Buffer' strategy smooths out the storms.
    """
    plt.figure(figsize=(12, 6))
    
    # Plot 10 random traces from Control (Red)
    # This shows the volatility of the small battery
    for i in range(min(10, len(control_traces))):
        plt.plot(control_traces[i]['battery'], color='red', alpha=0.15)
        
    # Plot 10 random traces from Battery Test (Blue)
    # This shows the stability of the large battery
    for i in range(min(10, len(battery_traces))):
        plt.plot(battery_traces[i]['battery'], color='blue', alpha=0.15)
        
    # Dummy lines for legend
    plt.plot([], [], color='red', label='Control (Low Capacity)')
    plt.plot([], [], color='blue', label='Battery Test (High Capacity)')

    plt.title("Battery Buffer Stability During Storms (Sample Traces)", fontsize=14)
    plt.xlabel("Mission Day")
    plt.ylabel("Battery Charge (kWh)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("plot_battery_traces.png")
    print("Saved: plot_battery_traces.png")