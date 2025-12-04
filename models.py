import random
import math

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
        return (self.base_food * self.health * bio_factor, self.base_o2 * self.health * bio_factor)

class MarsEnvironment:
    def __init__(self):
        self.is_storming = False
        self.storm_counter = 0

    def get_sunlight_efficiency(self, Ls_degrees):
        """
        Returns sunlight efficiency (0.0 to 1.0) based on Martian season (Ls) and dust storms.

        Args:
            Ls_degrees (float): Solar Longitude in degrees (0-360)

        Returns:
            float: Sunlight efficiency factor
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
