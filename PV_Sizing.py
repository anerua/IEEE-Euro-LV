import dss
import pandas as pd

from Battery_Sizing import BatterySizing


class PVSizing:

    def __init__(self, periods):
        BASE = '/mnt/6840331B4032F004/Users/MARTINS/Documents/Texts/Acad/OAU/Part 5/Rain Semester/EEE502 - Final Year Project II/Work/IEEE Euro LV/Master_Control.dss'
        ENG = dss.DSS
        TEXT = ENG.Text
        TEXT.Command = 'Clear'
        self.CIRCUIT = ENG.ActiveCircuit        # Sets CIRCUIT to be the ActiveCircuit in DSS
        TEXT.Command = "compile '" + BASE + "'"
        ENG.AllowForms = False

        self.periods = periods

        self.PT_curve = {
            '0': 1.2,
            '25': 1.0,
            '30': 0.98,
            '35': 0.96,
            '40': 0.94,
            '45': 0.92,
            '50': 0.90,
            '55': 0.88,
            '60': 0.86
        }

        self.irrad_curve = [0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.5, 0.8, 0.9, 1.0, 1.0, 0.99, 0.9, 0.7, 0.4, 0.1, 0, 0, 0, 0, 0]
        self.temp_curve = [25, 25, 25, 25, 25, 25, 25, 25, 35, 40, 45, 50, 60, 60, 55, 40, 35, 30, 25, 25, 25, 25, 25, 25]

    
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

    
    def size_PV(self):
        total_loadshape = self.__get_total_loadshape__()

        bs = BatterySizing(self.periods)
        bs.size_battery()
        battery_sizes = bs.get_battery_sizes()

        self.PV_sizes = {}
        for period in self.periods:

            POWER_OUT_HOUR, POWER_ON_HOUR = period

            max_demand = 0
            max_demand_hour = 0

            backup_hours = []
            if POWER_OUT_HOUR < POWER_ON_HOUR:
                backup_hours = list(range(POWER_OUT_HOUR, POWER_ON_HOUR, 1))
            else:
                backup_hours = list(range(0, POWER_ON_HOUR, 1)) + list(range(POWER_OUT_HOUR, 24, 1))
            
            for step in range(1440):
                hour = (step//60) % 24
                if (hour in backup_hours) and (self.irrad_curve[hour] > 0.1):
                    if total_loadshape[step] > max_demand:
                        max_demand = total_loadshape[step]
                        max_demand_hour = hour
            
            pmpp = 0
            charging_kw = battery_sizes[f"{POWER_OUT_HOUR}-{POWER_ON_HOUR}"]['kW']
            if max_demand == 0:
                pmpp = charging_kw * 1.25
            else:
                pmpp = (max_demand * 1.25) / (self.irrad_curve[max_demand_hour] * self.PT_curve[f"{self.temp_curve[max_demand_hour]}"])
                if pmpp < charging_kw * 1.25:
                    pmpp = charging_kw * 1.25
            self.PV_sizes[f"{POWER_OUT_HOUR}-{POWER_ON_HOUR}"] = pmpp
        

    def get_PV_sizes(self):
        return self.PV_sizes

    def save_PV_sizes(self):
        data = pd.DataFrame(columns=['Start hour', 'End hour', 'Required PV Pmpp (kW)'])
        PV_sizes = self.get_PV_sizes()
        for period in PV_sizes:
            start, end = period.split("-")
            data = data.append({
                'Start hour': start,
                'End hour': end,
                'Required PV Pmpp (kW)': PV_sizes[period]
            }, ignore_index=True)
        try:
            data.to_csv(f"Simulation results/PV_sizing.csv")
        except Exception as e:
            print(f"Could not save file: {str(e)}")




if __name__ == '__main__':

    periods = [(0,6), (6,12), (12,18), (18,0), (0,12), (12,0), (6,18), (18,6)]

    pvs = PVSizing(periods)
    pvs.size_PV()
    pvs.save_PV_sizes()

    PV_sizes = pvs.get_PV_sizes()
    
    for period in PV_sizes:
        start, end = period.split("-")
        print("+----------------------------------------")
        print(f"| {start} - {end}")
        print(f"| PV Pmpp: {PV_sizes[period]} kW")
        print("+----------------------------------------\n")

