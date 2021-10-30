import pandas as pd


def price_function(periods):

    data = pd.DataFrame(columns=['Start hour', 'End hour', 'Price multiplier', 'Additional charge multiplier'])
    for period in periods:
        start, end, length = period
        file_name = f"{start}-{end}.csv"
        sim_data = pd.read_csv(f"Simulation results/1_day_simulations/{length}hr_periods/{file_name}")

        total_price_mult = sum(sim_data['Price_multiplier'])
        total_add_mult = sum(sim_data['Additional_charge_multiplier'])

        data = data.append({
            'Start hour': start,
            'End hour': end,
            'Price multiplier': total_price_mult,
            'Additional charge multiplier': total_add_mult
        }, ignore_index=True)

        print("------------------------------")
        print(f"{start} - {end}:")
        print(f"Total price multiplier: {total_price_mult}")
        print(f"Total additional charge: {total_add_mult}")
        print("------------------------------", flush=True)

    try:
        data.to_csv(f"Simulation results/price_function.csv")
    except Exception as e:
        print(f"Could not save file: {str(e)}")
    print("Done!")



if __name__ == '__main__':

    periods = [(0,6,6), (6,12,6), (12,18,6), (18,0,6), (0,12,12), (12,0,12), (6,18,12), (18,6,12)]

    price_function(periods)