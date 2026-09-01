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
    df = pd.read_csv(DATA_PATH)
    df["date_time"] = pd.to_datetime(df["date_time"])
    df = df.sort_values("date_time").reset_index(drop=True)

    df["year"] = df["date_time"].dt.year
    df["day_of_week_num"] = df["date_time"].dt.dayofweek
    df["day_sin"] = np.sin(2 * np.pi * df["day_of_week_num"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_of_week_num"] / 7)
    df["holiday"] = df["holiday"].apply(
        lambda x: 0 if str(x).strip().lower() in {"not holiday", "none", "nan", ""} else 1
    )
    return df


def build_model() -> tuple[Pipeline, list[str], list[str], str]:
    df = prepare_dataframe()
    X = df.drop(columns=["traffic_volume", "date_time", "hour", "month", "day_of_week", "day_of_week_num"])
    y = df["traffic_volume"]

    split_index = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    categorical_features = ["weather_main"]
    numerical_features = [
        "holiday", "temp", "rain_1h", "snow_1h", "clouds_all", "year",
        "hour_sin", "hour_cos", "month_sin", "month_cos", "day_sin", "day_cos",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ]
    )

    models = {
        "Linear Regression": Pipeline([("preprocessor", preprocessor), ("model", LinearRegression())]),
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
        results.append(
            {
                "Model": name,
                "MAE": mean_absolute_error(y_test, y_pred),
                "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
                "R2": r2_score(y_test, y_pred),
            }
        )

    results_df = pd.DataFrame(results).sort_values("R2", ascending=False).reset_index(drop=True)
    best_model_name = results_df.iloc[0]["Model"]
    best_model = models[best_model_name]
    return best_model, numerical_features, categorical_features, best_model_name


def main() -> None:
    model, numerical_features, categorical_features, model_name = build_model()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    scaler = model.named_steps["preprocessor"].named_transformers_["num"]
    encoder = model.named_steps["preprocessor"].named_transformers_["cat"]

    scaler_path = ARTIFACT_DIR / "traffic_volume_scaler.joblib"
    encoder_path = ARTIFACT_DIR / "traffic_volume_encoder.joblib"
    pipeline_path = ARTIFACT_DIR / "traffic_volume_model_pipeline.joblib"
    metadata_path = ARTIFACT_DIR / "traffic_volume_model_metadata.json"

    joblib.dump(scaler, scaler_path)
    joblib.dump(encoder, encoder_path)
    joblib.dump(model, pipeline_path)

    metadata = {
        "model_name": model_name,
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "scaler_path": str(scaler_path),
        "encoder_path": str(encoder_path),
        "pipeline_path": str(pipeline_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Model artifacts saved in: {ARTIFACT_DIR}")
    print(f"Scaler: {scaler_path.name}")
    print(f"Encoder: {encoder_path.name}")
    print(f"Pipeline: {pipeline_path.name}")
    print(f"Metadata: {metadata_path.name}")


if __name__ == "__main__":
    main()
