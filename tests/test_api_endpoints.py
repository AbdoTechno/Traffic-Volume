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
    for script_name in ["simulator.js", "forecast.js", "weather-board.js"]:
        response = client.get(f"/js/{script_name}")
        assert response.status_code == 200, f"Failed to load /js/{script_name}"


def test_static_mount_backward_compatibility():
    response = client.get("/static/styles.css")
    assert response.status_code == 200

