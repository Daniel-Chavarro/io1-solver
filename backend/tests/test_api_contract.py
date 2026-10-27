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
    assert r.json()["code"] == "INVALID_NUMBER"
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
    r = client.post("/api/resolver", json=body)
    assert r.status_code == 422
    assert r.json()["code"] == "DUPLICATE_NAME"


# ---- error mapping: 422 in Spanish with exactly {code, message} ----

def _problem(**over):
    p = {
        "name": "t",
        "variables": [{"name": "x1", "unit": "u"}],
        "objective": {"sense": "max", "coefficients": ["1"]},
        "constraints": [{"name": "c1", "coefficients": ["1"], "op": "<=", "rhs": "4"}],
    }
    p.update(over)
    return p


def _post(problem, method="simplex"):
    return client.post("/api/resolver", json={"method": method, "problem": problem})


def _assert_error(r, code):
    assert r.status_code == 422
    body = r.json()
    assert set(body) == {"code", "message"}
    assert body["code"] == code
    assert body["message"].strip()


def test_empty_number_is_empty_field():
    p = _problem(objective={"sense": "max", "coefficients": [""]})
    _assert_error(_post(p), "EMPTY_FIELD")


def test_empty_variable_name_is_empty_field():
    p = _problem(variables=[{"name": "  ", "unit": "u"}])
    _assert_error(_post(p), "EMPTY_FIELD")


def test_empty_problem_name_is_empty_field():
    _assert_error(_post(_problem(name=" ")), "EMPTY_FIELD")


def test_missing_field_is_empty_field_in_spanish():
    p = _problem()
    del p["objective"]
    r = _post(p)
    _assert_error(r, "EMPTY_FIELD")
    assert "objective" in r.json()["message"]


def test_invalid_rhs_is_invalid_number():
    p = _problem(constraints=[{"name": "c1", "coefficients": ["1"], "op": "<=", "rhs": "1,5"}])
    _assert_error(_post(p), "INVALID_NUMBER")


def test_too_many_variables_is_size_limit():
    n = 9
    p = _problem(
        variables=[{"name": f"x{i}", "unit": "u"} for i in range(n)],
        objective={"sense": "max", "coefficients": ["1"] * n},
        constraints=[{"name": "c1", "coefficients": ["1"] * n, "op": "<=", "rhs": "1"}],
    )
    _assert_error(_post(p), "SIZE_LIMIT")


def test_too_many_or_zero_constraints_is_size_limit():
    cons = [{"name": f"c{i}", "coefficients": ["1"], "op": "<=", "rhs": "1"} for i in range(9)]
    _assert_error(_post(_problem(constraints=cons)), "SIZE_LIMIT")
    _assert_error(_post(_problem(constraints=[])), "SIZE_LIMIT")


def test_method_not_admissible_for_simplex_with_ge():
    p = _problem(constraints=[{"name": "c1", "coefficients": ["1"], "op": ">=", "rhs": "1"}])
    _assert_error(_post(p), "METHOD_NOT_ADMISSIBLE")


def test_unknown_method_and_malformed_json_do_not_crash():
    _assert_error(_post(_problem(), method="nope"), "INVALID_INPUT")
    r = client.post("/api/resolver", content="{no es json", headers={"Content-Type": "application/json"})
    _assert_error(r, "INVALID_INPUT")


# ---- success contract + elapsed_ms ----

# Ejercicio del Grupo 3 (simplex-grupo1.pdf): x1=10, x2=20, x3=15, Z=1575.
GRUPO1 = {
    "name": "Contenedores en la nube",
    "variables": [{"name": "x1", "unit": "contenedores"},
                  {"name": "x2", "unit": "contenedores"},
                  {"name": "x3", "unit": "contenedores"}],
    "objective": {"sense": "max", "coefficients": ["40", "25", "45"]},
    "constraints": [
        {"name": "vCPU", "coefficients": ["2", "1", "2"], "op": "<=", "rhs": "70"},
        {"name": "RAM", "coefficients": ["1", "2", "1"], "op": "<=", "rhs": "65"},
        {"name": "SSD", "coefficients": ["3", "1", "4"], "op": "<=", "rhs": "110"},
        {"name": "Licencias", "coefficients": ["0", "1", "0"], "op": "<=", "rhs": "30"},
    ],
}


def test_success_matches_contract_and_reports_elapsed_ms():
    r = _post(GRUPO1)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"method", "status", "solution", "objective", "special_cases",
                         "iterations", "final_table", "elapsed_ms"}
    assert body["status"] == "optimal"
    assert [v["value"] for v in body["solution"]] == ["10", "20", "15"]
    assert body["objective"] == {"sense": "max", "value": "1575"}
    assert isinstance(body["elapsed_ms"], (int, float)) and body["elapsed_ms"] > 0
    assert body["iterations"][0]["number"] == 0
    assert set(body["final_table"]) == {"sense", "columns", "cj", "rows", "zj", "cj_zj"}


def test_braces_in_user_input_never_break_the_error_message():
    for bad in ["{where}", "{0}", "{"]:
        p = _problem(objective={"sense": "max", "coefficients": [bad]})
        r = _post(p)
        _assert_error(r, "INVALID_NUMBER")
        assert bad in r.json()["message"]