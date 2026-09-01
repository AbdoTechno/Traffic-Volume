# Metro Interstate Traffic Volume

A Python project for traffic forecasting, data analysis, and a lightweight web dashboard for predictive road conditions.

## Project goal

This project forecasts hourly vehicle volume on Interstate 94 using historical traffic, weather, holiday, and calendar patterns. The workflow includes:

- data preparation and feature engineering
- model comparison and selection
- production artifact export
- live weather-based prediction through a FastAPI backend
- a simple front-end dashboard for simulation and forecasting

## Tech stack

- Python
- pandas, numpy, scikit-learn
- XGBoost
- FastAPI
- Uvicorn
- requests
- holidays
- HTML, CSS, JavaScript

## Dataset

The project uses the Metro Interstate Traffic Volume dataset from the UCI Machine Learning Repository.

Source:
https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume

Key properties:
- 48,204 hourly rows
- 2012 to 2018 time range
- regression task
- features include temperature, weather, cloud cover, holiday, and time dimensions
- target is traffic_volume

## Model performance

The selected production model is XGBoost.

Final validation metrics:
- MAE: 241.99
- RMSE: 397.13
- R²: 0.9594

## Repository structure

- app/
  - FastAPI application entrypoint and routes
- src/
  - front-end assets and reusable production logic
  - models/ contains saved model artifacts
  - production/ contains feature builder and predictor code
  - utils/ contains shared helper functions
- data/
  - raw/ and processed/ datasets
- docs/
  - reports and supporting documentation
- notebooks/
  - Jupyter workflow for exploration, modeling, and reporting
- reports/
  - outputs and summaries
- requirements.txt
- .env.example
- .gitignore
- Procfile
- railway.json
- runtime.txt

## Local setup

1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies.

Example:

python -m venv .venv

Windows PowerShell:
.\.venv\Scripts\Activate.ps1

Then:

pip install -r requirements.txt

## Environment variables

Create a local file named .env and add:

WEATHER_API_KEY=your_weatherapi_key_here

Do not commit the real key. The project ignores .env automatically.

## Run the API locally

From the project root:

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Then open the app via the browser and use the forecast form or the simulator.

## Production deployment

This project is configured for Railway.

Required environment variable:
- WEATHER_API_KEY

Deployment files:
- Procfile
- railway.json
- runtime.txt

## Notes

- The real environment file is intentionally excluded from Git.
- The template file .env.example is the safe version to share.
- The project uses WeatherAPI for live weather data and a trained pipeline for traffic forecasting.

## License

The dataset is provided under the Creative Commons Attribution 4.0 International license.

## References

- UCI dataset: Metro Interstate Traffic Volume
- WeatherAPI: https://www.weatherapi.com
