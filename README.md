# Metro Interstate Traffic Volume — Hybrid AI Forecasting Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v2.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Tabular XGBoost](https://img.shields.io/badge/Tabular_XGBoost-R%C2%B2%200.963%20%7C%20MAE%20234-orange.svg)](https://xgboost.readthedocs.io/)
[![Time-Series Lag-XGBoost](https://img.shields.io/badge/Lag_XGBoost-R%C2%B2%200.986%20%7C%20MAE%20147-brightgreen.svg)](https://xgboost.readthedocs.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20Dual--Engine-purple.svg)](#hybrid-production-architecture)
[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

An end-to-end, production-grade Machine Learning and Time-Series platform for forecasting hourly traffic volume on **Interstate 94 (I-94 westbound between Minneapolis and St. Paul, Minnesota)**. 

The platform deploys an **Intelligent Hybrid Dual-Engine**:
1. **AutoRegressive Lag-XGBoost Engine ($R^2 = 0.9864, \text{MAE} = 146.71$):** Captures real-time highway momentum and short-term traffic inertia for immediate nowcasting when live sensor readings are available.
2. **Tabular XGBoost Engine ($R^2 = 0.9629, \text{MAE} = 234.07$):** Provides drift-free, multi-day advance trip planning (1–3 days ahead) by leveraging cyclical temporal harmonics, US holiday schedules, and weather forecast APIs without recursive error compounding.

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Hybrid Production Architecture](#hybrid-production-architecture)
- [Dataset Overview & The 22.8% Missing Data Challenge](#dataset-overview--the-228-missing-data-challenge)
- [Machine Learning & Time-Series Benchmarks](#machine-learning--time-series-benchmarks)
- [End-to-End Operational Workflow & Scenarios](#end-to-end-operational-workflow--scenarios)
- [External Weather Ingestion & Historical Benchmark Engine](#external-weather-ingestion--historical-benchmark-engine)
- [Project Directory Structure](#project-directory-structure)
- [REST API Reference](#rest-api-reference)
- [Local Installation & Execution](#local-installation--execution)
- [Automated Testing & Quality Assurance](#automated-testing--quality-assurance)
- [Production Deployment (Railway)](#production-deployment-railway)
- [Citation & License](#citation--license)

---

## Executive Summary

Metropolitan highway congestion incurs massive economic losses in fuel consumption, carbon emissions, and transit delays. While tabular machine learning models excel at capturing broad seasonal and calendar dynamics, they treat each hour as an independent point, ignoring the physical inertia of traffic flow (what happened 1 or 2 hours ago). Conversely, classical time-series models (like ARIMA) fail over multi-day horizons due to **recursive error compounding drift** and cannot easily digest exogenous multi-variable weather signals.

This platform bridges both paradigms into a unified, high-availability web service:
- **Real-Time Highway Management:** Operators can feed current loop detector counts to achieve pinpoint short-term precision (**146.71 vehicles/hour MAE**, a **37.3% error reduction** over standard ML).
- **Advance Commuter Planning:** Travelers can schedule trips 72 hours in advance based solely on calendar and weather forecasts with **zero autoregressive drift**.
- **Graceful Degradation (Fail-Safe):** If highway detector telemetry disconnects, the system automatically routes to the tabular engine with zero downtime.

---

## Hybrid Production Architecture

```
                                  USER / CLIENT REQUEST
                 POST /predict (start_date, days, start_hour, end_hour, current_volume?)
                                            │
                                            ▼
                                   FASTAPI WEB SERVER
                     [ app/routers/forecast.py · Validation via Pydantic ]
                                            │
                                            ▼
                                DUAL-ENGINE SMART ROUTER
                               [ src/production/predictor.py ]
                                            │
                ┌───────────────────────────┴───────────────────────────┐
                │                                                       │
  [ Scenario A: Real-Time Momentum ]                     [ Scenario B: Advance Planning ]
    Day 1 (t <= 24h) + Live Sensor                          Days 2–3 OR Sensor Disconnected
                │                                                       │
                ▼                                                       ▼
      [ FeatureBuilder ]                                      [ FeatureBuilder ]
  - Extracts Lags: y(t-1), y(t-2), y(t-24)               - Computes Cyclical (sin/cos hour, month)
  - Computes rolling 3h stats                            - Queries US Federal Holidays
  - Integrates weather & calendar                        - Formats weekday & weather features
                │                                                       │
                ▼                                                       ▼
  [ Engine A: AutoRegressive Lag-XGBoost ]                [ Engine B: Tabular XGBoost ]
  traffic_volume_lag_pipeline.joblib                     traffic_volume_model_pipeline.joblib
  MAE: 146.71 veh/hr  |  R²: 0.9864                      MAE: 234.07 veh/hr  |  R²: 0.9629
  (Captures live commute wave)                           (Zero recursive error accumulation)
                │                                                       │
                └───────────────────────────┬───────────────────────────┘
                                            │
                                            ▼
                               [ UNIFIED RESPONSE SYNTHESIZER ]
                  - Merges hourly predictions with transparent `model_used` tags
                  - Calculates daily averages and peak congestion alerts
                  - Response latency: < 45 ms
                                            │
                                            ▼
                               [ LIVE WEB DASHBOARD / CLIENT ]
                 - Highway Signage UI, color-coded hourly bars, peak warnings
                 - Model badges: "Lag-XGBoost (Time-Series)" vs "Tabular XGBoost"
```

---

## Dataset Overview & The 22.8% Missing Data Challenge

The model was trained and evaluated on the **UCI Machine Learning Repository** dataset (ID 492: *Metro Interstate Traffic Volume*), collected from an automated inductive loop detector on I-94 westbound near Minneapolis–St. Paul.

### Chronological Span & Summary Statistics
- **Date Range:** 2012-10-02 to 2018-09-30 (6 full calendar years).
- **Highway Capacity:** Peak observed capacity reaches **7,280 vehicles/hour**.
- **Average Flow:** 3,291 vehicles/hour (Median: 3,429, Std Dev: 1,985).
- **Split Strategy:** Strict chronological 80% train / 20% test split (Test set = 8,113 consecutive hours in 2017–2018, completely free of lookahead bias).

### The Missing Data Challenge & 4-Step Resolution Pipeline
Across the 6-year period, the chronological timeline should theoretically contain **52,551 hourly intervals**. However, the raw recorded data contained only **40,564 hours**—meaning **11,987 hours (22.8%) were missing** due to sensor power outages, optical line maintenance, and road resurfacing on I-94.

In traditional time-series modeling, naive row shifting (`shift(1)`) creates severe data corruption (e.g., row $i-1$ could physically be from 3 days earlier). We solved this via a dedicated 4-step pipeline:

```
[1. Timeline Regularization] ──► [2. Domain-Specific Imputation] ──► [3. ACF-Guided Lags] ──► [4. Supervised ML Formulation]
  resample('1h').asfreq()          fillna(0) for rain/snow           Lag 1 (r=0.926), Lag 2        XGBoost tree splits handle
  Constructs uniform 52,551        time-spline for temp/clouds       Lag 24 (daily), Lag 168       missing gaps natively without
  hour physical grid (dt=1h)       Forward fill for weather          3h rolling mean/std           ARMA matrix inversion crashes
```

1. **Timeline Regularization:** Applied `df.resample('1h').asfreq()` to enforce an unbroken 52,551-hour index.
2. **Domain-Specific Imputation:**
   - `rain_1h` & `snow_1h`: Imputed with `0.0` (absence of precipitation records corresponds to dry weather).
   - `temp` & `clouds_all`: Time-weighted interpolation (`interpolate(method='time')`) to preserve natural diurnal temperature curves.
   - `weather_main`: Forward/backward filled to preserve meteorological system continuity.
3. **Autocorrelation-Driven Lag Engineering:** Analyzed the Autocorrelation Function (ACF) to extract physically meaningful intervals:
   - **Immediate Momentum:** $\text{Lag}_1$ ($r = 0.9259$) & $\text{Lag}_2$ ($r = 0.7643$).
   - **Diurnal Commute Periodicity:** $\text{Lag}_{24}$ ($r = 0.8594$) — yesterday at the exact same hour.
   - **Weekly Periodicity:** $\text{Lag}_{168}$ ($r = 0.9080$) — same day and hour of the previous week.
   - **Intraday Smoothing:** 3-hour rolling mean and rolling standard deviation.
4. **Supervised ML Formulation:** By formulating time-series forecasting as supervised regression with gradient-boosted trees (XGBoost), tree threshold splits handle non-linear interactions natively and remain completely resilient to historical sensor gaps.

---

## Machine Learning & Time-Series Benchmarks

Both candidate models were evaluated on the identical held-out test split (8,113 hours):

### 1. Time-Series Benchmark (Notebook 04.2)
| Model Architecture | Methodology | MAE (Veh/hr) | RMSE (Veh/hr) | $R^2$ Score | Error Reduction vs Baseline |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **AutoRegressive Lag-XGBoost** | **Lags + Rolling Stats + Weather** | **146.71** | **227.87** | **0.9864** | **-37.3% MAE** (Champion) |
| Tabular XGBoost | Cyclical Calendar + Weather | 234.07 | 373.84 | 0.9629 | Tabular Baseline |
| Facebook Prophet | Additive Model with US Holidays | 469.70 | 692.15 | 0.9120 | Moderate Accuracy |
| Naive Persistence ($y_{t-1}$) | Prior hour shifted forward | 687.90 | 1084.20 | 0.8210 | High Error |
| SARIMAX(1,0,1) + Exogenous | Classical State-Space Model | 760.30 | 1022.40 | 0.8841 | Collapses on Non-linearities |

### 2. Tabular ML Benchmark (Notebook 04.1)
| Model Architecture | MAE (Veh/hr) | RMSE (Veh/hr) | $R^2$ Score | Execution Latency |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost Regressor** (300 trees, lr=0.05, depth=6) | **234.07** | **373.84** | **0.9629** | < 15 ms |
| Random Forest Regressor (200 trees) | 250.92 | 411.27 | 0.9564 | $\sim 85$ ms |
| Ridge Regression (L2 Regularized) | 821.57 | 1042.94 | 0.7198 | < 5 ms |

---

## End-to-End Operational Workflow & Scenarios

The web application supports 3 distinct operational scenarios:

### Scenario 1: Real-Time Traffic Operations (Nowcasting with Live Sensor)
- **User Action:** The traffic operator enters the target date, specifies an hour range (e.g. 14:00 to 18:00), and provides the current detector count in **Live Traffic Sensor ($y_{t-1}$)** (e.g., `3888` veh/hr).
- **Backend Flow:** The `TrafficPredictor` gateway detects `current_volume`. For Day 1, it synthesizes `lag_1 = 3888`, computes rolling estimates, and invokes `traffic_volume_lag_pipeline.joblib`.
- **Outcome:** The user receives a high-precision prediction labeled `Lag-XGBoost (Time-Series)` with an expected error margin of only $\sim 146$ vehicles/hour.

### Scenario 2: Multi-Day Advance Trip Planning (No Sensor Required)
- **User Action:** A commuter selects a future 3-day travel window without entering a sensor reading.
- **Backend Flow:** The router routes all days to `traffic_volume_model_pipeline.joblib`. The feature builder fetches weather forecasts from WeatherAPI.com and generates cyclical time features.
- **Outcome:** A drift-free 72-hour forecast with zero recursive error accumulation, labeled `Tabular XGBoost`.

### Scenario 3: Historical Validation on 2018 Test Data (1-Click Benchmarking)
- **User Action:** The user clicks any of the **Quick 2018 Test Samples** buttons on the dashboard (e.g. *Weekday Morning Rush*, *Snowstorm*, *Sunday Leisure*).
- **Backend Flow:** The backend recognizes the 2018 historical date, automatically retrieves the true recorded historical weather from `traffic_volume_cleaned.csv`, and compares the prediction against the actual recorded ground truth.
- **Reference File:** Pre-compiled test scenarios are documented in [`data/test_samples_2018.json`](file:///d:/SIC/Traffic%20Volume/data/test_samples_2018.json).

---

## External Weather Ingestion & Historical Benchmark Engine

Meteorological data is dynamically ingested and mapped into the model feature space:

| Source API / Input Field | Engineering & Transformation | Model Feature | Representation |
| :--- | :--- | :--- | :--- |
| `hour.temp_c` | Auto-converted: $K = ^\circ\text{C} + 273.15$ (Values $< 200$ treated as Celsius) | `temp` | Continuous (Kelvin) |
| `hour.precip_mm` | Hourly liquid precipitation | `rain_1h` | Continuous (mm) |
| `hour.snow_cm` | Extracted & converted: $\text{cm} \times 10 = \text{mm}$ | `snow_1h` | Continuous (mm) |
| `hour.cloud` | Percentage cloud coverage (0–100) | `clouds_all` | Continuous (%) |
| `hour.condition.text` | Normalized via `WEATHER_MAIN_MAP` (`Sunny` $\rightarrow$ `Clear`, etc.) | `weather_main` | Categorical |
| System Calendar | Python `holidays.US` lookup across all 24 hours of holiday dates | `holiday` | Categorical |
| System Calendar | Day name string (`Monday`, `Tuesday`, ...) | `day_of_week` | Categorical |
| Target Hour / Month | $\sin, \cos$ harmonic functions preserving cyclic continuity | `hour_sin`, `month_cos` | Continuous $[-1, 1]$ |

---

## Project Directory Structure

```text
Traffic Volume/
├── app/                                 # FastAPI Backend Application
│   ├── __init__.py
│   ├── main.py                          # App setup, CORS middleware, static mounts, route inclusion
│   ├── schemas.py                       # Pydantic models (ForecastRequest with optional current_volume)
│   └── routers/
│       ├── __init__.py
│       └── forecast.py                  # Endpoints (/predict, /predict-single, /api/health)
│
├── data/                                # Data Storage Layer
│   ├── raw/                             # Original raw UCI CSV dataset
│   ├── processed/                       # Cleaned dataset (traffic_volume_cleaned.csv - 40,564 rows)
│   └── test_samples_2018.json           # Curated 2018 ground-truth test cases for live verification
│
├── docs/                                # Technical Documentation & Slide Guides
│   ├── 01_problem_statement.md          # Business problem & objectives
│   ├── 02_data_cleaning.md              # Deduplication, outlier filtering, 0K correction
│   ├── 03_eda.md                        # Exploratory data analysis insights
│   ├── 04.2_time_series_report.md       # Comprehensive Time-Series & Hybrid modeling report
│   ├── 06_presentation.md               # Presentation outline & slide breakdown
│   ├── 08_hybrid_deployment_slide.md    # Defense notes & architecture for Slide 16 (Hybrid)
│   ├── 09_timeseries_missing_data_slide.md # Defense notes & architecture for Slide 14 (Time-Series)
│   ├── how_to_present_slides_ar.md      # Egyptian Arabic speaking script & Q&A defense guide
│   └── how_to_test_guide.md             # Complete step-by-step verification guide
│
├── notebooks/                           # Research & Development Jupyter Notebooks
│   ├── 00_data_collection.ipynb         # Data retrieval from UCI repository
│   ├── 01_problem_statement.ipynb       # Project framing and cost analysis
│   ├── 02_data_cleaning.ipynb           # Cleaning, deduplication, cyclical encoding
│   ├── 03_eda.ipynb                     # Autocorrelation, distributions, heatmaps
│   ├── 04.1_modeling_trial.ipynb        # Tabular model comparison (Ridge, RF, XGBoost)
│   ├── 04.2_time_series_modeling.ipynb  # Regularization, ACF/PACF, SARIMAX, Lag-XGBoost
│   └── 05_conclusion.ipynb              # Final synthesis, findings, and future roadmap
│
├── reports/                             # Presentations, Figures & Visualizations
│   ├── visualizations/                  # High-resolution architectural diagrams (300 DPI)
│   │   ├── hybrid_architecture_diagram.png       # Slide 16 hybrid architecture visual
│   │   └── timeseries_missing_data_diagram.png   # Slide 14 missing data resolution visual
│   └── Traffic_Volume_Presentation.pptx # Official PowerPoint presentation (20 slides)
│
├── src/                                 # Production Source Code & Web Assets
│   ├── index.html                       # Responsive web dashboard (clean UI, 0 emojis)
│   ├── styles.css                       # Modern highway signage design system
│   ├── js/                              # Frontend scripts
│   │   ├── forecast.js                  # Simulator controller, model badges, 2018 presets
│   │   ├── weather-board.js             # Live weather widget
│   │   └── navigation.js                # Responsive navigation drawer
│   ├── models/                          # Serialized Model Artifacts
│   │   ├── traffic_volume_model_pipeline.joblib   # Champion Tabular XGBoost pipeline
│   │   ├── traffic_volume_model_metadata.json     # Tabular metadata (R² = 0.9629)
│   │   ├── traffic_volume_lag_pipeline.joblib     # Champion Lag-XGBoost pipeline
│   │   └── traffic_volume_lag_metadata.json       # Lag metadata (R² = 0.9864)
│   └── production/                      # Inference Engine
│       ├── feature_builder.py           # Multi-mode feature builder (Tabular + Lag vectors)
│       ├── predictor.py                 # TrafficPredictor dual-engine class
│       └── weather_client.py            # WeatherAPI.com client with historical fallback
│
├── tests/                               # Automated Test Suite
│   ├── test_api_endpoints.py            # Route, schema validation, and prediction tests
│   └── test_environment_alignment.py   # Version pinning & artifact integrity tests
│
├── .env.example                         # Environment template
├── .gitignore                           # Git ignore rules (protects presentation artifacts)
├── Procfile                             # Web process definition for Railway
├── railway.json                         # Deployment configuration
├── requirements.txt                     # Pinned project dependencies
└── runtime.txt                          # Python version definition (python-3.12)
```

---

## REST API Reference

### 1. Health Check
```http
GET /api/health
```
**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Traffic Volume Forecast API v2 is running"
}
```

### 2. Multi-Day Hybrid Traffic Forecast
```http
POST /predict
Content-Type: application/json
```

**Request Payload:**
```json
{
  "start_date": "2018-09-24",
  "days": 2,
  "city": "Minneapolis",
  "country": "US",
  "start_hour": 7,
  "end_hour": 9,
  "current_volume": 4750.0
}
```

**Response Payload (200 OK):**
```json
{
  "city": "Minneapolis",
  "country": "US",
  "start_date": "2018-09-24",
  "days": 2,
  "start_hour": 7,
  "end_hour": 9,
  "current_volume": 4750.0,
  "engine": "Hybrid (Time-Series Lag + Tabular)",
  "predictions": [
    {
      "date": "2018-09-24",
      "daily_avg": 4680.15,
      "peak_hour": 7,
      "peak_volume": 5210.40,
      "primary_model": "Lag-XGBoost (Time-Series)",
      "hourly": [
        { "hour": 7, "predicted_traffic_volume": 5210.40, "model_used": "Lag-XGBoost (Time-Series)" },
        { "hour": 8, "predicted_traffic_volume": 4815.10, "model_used": "Lag-XGBoost (Time-Series)" },
        { "hour": 9, "predicted_traffic_volume": 4014.95, "model_used": "Lag-XGBoost (Time-Series)" }
      ]
    },
    {
      "date": "2018-09-25",
      "daily_avg": 4520.30,
      "peak_hour": 7,
      "peak_volume": 5080.20,
      "primary_model": "Tabular XGBoost",
      "hourly": [
        { "hour": 7, "predicted_traffic_volume": 5080.20, "model_used": "Tabular XGBoost" },
        { "hour": 8, "predicted_traffic_volume": 4710.50, "model_used": "Tabular XGBoost" },
        { "hour": 9, "predicted_traffic_volume": 3770.20, "model_used": "Tabular XGBoost" }
      ]
    }
  ]
}
```

---

## Local Installation & Execution

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/AbdoTechno/Traffic-Volume.git
cd "Traffic Volume"

# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate on Linux / macOS
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure WeatherAPI Key
Create a `.env` file in the project root:
```env
WEATHER_API_KEY=your_actual_weatherapi_key_here
```
*(Get a free key at [WeatherAPI.com](https://www.weatherapi.com). If testing 2018 historical benchmark dates, the system automatically uses real historical dataset weather even if no key is configured).*

### 4. Start the Application Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Web Dashboard:** Open [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** Open [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **Alternative (Live Server):** You can also preview `src/index.html` via VS Code Live Server (`http://127.0.0.1:5500/src/index.html`), which connects seamlessly to the backend on port 8000.

---

## Automated Testing & Quality Assurance

Run the automated test suite to verify routes, schema validation, model inference, and artifact integrity:
```bash
pytest -v
```
All 9 unit and integration tests execute with zero failures:
```text
tests/test_api_endpoints.py::test_health_check PASSED
tests/test_api_endpoints.py::test_predict_endpoint PASSED
tests/test_api_endpoints.py::test_predict_invalid_hour_range PASSED
tests/test_api_endpoints.py::test_static_index_serves_html PASSED
tests/test_api_endpoints.py::test_static_css_serves_stylesheet PASSED
tests/test_api_endpoints.py::test_static_js_serves_javascript PASSED
tests/test_api_endpoints.py::test_404_on_nonexistent_route PASSED
tests/test_environment_alignment.py::test_requirements_exist PASSED
tests/test_environment_alignment.py::test_procfile_format PASSED
```

---

## Production Deployment (Railway)

The application is production-ready for automated continuous deployment on [Railway](https://railway.app):

1. **Push Repository:** Push your code to your GitHub repository.
2. **Create Railway Service:** Select **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. **Configure Environment Variable:** In the Railway dashboard under **Variables**, set:
   - `WEATHER_API_KEY`: Your WeatherAPI secret key.
4. **Zero-Config Build:** Railway automatically detects `railway.json`, `runtime.txt` (`python-3.12`), and `Procfile`:
   ```text
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

---

## Citation & License

### Dataset Citation
```bibtex
@misc{hogue_2019_metro_traffic,
  author       = {John Hogue},
  title        = {{Metro Interstate Traffic Volume}},
  year         = {2019},
  howpublished = {UCI Machine Learning Repository},
  doi          = {10.24432/C5X60B},
  note         = {Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)}
}
```

### License
This project and dataset are distributed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
