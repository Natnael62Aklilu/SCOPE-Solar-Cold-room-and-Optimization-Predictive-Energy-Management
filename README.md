# SCOPE — Solar Cold-Room Optimization and Predictive Energy Management-Actual cold room in kampala of 8m3 

**An intelligent energy management system integrating solar PV, battery storage, grid power and weather forecasting for a cold-storage application.**

## 1. Project Overview

SCOPE is an engineering project focused on improving the energy efficiency and reliability of a solar-powered cold-storage system.

The project combines solar PV generation, battery energy storage, grid electricity and predictive energy management to reduce grid dependence while maintaining a reliable energy supply for cold-room operation.

Python-based simulations and forecasting techniques are used to analyse energy demand, solar availability, battery behaviour and future energy requirements.

## 2. Project Objectives

- Optimise solar PV capacity based on historical solar resources and cold-room energy demand.
- Determine suitable battery storage capacity.
- Reduce unnecessary grid electricity consumption.
- Maintain sufficient battery reserves during periods of low solar generation.
- Use weather and energy forecasts to improve battery management decisions.
- Improve the reliability and economic performance of the energy system.

## 3. System Architecture

The project consists of the following main components:

1. Weather Data Processing: Processing historical temperature, humidity and solar irradiance data.
2. Cold-Room Energy Modelling: Estimating hourly electricity demand based on the cold-room thermal load.
3. Solar PV Optimisation:** Evaluating different PV capacities using historical solar generation and energy demand.
4. Battery Energy Storage:** Modelling battery charging, discharging, efficiency, state of charge and reserve requirements.
5. Solar and Load Forecasting:** Predicting future solar generation and cold-room energy demand.
6. Predictive Energy Management:** Managing battery reserves, discharge decisions and grid utilisation using forecast information.

## 4. Intelligent Energy Management

The predictive energy management system incorporates three main control strategies:

- *Dynamic Battery Reserve:* Adjusting the minimum battery reserve according to anticipated future energy deficits.
- *Forecast-Based Discharge Limits:* Managing battery discharge to preserve sufficient energy for upcoming periods of low solar generation.
- *Predictive Grid Utilisation:* Using grid electricity strategically when preserving battery energy is more beneficial.

## 5. Technologies and Tools

- Python
- Pandas and NumPy
- Matplotlib
- MATLAB
-
- Open-Meteo Weather API
- Git and GitHub

## 6. Data and Simulation

The project uses ten years of historical hourly weather and solar irradiance data (2016–2025), together with modelled hourly cold-room electricity demand.

Historical datasets are used for system sizing, simulation and performance evaluation, while weather forecasts support predictive energy management.

## 7. Repository Structure

```text
SCOPE/
│
├── Raw Temperature Humidity and Irradiance Data/
├── Raw Data Processing scripts/
├── Processed Data CSV/
├── Solar panel and Battery sizing/
├── solar and battery design results/
├── battery management system scripts/
└── optimized analysis of SCOPE Controller outputs and results/
```

## 8. Project Status

The solar PV design, battery sizing and energy management simulation components have been developed. Predictive control strategies are being integrated and evaluated using historical data and weather forecasts.

## 9. Project Goal

The long-term goal is to demonstrate how forecasting, optimisation and intelligent control can improve the efficiency, reliability and sustainability of decentralised electrical energy systems.

---

**Developed as an Electrical Engineering project focused on renewable energy integration, battery storage and intelligent energy management on my own cold room**
