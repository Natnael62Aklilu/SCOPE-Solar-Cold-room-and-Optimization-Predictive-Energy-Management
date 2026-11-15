import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "Raw Data Processing scripts"))

from  Raw_Data_Processor import w

# where the weather file is saved
folder = Path(__file__).resolve().parent.parent / "Processed Data CSV"
solar_panel = pd.read_csv(folder / "Total Cold-room Hourly processed data.csv", parse_dates=["time"])

# the solar panel numbers
#panel_size_kW = int(input("Give the panel size for simulation : "))
solar_panel["hourly_energy_demand"] = w["energy_kwh"]

if __name__ == "__main__":

    losses = 0.75

    solar_panel["solar_kwh"] = solar_panel["irradiance"] / 1000 * 1 * losses
    solar_panel["hourly_energy_demand"] = w["energy_kwh"]

    plt.plot(solar_panel["solar_kwh"][-100:-1], label='solar_generated', color='blue', marker='o', linewidth=2)
    plt.plot(solar_panel["hourly_energy_demand"][-100:-1], label='hourly demand', color='orange', marker='s', linewidth=2)

    plt.xlabel('Hour', fontsize=12)
    plt.ylabel('energy In KWH', fontsize=12)
    plt.title('Plot of demand and energy produced by 1kw panel vs. Hour for last 100 hours from our 10 years', fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    results = []

    for panel_size_kW in np.arange(0.5, 7, 0.5):

        solar_kwh = solar_panel["irradiance"] / 1000 * panel_size_kW * losses

        demand = solar_panel["hourly_energy_demand"]

        solar_used = np.minimum(solar_kwh, demand)
        solar_excess = np.maximum(0, solar_kwh - demand)
        grid_energy = np.maximum(0, demand - solar_kwh)

        results.append([
            panel_size_kW,
            solar_used.sum()/10,
            solar_excess.sum()/10,
            grid_energy.sum()/10
        ])

    summary = pd.DataFrame(results, columns=[
        "Panel size (kW)",
        "Solar used (kWh/year)",
        "Excess solar (kWh/year)",
        "Grid purchased (kWh/year)"
    ])

    summary["Extra grid saving (kWh/year)"] = (
        summary["Grid purchased (kWh/year)"].shift(1)
        - summary["Grid purchased (kWh/year)"]
    )

    summary = summary.fillna(0).round(2)

    # Total investment payback
    panel_size = summary["Panel size (kW)"]
    cost_per_kw = 500 * 4104

    total_cost = panel_size * cost_per_kw
    tariff = 800
    annual_savings_ugx = summary["Solar used (kWh/year)"] * 800

    summary["Total_investment_payback_years"] = total_cost / annual_savings_ugx

    # Incremental payback
    summary["incremental_payback"] = (
        (summary["Panel size (kW)"].diff() * cost_per_kw) /
        (summary["Extra grid saving (kWh/year)"] * tariff)
    )

    print(summary.to_string(index=False))

    # Total system payback plot
    plt.figure(figsize=(9, 5))

    plt.plot(
        summary["Panel size (kW)"],
        summary["Total_investment_payback_years"],
        marker="o"
    )

    plt.xlabel("Solar Panel Capacity (kW)")
    plt.ylabel("Total Payback Period (years)")
    plt.title("PV Capacity vs Total System Payback")
    plt.grid(True)

    results_dir = Path(__file__).resolve().parent.parent / "solar and battery design results"
    plt.savefig(results_dir / "total system payback.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Incremental payback plot
    plt.figure(figsize=(9, 5))

    plt.plot(
        summary["Panel size (kW)"],
        summary["incremental_payback"],
        marker="o"
    )

    plt.xlabel("Solar Panel Capacity (kW)")
    plt.ylabel("Incremental Payback Period (years)")
    plt.title("PV Capacity vs Incremental Payback")
    plt.grid(True)

    results_dir1 = Path(__file__).resolve().parent.parent / "solar and battery design results"
    plt.savefig(results_dir1 / "incremental_payback.png", dpi=300, bbox_inches="tight")
    plt.show()
    

    summary.to_csv(Path(__file__).resolve().parent.parent / "solar and battery design results" / "Solar sizing and grid purchased by each size and payment period of different panel sizes.csv",index=False)

    print("\n\n\nFrom the total investment, the payback period should be less that 5 years so in that case the 3kw panel size is chosen from the simulation")
