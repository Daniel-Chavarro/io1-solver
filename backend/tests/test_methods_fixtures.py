"""Fixture-driven tests over examples/*.json (contracts section 7).

The same JSON feeds the UI (/api/ejemplos) and pytest. Skips come off as each
method lands (simplex and big_m are both live now).
"""
import json
from fractions import Fraction
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from solver.main import app
from solver.methods import REGISTRY, MethodNotAdmissibleError
from solver.schemas import Problem

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
CASES = [
    (eid, method)
    for eid in ("bakery-real", "test-unbounded", "test-infeasible", "simplex-grupo1")
    for method in ("simplex", "big_m")
]


def _load(example_id):
    return json.loads((EXAMPLES / f"{example_id}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(("example_id", "method_id"), CASES)
def test_fixture(example_id, method_id):
    ex = _load(example_id)
    expected = ex["expected"][method_id]
    problem = Problem(**ex["problem"])
    if expected.get("admissible") is False:
        with pytest.raises(MethodNotAdmissibleError):
            REGISTRY[method_id].build(problem)
        return
    result = REGISTRY[method_id].run(problem)
    assert result.status == expected["status"]
    if "objective_value" in expected:
        assert result.objective["value"] == expected["objective_value"]


def test_simplex_grupo1_matches_pdf_walkthrough():
    problem = Problem(**_load("simplex-grupo1")["problem"])
    result = REGISTRY["simplex"].run(problem)

    assert result.status == "optimal"
    assert [(v.name, v.value) for v in result.solution] == [
        ("Web", "10"), ("Base de datos", "20"), ("Procesamiento", "15"),
    ]
    assert result.objective == {"sense": "max", "value": "1575"}
    assert result.special_cases == []

    steps = [(it.entering, it.leaving, it.pivot) for it in result.iterations[1:]]
    assert steps == [
        ("Procesamiento", "s3", "4"),
        ("Base de datos", "s2", "7/4"),
        ("Web", "s1", "3/7"),
    ]
    assert result.iterations[1].ratios == ["35", "65", "55/2", "-"]
    assert result.iterations[2].ratios == ["30", "150/7", "110", "30"]
    assert result.iterations[3].ratios == ["10", "150", "31", "-"]
    # Z after each table (last slot of zj is the current objective value)
    assert [it.tableau.zj[-1] for it in result.iterations] == ["0", "2475/2", "10725/7", "1575"]


def test_bakery_real_big_m_respects_all_bounds():
    problem = Problem(**_load("bakery-real")["problem"])
    result = REGISTRY["big_m"].run(problem)
    assert result.status == "optimal"
    x = {v.name: Fraction(v.value) for v in result.solution}
    assert x["Tradicional"] >= 35
    assert x["Premium Balanceado"] >= 30
    assert x["Orgánico"] <= 35
    assert x["Origen Regional"] <= 40
    assert Fraction("10.5") <= x["Mujeres Cafeteras"] <= 30
    assert x["Tradicional"] + x["Premium Balanceado"] >= 95
    coefs = [Fraction(c) for c in problem.objective.coefficients]
    names = [v.name for v in problem.variables]
    assert sum(c * x[n] for c, n in zip(coefs, names)) == Fraction(result.objective["value"])


@pytest.mark.xfail(
    strict=True,
    reason="sensitivity.analyze is still a stub (POST /api/sensibilidad returns 501)",
)
def test_simplex_grupo1_shadow_prices_match_pdf():
    problem = _load("simplex-grupo1")["problem"]
    body = TestClient(app).post(
        "/api/sensibilidad", json={"method": "simplex", "problem": problem}
    ).json()
    prices = {p["constraint"]: (p["value"], p["binding"]) for p in body["shadow_prices"]}
    assert prices == {
        "vCPU": ("10", True), "RAM": ("5", True),
        "SSD": ("5", True), "Licencias BD": ("0", False),
    }
