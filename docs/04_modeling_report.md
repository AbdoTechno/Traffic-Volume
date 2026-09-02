# Traffic Volume Prediction — Modeling Report

**Project:** Metro Interstate Traffic Volume  
**Task:** Supervised Time-Series Regression  
**Target Variable:** `traffic_volume` (Vehicles per hour)

---

## 1. Problem Classification
This is a **regression problem** because the target variable — `traffic_volume` — represents continuous vehicle counts ranging from 0 to 7,280 vehicles/hour.

---

## 2. Data Preparation & Feature Engineering
The cleaned traffic dataset (`traffic_volume_cleaned.csv`) was prepared following the methodology in `notebooks/04.1_modeling_trial.ipynb`:

- **Datetime Parsing & Chronological Ordering:** Data was sorted strictly by `date_time` ascending.
- **Cyclical Encoding:** The hour of the day (0–23) and month (1–12) were transformed into continuous sine and cosine waves:
  $$\text{hour\_sin} = \sin(2\pi \cdot \text{hour} / 24), \quad \text{hour\_cos} = \cos(2\pi \cdot \text{hour} / 24)$$
  $$\text{month\_sin} = \sin(2\pi \cdot \text{month} / 12), \quad \text{month\_cos} = \cos(2\pi \cdot \text{month} / 12)$$
- **Categorical Preservation:** `holiday` (e.g. `"Not Holiday"`, `"Thanksgiving"`), `day_of_week` (`"Monday"`, ..., `"Sunday"`), and `weather_main` (`"Clear"`, `"Rain"`, ...) were preserved as categorical labels for robust one-hot encoding.
- **Feature Matrix Split:** Raw `date_time`, integer `hour`, and integer `month` were removed from the training matrix `X` to eliminate collinear redundancy with their cyclical representations.

---

## 3. Train/Test Split
A **chronological split** (80% train / 20% test) was used:
- **Training Samples:** 32,451 observations.
- **Testing Samples:** 8,113 observations.
- This chronological split prevents look-ahead bias and accurately simulates forecasting future unseen traffic.

---

## 4. Preprocessing Pipeline
A unified `ColumnTransformer` was embedded inside each candidate pipeline:
- **Numerical Features (8):** `["temp", "rain_1h", "snow_1h", "clouds_all", "hour_sin", "hour_cos", "month_sin", "month_cos"]` standardized with `StandardScaler()`.
- **Categorical Features (3):** `["holiday", "weather_main", "day_of_week"]` transformed with `OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False)`.

---

## 5. Model Benchmarking & Results

| Model Architecture | Hyperparameters | MAE (Veh/hr) | RMSE (Veh/hr) | $R^2$ Score |
| :--- | :--- | :---: | :---: | :---: |
| **XGBoost Regressor** | `n_estimators=300, lr=0.05, max_depth=6` | **234.07** | **379.52** | **0.9629** |
| **Random Forest Regressor** | `n_estimators=200, random_state=42` | 250.92 | 411.27 | 0.9564 |
| **Linear Regression** | Default baseline | 821.57 | 1042.94 | 0.7198 |

---

## 6. Model Selection & Generalization Check
- **Selected Champion:** **XGBoost Regressor** achieved the highest $R^2$ (0.963) and lowest MAE (234.07 veh/hr).
- **Overfitting Verification:**
  - Training $R^2 = 0.9689$, Training MAE = 219.55.
  - Test $R^2 = 0.9629$, Test MAE = 234.07.
  - The close convergence between training and testing metrics confirms that the model generalizes robustly without overfitting.
- The pipeline was exported to `src/models/traffic_volume_model_pipeline.joblib` for live production serving via FastAPI.
