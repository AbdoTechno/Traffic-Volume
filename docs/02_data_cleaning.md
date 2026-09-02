# 02 — Data Cleaning & Preprocessing

## Overview
This document outlines the end-to-end data cleaning, anomaly resolution, and feature engineering procedures performed on the Metro Interstate Traffic Volume dataset (`notebooks/02_data_cleaning.ipynb`).

---

## 1. Initial Data Assessment
The raw dataset loaded from UCI contains **48,204 hourly records** across 9 columns:
- `holiday`, `temp`, `rain_1h`, `snow_1h`, `clouds_all`, `weather_main`, `weather_description`, `date_time`, `traffic_volume`.
- Checked for missing values: the raw table had 0 null entries, but several implicit anomalies and duplicate timestamps were present.

---

## 2. Cleaning & Transformation Steps

### 2.1 Timestamp Parsing & Time Extraction
- Converted `date_time` from string representation to `pd.to_datetime`.
- Extracted temporal components:
  - `hour`: Integer from 0 to 23.
  - `day_of_week`: Full string day name (`Monday`, `Tuesday`, ..., `Sunday`).
  - `month`: Integer from 1 to 12.

### 2.2 Deduplication & Weather Priority Resolution
- **Issue:** Several timestamps contained multiple rows because different weather events were reported within the same hour (e.g., both "Rain" and "Mist").
- **Resolution:** A priority mapping was established based on severity (`Squall` > `Thunderstorm` > `Snow` > `Rain` > `Drizzle` > `Fog` > `Mist` > `Haze` > `Clouds` > `Clear`).
- Sorted by `[date_time, weather_priority]` and deduplicated using:
  `df.drop_duplicates(subset='date_time', keep='first')`.
- This eliminated timestamp redundancies while retaining the most severe weather condition for the hour.

### 2.3 Holiday Propagation
- **Issue:** In the raw dataset, holidays were only marked at the midnight hour (`00:00:00`), while subsequent hours of that day were left blank or unmarked.
- **Resolution:** Mapped each calendar holiday date across all 24 hours of that calendar day.
- Non-holiday days were explicitly filled with the label `'Not Holiday'`.

### 2.4 Anomaly & Outlier Filtering
- **Temperature Anomaly (0 Kelvin):** Filtered out physically impossible sensor errors where `temp == 0` K (equivalent to absolute zero, $-273.15^\circ\text{C}$).
- **Rainfall Outlier:** Filtered out a corrupted recording of `rain_1h > 1000` mm (an unrealistic reading of nearly 10 meters of rain in a single hour).

### 2.5 Dimensionality Reduction
- Dropped `weather_description` (38 granular subcategories) to avoid high cardinality and model overfitting, keeping `weather_main` (11 standard categories).

---

## 3. Cyclical Temporal Encoding
To preserve the cyclical nature of time (ensuring that hour 23 and hour 0 are mathematically adjacent, and December is adjacent to January), trigonometric transformations were applied:

$$\text{hour\_sin} = \sin\left(\frac{2\pi \times \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \times \text{hour}}{24}\right)$$
$$\text{month\_sin} = \sin\left(\frac{2\pi \times \text{month}}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \times \text{month}}{12}\right)$$

---

## 4. Final Output Dataset
The processed data was saved to:
`data/processed/traffic_volume_cleaned.csv`

| Metric | Raw Dataset | Cleaned Dataset |
| :--- | :--- | :--- |
| Total Rows | 48,204 | **40,564** |
| Unique Timestamps | Duplicated | **Unique & Chronological** |
| Missing Values | 0 | **0** |
| Sensor Glitches (0 K, >1000 mm) | Present | **Removed** |
| Output Columns | 9 | **15** (Includes cyclical sine/cosine features) |
