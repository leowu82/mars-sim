from config import MISSION_DURATION, CREW_SIZE
from models import Machine, CropModule, MarsEnvironment

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
        self.oxygenators = [
            Machine(f"Oxy-{i}", self.cfg.o2_production_rate, self.cfg.oxygenator_mtbf)
            for i in range(self.cfg.num_oxygenators)
        ]

        # Water Reclaimers
        self.water_reclaimers = [
            Machine(f"WaterRec-{i}", self.cfg.water_reclamation_rate, self.cfg.water_reclaimer_mtbf)
            for i in range(self.cfg.num_water_reclaimers)
        ]

    def _run_machines(self, machines, power_cost, available_power, 
                      current_storage, max_storage, 
                      input_resource_limit=None):
        """
        Generic machine runner.

        Args:
            machines (list): List of Machine instances.
            power_cost (float): Power cost per machine per day.
            available_power (float): Available power for the day.
            current_storage (float): Current amount of the output resource.
            max_storage (float): Maximum capacity for the output resource.
            input_resource_limit (float, optional): Limit on input resource consumption.

        Returns:
            tuple: (produced amount, input consumed, power used)
        """
        produced = 0
        input_consumed = 0
        power_used = 0
        output_storage = current_storage
        
        for machine in machines:
            # Check power
            has_power = available_power >= power_cost

            # Check storage (stop if full)
            needs_output = output_storage < max_storage

            if has_power and needs_output:
                raw_prod = machine.daily_check()

                # Limit by input availability (waste water)
                actual_prod = raw_prod
                if input_resource_limit is not None:
                    actual_prod = min(raw_prod, input_resource_limit - input_consumed)

                # Determine if machine "ran" (consumed power)
                # It consumes power if it produced something OR if it's broken but tried to run
                if actual_prod > 0 or (raw_prod == 0 and machine.is_broken):
                    produced += actual_prod
                    input_consumed += actual_prod
                    output_storage += actual_prod
                    
                    power_used += power_cost
                    available_power -= power_cost
        
        return produced, input_consumed, power_used

    def step(self):
        """Simulates one day"""
        self.day += 1
        
        # --- 1. Environment & Power Generation ---
        sun_eff = self.env.get_sunlight_efficiency((self.day % 360))
        power_gen = self.cfg.solar_capacity * sun_eff * 8 # kWh per day (8 hours of effective sunlight)
        
        # --- 2. Base Consumption ---
        total_power_need = self.cfg.daily_base_power_consumption
        available_power = self.battery + power_gen - total_power_need
        total_o2_need = self.cfg.daily_o2_consumption * CREW_SIZE
        total_water_need = self.cfg.daily_water_consumption * CREW_SIZE
        total_food_need = self.cfg.daily_food_consumption * CREW_SIZE

        # --- 3. Crop Production ---
        crop_water_available = self.water >= (total_water_need + self.cfg.crop_daily_water_need)
        if crop_water_available:
            total_water_need += self.cfg.crop_daily_water_need
        
        food_produced, crop_o2_produced = self.crops.grow(crop_water_available)

        # --- 4. Waste Water ---
        # Waste water from crew consumption and crop transpiration
        self.waste_water += total_water_need * self.cfg.water_recycle_efficiency
        
        # --- 5. Machine Operation ---
        
        # Oxygenators
        o2_produced, _, oxy_power = self._run_machines(
            self.oxygenators,
            self.cfg.oxygenator_power_cost,
            available_power,
            current_storage=self.o2,
            max_storage=self.cfg.max_o2_tank,
            input_resource_limit=None
        )
        available_power -= oxy_power
        total_power_need += oxy_power

        # Water Reclaimers
        water_reclaimed, waste_processed, water_power = self._run_machines(
            self.water_reclaimers,
            self.cfg.water_reclaimer_power_cost,
            available_power,
            current_storage=self.water,
            max_storage=self.cfg.max_water_tank,
            input_resource_limit=self.waste_water
        )
        self.waste_water -= waste_processed
        available_power -= water_power
        total_power_need += water_power

        # --- 6. Update Resources ---
        self.battery = min(self.cfg.max_battery, self.battery + power_gen - total_power_need)
        self.o2 = min(self.cfg.max_o2_tank, self.o2 + o2_produced + crop_o2_produced - total_o2_need)
        self.water = min(self.cfg.max_water_tank, self.water + water_reclaimed - total_water_need)
        self.food += food_produced - total_food_need
        
        # --- 7. Check Survival Conditions ---
        if   self.battery < 0: self._die("Power Failure")
        elif self.o2 < 0:      self._die("Suffocation")
        elif self.water < 0:   self._die("Dehydration")
        elif self.food < 0:    self._die("Starvation")

    def _die(self, reason):
        self.alive = False
        self.cause_of_death = reason

    def run_mission(self):
        """Runs the full MISSION_DURATION days or until death"""
        history = []
        for _ in range(MISSION_DURATION):
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
