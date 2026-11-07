import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI
from core.middleware import RequestAuditMiddleware


def test_request_audit_middleware_headers():
    test_app = FastAPI()
    test_app.add_middleware(RequestAuditMiddleware)

    @test_app.get("/ping")
    def ping():
        return {"status": "ok"}

    client = TestClient(test_app)
    response = client.get("/ping")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")
    assert "X-Process-Time-Ms" in response.headers
    assert float(response.headers["X-Process-Time-Ms"]) >= 0.0
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "strict-origin" in response.headers["Referrer-Policy"]


def test_custom_request_id_preserved():
    test_app = FastAPI()
    test_app.add_middleware(RequestAuditMiddleware)

    @test_app.get("/ping")
    def ping():
        return {"status": "ok"}

    client = TestClient(test_app)
    custom_id = "test-custom-client-id-12345"
    response = client.get("/ping", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
