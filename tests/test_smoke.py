import os

import pytest
from fastapi.testclient import TestClient

from pfor.main import app

client = TestClient(app)
LIVE_INFRA = os.getenv("ENABLE_LIVE_INFRA", "false").lower() in {"1", "true", "yes", "on"}


@pytest.mark.skipif(not LIVE_INFRA, reason="Live PostgreSQL/Ollama dependency checks are disabled in CI by default.")
def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "version" in payload


@pytest.mark.skipif(not LIVE_INFRA, reason="Live PostgreSQL/Ollama dependency checks are disabled in CI by default.")
def test_generate_strategy_endpoint_contract():
    payload = {
        "prompt_text": "Нужно увеличить конверсию B2B-сайта с 4% до 8% за квартал и улучшить воронку продаж.",
        "language": "ru",
    }
    response = client.post("/api/v1/generate-strategy", json=payload)
    assert response.status_code in {200, 201, 503}


@pytest.mark.skipif(not LIVE_INFRA, reason="Live PostgreSQL/Ollama dependency checks are disabled in CI by default.")
def test_history_endpoint_contract():
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    payload = response.json()
    assert "total" in payload
    assert "items" in payload
