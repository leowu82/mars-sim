# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================

# --- Deterministic Constants ---
MISSION_DURATION = 500 # Days
CREW_SIZE = 6

class MCSimConfig:
    def __init__(self, mode="CONTROL"):
        """
        Parameters for the hypotheses.
        Modes: 'CONTROL', 'OXYGENATOR_REDUNDANCY_TEST', 'BATTERY_TEST'
        """
        self.mode = mode
        
        # --- Consumption per day ---
        self.daily_o2_consumption = 0.82  # kg/person (simplified average)
        self.daily_water_consumption = 2.5 # Liters/person (simplified average)
        self.daily_food_consumption = 3035 # kCal/person (simplified average)
        self.daily_base_power_consumption = 85.0 # kWh (base system excluding machines)

        # --- Initial Resources ---
        self.starting_o2 = 8.0 # kg
        self.max_o2_tank = 50.0 # kg
        self.starting_water = 1000.0 # Liters
        self.max_water_tank = 2000.0 # Liters
        self.starting_battery = 500.0 # kWh
        self.starting_food = 50000.0 # kCal

        # --- Crop Settings ---
        # Note: power cost for LEDs, pumps, etc. is included in daily_base_power_consumption
        self.crop_daily_water_need = 10.0 # Liters/day
        self.crop_food_production = 30000.0 # kCal/day
        self.crop_o2_production = 1.0 # kg/day

        # --- Default Machine Settings ---
        
        # Oxygenators
        self.num_oxygenators = 1
        self.oxygenator_mtbf = 120 # days (arbitrary)
        self.oxygenator_power_cost = 12.0 # kWh per machine per day
        self.o2_production_rate = 7.5 # kg/day per machine

        # Water Reclaimers
        self.num_water_reclaimers = 1
        self.water_reclaimer_mtbf = 120 # days (arbitrary)
        self.water_reclaimer_power_cost = 3.0 # kWh per machine per day
        self.water_reclamation_rate = 30.0 # Liters/day per machine
        self.water_recycle_efficiency = 0.97 # 97% efficient (estimate)

        # --- Power System ---
        self.solar_capacity = 60.0 # kW
        self.max_battery = 500.0 # kWh

        # --- Hypothesis 1 Variables (Oxygenator Redundancy) ---
        # Control: 1 Big Machine. Experiment: 3 Small Machines.
        if mode == "OXYGENATOR_REDUNDANCY_TEST":
            self.num_oxygenators = 3
            self.oxygenator_power_cost = 4.0 # kWh per machine per day
            self.o2_production_rate = 2.5 # Lower rate per machine (Ensure 2 machines > Demand)

        # --- Hypothesis 2 Variables (Battery vs Solar) ---
        # Control: Balanced. Experiment: Huge Battery, Less Solar.
        if mode == "BATTERY_TEST":
            # Assume 1 kW Solar -> 50 kWh Battery
            exchange_ratio = 50.0
            reduce_amount = 20.0 # kW reduction
            self.solar_capacity -= reduce_amount # Reduce solar
            self.max_battery += (reduce_amount * exchange_ratio) # Increase battery
