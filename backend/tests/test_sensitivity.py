"""Sensitivity analysis (contracts section 4): exact values, hand-verified."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from solver.main import app
from solver.methods import REGISTRY
from solver.schemas import Problem
from solver.sensitivity import analyze

client = TestClient(app)
EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _example(name: str) -> dict:
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))["problem"]


def _problem(sense, coefs, cons) -> Problem:
    return Problem(
        name="t",
        variables=[{"name": f"x{i + 1}", "unit": "u"} for i in range(len(coefs))],
        objective={"sense": sense, "coefficients": coefs},
        constraints=[
            {"name": f"c{i + 1}", "coefficients": a, "op": op, "rhs": b}
            for i, (a, op, b) in enumerate(cons)
        ],
    )


def _sp(report):
    return {s.constraint: (s.value, s.binding) for s in report.shadow_prices}


def _or(report):
    return {o.variable: (o.current, o.range) for o in report.objective_ranges}


def _rr(report):
    return {r.constraint: (r.current, r.range) for r in report.rhs_ranges}


@pytest.mark.parametrize("method", ["simplex", "big_m", "dual_simplex"])
def test_grupo1_full_report(method):
    report = analyze(Problem(**_example("simplex-grupo1")), REGISTRY[method])
    assert _sp(report) == {
        "vCPU": ("10", True), "RAM": ("5", True),
        "SSD": ("5", True), "Licencias BD": ("0", False),
    }
    assert report.reduced_costs == []
    assert _or(report) == {
        "Web": ("40", ("250/7", "45")),
        "Base de datos": ("25", ("35/2", "55")),
        "Procesamiento": ("45", ("40", "51")),
    }
    assert _rr(report) == {
        "vCPU": ("70", ("460/7", "79")),
        "RAM": ("65", ("35", "80")),
        "SSD": ("110", ("95", "120")),
        "Licencias BD": ("30", ("20", "+inf")),
    }
    # phrases mention problem names
    assert all("vCPU" in s.phrase for s in report.shadow_prices if s.constraint == "vCPU")
    assert "holgura de 10" in report.shadow_prices[3].phrase


def test_nonbasic_max_has_reduced_cost_and_minus_inf_range():
    p = _problem("max", ["3", "2", "1"],
                 [(["1", "1", "1"], "<=", "4"), (["2", "1", "3"], "<=", "5")])
    report = analyze(p, REGISTRY["simplex"])
    assert [(r.variable, r.value) for r in report.reduced_costs] == [("x3", "-3")]
    assert "x3" in report.reduced_costs[0].phrase and "u" in report.reduced_costs[0].phrase
    assert _or(report)["x3"] == ("1", ("-inf", "4"))
    assert _or(report)["x1"] == ("3", ("2", "4"))


def test_nonbasic_min_big_m_has_plus_inf_range():
    p = _problem("min", ["2", "3", "10"],
                 [(["1", "1", "1"], ">=", "4"), (["1", "3", "1"], ">=", "6")])
    report = analyze(p, REGISTRY["big_m"])
    assert [(r.variable, r.value) for r in report.reduced_costs] == [("x3", "8")]
    assert _or(report)["x3"] == ("10", ("2", "+inf"))
    assert _sp(report) == {"c1": ("3/2", True), "c2": ("1/2", True)}


@pytest.mark.parametrize("method", ["big_m", "dual_simplex"])
def test_contract_bakery_example(method):
    p = Problem(
        name="b",
        variables=[{"name": "pandesal", "unit": "lotes"}, {"name": "hojaldre", "unit": "lotes"}],
        objective={"sense": "max", "coefficients": ["40", "30"]},
        constraints=[
            {"name": "horno", "coefficients": ["1", "1"], "op": "<=", "rhs": "40"},
            {"name": "demanda_hojaldre_min", "coefficients": ["0", "1"], "op": ">=", "rhs": "5"},
        ],
    )
    report = analyze(p, REGISTRY[method])
    assert _sp(report) == {"horno": ("40", True), "demanda_hojaldre_min": ("-10", True)}
    assert _rr(report) == {
        "horno": ("40", ("5", "+inf")),
        "demanda_hojaldre_min": ("5", ("0", "40")),
    }

def test_negative_rhs_keeps_original_sign_and_range():
    # c2: -x1 - x2 <= -5 (non-binding at x1+x2 = 10); b2 may fall to -10.
    p = _problem("max", ["2", "3"],
                 [(["1", "1"], "<=", "10"), (["-1", "-1"], "<=", "-5")])
    report = analyze(p, REGISTRY["big_m"])
    assert _sp(report) == {"c1": ("3", True), "c2": ("0", False)}
    assert _rr(report)["c2"] == ("-5", ("-10", "+inf"))


@pytest.mark.parametrize("method", ["big_m", "dual_simplex"])
def test_equality_constraint_and_binding_le_in_min(method):
    # x1 + x2 = 10, x1 <= 4  ->  x = (4, 6), Z = 26
    p = _problem("min", ["2", "3"],
                 [(["1", "1"], "=", "10"), (["1", "0"], "<=", "4")])
    report = analyze(p, REGISTRY[method])
    assert _sp(report) == {"c1": ("3", True), "c2": ("-1", True)}
    assert _rr(report) == {"c1": ("10", ("4", "+inf")), "c2": ("4", ("0", "10"))}


def test_api_unbounded_and_infeasible_are_422():
    for name in ("test-unbounded", "test-infeasible"):
        r = client.post("/api/sensibilidad",
                        json={"method": "big_m", "problem": _example(name)})
        assert r.status_code == 422
        body = r.json()
        assert set(body) == {"code", "message"}
        assert "óptima" in body["message"]


def test_api_simplex_with_ge_is_method_not_admissible():
    r = client.post("/api/sensibilidad",
                    json={"method": "simplex", "problem": _example("bakery-real")})
    assert r.status_code == 422
    assert r.json()["code"] == "METHOD_NOT_ADMISSIBLE"


@pytest.mark.parametrize("method", ["big_m", "dual_simplex"])
def test_api_bakery_real_returns_report(method):
    r = client.post("/api/sensibilidad",
                    json={"method": method, "problem": _example("bakery-real")})
    assert r.status_code == 200
    body = r.json()
    n_cons = len(_example("bakery-real")["constraints"])
    assert len(body["shadow_prices"]) == len(body["rhs_ranges"]) == n_cons
