import pandas as pd


LIFESPAN = 5
CAPITAL_COST = 100000       # For a 2 kVA generator
MAINTENANCE_COST = 30000    # per year
CONSUMPTION_RATE = 1        # 1 litre per hour
PRICE_PER_LITRE = 165       # Price of petrol per litre


def alternative_costing(period_length):
    
    fuel_cost_per_year = PRICE_PER_LITRE * period_length * 365

    operating_cost_per_year = MAINTENANCE_COST + fuel_cost_per_year

    daily_system_cost = ((CAPITAL_COST / LIFESPAN) + operating_cost_per_year) / 365    # C_alt

    return operating_cost_per_year, daily_system_cost



if __name__ == '__main__':

    periods = [(0,6,6), (6,12,6), (12,18,6), (18,0,6), (0,12,12), (12,0,12), (6,18,12), (18,6,12)]

    data = pd.DataFrame(columns=['Start hour', 'End hour', 'Capital cost', 'Operating cost per year', 'C_alt'])

    for period in periods:
        start, end, period_length = period
        operating_cost, system_cost = alternative_costing(period_length)

        data = data.append({
            'Start hour': start,
            'End hour': end,
            'Capital cost': CAPITAL_COST,
            'Operating cost per year': operating_cost,
            'C_alt': system_cost
        }, ignore_index=True)

        try:
            data.to_csv(f"Simulation results/alternative_source_costing.csv")
        except Exception as e:
            print(f"Could not save file: {str(e)}")

