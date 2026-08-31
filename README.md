# Metro Interstate Traffic Volume Analysis & Prediction

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-orange.svg?logo=jupyter&logoColor=white)](https://jupyter.org/)
[![Dataset](https://img.shields.io/badge/UCI%20Repo-ID%20492-brightgreen.svg?logo=databricks&logoColor=white)](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## Project Overview

This project provides an end-to-end Machine Learning and Exploratory Data Analysis (EDA) pipeline for forecasting and analyzing **hourly westbound traffic volume** on Interstate 94 (I-94) between Minneapolis and St. Paul, Minnesota.

By combining historical traffic records with hourly weather conditions, seasonal patterns, and calendar holidays (2012–2018), this study aims to uncover the primary drivers of traffic congestion and build accurate regression models to forecast traffic flow.

---

## Dataset Characteristics

The dataset was obtained from the **UCI Machine Learning Repository** (donated by John Hogue, MN DoT ATR station 301).

| Property | Value |
| :--- | :--- |
| **Dataset Source** | [UCI ML Repository - Metro Interstate Traffic Volume](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume) |
| **Dataset Type** | Multivariate, Sequential, Time-Series |
| **Associated Task** | Regression |
| **Total Instances** | 48,204 rows |
| **Total Features** | 8 Features + 1 Target Variable |
| **Missing Values** | None (0 missing values across all columns) |
| **Time Range** | 2012 – 2018 (Hourly records in local CST) |

---

## Data Dictionary & Schema

| Variable Name | Role | Data Type | Description | Units / Format |
| :--- | :--- | :--- | :--- | :--- |
| `holiday` | Feature | Categorical | US National holidays and regional holidays (e.g., Minnesota State Fair) | Text (`None` or Holiday Name) |
| `temp` | Feature | Continuous | Average hourly temperature | Kelvin ($K$) |
| `rain_1h` | Feature | Continuous | Amount of rainfall that occurred during the hour | Millimeters ($mm$) |
| `snow_1h` | Feature | Continuous | Amount of snowfall that occurred during the hour | Millimeters ($mm$) |
| `clouds_all` | Feature | Integer | Percentage of cloud coverage | Percentage ($0 - 100\%$) |
| `weather_main` | Feature | Categorical | Short summary of the current weather category (e.g., Clear, Rain, Snow, Clouds) | Text |
| `weather_description` | Feature | Categorical | Granular textual description of the weather (e.g., light rain, sky is clear) | Text |
| `date_time` | Feature | DateTime | Timestamp of data collection (local CST time) | `YYYY-MM-DD HH:MM:SS` |
| **`traffic_volume`** | **Target** | **Integer** | **Reported westbound hourly traffic volume** | **Vehicles per hour** |

---

## Project Structure

```text
Traffic Volume/
├── data/
│   ├── raw/                      # Original downloaded dataset (CSV / GZ)
│   └── processed/                # Cleaned, engineered, and scaled data
├── docs/                         # Additional documentation and notes
├── notebooks/                    # Sequential Jupyter notebooks for the pipeline
│   ├── 01_problem_statement.ipynb # Problem definition & project scoping
│   ├── 01_data_collection.ipynb   # Ingestion via UCI API / raw download
│   ├── 02_data_cleaning.ipynb     # Outlier handling & datetime transformations
│   ├── 03_eda.ipynb               # Exploratory data analysis & visualizations
│   ├── 04_modeling.ipynb          # Feature engineering, model training & tuning
│   ├── 05_conclusion.ipynb        # Model evaluation, metrics & takeaways
│   └── 06_presentation.ipynb      # Executive summaries & key visual charts
├── reports/                      # Final reports, exported figures, and presentations
├── src/                          # Reusable Python helper scripts & utility modules
├── README.md                     # Project documentation & landing page
└── requirements.txt              # Environment dependencies
```

---

## Analytical & Modeling Workflow

1. **Data Acquisition & Extraction:**
   - Programmatically fetch data using `ucimlrepo` or from `data/raw/`.
2. **Data Cleaning & Preprocessing:**
   - Identify anomalous records (e.g., zero Kelvin temperatures, sensor spikes).
   - Date-time feature decomposition (Hour, Day of Week, Month, Year, Rush Hour indicator).
3. **Exploratory Data Analysis (EDA):**
   - Diurnal traffic cycles (rush hours: morning 7-9 AM vs. evening 4-6 PM).
   - Weekend vs. Weekday traffic volume distribution.
   - Weather impact (heavy snow, freezing rain vs. clear skies).
4. **Machine Learning & Modeling:**
   - Baselines: Ridge / Lasso Regression.
   - Non-linear & Ensemble Models: Random Forest Regressor, XGBoost, LightGBM, CatBoost.
   - Evaluation Metrics: $R^2$ Score, Mean Absolute Error (MAE), Root Mean Squared Error (RMSE).

---

## Getting Started

### 1. Clone & Set Up the Environment

```bash
# Clone the repository
git clone https://github.com/AbdoTechno/Traffic-Volume.git
cd Traffic-Volume

# Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Fetching Data with `ucimlrepo`

```python
from ucimlrepo import fetch_ucirepo 

# Fetch dataset by ID
metro_interstate_traffic_volume = fetch_ucirepo(id=492) 

# Extract features and target as pandas DataFrames
X = metro_interstate_traffic_volume.data.features 
y = metro_interstate_traffic_volume.data.targets 

# View metadata & variable details
print(metro_interstate_traffic_volume.metadata)
print(metro_interstate_traffic_volume.variables)
```

### 3. Running the Notebooks

Launch Jupyter Lab / Notebooks:
```bash
jupyter lab
```
Execute the notebooks in sequence from `notebooks/01_data_collection.ipynb` through `notebooks/06_presentation.ipynb`.

---

## Citation & Attribution

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

> **Citation (APA):**  
> Hogue, J. (2019). *Metro Interstate Traffic Volume* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5X60B

---

## License

This dataset is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
