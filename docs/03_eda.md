# 03 — Exploratory Data Analysis (EDA)

## Overview
This document summarizes the core findings, statistical distributions, and behavioral insights discovered during the exploratory data analysis of Interstate 94 (I-94) traffic volume (`notebooks/03_eda.ipynb`).

---

## 1. Target Variable Distribution (`traffic_volume`)
- **Range:** 0 to 7,280 vehicles/hour.
- **Mean:** $\approx 3,259$ vehicles/hour | **Median:** $\approx 3,380$ vehicles/hour.
- **Distribution Shape:** Bimodal distribution. The first peak occurs at low night volumes ($< 1,000$ veh/hr), and the second larger peak occurs during daytime/commute hours ($4,000 - 6,000$ veh/hr).
- Maximum theoretical capacity of this segment is approximately **7,280 vehicles/hour**.

---

## 2. Temporal Dynamics (Primary Traffic Driver)

### 2.1 Hourly Diurnal Rhythm
- **Morning Peak:** 07:00 – 09:00 AM ($\approx 5,800 - 6,100$ veh/hr average). Represents the inbound morning commute towards Minneapolis employment centers.
- **Evening Peak:** 04:00 – 06:00 PM ($\approx 5,600 - 6,400$ veh/hr average). Represents the evening return commute.
- **Trough Hours:** 01:00 – 04:00 AM ($< 500$ veh/hr average). Light free-flow traffic.

### 2.2 Weekday vs. Weekend Patterns
- **Workdays (Monday – Friday):** Distinct **M-shaped** bimodal curve with steep morning and evening rush-hour spikes.
- **Weekends (Saturday & Sunday):** Flatter, bell-shaped unimodal curve. Morning commute spike is completely absent; volume rises steadily from 10:00 AM, peaks in the early afternoon, and tapers off. Sunday traffic volume is approximately 25–30% lower than weekday averages.

### 2.3 Holiday Impact
- Public holidays (Labor Day, Thanksgiving, Christmas, New Year's Day, etc.) transform the weekday pattern into a low-volume weekend profile.
- The morning rush peak disappears, and overall volume decreases by approximately **35% to 40%** relative to a normal weekday.

---

## 3. Weather & Environmental Influences

### 3.1 Temperature (`temp`)
- Ambient temperature follows typical Midwestern seasonality (ranging from sub-zero winter temperatures $\sim 245$ K / $-28^\circ\text{C}$ to summer heat $\sim 310$ K / $+37^\circ\text{C}$).
- Moderate temperatures ($285 - 295$ K / $12 - 22^\circ\text{C}$) correlate with higher travel frequency and sustained peak volumes.
- Sub-zero temperatures ($< -15^\circ\text{C}$) show modest traffic dampening ($\sim 8 - 12\%$).

### 3.2 Precipitation (`rain_1h` & `snow_1h`)
- **Rain:** Light to moderate rain causes minor speed reductions but only slight throughput drops ($5 - 10\%$). Heavy downpours lead to noticeable traffic suppression ($15 - 20\%$).
- **Snowfall:** Snow has the most severe meteorological impact. Heavy snowfall and blizzard conditions reduce highway throughput by up to **32%** due to road closures, gritting operations, and reduced travel demand.

### 3.3 Weather Categories (`weather_main`)
- Average volumes by general weather state:
  - **Clear / Clouds:** Highest throughput (normal capacity).
  - **Drizzle / Mist / Fog:** Minor slowdowns ($\sim 5 - 10\%$).
  - **Rain / Thunderstorm:** Noticeable volume reduction ($\sim 12 - 18\%$).
  - **Snow / Squall:** Most severe throughput impediment ($\sim 25 - 35\%$).

---

## 4. Key EDA Takeaways for Modeling
1. **Time features are paramount:** Hour of day and day of week explain the vast majority of variance in traffic volume.
2. **Cyclical encoding is essential:** Representing hour and month as sine/cosine waves allows models to smoothly transition across periodic boundaries.
3. **Nonlinear interactions dominate:** High volume requires both a commute hour AND a working day AND reasonable weather. Tree-based ensemble models (Random Forest, XGBoost) are inherently suited to capture these multi-way conditional splits.
