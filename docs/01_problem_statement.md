# 01 - Problem Statement & Project Scoping

## Project Overview
This project formulates an end-to-end Machine Learning pipeline to analyze and forecast hourly westbound traffic volume on Interstate 94 (I-94) between Minneapolis and St. Paul, Minnesota, utilizing the Metro Interstate Traffic Volume dataset from the UCI Machine Learning Repository.

## Business Problem & Context
Traffic congestion in metropolitan transit corridors causes severe economic loss, excess fuel consumption and emissions, and unpredictable commute delays. Transportation authorities and commuters require accurate, forward-looking traffic flow predictions that account for time-of-day dynamics, day-of-week rhythms, calendar holidays, and severe Midwestern weather patterns (snow, freezing rain, extreme temperature drops).

## Research Questions
1. How do diurnal commute patterns (rush hours) differ between weekdays, weekends, and holidays?
2. To what degree do adverse meteorological conditions (precipitation, snow, temperature extremes) depress traffic capacity?
3. Which regression algorithms (Ridge/Lasso, Random Forest, XGBoost, LightGBM) deliver the highest forecasting precision on unseen future time horizons?

## Target & Success Metrics
- **Target Variable:** `traffic_volume` (Hourly vehicle count).
- **Evaluation Criteria:**
  - $R^2 \ge 0.90$
  - Mean Absolute Error (MAE) in vehicles/hour.
  - Root Mean Squared Error (RMSE) to penalize outlier deviations.

## Next Stage
Proceed to `notebooks/01_data_collection.ipynb` for automated data ingestion via `ucimlrepo` and local raw storage.
