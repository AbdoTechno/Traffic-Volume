# 04 — Modeling & Evaluation

## Overview
This document details the model selection, pipeline engineering, validation strategy, and benchmarking results for forecasting hourly traffic volume on I-94 (`notebooks/04.1_modeling_trial.ipynb`).

---

## 1. Problem Formulation
- **Task Type:** Supervised Regression (continuous target: `traffic_volume` in vehicles/hour).
- **Evaluation Methodology:** Strict chronological split (80% train = 32,451 samples, 20% test = 8,113 samples) to mimic real-world deployment where future periods are forecasted from historical observations.

---

## 2. Feature Schema & Preprocessing Pipeline

The model utilizes **11 input features** transformed through a Scikit-Learn `ColumnTransformer`:

### 2.1 Categorical Features (OneHotEncoder)
- `holiday`: Text (e.g. `"Not Holiday"`, `"Labor Day"`, `"Christmas Day"`).
- `weather_main`: Text (e.g. `"Clear"`, `"Rain"`, `"Snow"`, `"Clouds"`).
- `day_of_week`: Text (e.g. `"Monday"`, `"Tuesday"`, ..., `"Sunday"`).
- **Transformation:** `OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False)`

### 2.2 Numerical Features (StandardScaler)
- `temp`: Ambient temperature (Kelvin).
- `rain_1h`: Hourly rainfall (mm).
- `snow_1h`: Hourly snowfall (mm).
- `clouds_all`: Cloud cover percentage (0–100%).
- `hour_sin`, `hour_cos`: Cyclical sine/cosine of hour (period = 24).
- `month_sin`, `month_cos`: Cyclical sine/cosine of month (period = 12).
- **Transformation:** `StandardScaler()`

---

## 3. Benchmarked Models

| Model Architecture | Hyperparameters | Purpose |
| :--- | :--- | :--- |
| **Linear Regression** | Default (`fit_intercept=True`) | Baseline linear model |
| **Random Forest Regressor** | `n_estimators=200, random_state=42, n_jobs=-1` | Non-linear bagging ensemble |
| **XGBoost Regressor** | `n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42` | Gradient boosting ensemble |

---

## 4. Benchmark Results on Chronological Test Set

| Model | MAE (Vehicles/hr) | RMSE (Vehicles/hr) | $R^2$ Score | Rank / Status |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost** | **234.07** | **379.52** | **0.9629** | **Champion (Production)** |
| **Random Forest** | 250.92 | 411.27 | 0.9564 | Runner-up |
| **Linear Regression** | 821.57 | 1042.94 | 0.7198 | Baseline |

---

## 5. Overfitting & Generalization Analysis

Evaluating the best model (**XGBoost**) across train vs. test splits:

| Split | $R^2$ Score | MAE (Vehicles/hr) |
| :--- | :---: | :---: |
| **Train Set (80%)** | **0.9689** | 219.55 |
| **Test Set (20%)** | **0.9629** | 234.07 |

- The minimal difference ($\Delta R^2 < 0.006$) demonstrates strong generalization on unseen chronological time horizons with zero overfitting.

---

## 6. Exported Production Artifacts
The champion pipeline is saved directly to `src/models/`:
- `traffic_volume_model_pipeline.joblib`: Serialized end-to-end pipeline (preprocessing + XGBoost).
- `traffic_volume_model_metadata.json`: Feature schema definitions and performance benchmark logs.
