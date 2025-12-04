import random
import math


# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================

# --- Deterministic Constants ---
mission_duration = 500 # Days
crew_size = 6

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
        self.solar_capacity = 45.0 # kW
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
            reduce_amount = 10.0 # kW reduction
            self.solar_capacity -= reduce_amount # Reduce solar
            self.max_battery += (reduce_amount * exchange_ratio) # Increase battery


# ==========================================
# RANDOM VARIABLE MODELS
# ==========================================

class Machine:
    """
    Represents a machine (Oxygenator, Water Reclaimer).
    Includes Random Variables:
    - Failure (Exponential Distribution)
    - Repair Time (Log-Normal Distribution)
    """
    def __init__(self, name, production_rate, mtbf_days):
        self.name = name
        self.production_rate = production_rate
        self.mtbf = mtbf_days # Mean Time Between Failures
        self.is_broken = False
        self.days_to_repair = 0

    def daily_check(self):
        # If already broken, decrement repair timer
        if self.is_broken:
            self.days_to_repair -= 1
            if self.days_to_repair <= 0:
                self.is_broken = False
                self.days_to_repair = 0
            return 0.0 # No production if broken

        # Check for random failure
        # Math: Probability of failing today = 1 - e^(-1/MTBF)
        fail_prob = 1 - math.exp(-1 / self.mtbf)
        if random.random() < fail_prob:
            self.is_broken = True
            # Repair Time (Log-Normal)
            repair_time = random.lognormvariate(1.0, 0.8) # Mean ~2.7 days, Sigma=0.8
            self.days_to_repair = math.ceil(repair_time)
            return 0.0
        
        return self.production_rate
    
class CropModule:
    """
    Simulates Crop Growth.
    - Requires: Water + Sunlight.
    - Produces: Food + Oxygen.
    Includes Random Variables:
    - Biological Variability (Normal Distribution)
    """
    def __init__(self, base_food, base_o2):
        self.base_food = base_food
        self.base_o2 = base_o2
        self.health = 1.0 # Health factor

    def grow(self, has_water):
        if not has_water:
            # Health degrades without water
            self.health -= 0.2 # Dies in 5 days without water
        else:
            self.health += 0.1 # Slowly recovers

        # Clamp health between 0 and 1
        self.health = max(0.0, min(1.0, self.health))

        # If dead, no production
        if self.health <= 0.0:
            self.health = 0.0
            return 0.0, 0.0
        
        # Biological Variability (Normal Distribution)
        # Plants vary by +/- 10% naturally (Mean=1.0, Sigma=0.1)
        bio_factor = max(0.8, min(1.2, random.gauss(1.0, 0.1))) # Clamp between 0.8 and 1.2
        
        # Production
        actual_food = self.base_food * bio_factor * self.health
        actual_o2 = self.base_o2 * bio_factor * self.health
        
        # Prevent negative production
        return max(0, actual_food), max(0, actual_o2)

class MarsEnvironment:
    def __init__(self):
        self.is_storming = False
        self.storm_counter = 0

    def get_sunlight_efficiency(self, Ls_degrees):
        """
        Returns sunlight efficiency (0.0 to 1.0) based on Martian season (Ls) and dust storms.
        :param Ls_degrees: Solar Longitude in degrees (0-360)
        """
        # --- 1. SEASONAL VARIATION ---
        # Formula approximates the seasonal dust opacity variation
        # Ls 0-180 (Clear Season) -> Tau ~0.3
        # Ls 180-360 (Dusty Season) -> Tau ~1.0
        ls_rad = math.radians(Ls_degrees) # Convert to radians
        tau_base = 0.65 - 0.35 * math.sin(ls_rad)

        # --- 2. DUST STORM MODEL ---
        # Montabone statistics: Global storms ONLY occur between Ls 180 and 300.
        # ~33% chance per year.
        if self.is_storming:
            # Storm decay phase
            self.storm_counter -= 1
            storm_opacity = 4.0 # Massive blockage
            if self.storm_counter <= 0:
                self.is_storming = False
        else:
            storm_opacity = 0.0
            # Trigger risk zone
            if 200 < Ls_degrees < 300:
                # 0.5% daily chance triggers a ~33% seasonal chance
                if random.random() < 0.005: 
                    self.is_storming = True
                    self.storm_counter = random.randint(5, 15) # Storm lasts 5-15 days (arbitrary)

        # --- 3. TOTAL OPACITY ---
        total_tau = tau_base + storm_opacity
        
        # Convert Optical Depth (Tau) to Sunlight Efficiency
        # Beer-Lambert Law: Intensity = I_0 * e^(-tau)
        efficiency = math.exp(-total_tau)
        
        return max(0.02, efficiency) # Never goes below 2% (ambient light)


# ==========================================
# CORE SIMULATION LOGIC
# ==========================================

class MarsColony:
    def __init__(self, config):
        self.cfg = config
        self.day = 0
        self.alive = True
        self.cause_of_death = ""
        
        # Resources
        self.o2 = self.cfg.starting_o2
        self.water = self.cfg.starting_water
        self.waste_water = 0.0
        self.battery = self.cfg.starting_battery
        self.food = self.cfg.starting_food
        
        # Systems
        self.env = MarsEnvironment()
        self.crops = CropModule(self.cfg.crop_food_production, self.cfg.crop_o2_production)
        
        # Oxygenators
        self.oxygenators = []
        for i in range(self.cfg.num_oxygenators):
            self.oxygenators.append(Machine(f"Oxy-{i}", self.cfg.o2_production_rate, self.cfg.oxygenator_mtbf))

        # Water Reclaimers
        self.water_reclaimers = []
        for i in range(self.cfg.num_water_reclaimers):
            self.water_reclaimers.append(Machine(f"WaterRec-{i}", self.cfg.water_reclamation_rate, self.cfg.water_reclaimer_mtbf))

    def step(self):
        """Simulates one day"""
        self.day += 1
        
        # --- 1. Environment & Power Generation ---
        sun_eff = self.env.get_sunlight_efficiency((self.day % 360))
        power_gen = self.cfg.solar_capacity * sun_eff * 8 # kWh per day (8 hours of effective sunlight)
        
        # --- 2. Base Consumption ---
        total_power_need = self.cfg.daily_base_power_consumption
        available_power = self.battery + power_gen - total_power_need
        total_o2_need = self.cfg.daily_o2_consumption * crew_size
        total_water_need = self.cfg.daily_water_consumption * crew_size
        total_food_need = self.cfg.daily_food_consumption * crew_size

        # --- 3. Crop Production ---
        crop_water_available = False
        if self.water >= total_water_need + self.cfg.crop_daily_water_need:
            total_water_need += self.cfg.crop_daily_water_need
            crop_water_available = True
        
        food_produced, crop_o2_produced = self.crops.grow(crop_water_available)

        # --- 4. Waste Water ---
        # Waste water from crew consumption and crop transpiration
        self.waste_water += total_water_need * self.cfg.water_recycle_efficiency
        
        # --- 5. Machine Operation ---
        o2_produced = 0
        for oxy in self.oxygenators:
            machine_power = self.cfg.oxygenator_power_cost # kWh cost to run machine
            needs_o2 = self.o2 < self.cfg.max_o2_tank
            if available_power >= machine_power and needs_o2:
                o2_produced += oxy.daily_check()
                available_power -= machine_power
                total_power_need += machine_power
            else:
                # Not enough power to run machine
                pass 

        water_reclaimed = 0
        for water_rec in self.water_reclaimers:
            machine_power = self.cfg.water_reclaimer_power_cost # kWh cost to run machine
            needs_water = self.water < self.cfg.max_water_tank
            if available_power >= machine_power and needs_water:
                # Logic: Can only process what is in the waste tank
                actual_processed = min(water_rec.daily_check(), self.waste_water)
                water_reclaimed += actual_processed
                self.waste_water -= actual_processed # Remove from waste tank
                available_power -= machine_power
                total_power_need += machine_power
            else:
                # Not enough power to run machine
                pass

        # --- 6. Update Resources ---
        
        # Power Balance
        self.battery += (power_gen - total_power_need)
        if self.battery > self.cfg.max_battery:
            self.battery = self.cfg.max_battery
        
        # Oxygen Balance
        self.o2 += (o2_produced + crop_o2_produced - total_o2_need)
        if self.o2 > self.cfg.max_o2_tank:
            self.o2 = self.cfg.max_o2_tank

        # Water Balance
        self.water += (water_reclaimed - total_water_need)
        if self.water > self.cfg.max_water_tank:
            self.water = self.cfg.max_water_tank

        # Food Balance
        self.food += (food_produced - total_food_need)
        
        # --- 7. Check Survival Conditions ---
        if self.battery < 0:
            self.alive = False
            self.cause_of_death = "Power Failure"
        
        elif self.o2 < 0:
            self.alive = False
            self.cause_of_death = "Suffocation"

        elif self.water < 0:
            self.alive = False
            self.cause_of_death = "Dehydration"

        elif self.food < 0:
            self.alive = False
            self.cause_of_death = "Starvation"

    def run_mission(self):
        """Runs the full mission_duration days or until death"""
        history = []
        for _ in range(mission_duration):
            if not self.alive:
                break
            self.step()
            history.append({
                'day': self.day,
                'o2': self.o2,
                'water': self.water,
                'waste_water': self.waste_water,
                'food': self.food,
                'crop_health': self.crops.health,
                'battery': self.battery,
                'storm': self.env.is_storming
            })
        return self.alive, self.cause_of_death, history


# ==========================================
# MONTE CARLO SIMULATION
# ==========================================

def run_mcs(experiment_mode, n_simulations=1000):
    print(f"\n--- Starting Experiment: {experiment_mode} ---")
    success_count = 0
    death_reasons = {}
    
    cfg = MCSimConfig(experiment_mode)
    
    for _ in range(n_simulations):
        colony = MarsColony(cfg)
        survived, cause, _ = colony.run_mission()
        
        if survived:
            success_count += 1
        else:
            death_reasons[cause] = death_reasons.get(cause, 0) + 1
            
    success_rate = (success_count / n_simulations) * 100
    print(f"Simulations: {n_simulations}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Failure Causes: {death_reasons}")
    return success_rate


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    # Number of simulations per experiment
    n_simulations = 1000
    
    # Run Control
    run_mcs("CONTROL", n_simulations=n_simulations)
    
    # Run Hypothesis 1 (Oxygenator Redundancy)
    run_mcs("OXYGENATOR_REDUNDANCY_TEST", n_simulations=n_simulations)
    
    # Run Hypothesis 2 (Battery Buffer)
    run_mcs("BATTERY_TEST", n_simulations=n_simulations)