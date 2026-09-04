# Metro Interstate Traffic Volume — Comprehensive Project Guide

This master guide provides a thorough technical and conceptual overview of the project, including business context, dataset breakdown, preprocessing methodology, machine learning strategy, key findings, and committee presentation defense Q&A.

---

## 1. Elevator Pitch

This project delivers an end-to-end Machine Learning platform designed to forecast **hourly traffic volume (vehicles/hour)** on Interstate 94 (I-94 westbound) connecting Minneapolis and St. Paul, Minnesota. 

By modeling complex multi-way interactions between temporal signals (hour, day, month, holidays) and Midwestern weather conditions (temperature, snowfall, precipitation, cloud cover), the system generates reliable forecasts deployed as a real-time FastAPI service and interactive web dashboard.

---

## 2. Business Problem & Motivation

### The Challenge
- **Severe Economic Loss:** Metropolitan highway bottlenecks lead to fuel wastage, commercial freight supply-chain delays, and lost working hours.
- **Environmental Footprint:** Stop-and-go congestion dramatically increases greenhouse gas emissions.
- **Safety Risks:** Accident probabilities escalate sharply during peak rush hours and severe winter conditions (Minnesota blizzards, freezing rain, and black ice).

### The AI Solution
- Transitioning transportation management from **reactive response** to **predictive control**.
- Empowering transportation departments (e.g., MnDOT) to dynamically adjust ramp meters, preemptively deploy winter gritting crews, and optimize maintenance schedules.
- Enabling navigation systems to route commercial logistics and commuters around forecasted congestion windows.

---

## 3. Dataset Characteristics & Schema

Sourced from the **UCI Machine Learning Repository** (ID 492: Metro Interstate Traffic Volume), recorded via Minnesota Department of Transportation (MnDOT) detector station 301.

- **Total Records:** 48,204 raw hourly observations (October 2012 – September 2018).
- **Cleaned Records:** 40,564 unique chronological hours.
- **Problem Formulation:** Multivariate Supervised Time-Series Regression.
- **Target Variable:** `traffic_volume` (Hourly vehicle count, ranging from 0 to 7,280 veh/hr).

### Feature Dictionary

| Feature | Role | Data Type | Units / Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `holiday` | Input | Categorical | Text | US federal/state holiday name or `"Not Holiday"` |
| `temp` | Input | Numerical | Kelvin (K) | Hourly average ambient temperature |
| `rain_1h` | Input | Numerical | mm | Hourly accumulated rainfall |
| `snow_1h` | Input | Numerical | mm | Hourly accumulated snowfall |
| `clouds_all` | Input | Numerical | % (0–100) | Cloud cover percentage |
| `weather_main` | Input | Categorical | Text | General weather category (Clear, Rain, Snow, Clouds...) |
| `day_of_week` | Input | Categorical | Text | Day name (`Monday`, `Tuesday`, ..., `Sunday`) |
| `hour_sin`, `hour_cos` | Input | Numerical | [-1, 1] | Cyclical sine/cosine representation of hour (period = 24) |
| `month_sin`, `month_cos`| Input | Numerical | [-1, 1] | Cyclical sine/cosine representation of month (period = 12) |
| `traffic_volume` | **Target** | Numerical | Vehicles / hr | Hourly westbound vehicle throughput |

---

## 4. Key Exploratory Data Analysis (EDA) Insights

1. **Bimodal Commute Rhythms:**
   - On weekdays, traffic exhibits two sharp spikes:
     - **Morning Peak (07:00 – 09:00 AM):** Reaches 5,800 to 6,100 vehicles/hour inbound to Minneapolis.
     - **Evening Peak (16:00 – 18:00 PM):** Reaches 5,600 to 6,400 vehicles/hour outbound.
   - Night troughs (01:00 – 04:00 AM) drop below 500 vehicles/hour.

2. **Weekday vs. Weekend Contrast:**
   - Weekends lack the sharp morning spike; traffic climbs gradually to a single, broad midday peak (12:00 – 15:00 PM) before declining. Sunday traffic volume is approximately 25–30% lower than weekday volumes.

3. **Holiday Impact:**
   - National holidays eliminate the morning commute entirely, transforming weekday flow into a relaxed holiday curve ($\sim 35 - 40\%$ reduction in daily volume).

4. **Adverse Weather Impact:**
   - Heavy snowfall ($>2$ mm) reduces highway capacity by up to **32%** due to slower driving speeds, gritting trucks, and trip cancellations.

---

## 5. Preprocessing & Feature Engineering Pipeline

1. **Timestamp Sorting & Deduplication:**
   - Sorted strictly by timestamp. Resolved multiple hourly weather entries by establishing a meteorological severity hierarchy (`Squall` > `Thunderstorm` > `Snow` > `Rain` > `Clouds` > `Clear`) and dropping duplicate timestamps.
2. **Holiday Propagation:**
   - Propagated holiday indicators across all 24 hours of each designated holiday date, labeling non-holidays as `"Not Holiday"`.
3. **Outlier Treatment:**
   - Removed physically invalid $0\text{ K}$ ($-273.15^\circ\text{C}$) sensor glitches.
   - Filtered an erroneous rainfall recording of $> 1,000\text{ mm}$.
4. **Cyclical Temporal Transformations:**
   - Applied sine/cosine transformations to preserve periodicity across midnight and year-end boundaries:
     $$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$
     $$\text{month\_sin} = \sin\left(\frac{2\pi \cdot \text{month}}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot \text{month}}{12}\right)$$
5. **Unified Scikit-Learn Pipeline:**
   - Numerical features (8) $\rightarrow$ `StandardScaler()`
   - Categorical features (3: `holiday`, `weather_main`, `day_of_week`) $\rightarrow$ `OneHotEncoder(drop='first', handle_unknown='ignore')`

---

## 6. Machine Learning Strategy & Benchmarks

To avoid temporal data leakage, data was split chronologically:
- **Training Set (80%):** 32,451 observations.
- **Testing Set (20%):** 8,113 observations.

### Comparative Results (`notebooks/04.1_modeling_trial.ipynb`):

| Model Architecture | MAE (Vehicles/hr) | RMSE (Vehicles/hr) | $R^2$ Score | Status |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost Regressor** (300 trees, lr=0.05, max_depth=6) | **234.07** | **379.52** | **0.9629** | **Champion (Production)** |
| Random Forest Regressor (200 trees) | 250.92 | 411.27 | 0.9564 | Strong Runner-up |
| Linear Regression | 821.57 | 1042.94 | 0.7198 | Baseline |

### Generalization & Overfitting Check
- **Train $R^2$:** 0.9689 (MAE = 219.55 veh/hr)
- **Test $R^2$:** 0.9629 (MAE = 234.07 veh/hr)
- The tight alignment ($\Delta R^2 < 0.006$) verifies that the model generalizes robustly on unseen future periods.

---

## 7. Production Architecture & Deployment

- **Backend:** FastAPI service modularized into `app/main.py`, `app/schemas.py`, and `app/routers/forecast.py`.
- **Live Weather Integration:** Interacts with WeatherAPI.com to fetch live forecasts, mapping meteorological parameters directly into model inputs.
- **Frontend Dashboard:** Highway signage design featuring:
  - Interactive Simulator with real-time capacity and weather drag calculations.
  - Multi-day, hour-range forecast sliders (`start_hour` to `end_hour`).
  - Color-coded hourly congestion bar charts (`Light`, `Normal`, `Moderate`, `Heavy`).
  - Live animated variable message sign (VMS).

---

## 8. Presentation Defense & Committee Q&A Guide

### Q1: What real-world problem does your project solve?
> **Answer:** It solves the challenge of proactive traffic management by accurately forecasting hourly traffic volume on highway corridors (I-94) before congestion manifests. By integrating calendar rhythms and live weather forecasts, it enables transportation authorities to dynamically optimize signals, deploy snow removal crews early, and schedule roadwork outside peak hours.

### Q2: What is the target variable and machine learning task type?
> **Answer:** The task is supervised time-series regression. The target variable is `traffic_volume`, a continuous numerical variable representing vehicle throughput per hour.

### Q3: Which factor drives traffic volume more: time or weather?
> **Answer:** Temporal features (hour of day and day of week) account for over 80% of the variance, defining the fundamental bimodal commute peaks. Weather acts as a capacity modifier: while clear weather sustains maximum flow, adverse weather (like heavy snow) suppresses throughput by up to 32%.

### Q4: Why did you use cyclical sine/cosine encodings for time?
> **Answer:** Linear encodings create an artificial discontinuity between 23:00 and 00:00 (a difference of 23 instead of 1 hour). Sine and cosine projections wrap hours and months into continuous circles, preserving true geometric proximity for machine learning algorithms.

### Q5: Why did you use a chronological train/test split instead of a random k-fold split?
> **Answer:** In time-series data, random splitting causes future observations to bleed into training data (look-ahead bias/data leakage). A chronological 80/20 split ensures the model is trained exclusively on past history and evaluated on strictly future, unseen periods.

### Q6: Why did XGBoost outperform Linear Regression and Random Forest?
> **Answer:** Traffic patterns involve complex, non-linear conditional relationships (e.g., commute spikes only happen if it's a weekday AND a working hour AND roads aren't snowbound). Linear models cannot capture these multi-way thresholds. XGBoost's gradient-boosted decision trees systematically minimize residual errors, delivering superior precision ($R^2 = 0.963$, MAE = 234 veh/hr).
