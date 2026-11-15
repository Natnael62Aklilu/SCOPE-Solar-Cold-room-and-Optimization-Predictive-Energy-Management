import matplotlib.dates as mdates
import requests
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Kampala coordinates
latitude = 0.3476
longitude = 32.5825
panel_losses=0.75
panel_capacity=3

# Open-Meteo API
url = "https://api.open-meteo.com/v1/forecast"

# Request temperature, humidity and solar irradiance
params = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "shortwave_radiation"
    ],
    "forecast_hours": 24,
    "timezone": "Africa/Kampala"
}

try:
    # Send API request
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    # Extract API data
    data = response.json()

    # Create DataFrame
    forecast = pd.DataFrame({
        "Time": data["hourly"]["time"],
        "Temperature_C": data["hourly"]["temperature_2m"],
        "Humidity_percent": data["hourly"]["relative_humidity_2m"],
        "Irradiance_Wm2": data["hourly"]["shortwave_radiation"]
    })

    # Format time for display
    forecast["Time"] = pd.to_datetime(forecast["Time"])

    display_forecast = forecast.copy()
    display_forecast["Time"] = (
        display_forecast["Time"].dt.strftime("%d-%m-%Y %I:%M %p")
    )

    # Display results
    print("successfully retrieved HUMIDITY  TEMPERATURE AND RADIANCE for the next 24 hours")
    

except requests.exceptions.RequestException as error:
    print("API connection error:", error)

except (KeyError, TypeError, ValueError) as error:
    print("Error processing forecast data:", error)


forecast["Solar_kWh"] = (
    forecast["Irradiance_Wm2"] / 1000
    * panel_capacity
    * panel_losses
)


# Use API forecast
w = forecast.copy()

w["Time"] = pd.to_datetime(w["Time"])
w["hour"] = w["Time"].dt.hour

# 1. DOOR OPENINGS
openings = [
    1, 0, 0, 0, 0, 0, 0, 0,
    1, 0, 0, 1, 0, 1, 6, 1,
    0, 1, 0, 0, 1, 0, 1, 5
]

w["openings"] = [openings[h] for h in w["hour"]]

# Air entering per opening
room_volume = 8
air_density = 1.13
share_replaced = 0.2

air_per_opening = room_volume * air_density * share_replaced

# 2. SENSIBLE HEAT FROM DOOR OPENINGS
room_temp = 0
specific_heat = 1.006

w["sensible_heat"] = (
    air_per_opening
    * specific_heat
    * (w["Temperature_C"] - room_temp)
)

# 3. LATENT HEAT FROM MOISTURE
w["max_water"] = 5.4 * 1.059 ** w["Temperature_C"]

w["water_per_opening"] = (
    w["max_water"] * w["Humidity_percent"] / 100 * 1.6
)

latent_heat_of_water = 2500

w["latent_heat"] = (
    w["water_per_opening"] / 1000 * latent_heat_of_water
)

# 4. TOTAL DOOR HEAT
w["heat_per_opening"] = (
    w["sensible_heat"] + w["latent_heat"]
)

w["door_heat_W"] = (
    w["heat_per_opening"]
    * w["openings"] * 1000 / 3600
)

# 5. MEAT DELIVERY HEAT
meat_kg_night = 250
meat_kg_day = 70
meat_c = 3.2

w["delivery_heat"] = 0.0

night = w["hour"] == 23
day = w["hour"] == 14

w.loc[night, "delivery_heat"] = (
    meat_kg_night * meat_c
    * (w.loc[night, "Temperature_C"] + 10)
)

w.loc[day, "delivery_heat"] = (
    meat_kg_day * meat_c
    * w.loc[day, "Temperature_C"]
)

# Spread each delivery over six hours
w["meat_heat_kJ"] = 0.0

for k in range(6):
    w["meat_heat_kJ"] += (
        w["delivery_heat"].shift(k).fillna(0) / 6
    )

w["meat_heat_W"] = w["meat_heat_kJ"] * 1000 / 3600

# 6. WALL HEAT
ua = 10.3

w["wall_heat_W"] = (
    ua * (w["Temperature_C"] - room_temp)
)

# 7. DEFROST HEAT
defrost_power = 1350
defrost_minutes = 20
defrosts_per_day = 6

w["defrost_heat_W"] = (
    defrost_power * defrost_minutes
    * defrosts_per_day / (24 * 60)
)

# 8. TOTAL THERMAL LOAD
w["total_heat_W"] = (
    w["door_heat_W"]
    + w["meat_heat_W"]
    + w["wall_heat_W"]
    + w["defrost_heat_W"]
)

# 9. COMPRESSOR DUTY CYCLE
cooling_power = 3000
fan_power = 75
net_cooling = cooling_power - fan_power

share_available = 1 - (20 * 6) / (24 * 60)

w["duty_cycle"] = (
    w["total_heat_W"] / net_cooling / share_available
).clip(0, 1)

w["duty_percent"] = w["duty_cycle"] * 100

# 10. HOURLY ELECTRICAL ENERGY
compressor_power_kW = 2.008
defrost_power_kW = 1.35

w["minutes_running"] = w["duty_cycle"] * 60

w["compressor_kWh"] = (
    compressor_power_kW * w["minutes_running"] / 60
)

defrost_kWh_per_day = (
    defrost_power_kW * 20 * 6 / 60
)

w["defrost_kWh"] = defrost_kWh_per_day / 24

w["energy_kwh"] = (
    w["compressor_kWh"] + w["defrost_kWh"]
)


solar_forecast=forecast["Solar_kWh"]
load_forecast=w["energy_kwh"]
time=w["Time"]
# Plot Solar Generation vs Energy Demand

# Solar Generation vs Cold-room Energy Demand


plt.figure(figsize=(14, 6))

plt.plot(time, solar_forecast.to_numpy(), marker='o',
         label='Solar PV Generation')

plt.plot(time, load_forecast.to_numpy(), marker='o',
         label='Energy Demand')

plt.title('FORECASTED 24-Hour Solar Generation vs Energy Demand')
plt.xlabel('Time')
plt.ylabel('Energy (kWh)')

# Display full date and time on the x-axis
plt.gca().xaxis.set_major_formatter(
    mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
)

plt.xticks(time, rotation=90)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.tight_layout()

results_dir = Path(__file__).resolve().parent.parent / "optimized analysis of SCOPE Controller outputs and results"

plt.savefig(results_dir / "24_hour_solar_generation_vs_energy_demand.png",
            dpi=300, bbox_inches="tight")

plt.show()

plt.show()
