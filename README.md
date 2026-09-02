# Metro Interstate Traffic Volume — AI Forecasting Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v2.0-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-R%C2%B2%200.963-orange.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

An end-to-end Machine Learning platform for forecasting hourly traffic volume on Interstate 94 (I-94 westbound between Minneapolis and St. Paul). The system integrates historical traffic patterns, cyclical time dynamics, US public holidays, and live weather forecast APIs into an interactive web dashboard and production REST API.

---

## Table of Contents

- [Project Architecture](#project-architecture)
- [Dataset Overview](#dataset-overview)
- [End-to-End Workflow: What Happens Behind the Scenes](#end-to-end-workflow-what-happens-behind-the-scenes)
- [External Weather API: Data Ingestion & Model Mapping](#external-weather-api-data-ingestion--model-mapping)
- [Machine Learning Modeling & Benchmark](#machine-learning-modeling--benchmark)
- [Project Directory Structure](#project-directory-structure)
- [API Documentation](#api-documentation)
- [Local Setup & Running](#local-setup--running)
- [Production Deployment (Railway)](#production-deployment-railway)
- [Citation & License](#citation--license)

---

## Project Architecture

```
                                  USER INTERFACE
                  [ Live Web Dashboard: index.html + Vanilla JS ]
                                        │
                         HTTP POST /predict (JSON Payload)
                                        │
                                  FASTAPI SERVER
       ┌────────────────────────────────┴────────────────────────────────┐
       ▼                                                                 ▼
[ WeatherClient ]                                             [ FeatureBuilder ]
Fetches live forecast from                                    - Computes US Holidays (holidays.US)
WeatherAPI.com (temp, rain,                                   - Calculates Cyclical Time (sin/cos)
snow, cloud, condition)                                       - Formats Day of Week & Month
       │                                                                 │
       └────────────────────────────────┬────────────────────────────────┘
                                        │
                              [ Feature DataFrame ]
               (11 features matching notebook 04.1 training schema)
                                        │
                                        ▼
                         [ Scikit-Learn Pipeline ]
             StandardScaler (numerics) + OneHotEncoder (categoricals)
                                        │
                                        ▼
                             [ XGBoost Regressor ]
                                        │
                         Hourly Traffic Volume Predictions
                               (Vehicles / Hour)
                                        │
                                        ▼
                  [ Aggregation: Daily Avg, Peak Hour, Status ]
                                        │
                          JSON Response to Dashboard
```

---

## Dataset Overview

Sourced from the **UCI Machine Learning Repository** (ID 492: Metro Interstate Traffic Volume).

- **Total Records:** 48,204 hourly observations (2012 – 2018).
- **Target Variable:** `traffic_volume` (Hourly westbound traffic count on I-94).
- **Evaluation Methodology:** Strict chronological 80/20 train-test split (no data leakage).

| Feature | Role | Type | Unit / Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `holiday` | Feature | Categorical | Text | US national holiday name or `"Not Holiday"` |
| `temp` | Feature | Numerical | Kelvin (K) | Average hourly ambient temperature |
| `rain_1h` | Feature | Numerical | mm | Hourly accumulated rainfall |
| `snow_1h` | Feature | Numerical | mm | Hourly accumulated snowfall |
| `clouds_all`| Feature | Numerical | % (0–100) | Cloud cover percentage |
| `weather_main` | Feature | Categorical | Text | Major weather condition (Clear, Rain, Snow, Clouds...) |
| `day_of_week` | Feature | Categorical | Text | Day name (`Monday`, `Tuesday`, ..., `Sunday`) |
| `hour_sin` / `hour_cos` | Feature | Numerical | [-1, 1] | Cyclical representation of hour (period = 24) |
| `month_sin` / `month_cos` | Feature | Numerical | [-1, 1] | Cyclical representation of month (period = 12) |
| `traffic_volume` | **Target** | Integer | Vehicles/hr | Hourly westbound flow |

---

## End-to-End Workflow: What Happens Behind the Scenes

When a user requests a forecast on the dashboard or via API, here is the step-by-step lifecycle:

```
[1. User Input] ──► [2. API Request] ──► [3. Weather Fetch] ──► [4. Feature Builder] 
                                                                         │
[8. Visual Charts] ◄── [7. Post-Process] ◄── [6. Model Inference] ◄──────┘
```

### Step 1: User Configures the Forecast
- The user selects:
  1. **Start Date** (e.g. `2026-09-03`).
  2. **Horizon** (1 to 3 days).
  3. **City** (e.g. `Minneapolis`, `Chicago`, `Seattle`...).
  4. **Hour Range** using interactive sliders (e.g. from `08:00` to `18:00`).

### Step 2: Client Sends Request
- `src/js/forecast.js` validates that `start_hour <= end_hour` and packages the request into JSON:
  ```json
  {
    "start_date": "2026-09-03",
    "days": 2,
    "city": "Minneapolis",
    "country": "US",
    "start_hour": 8,
    "end_hour": 18
  }
  ```
- The request hits FastAPI's `/predict` route. `app/schemas.py` validates the payload using Pydantic.

### Step 3: Live Weather Retrieval
- `src/production/weather_client.py` makes an authenticated HTTP call to **WeatherAPI.com**:
  `https://api.weatherapi.com/v1/forecast.json?key={KEY}&q={city}&days={days}`
- The API returns hourly weather forecasts (temperature, rain, snow, cloudiness, weather description).

### Step 4: Feature Construction & Mathematical Transformation
- `src/production/feature_builder.py` synthesizes the exact feature vector expected by the model for every $(date \times hour)$ combination:
  1. **Calendar & Holiday Lookup:** Queries the `holidays.US` Python library. If the date is Labor Day or Memorial Day, it returns the official name; otherwise `"Not Holiday"`.
  2. **Weekday Encoding:** Extracts the full weekday name (`"Wednesday"`) for categorical one-hot encoding.
  3. **Cyclical Transformations:** Applies trigonometry to preserve continuity across midnight and year-end:
     $$\text{hour\_sin} = \sin\left(\frac{2\pi \times \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \times \text{hour}}{24}\right)$$
     $$\text{month\_sin} = \sin\left(\frac{2\pi \times \text{month}}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \times \text{month}}{12}\right)$$
  4. **Weather Metrics Alignment:** Converts Celsius to Kelvin ($K = ^\circ\text{C} + 273.15$), extracts rain/snow mm, cloud %, and normalizes weather categories.

### Step 5: Pipeline Transformation & Model Inference
- The pre-trained Scikit-Learn `Pipeline` (`traffic_volume_model_pipeline.joblib`) processes the DataFrame:
  - **StandardScaler:** Scales the 8 numerical features using training mean and standard deviation.
  - **OneHotEncoder (drop='first'):** Encodes `holiday`, `weather_main`, and `day_of_week`. Unknown categories are handled gracefully.
  - **XGBoost Regressor:** Evaluates the ensemble of 300 gradient-boosted trees and generates predictions in vehicles/hour.

### Step 6: Aggregation & Response Delivery
- `app/routers/forecast.py` aggregates predictions:
  - Groups results by date.
  - Computes **daily average volume**.
  - Identifies the **peak congestion hour** and its volume.
  - Returns structured JSON to the client.

### Step 7: Dynamic Visualization on Frontend
- `src/js/forecast.js` renders:
  - **Day Cards:** With overall congestion badges (`Light`, `Normal`, `Moderate`, `Heavy`).
  - **Hourly Bar Charts:** Interactive color-coded horizontal bars proportional to highway capacity (7,280 veh/hr).
  - **Peak Alert:** Highlighting the exact rush-hour peak.

---

## External Weather API: Data Ingestion & Model Mapping

The system integrates real-world meteorological forecasts through [WeatherAPI.com](https://www.weatherapi.com). Here is how raw external API responses map to the model features:

| External API Field (`WeatherAPI`) | Transformation / Processing | Model Feature Name | Model Data Type | Pipeline Processor |
| :--- | :--- | :--- | :--- | :--- |
| `forecastday[i].hour[h].temp_c` | $K = \text{temp\_c} + 273.15$ | `temp` | Continuous (Kelvin) | `StandardScaler` |
| `forecastday[i].hour[h].precip_mm` | Hourly precipitation in mm | `rain_1h` | Continuous (mm) | `StandardScaler` |
| `forecastday[i].hour[h].snow_cm` | Extracted & converted: $\text{cm} \times 10 = \text{mm}$ | `snow_1h` | Continuous (mm) | `StandardScaler` |
| `forecastday[i].hour[h].cloud` | Cloud cover percentage (0–100) | `clouds_all` | Continuous (%) | `StandardScaler` |
| `forecastday[i].hour[h].condition.text` | Mapped via `WEATHER_MAIN_MAP` (`"Sunny"` $\rightarrow$ `"Clear"`, `"Overcast"` $\rightarrow$ `"Clouds"`) | `weather_main` | Categorical | `OneHotEncoder` |
| *Local Date Lookup* | Evaluated via Python `holidays.US` | `holiday` | Categorical | `OneHotEncoder` |
| *Local Date Lookup* | `date.strftime("%A")` | `day_of_week` | Categorical | `OneHotEncoder` |
| *Target Hour Parameter* | $\sin(2\pi h / 24), \cos(2\pi h / 24)$ | `hour_sin`, `hour_cos` | Continuous (Cyclic) | `StandardScaler` |
| *Target Date Parameter* | $\sin(2\pi m / 12), \cos(2\pi m / 12)$ | `month_sin`, `month_cos`| Continuous (Cyclic) | `StandardScaler` |

---

## Machine Learning Modeling & Benchmark

Three model architectures were benchmarked on a chronological 80% train / 20% test split (32,451 training samples, 8,113 test samples) inside `notebooks/04.1_modeling_trial.ipynb`:

| Model Architecture | MAE (Vehicles/hr) | RMSE (Vehicles/hr) | $R^2$ Score | Deployment Status |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost Regressor** (300 trees, lr=0.05, depth=6) | **234.07** | **379.52** | **0.9629** | **Production Champion** |
| Random Forest Regressor (200 trees) | 250.92 | 411.27 | 0.9564 | Runner-up |
| Linear Regression (Baseline) | 821.57 | 1042.94 | 0.7198 | Baseline |

- **Generalization:** Train $R^2 = 0.9689$ vs. Test $R^2 = 0.9629$ confirms zero overfitting.
- **Top Feature Drivers:**
  1. **Hour of day:** Strongest diurnal predictor (bimodal peaks at 8 AM and 5 PM).
  2. **Day of week:** Weekdays exhibit $\sim 1.5\times$ the volume of weekends.
  3. **Weather events:** Heavy snow cuts highway throughput by up to 32%.
  4. **Holidays:** Eliminates the morning rush entirely, flattening volume into a gentle midday curve.

---

## Project Directory Structure

The project is structured into modular layers following clean software architecture:

```text
Traffic Volume/
├── app/                                 # FastAPI Backend Service
│   ├── __init__.py
│   ├── main.py                          # App setup, CORS, static mounts, route inclusion
│   ├── schemas.py                       # Pydantic input/output validation models
│   └── routers/
│       ├── __init__.py
│       └── forecast.py                  # API endpoints (/predict, /predict-single, /api/health)
│
├── notebooks/                           # Research & Exploration Notebooks
│   ├── 00_data_collection.ipynb         # Dataset extraction from UCI repository
│   ├── 01_problem_statement.ipynb       # Business context and objective definition
│   ├── 02_data_cleaning.ipynb           # Outlier treatment, timestamp parsing, deduplication
│   ├── 03_eda.ipynb                     # In-depth visual and statistical exploration
│   ├── 04.1_modeling_trial.ipynb        # Model comparison, tuning, and pipeline export
│   └── 05_conclusion.ipynb              # Findings, recommendations, and future work
│
├── src/                                 # Frontend Assets & Production Machine Learning Code
│   ├── index.html                       # Highway signage dashboard UI
│   ├── styles.css                       # Design system (highway green, amber VMS, responsive)
│   ├── js/                              # Modular JavaScript files
│   │   ├── simulator.js                 # Interactive client-side simulator
│   │   ├── forecast.js                  # Production forecast UI, hour-range sliders, charts
│   │   └── weather-board.js             # Live weather widget & mascot animation
│   ├── models/                          # Exported Model Artifacts
│   │   ├── save_production_artifacts.py # Standalone script to train & export pipeline
│   │   ├── traffic_volume_model_pipeline.joblib # Serialized Scikit-Learn + XGBoost pipeline
│   │   └── traffic_volume_model_metadata.json   # Model parameters and metric logs
│   ├── production/                      # Production Feature Pipeline
│   │   ├── feature_builder.py           # Feature engineering & transformation engine
│   │   ├── predictor.py                 # TrafficPredictor class (inference & range prediction)
│   │   └── weather_client.py            # WeatherAPI HTTP client
│   └── utils/
│       └── helpers.py                   # Shared helper utilities
│
├── tests/                               # Automated Test Suite
│   ├── test_api_endpoints.py            # Route, static file, and prediction tests
│   └── test_environment_alignment.py   # Version pinning tests
│
├── .env.example                         # Environment variables template
├── .gitignore                           # Git ignore rules
├── Procfile                             # Process file for Railway deployment
├── railway.json                         # Railway deployment configuration
├── runtime.txt                          # Python version specification (python-3.12)
├── requirements.txt                     # Pinned project dependencies
└── README.md                            # Comprehensive project documentation
```

---

## API Documentation

### 1. Health Check
`GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "message": "Traffic Volume Forecast API v2 is running"
}
```

### 2. Multi-Day, Hour-Range Prediction
`POST /predict`

**Request Body:**
```json
{
  "start_date": "2026-09-03",
  "days": 2,
  "city": "Minneapolis",
  "country": "US",
  "start_hour": 8,
  "end_hour": 10
}
```

**Response Body:**
```json
{
  "city": "Minneapolis",
  "country": "US",
  "start_date": "2026-09-03",
  "days": 2,
  "start_hour": 8,
  "end_hour": 10,
  "predictions": [
    {
      "date": "2026-09-03",
      "daily_avg": 4452.75,
      "peak_hour": 8,
      "peak_volume": 5021.69,
      "hourly": [
        { "hour": 8, "predicted_traffic_volume": 5021.69 },
        { "hour": 9, "predicted_traffic_volume": 4407.64 },
        { "hour": 10, "predicted_traffic_volume": 3928.92 }
      ]
    },
    {
      "date": "2026-09-04",
      "daily_avg": 4224.76,
      "peak_hour": 8,
      "peak_volume": 4699.53,
      "hourly": [
        { "hour": 8, "predicted_traffic_volume": 4699.53 },
        { "hour": 9, "predicted_traffic_volume": 4121.53 },
        { "hour": 10, "predicted_traffic_volume": 3853.21 }
      ]
    }
  ]
}
```

---

## Local Setup & Running

### 1. Clone & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/AbdoTechno/Traffic-Volume.git
cd "Traffic Volume"

# Create and activate Python virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Weather API Key
Create a `.env` file in the root folder:
```env
WEATHER_API_KEY=your_weatherapi_key_here
```
*(Get a free API key at [weatherapi.com](https://www.weatherapi.com))*

### 4. Run the Application
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Open **`http://127.0.0.1:8000`** in your browser to view the interactive dashboard.
- Interactive API Docs available at **`http://127.0.0.1:8000/docs`**.

### 5. Running with VS Code Live Server
You can also open `src/index.html` using the **Live Server** extension (port 5500). All stylesheets and scripts load via relative paths, and API requests will automatically route to your backend on port 8000.

### 6. Run Automated Tests
```bash
pytest -v
```

---

## Production Deployment (Railway)

The application is fully configured for zero-configuration continuous deployment on [Railway](https://railway.app):

1. **Connect Repo:** Link this GitHub repository to your Railway project.
2. **Set Environment Variable:** In the Railway dashboard under **Variables**, set:
   - `WEATHER_API_KEY`: Your private WeatherAPI key.
3. **Automatic Build & Start:**
   - Railway detects `railway.json` and `runtime.txt` (`python-3.12`).
   - Starts via `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

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
This project and dataset are licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
