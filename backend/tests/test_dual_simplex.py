"""Unit and integration tests for the Dual Simplex Method."""
from fractions import Fraction
import pytest
from fastapi.testclient import TestClient

from solver.main import app
from solver.methods import REGISTRY, MethodNotAdmissibleError
from solver.methods.dual_simplex import DualSimplexMethod
from solver.schemas import Problem, ResolverRequest

client = TestClient(app)


def _make_problem(sense, coefs, cons, var_names=None, units=None) -> Problem:
    n_vars = len(coefs)
    if var_names is None:
        var_names = [f"x{i + 1}" for i in range(n_vars)]
    if units is None:
        units = ["u"] * n_vars
    return Problem(
        name="test_problem",
        variables=[
            {"name": name, "unit": unit} for name, unit in zip(var_names, units)
        ],
        objective={"sense": sense, "coefficients": coefs},
        constraints=[
            {"name": f"c{i + 1}", "coefficients": coeffs, "op": op, "rhs": rhs}
            for i, (coeffs, op, rhs) in enumerate(cons)
        ],
    )


def test_pure_dual_simplex_classic():
    """
    Min 3x1 + 2x2
    s.t.
      3x1 +  x2 >= 3  -> -3x1 -  x2 <= -3
      4x1 + 3x2 >= 6  -> -4x1 - 3x2 <= -6
       x1 + 2x2 <= 3  ->   x1 + 2x2 <=  3
    Optimal: x1 = 3/5, x2 = 6/5, Z = 21/5
    """
    prob = _make_problem(
        "min",
        ["3", "2"],
        [
            (["3", "1"], ">=", "3"),
            (["4", "3"], ">=", "6"),
            (["1", "2"], "<=", "3"),
        ],
    )
    method = DualSimplexMethod()
    res = method.run(prob)
    assert res.status == "optimal"
    assert res.objective["value"] == "21/5"
    sol = {v.name: v.value for v in res.solution}
    assert sol["x1"] == "3/5"
    assert sol["x2"] == "6/5"
    # Started with normalized constraints reported
    norm_cases = [c for c in res.special_cases if c.type == "normalized_constraint"]
    assert len(norm_cases) == 2
    # Verify iterations
    assert len(res.iterations) > 0


def test_bakery_contract_dual_simplex():
    """
    Bakery problem:
    Max 40 pandesal + 30 hojaldre
    s.t.
      pandesal + hojaldre <= 40
      hojaldre >= 5
    Optimal: pandesal = 35, hojaldre = 5, Z = 1550
    """
    prob = _make_problem(
        "max",
        ["40", "30"],
        [(["1", "1"], "<=", "40"), (["0", "1"], ">=", "5")],
        var_names=["pandesal", "hojaldre"],
        units=["lotes", "lotes"],
    )
    method = REGISTRY["dual_simplex"]
    res = method.run(prob)
    assert res.status == "optimal"
    assert res.objective["value"] == "1550"
    sol = {v.name: v.value for v in res.solution}
    assert sol["pandesal"] == "35"
    assert sol["hojaldre"] == "5"


def test_equality_constraint_split():
    """
    Min 2x1 + 3x2 and Max 2x1 + 3x2 s.t. x1 + x2 = 10, x1 <= 4
    Min: x1 = 4, x2 = 6 -> Z = 26
    Max: x1 = 0, x2 = 10 -> Z = 30
    """
    method = REGISTRY["dual_simplex"]

    prob_min = _make_problem(
        "min",
        ["2", "3"],
        [(["1", "1"], "=", "10"), (["1", "0"], "<=", "4")],
    )
    res_min = method.run(prob_min)
    assert res_min.status == "optimal"
    assert res_min.objective["value"] == "26"
    sol_min = {v.name: v.value for v in res_min.solution}
    assert sol_min["x1"] == "4"
    assert sol_min["x2"] == "6"

    prob_max = _make_problem(
        "max",
        ["2", "3"],
        [(["1", "1"], "=", "10"), (["1", "0"], "<=", "4")],
    )
    res_max = method.run(prob_max)
    assert res_max.status == "optimal"
    assert res_max.objective["value"] == "30"
    sol_max = {v.name: v.value for v in res_max.solution}
    assert sol_max["x1"] == "0"
    assert sol_max["x2"] == "10"


def test_dual_simplex_infeasible():
    """
    x1 <= 2, x1 >= 5 -> Infeasible
    """
    prob = _make_problem(
        "max",
        ["1"],
        [(["1"], "<=", "2"), (["1"], ">=", "5")],
    )
    method = REGISTRY["dual_simplex"]
    res = method.run(prob)
    assert res.status == "infeasible"
    infeasible_cases = [c for c in res.special_cases if c.type == "infeasible"]
    assert len(infeasible_cases) >= 1
    assert "infactible" in infeasible_cases[0].detail.lower() or "factible" in infeasible_cases[0].detail.lower()


def test_dual_simplex_unbounded():
    """
    Max x1 + x2 s.t. x1 - x2 <= 2
    """
    prob = _make_problem(
        "max",
        ["1", "1"],
        [(["1", "-1"], "<=", "2")],
    )
    method = REGISTRY["dual_simplex"]
    res = method.run(prob)
    assert res.status == "unbounded"
    unbounded_cases = [c for c in res.special_cases if c.type == "unbounded"]
    assert len(unbounded_cases) >= 1
    assert "no está acotado" in unbounded_cases[0].detail.lower()


def test_dual_simplex_alternative_optima():
    """
    Max 2x1 + 4x2 s.t. x1 + 2x2 <= 5
    Multiple optima along x1 + 2x2 = 5, Z = 10
    """
    prob = _make_problem(
        "max",
        ["2", "4"],
        [(["1", "2"], "<=", "5")],
    )
    method = REGISTRY["dual_simplex"]
    res = method.run(prob)
    assert res.status == "optimal"
    assert res.objective["value"] == "10"
    alt_cases = [c for c in res.special_cases if c.type == "alternative_optima"]
    assert len(alt_cases) >= 1


def test_dual_simplex_degenerate():
    """
    Degenerate problem with redundant/tight constraints at origin.
    Max 3x1 + 9x2
    s.t.
      x1 + 4x2 <= 8
      x1 + 2x2 <= 4
    """
    prob = _make_problem(
        "max",
        ["3", "9"],
        [(["1", "4"], "<=", "8"), (["1", "2"], "<=", "4")],
    )
    method = REGISTRY["dual_simplex"]
    res = method.run(prob)
    assert res.status == "optimal"
    assert res.objective["value"] == "18"
    degen_cases = [c for c in res.special_cases if c.type == "degenerate_pivot"]
    assert len(degen_cases) >= 1


def test_api_resolver_contract_dual_simplex():
    prob = _make_problem(
        "min",
        ["3", "2"],
        [
            (["3", "1"], ">=", "3"),
            (["4", "3"], ">=", "6"),
            (["1", "2"], "<=", "3"),
        ],
    )
    resp = client.post(
        "/api/resolver",
        json={"method": "dual_simplex", "problem": prob.model_dump()},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["method"] == "dual_simplex"
    assert data["status"] == "optimal"
    assert data["objective"]["value"] == "21/5"


def test_api_sensibilidad_contract_dual_simplex():
    prob = _make_problem(
        "min",
        ["3", "2"],
        [
            (["3", "1"], ">=", "3"),
            (["4", "3"], ">=", "6"),
            (["1", "2"], "<=", "3"),
        ],
    )
    resp = client.post(
        "/api/sensibilidad",
        json={"method": "dual_simplex", "problem": prob.model_dump()},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "shadow_prices" in data
    assert len(data["shadow_prices"]) == 3
    assert len(data["rhs_ranges"]) == 3


def test_api_comparar_contract_includes_dual_simplex():
    prob = _make_problem(
        "max",
        ["40", "30"],
        [(["1", "1"], "<=", "40"), (["0", "1"], ">=", "5")],
    )
    resp = client.post(
        "/api/comparar",
        json={"problem": prob.model_dump()},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "dual_simplex" in data["results"]
    assert data["results"]["dual_simplex"]["status"] == "optimal"
    assert data["results"]["big_m"]["status"] == "optimal"
    assert data["same_objective"] is True
