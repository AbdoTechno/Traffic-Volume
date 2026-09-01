# Traffic Volume Prediction — Modeling Report

**Author:** Zeina Mostafa Ali

## Problem Classification

This is a **regression problem**, since the target variable — `traffic_volume` — is continuous.

## Data Preparation & Feature Engineering

The cleaned traffic dataset (`traffic_volume_cleaned.csv`) was loaded and prepared as follows:

- **Datetime parsing**: `date_time` was converted to a proper datetime type, and the data was sorted chronologically.
- **Derived time features**: `year` and a numeric day-of-week (`day_of_week_num`) were extracted from `date_time`.
- **Cyclical encoding**: hour, month, and day-of-week were encoded using sine/cosine transforms (`hour_sin`/`hour_cos`, `month_sin`/`month_cos`, `day_sin`/`day_cos`) so the model understands that, for example, 11 PM and midnight are close together rather than far apart numerically.
- **Holiday encoding**: the `holiday` column was converted into a simple binary flag (`1` = holiday, `0` = not holiday).
- **Feature/target split**: redundant or non-numeric columns (`date_time`, raw `hour`, `month`, `day_of_week`, `day_of_week_num`) were dropped in favor of their cyclical/derived versions, leaving a clean feature set `X` and target `y`.

## Train/Test Split

Since this is time-ordered data, a **chronological (time-based) split** was used instead of a random split — the earliest 80% of records were used for training and the most recent 20% for testing. This mirrors how the model would actually be used in practice: predicting future traffic from past patterns.

## Preprocessing

A shared preprocessing pipeline was built with `ColumnTransformer`:

- **Numerical features** (`holiday`, `temp`, `rain_1h`, `snow_1h`, `clouds_all`, `year`, and the cyclical hour/month/day features) were standardized with `StandardScaler`.
- **Categorical feature** (`weather_main`) was one-hot encoded with `OneHotEncoder`.

This same preprocessor was reused inside every model's pipeline to keep the comparison fair and consistent.

## Model Selection

Three regression models were trained and compared:

1. **Linear Regression** — a simple baseline to establish how much of the variance can be explained linearly.
2. **Random Forest Regressor** — an ensemble of decision trees, able to capture nonlinear relationships and feature interactions.
3. **XGBoost Regressor** — a gradient-boosted tree ensemble, generally strong on tabular data with mixed numeric/categorical features.

## Evaluation & Validation

Each model was evaluated on the held-out test set using three metrics:

- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **R²** (coefficient of determination)

| Model | MAE | RMSE | R² |
|---|---|---|---|
| **XGBoost** | 242.0 | 397.1 | **0.959** |
| Random Forest | 254.1 | 419.9 | 0.955 |
| Linear Regression | 837.6 | 1077.5 | 0.701 |

## Best Model

**XGBoost** was selected as the final model. It achieved the lowest error (MAE and RMSE) and the highest R² (≈0.96), meaning it explains about 96% of the variance in traffic volume on unseen data. Random Forest performed nearly as well, while Linear Regression lagged significantly behind — expected, since traffic volume depends on nonlinear interactions between time of day, weather, and holidays that a purely linear model cannot capture.
