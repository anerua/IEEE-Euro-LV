import pandas as pd


DOLLAR_RATE = 415
LIFESPAN_PV = 25
LIFESPAN_BATTERY = 10
CAPITAL_RATE_PV = 1000          # $1000 per kW
CAPITAL_RATE_BATTERY = 150      # $150 per kWh
OPERATING_RATE_BATTERY = 0.01   # 1% of capital cost throughout battery lifespan

def system_costing(pv_size, battery_size):

    capital_cost_PV = CAPITAL_RATE_PV * pv_size * DOLLAR_RATE
    capital_cost_battery = CAPITAL_RATE_BATTERY * battery_size * DOLLAR_RATE
    operating_cost_battery = OPERATING_RATE_BATTERY * capital_cost_battery

    capital_cost_total = capital_cost_PV + capital_cost_battery

    capital_cost_PV_per_year = capital_cost_PV / LIFESPAN_PV
    capital_cost_battery_per_year = capital_cost_battery / LIFESPAN_BATTERY
    operating_cost_per_year = operating_cost_battery / LIFESPAN_BATTERY

    operating_cost_per_day = operating_cost_per_year / 365    # Bk

    system_cost_per_day = (capital_cost_PV_per_year + capital_cost_battery_per_year + operating_cost_per_year) / 365

    return capital_cost_total, operating_cost_per_year, operating_cost_per_day, system_cost_per_day

    


if __name__ == '__main__':

    PV_data = pd.read_csv(f"Simulation results/PV_sizing.csv")
    battery_data = pd.read_csv(f"Simulation results/battery_sizing.csv")

    data = pd.DataFrame(columns=['Start hour', 'End hour', 'Capital cost', 'Operating cost per year', 'Bk', 'C_sys'])

    start_hours = PV_data['Start hour']
    end_hours = PV_data['End hour']
    pv_sizes = PV_data['Required PV Pmpp (kW)']
    battery_sizes = battery_data['Required battery energy (kWh)']

    for start, end, pv_size, battery_size in zip(start_hours, end_hours, pv_sizes, battery_sizes):

        capital_cost, operating_cost, Bk, C_sys = system_costing(pv_size, battery_size)
        data = data.append({
            'Start hour': start,
            'End hour': end,
            'Capital cost': f"{capital_cost:.2f}",
            'Operating cost per year': f"{operating_cost:.2f}",
            'Bk': f"{Bk:.2f}",
            'C_sys': f"{C_sys:.2f}"
        }, ignore_index=True)

    try:
        data.to_csv(f"Simulation results/system_costing.csv")
    except Exception as e:
        print(f"Could not save file: {str(e)}")

    



