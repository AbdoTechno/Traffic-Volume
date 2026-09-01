# Metro Interstate Traffic Volume

A polished end-to-end machine learning project for forecasting hourly traffic volume on Interstate 94, combining historical traffic patterns, weather conditions, public holidays, and production-ready prediction APIs.

## Project Overview

This project covers the full lifecycle of a traffic forecasting workflow:

- data acquisition and cleaning
- exploratory data analysis
- feature engineering and cyclical time encoding
- model comparison and selection
- production artifact export
- live weather-driven forecasting via FastAPI
- a lightweight front-end dashboard for simulation and prediction

The goal is to estimate traffic volume using historical signals such as time-of-day, weekday structure, weather, and holiday periods.

---

## Dataset Characteristics

The dataset is sourced from the UCI Machine Learning Repository.

| Property | Value |
| :--- | :--- |
| Dataset Source | [UCI Machine Learning Repository - Metro Interstate Traffic Volume](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume) |
| Dataset Type | Multivariate, sequential, time-series |
| Task | Regression |
| Total Records | 48,204 |
| Time Range | 2012 - 2018 |
| Missing Values | None |
| Target | traffic_volume |

---

## Data Dictionary

| Variable | Role | Type | Description |
| :--- | :--- | :--- | :--- |
| holiday | Feature | Categorical | Holiday or non-holiday indicator |
| temp | Feature | Continuous | Average hourly temperature |
| rain_1h | Feature | Continuous | Rainfall amount in the last hour |
| snow_1h | Feature | Continuous | Snowfall amount in the last hour |
| clouds_all | Feature | Integer | Cloud cover percentage |
| weather_main | Feature | Categorical | General weather condition |
| date_time | Feature | Datetime | Timestamp of the record |
| traffic_volume | Target | Integer | Hourly westbound traffic volume |

---

## Modeling Summary

The final production model selected for deployment is XGBoost.

Validation metrics:

- MAE: 241.99
- RMSE: 397.13
- R²: 0.9594

This makes it the strongest performer among the benchmarked models.

---

## Project Structure

```text
Traffic Volume/
├── app/
│   └── main.py                 # FastAPI app and prediction endpoints
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   └── project documentation
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_modeling.ipynb
│   └── 04_modeling_final.ipynb
├── reports/
├── src/
│   ├── index.html
│   ├── script.js
│   ├── styles.css
│   ├── models/
│   ├── production/
│   └── utils/
├── .env.example
├── .gitignore
├── Procfile
├── railway.json
├── runtime.txt
├── README.md
├── requirements.txt
└── deploy_checklist.md
```

---

## Tech Stack

- Python
- pandas
- numpy
- scikit-learn
- XGBoost
- FastAPI
- Uvicorn
- requests
- holidays
- HTML, CSS, JavaScript

---

## Local Setup

1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install requirements:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a local `.env` file with the weather provider key:

```env
WEATHER_API_KEY=your_weatherapi_key_here
```

Important:
- do not commit the real key
- the project ignores `.env` through `.gitignore`
- use `.env.example` as the template

---

## Running the API Locally

From the project root:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open the application in the browser and use the forecast form or simulator.

---

## API Usage

### Health check

```bash
curl http://127.0.0.1:8000/
```

Example response:

```json
{"message":"Traffic Volume Forecast API is running"}
```

### Prediction request

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-09-01",
    "days": 2,
    "city": "Minneapolis",
    "country": "US",
    "hour": 12
  }'
```

Example response:

```json
{
  "city": "Minneapolis",
  "country": "US",
  "start_date": "2026-09-01",
  "days": 2,
  "hour": 12,
  "predictions": [
    {
      "date": "2026-09-01",
      "hour": 12,
      "predicted_traffic_volume": 4220.05
    },
    {
      "date": "2026-09-02",
      "hour": 12,
      "predicted_traffic_volume": 3810.66
    }
  ]
}
```

---

## Weather Provider

The project uses the WeatherAPI service at:

https://api.weatherapi.com/v1

and expects the key in the environment variable `WEATHER_API_KEY`.

---

## Deployment

This project is configured for Railway deployment.

Required environment variable:
- WEATHER_API_KEY

Deployment files:
- Procfile
- railway.json
- runtime.txt

---

## Analytical Workflow

1. Data acquisition and extraction
2. Cleaning and preprocessing
3. Feature engineering and cyclic temporal encoding
4. Model training and comparison
5. Selection of the best-performing regressor
6. Saving production artifacts
7. Weather-based prediction via FastAPI

---

## Citation

If you use this dataset or code in your research or project, please cite:

```bibtex
@misc{hogue_2019_metro_traffic,
  author       = {John Hogue},
  title        = {{Metro Interstate Traffic Volume}},
  year         = {2019},
  howpublished = {UCI Machine Learning Repository},
  doi          = {10.24432/C5X60B},
  note         = {Licensed under CC BY 4.0}
}
```

---

## License

This dataset is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.

---

## References

- UCI dataset: Metro Interstate Traffic Volume
- WeatherAPI: https://www.weatherapi.com
