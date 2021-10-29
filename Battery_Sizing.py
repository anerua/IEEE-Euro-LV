import dss
import pandas as pd


def get_total_loadshape():
    
    BASE = '/mnt/6840331B4032F004/Users/MARTINS/Documents/Texts/Acad/OAU/Part 5/Rain Semester/EEE502 - Final Year Project II/Work/IEEE Euro LV/Master_Control.dss'
    ENG = dss.DSS
    TEXT = ENG.Text
    TEXT.Command = 'Clear'
    CIRCUIT = ENG.ActiveCircuit        # Sets CIRCUIT to be the ActiveCircuit in DSS
    TEXT.Command = "compile '" + BASE + "'"
    ENG.AllowForms = False

    loadshapes = CIRCUIT.LoadShapes
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


if __name__ == '__main__':

    total_loadshape = get_total_loadshape()
    total_energyuse_shape = list((kw / 60) for kw in total_loadshape)

    data = pd.DataFrame(columns=['Start hour', 'End hour', 'Total energy demand (kWh)', 'Required battery size (kWh)'])

    periods = [(0,6), (6,12), (12,18), (18,0), (0,12), (12,0), (6,18), (18,6), (0,18), (18,12), (12,6), (6,0)]
    for period in periods:
        print("--------------------------------------")
        print(f"Running {period[0]} - {period[1]} ...", flush=True)
        print("--------------------------------------")

        POWER_OUT_HOUR, POWER_ON_HOUR = period

        backup_hours = []
        if POWER_OUT_HOUR < POWER_ON_HOUR:
            backup_hours = list(range(POWER_OUT_HOUR, POWER_ON_HOUR, 1))
        else:
            backup_hours = list(range(0, POWER_ON_HOUR, 1)) + list(range(POWER_OUT_HOUR, 24, 1))

        valid_energy = []
        for step in range(1440):
            hour = (step//60) % 24
            if hour in backup_hours:
                valid_energy.append(total_energyuse_shape[step])
        
        total_energy = sum(valid_energy)
        battery_size = 4 * total_energy

        data = data.append({
            'Start hour': POWER_OUT_HOUR,
            'End hour': POWER_ON_HOUR,
            'Total energy demand (kWh)': total_energy,
            'Required battery size (kWh)': battery_size
        }, ignore_index=True)

        print(f"Total energy: {total_energy} kWh")
        print(f"Battery energy: {battery_size} kWh")

        print("--------------------------------------\n", flush=True)
    
    try:
        data.to_csv(f"Simulation results/battery_sizing.csv")
    except Exception as e:
        print(f"Could not save file: {str(e)}")
        
    print("Done!")
