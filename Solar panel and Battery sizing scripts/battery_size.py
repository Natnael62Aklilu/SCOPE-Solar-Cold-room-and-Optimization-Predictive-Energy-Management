from Solar_panel_size import solar_panel
import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "Raw Data Processing scripts"))
from Raw_Data_Processor import w

average_hourly_kwh = w["energy_kwh"].mean()

solar_panel_sizes=solar_panel
losses=0.75

for s in np.arange(1,7,0.5):
    solar_panel_sizes[f"solar_panel_generated with {s} kw"]=solar_panel["irradiance"] / 1000 * s * losses


battery_sizes = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]

min_soc = 0.20
max_soc = 1.00
charge_efficiency = 0.95
discharge_efficiency = 0.95

solar = solar_panel_sizes["solar_panel_generated with 3.0 kw"].to_numpy()
load = solar_panel["hourly_energy_demand"].to_numpy()

results = []

for capacity in battery_sizes:

    soc = capacity * min_soc

    grid_total = 0

    for i in range(len(solar)):

        surplus = max(0, solar[i] - load[i])
        deficit = max(0, load[i] - solar[i])

        available_space = capacity * max_soc - soc

        energy_stored = min(
            surplus * charge_efficiency,
            available_space
        )

        soc += energy_stored

        available_energy = max(0, soc - capacity * min_soc)

        battery_output = min(
            deficit,
            available_energy * discharge_efficiency
        )

        soc -= battery_output / discharge_efficiency

        grid = deficit - battery_output

        grid_total += grid

    average_daily_grid = grid_total / len(solar) * 24

    results.append({
        "battery_kwh": capacity,
        "grid_kwh_per_day": average_daily_grid
    })

battery_results = pd.DataFrame(results)

baseline = battery_results.loc[
    battery_results["battery_kwh"] == 0,
    "grid_kwh_per_day"
].iloc[0]

battery_results["saved_kwh_per_day"] = (
    baseline - battery_results["grid_kwh_per_day"]
)

print(battery_results.round(3))
# Battery investment and payback calculations

battery_cost_per_kwh = 200 * 4104  # 170 dollars for 1kwh
tariff = 800  # UGX per kWh

battery_results["total_investment_ugx"] = (
    battery_results["battery_kwh"] * battery_cost_per_kwh
)

battery_results["annual_savings_ugx"] = (
    battery_results["saved_kwh_per_day"] * 365 * tariff
)

battery_results["total_payback_years"] = (
    battery_results["total_investment_ugx"] /
    battery_results["annual_savings_ugx"].replace(0, np.nan)
)

# Incremental investment payback
battery_results["incremental_investment_ugx"] = (
    battery_results["battery_kwh"].diff() * battery_cost_per_kwh
)

battery_results["incremental_annual_savings_ugx"] = (
    battery_results["annual_savings_ugx"].diff()
)

battery_results["incremental_payback_years"] = (
    battery_results["incremental_investment_ugx"] /
    battery_results["incremental_annual_savings_ugx"].replace(0, np.nan)
)
battery_results.to_csv(
    Path(__file__).resolve().parent.parent / "solar and battery design results" / "Battery sizing and payback period and money saved.csv",
    index=False
)
print(battery_results.round(3).to_string(index=False))
print("\n\n\n Battery sizing computed and 8kwh battery results in a payback period of less than 5 so it is chosen from the simulation")
