
import numpy as np
import pandas as pd
import json
import os

from solar_and_load_forecast import solar_forecast, load_forecast, time




STATE_FILE = "battery_state.json"


def load_battery_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)

    return {
        "energy": 6.4,
        "last_time": None,
        "predicted_energy": {}
    }


def save_battery_state(energy, timestamp, predicted_energy):
    with open(STATE_FILE, "w") as file:
        json.dump({
            "energy": float(energy),
            "last_time": str(timestamp),
            "predicted_energy": predicted_energy
        }, file, indent=4)


# ORIGINAL BATTERY CONTROLLER — UNCHANGED


def battery_management(
    solar_forecast,
    load_forecast,
    capacity=8.0,
    initial_energy=6.4,
    min_energy=1.7,
    charge_eff=0.95,
    discharge_eff=0.95,
    pv_safety_margin=0.10,
    reserve_hours=2
):

    solar = np.asarray(solar_forecast, dtype=float)
    load = np.asarray(load_forecast, dtype=float)

    if len(solar) != len(load):
        raise ValueError("Solar and load forecasts must have the same length.")

    if np.any(solar < 0) or np.any(load < 0):
        raise ValueError("Solar and load forecasts cannot contain negative values.")

    if not min_energy <= initial_energy <= capacity:
        raise ValueError("Initial battery energy must be between min_energy and capacity.")

    def calculate_reserve(future_solar, future_load):

        if len(future_solar) == 0:
            return min_energy

        def can_supply(start_energy):
            energy = start_energy

            for pv, demand in zip(future_solar, future_load):

                pv *= (1 - pv_safety_margin)

                pv_to_load = min(pv, demand)
                surplus = pv - pv_to_load
                deficit = demand - pv_to_load

                pv_charge = min(
                    surplus,
                    (capacity - energy) / charge_eff
                )

                energy += pv_charge * charge_eff

                battery_required = deficit / discharge_eff

                if energy - battery_required < min_energy:
                    return False

                energy -= battery_required

            return True

        if not can_supply(capacity):
            return capacity

        low = min_energy
        high = capacity

        for _ in range(40):
            middle = (low + high) / 2

            if can_supply(middle):
                high = middle
            else:
                low = middle

        return high

    energy = initial_energy
    results = []

    for hour in range(len(solar)):

        pv = solar[hour]
        demand = load[hour]

        future_solar = solar[hour + 1:hour + 1 + reserve_hours]
        future_load = load[hour + 1:hour + 1 + reserve_hours]

        reserve = calculate_reserve(future_solar, future_load)

        # PV supplies the load first
        pv_to_load = min(pv, demand)
        surplus = pv - pv_to_load
        deficit = demand - pv_to_load

        # Charge the battery using PV surplus
        pv_charge = min(
            surplus,
            (capacity - energy) / charge_eff
        )

        energy += pv_charge * charge_eff
        pv_curtailed = surplus - pv_charge

        # Discharge only the energy above the dynamic reserve
        battery_to_load = min(
            deficit,
            max(0, energy - reserve) * discharge_eff
        )

        energy -= battery_to_load / discharge_eff

        # Grid supplies any remaining load
        grid_to_load = deficit - battery_to_load

        # Grid restores the battery to its dynamic reserve
        reserve_shortfall = max(0, reserve - energy)

        grid_charge = min(
            reserve_shortfall / charge_eff,
            (capacity - energy) / charge_eff
        )

        energy += grid_charge * charge_eff

        total_grid = grid_to_load + grid_charge

        results.append({

            "PV to Load (kWh)": pv_to_load,
            "PV to Battery (kWh)": pv_charge,
            "Battery to Load (kWh)": battery_to_load,
            "Grid to Load (kWh)": grid_to_load,
            "Grid to Battery (kWh)": grid_charge,
            "Total Grid (kWh)": total_grid,
            "Dynamic Reserve (kWh)": reserve,
            "Battery Energy (kWh)": energy,
            "Battery SOC (%)": energy / capacity * 100,

        })

    return pd.DataFrame(results)


# ==================================================
# RUN THE BATTERY MANAGEMENT SYSTEM
# ==================================================

state = load_battery_state()

# Normalize forecast timestamps
forecast_times = (
    pd.to_datetime(time)
    .reset_index(drop=True)
    .dt.floor("h")
)

# Current Kampala hour
current_time = pd.Timestamp.now(
    tz="Africa/Kampala"
).tz_localize(None).floor("h")

# Find current hour or next available forecast hour
current_index = forecast_times[
    forecast_times >= current_time
].index

if len(current_index) == 0:
    raise ValueError("No current or future forecast hour is available.")

current_position = current_index[0]
processing_time = forecast_times.iloc[current_position]

print("Current time:", current_time)
print("Processing forecast hour:", processing_time)


# RECOVER BATTERY ENERGY FROM SAVED STATE


initial_energy = float(state["energy"])

same_hour = False

if state["last_time"] is not None:

    last_time = pd.Timestamp(state["last_time"]).floor("h")

    if processing_time < last_time:
        raise ValueError(
            "Forecast hour is older than the saved battery state."
        )

    if processing_time == last_time:

        same_hour = True

        print("This hour has already been processed.")
        print("Running simulation without updating saved state.")

    else:

        missed_hours = pd.date_range(
            start=last_time + pd.Timedelta(hours=1),
            end=processing_time - pd.Timedelta(hours=1),
            freq="h"
        )

        for missed_time in missed_hours:

            key = missed_time.strftime("%Y-%m-%d %H:%M:%S")

            if key not in state.get("predicted_energy", {}):
                raise ValueError(
                    f"No saved battery prediction for missed hour {missed_time}."
                )

            initial_energy = float(
                state["predicted_energy"][key]
            )


# RUN ORIGINAL 24-HOUR BATTERY CONTROLLER


battery_results = battery_management(
    solar_forecast,
    load_forecast,
    initial_energy=initial_energy
)

battery_results["24 hour ahead"] = forecast_times


# UPDATE JSON STATE AND FUTURE PREDICTIONS


if not same_hour:

    predicted_energy = {}

    for i in range(current_position + 1, len(battery_results)):

        timestamp = forecast_times.iloc[i]

        key = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        predicted_energy[key] = float(
            battery_results.iloc[i]["Battery Energy (kWh)"]
        )

    current_energy = float(
        battery_results.iloc[current_position]["Battery Energy (kWh)"]
    )

    save_battery_state(
        current_energy,
        processing_time,
        predicted_energy
    )

    print("\nBattery state successfully updated.")
    print(f"Saved battery energy: {current_energy:.3f} kWh")

else:

    print("\nJSON state unchanged.")
    print(f"Previously saved energy: {initial_energy:.3f} kWh")


# DISPLAY COMPLETE SIMULATION


print("\n========== 24-HOUR BATTERY SIMULATION ==========\n")

battery_result=battery_results.round(3)
battery_result.to_csv(
    Path(__file__).resolve().parent.parent / "optimized analysis of SCOPE Controller outputs and results" / "Prediction and Optimization of Battery Data.csv",
    index=False)


