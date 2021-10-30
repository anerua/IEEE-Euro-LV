import dss
import pandas as pd


class BatterySizing:

    def __init__(self, periods):

        BASE = '/mnt/6840331B4032F004/Users/MARTINS/Documents/Texts/Acad/OAU/Part 5/Rain Semester/EEE502 - Final Year Project II/Work/IEEE Euro LV/Master_Control.dss'
        ENG = dss.DSS
        TEXT = ENG.Text
        TEXT.Command = 'Clear'
        self.CIRCUIT = ENG.ActiveCircuit        # Sets CIRCUIT to be the ActiveCircuit in DSS
        TEXT.Command = "compile '" + BASE + "'"
        ENG.AllowForms = False

        self.periods = periods
        


    def __get_total_loadshape__(self):
        loadshapes = self.CIRCUIT.LoadShapes
        loadshapes_dict = {}
        for i in range(1,56):
            shape_name = f"Shape_{i}"
            loadshapes.Name = shape_name
            loadshapes_dict[shape_name] = loadshapes.Pmult

        total_loadshape = []
        for i in range(1440):
            total = sum((loadshapes_dict[shape][i]) for shape in loadshapes_dict)
            total_loadshape.append(total)

        return total_loadshape.copy()
    

    def size_battery(self):
        total_loadshape = self.__get_total_loadshape__()
        total_energyuse_shape = list((kw / 60) for kw in total_loadshape)

        self.battery_sizes = {}
        for period in self.periods:

            POWER_OUT_HOUR, POWER_ON_HOUR = period

            backup_hours = []
            if POWER_OUT_HOUR < POWER_ON_HOUR:
                backup_hours = list(range(POWER_OUT_HOUR, POWER_ON_HOUR, 1))
            else:
                backup_hours = list(range(0, POWER_ON_HOUR, 1)) + list(range(POWER_OUT_HOUR, 24, 1))

            valid_energy = []
            battery_rated_kw = 0
            for step in range(1440):
                hour = (step//60) % 24
                if hour in backup_hours:
                    if total_loadshape[step] > battery_rated_kw:
                        battery_rated_kw = total_loadshape[step]
                    valid_energy.append(total_energyuse_shape[step])
            
            total_energy = sum(valid_energy)
            battery_rated_kwh = 4 * total_energy

            battery_params = {
                'kW': battery_rated_kw * 1.25,
                'kWh': battery_rated_kwh
            }
            
            self.battery_sizes[f"{POWER_OUT_HOUR}-{POWER_ON_HOUR}"] = battery_params
    
    def save_battery_sizes(self):
        data = pd.DataFrame(columns=['Start hour', 'End hour', 'Required battery power (kW)', 'Required battery energy (kWh)'])
        battery_sizes = self.get_battery_sizes()
        for period in battery_sizes:
            start, end = period.split("-")
            data = data.append({
                'Start hour': start,
                'End hour': end,
                'Required battery power (kW)': battery_sizes[period]['kW'],
                'Required battery energy (kWh)': battery_sizes[period]['kWh']
            }, ignore_index=True)
        try:
            data.to_csv(f"Simulation results/battery_sizing.csv")
        except Exception as e:
            print(f"Could not save file: {str(e)}")


    def get_battery_sizes(self):
        return self.battery_sizes




if __name__ == '__main__':

    periods = [(0,6), (6,12), (12,18), (18,0), (0,12), (12,0), (6,18), (18,6)]

    bs = BatterySizing(periods)

    bs.size_battery()
    bs.save_battery_sizes()

    battery_sizes = bs.get_battery_sizes()
    
    for period in battery_sizes:
        start, end = period.split("-")
        print("+----------------------------------------")
        print(f"| {start} - {end}")
        print(f"| Battery rated power: {battery_sizes[period]['kW']} kW")
        print(f"| Battery rated energy: {battery_sizes[period]['kWh']} kWh")
        print("+----------------------------------------\n")
