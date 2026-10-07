"""API contract tests that already pass with the scaffold (contracts sections 1, 5, 6)."""
from fastapi.testclient import TestClient

from solver.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_examples_are_listed():
    ids = {e["id"] for e in client.get("/api/ejemplos").json()}
    assert {"bakery-real", "test-unbounded", "test-infeasible"} <= ids


def test_example_detail_returns_problem():
    data = client.get("/api/ejemplos/bakery-real").json()
    assert data["problem"]["objective"]["sense"] == "max"


def test_invalid_number_is_rejected_in_spanish():
    body = {
        "method": "simplex",
        "problem": {
            "name": "t",
            "variables": [{"name": "x1", "unit": "u"}],
            "objective": {"sense": "max", "coefficients": ["abc"]},
            "constraints": [{"name": "c1", "coefficients": ["1"], "op": "<=", "rhs": "2"}],
        },
    }
    r = client.post("/api/resolver", json=body)
    assert r.status_code == 422
    assert "numero" in r.json()["message"]


def test_duplicate_variables_rejected():
    body = {
        "method": "simplex",
        "problem": {
            "name": "t",
            "variables": [{"name": "x1", "unit": "u"}, {"name": "x1", "unit": "u"}],
            "objective": {"sense": "max", "coefficients": ["1", "1"]},
            "constraints": [{"name": "c1", "coefficients": ["1", "1"], "op": "<=", "rhs": "2"}],
        },
    }
    assert client.post("/api/resolver", json=body).status_code == 422
