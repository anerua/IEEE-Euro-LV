import pandas as pd


N = 55  # Number of consumers on the backup supply system

def tariff_params(A, B, Bk, C_sys, C_alt):

    if B:
        k = Bk / B
    else:
        k = 0
    lower_limit = (C_sys - Bk) / A
    upper_limit = ((N*C_alt) - Bk) / A

    return k, lower_limit, upper_limit



if __name__ == '__main__':

    data = pd.DataFrame(columns=['Start hour', 'End hour', 'k', 'lower_p', 'upper_p'])

    price_function_data = pd.read_csv(f"Simulation results/price_function.csv")
    backup_costing_data = pd.read_csv(f"Simulation results/system_costing.csv")
    alt_source_data = pd.read_csv(f"Simulation results/alternative_source_costing.csv")

    start_hours = price_function_data['Start hour']
    end_hours = price_function_data['End hour']

    A_s = price_function_data['Price multiplier']
    B_s = price_function_data['Additional charge multiplier']

    Bk_s = backup_costing_data['Bk']
    C_sys_s = backup_costing_data['C_sys']

    C_alt_s = alt_source_data['C_alt']

    for start, end, A, B, Bk, C_sys, C_alt in zip(start_hours, end_hours, A_s, B_s, Bk_s, C_sys_s, C_alt_s):
        
        k, lower_limit, upper_limit = tariff_params(A, B, Bk, C_sys, C_alt)

        data = data.append({
            'Start hour': start,
            'End hour': end,
            'k': k,
            'lower_p': lower_limit,
            'upper_p': upper_limit
        }, ignore_index=True)

    try:
        data.to_csv(f"Simulation results/tariff_params.csv")
    except Exception as e:
        print(f"Could not save file: {str(e)}")
