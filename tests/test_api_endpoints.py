from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_styles_at_root():
    response = client.get("/styles.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_static_js_modules():
    for script_name in ["simulator.js", "forecast.js", "weather-board.js", "navigation.js"]:
        response = client.get(f"/js/{script_name}")
        assert response.status_code == 200, f"Failed to load /js/{script_name}"


def test_favicon_endpoints():
    for path in ["/favicon.svg", "/favicon.ico"]:
        response = client.get(path)
        assert response.status_code == 200, f"Failed to load {path}"


def test_static_mount_backward_compatibility():
    response = client.get("/static/styles.css")
    assert response.status_code == 200


def test_predict_endpoint_tabular():
    payload = {
        "start_date": "2026-09-04",
        "days": 1,
        "city": "Minneapolis",
        "country": "US",
        "start_hour": 8,
        "end_hour": 9,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "Tabular XGBoost"
    assert len(data["predictions"]) == 1
    assert data["predictions"][0]["hourly"][0]["model_used"] == "Tabular XGBoost"


def test_predict_endpoint_hybrid_time_series():
    payload = {
        "start_date": "2026-09-04",
        "days": 2,
        "city": "Minneapolis",
        "country": "US",
        "start_hour": 8,
        "end_hour": 9,
        "current_volume": 4800.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Hybrid" in data["engine"]
    assert len(data["predictions"]) == 2
    # Day 1 utilizes live momentum AutoRegressive Lag-XGBoost
    assert data["predictions"][0]["hourly"][0]["model_used"] == "AutoRegressive Lag-XGBoost"
    # Day 2 seamlessly switches to Tabular XGBoost
    assert data["predictions"][1]["hourly"][0]["model_used"] == "Tabular XGBoost"


