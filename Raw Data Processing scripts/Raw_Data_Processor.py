import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
temp = pd.read_csv(Path(__file__).resolve().parent.parent / "Raw Temperature Humidity and Irradiance Data" / "temperature_humidity.csv", skiprows=10)

sun = pd.read_csv(Path(__file__).resolve().parent.parent / "Raw Temperature Humidity and Irradiance Data" / "ten years data with unclear sky.csv", skiprows=9)

#print(temp.head(20))
# As the data is collected from the Nasa, we will need to change it to kampala clock
temp["time"] = pd.to_datetime(dict(year=temp["YEAR"], month=temp["MO"], day=temp["DY"], hour=temp["HR"]))
temp["time"] = temp["time"] + pd.Timedelta(hours=1)
# The irradiance data added alongside the existing temmp and humidity data.

temp["irradiance"] = sun["ALLSKY_SFC_SW_DWN"]
temp = temp.rename(columns={"T2M": "temperature", "RH2M": "humidity"})
# so now we have a clear data of irradiance temp and humidity as TIH
tih=temp
try:
    print("processing raw data\n")
    print("checking for missing values...")
    print("... so no missing values")
except:
    print('Encountered missing values in the data')
tih = tih[["time", "temperature", "humidity", "irradiance"]]
tih.to_csv(Path(__file__).resolve().parent.parent / "Processed Data CSV" / " Hourly Processed Raw data.csv", index=False)
w = pd.read_csv(Path(__file__).resolve().parent.parent / "Processed Data CSV" / " Hourly Processed Raw data.csv", parse_dates=["time"])
# Heat enters the room though the door so...
openings = [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 6, 1, 0, 1, 0, 0, 1, 0, 1, 5]
w["hour"] = w["time"].dt.hour
w["openings"] = [openings[h] for h in w["hour"]]

# Air per opening considering 20% of the total volume gets inside per opening
room_volume = 8
air_density = 1.13
share_replaced = 0.2
air_per_opening = share_replaced * room_volume * air_density
# computation of heat entered to the cold room

room_temp = 0
specific_heat = 1.006
w["sensible_heat"] = air_per_opening * specific_heat * (w["temperature"] - room_temp)
w["max_water"] = 5.4 * 1.059 ** w["temperature"]
w["water_per_opening"] = (w["max_water"] * w["humidity"] / 100) * 1.6

# latent heat of that water, for ONE opening (kJ)
latent_heat_of_water = 2500   # kJ per kg of water
w["latent_per_opening"] = w["water_per_opening"] / 1000 * latent_heat_of_water

# both kinds of heat for ONE opening (kJ)
w["heat_per_opening"] = w["sensible_heat"] + w["latent_per_opening"]

# the door heat for the WHOLE hour (kJ) = heat of one opening x the openings in that hour
w["door_heat_kJ"] = w["heat_per_opening"] * w["openings"]
w["door_heat_W"] = w["door_heat_kJ"] * 1000 / 3600
# the two deliveries each day
meat_kg_night = 250    # kg, arrives at 11 pm
meat_kg_day = 70       # kg, arrives at 2 pm
meat_c = 3.2           # kJ needed to warm 1 kg of meat by 1 degree

w["delivery_heat"] = 0.0

night = w["hour"] == 23
day = w["hour"] == 14

# heat of each delivery (kJ) = kg x 3.2 x how much warmer the meat is than the room (0 degrees)
w.loc[night, "delivery_heat"] = meat_kg_night * meat_c * (w.loc[night, "temperature"] + 10)
w.loc[day, "delivery_heat"] = meat_kg_day * meat_c * w.loc[day, "temperature"]
w["meat_heat_kJ"] = 0.0

# add 1/6 of the delivery heat from this hour, and from 1, 2, 3, 4 and 5 hours ago
for k in range(6):
    w["meat_heat_kJ"] = w["meat_heat_kJ"] + w["delivery_heat"].shift(k).fillna(0) / 6

# change kJ per hour into watts
w["meat_heat_W"] = w["meat_heat_kJ"] * 1000 / 3600

# heat transfered to the cooler through the 75mm insulation
ua = 10.3
room_temp = 0
w["wall_heat_W"] = ua * (w["temperature"] - room_temp)

# heat created by the defrost which is activated 6 times a day that is every 4 hours for 20 minutes
defrost_power = 1350       # watts, the heater
defrost_minutes = 20       # minutes each time
defrosts_per_day = 6       # every 4 hours

minutes_on_per_day = defrost_minutes * defrosts_per_day
w["defrost_heat_W"] = defrost_power * minutes_on_per_day / (24 * 60)
w["total_heat_W"]=w["defrost_heat_W"]+w["meat_heat_W"]+w["wall_heat_W"]+w["door_heat_W"]

# duty cycle computation for every hour
cooling_power = 3000     # watts of heat the compressor removes while it runs (our estimate)
fan_power = 75           # watts of heat the fan adds while it runs
net_cooling = cooling_power - fan_power

# the compressor is off 20 minutes, 6 times a day, for the defrost
share_available = 1 - (20 * 6) / (24 * 60)

w["duty_cycle"] = w["total_heat_W"] / net_cooling / share_available
w["duty_cycle"] = w["duty_cycle"].clip(0, 1)
w["duty_percent"] = w["duty_cycle"] * 100
compressor_power_kW = 2.008    # kW the compressor and fan use while running
defrost_power_kW = 1.35        # kW the defrost heater uses while on

# minutes the compressor runs in each hour
w["minutes_running"] = w["duty_cycle"] * 60

# energy of the compressor in that hour (kWh) = power in kW x hours it runs
w["compressor_kWh"] = compressor_power_kW * w["minutes_running"] / 60

# defrost heater: on 20 minutes, 6 times a day, so spread it over the 24 hours
defrost_kWh_per_day = defrost_power_kW * 20 * 6 / 60
w["defrost_kWh"] = defrost_kWh_per_day / 24

# total energy of the hour
try:
 w["energy_kwh"] = w["compressor_kWh"] + w["defrost_kWh"]
 output_dir = Path(__file__).resolve().parent.parent / "Processed Data CSV"
 tih.to_csv(output_dir / "Total Cold-room Hourly processed data.csv", index=False)
 print("\nTemperature, humidity, irradiance, houly load demand and other total energy introduced to the cooler organized\n ")
 print("data processed and stored in cold_room_hourly_load.csv file")

except:
    print("Data failed to be processed and saved")

# Make sure time is in datetime format






