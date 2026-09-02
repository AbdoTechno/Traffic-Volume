from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor
import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "traffic_volume_cleaned.csv"
ARTIFACT_DIR = PROJECT_ROOT / "src" / "models"


def prepare_dataframe() -> pd.DataFrame:
    """Load and sort the cleaned dataset — identical to notebook 04.1."""
    df = pd.read_csv(DATA_PATH)
    df["date_time"] = pd.to_datetime(df["date_time"])
    df = df.sort_values("date_time").reset_index(drop=True)
    # holiday and day_of_week stay as text (same as raw CSV / notebook 04.1)
    return df


def build_model() -> tuple[Pipeline, list[str], list[str], str]:
    """
    Train exactly the same way as notebook 04.1_modeling_trial.ipynb:

    X = df.drop(columns=["traffic_volume", "date_time", "hour", "month"])
    → columns: holiday, temp, rain_1h, snow_1h, clouds_all, weather_main,
               day_of_week, hour_sin, hour_cos, month_sin, month_cos

    categorical_features = ["holiday", "weather_main", "day_of_week"]
    numerical_features   = ["temp", "rain_1h", "snow_1h", "clouds_all",
                             "hour_sin", "hour_cos", "month_sin", "month_cos"]
    """
    df = prepare_dataframe()

    # Identical drop to notebook 04.1
    X = df.drop(columns=["traffic_volume", "date_time", "hour", "month"])
    y = df["traffic_volume"]

    split_index = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    categorical_features = ["holiday", "weather_main", "day_of_week"]
    numerical_features = [
        "temp", "rain_1h", "snow_1h", "clouds_all",
        "hour_sin", "hour_cos", "month_sin", "month_cos",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), categorical_features),
        ]
    )

    models = {
        "Linear Regression": Pipeline([
            ("preprocessor", preprocessor),
            ("model", LinearRegression()),
        ]),
        "Random Forest": Pipeline([
            ("preprocessor", preprocessor),
            ("model", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
        ]),
        "XGBoost": Pipeline([
            ("preprocessor", preprocessor),
            ("model", XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42, n_jobs=-1)),
        ]),
    }

    results = []
    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        results.append({
            "Model": name,
            "MAE": mean_absolute_error(y_test, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
            "R2": r2_score(y_test, y_pred),
        })

    results_df = pd.DataFrame(results).sort_values("R2", ascending=False).reset_index(drop=True)
    best_model_name = results_df.iloc[0]["Model"]
    best_model = models[best_model_name]

    # Print summary
    print("\n=== Model Results ===")
    print(results_df.to_string(index=False))
    print(f"\n>>> Best model: {best_model_name}")

    return best_model, numerical_features, categorical_features, best_model_name, results_df


def main() -> None:
    best_model, numerical_features, categorical_features, model_name, results_df = build_model()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    pipeline_path = ARTIFACT_DIR / "traffic_volume_model_pipeline.joblib"

    # Save the full sklearn Pipeline (preprocessor + model)
    joblib.dump(best_model, pipeline_path)

    # Save metadata that matches the notebook feature schema
    metadata = {
        "model_name": model_name,
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "pipeline_path": str(pipeline_path),
        "test_mae": round(float(results_df.iloc[0]["MAE"]), 2),
        "test_rmse": round(float(results_df.iloc[0]["RMSE"]), 2),
        "test_r2": round(float(results_df.iloc[0]["R2"]), 4),
    }
    metadata_path = ARTIFACT_DIR / "traffic_volume_model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n[OK] Pipeline  : {pipeline_path}")
    print(f"[OK] Metadata  : {metadata_path}")


if __name__ == "__main__":
    main()
