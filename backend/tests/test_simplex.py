"""Unit and integration tests for SimplexMethod (contracts section 3 & 6)."""
from fractions import Fraction

import pytest
from fastapi.testclient import TestClient

from solver.engine.frac_m import FracM
from solver.main import app
from solver.methods.base import MethodNotAdmissibleError
from solver.methods.simplex import SimplexMethod
from solver.schemas import Problem

client = TestClient(app)


def _make_problem(
    *,
    sense="max",
    variables=None,
    obj_coeffs=None,
    constraints=None,
) -> Problem:
    return Problem(
        name="Problema de prueba",
        variables=variables
        or [
            {"name": "pandesal", "unit": "lotes"},
            {"name": "hojaldre", "unit": "lotes"},
        ],
        objective={
            "sense": sense,
            "coefficients": obj_coeffs or ["3", "2"],
        },
        constraints=constraints
        or [
            {"name": "horno", "coefficients": ["1", "1"], "op": "<=", "rhs": "4"},
            {"name": "harina", "coefficients": ["2", "1"], "op": "<=", "rhs": "5"},
        ],
    )


class TestSimplexBuild:
    def test_build_standard_tableau(self):
        method = SimplexMethod()
        problem = _make_problem()
        tableau = method.build(problem)

        assert tableau.sense == "max"
        assert tableau.columns == ["pandesal", "hojaldre", "s1", "s2", "bj"]
        assert tableau.cj == [
            FracM(Fraction(3)),
            FracM(Fraction(2)),
            FracM(Fraction(0)),
            FracM(Fraction(0)),
            FracM(Fraction(0)),
        ]
        assert [r.basic for r in tableau.rows] == ["s1", "s2"]
        assert all(r.cb == FracM(Fraction(0)) for r in tableau.rows)
        assert tableau.rows[0].cells == [
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(0),
            Fraction(4),
        ]
        assert tableau.rows[1].cells == [
            Fraction(2),
            Fraction(1),
            Fraction(0),
            Fraction(1),
            Fraction(5),
        ]
        # evaluate() must have been called: initial Z_j = 0, C_j - Z_j = [3, 2, 0, 0]
        assert all(z == FracM(Fraction(0)) for z in tableau.zj)
        assert tableau.cj_zj == [
            FracM(Fraction(3)),
            FracM(Fraction(2)),
            FracM(Fraction(0)),
            FracM(Fraction(0)),
        ]

    @pytest.mark.parametrize("op", [">=", "="])
    def test_build_rejects_non_le_constraint_in_spanish(self, op):
        method = SimplexMethod()
        problem = _make_problem(
            constraints=[
                {"name": "demanda_min", "coefficients": ["1", "0"], "op": op, "rhs": "2"}
            ]
        )
        with pytest.raises(MethodNotAdmissibleError) as exc_info:
            method.build(problem)
        msg = str(exc_info.value)
        assert "Simplex" in msg
        assert "Gran M" in msg

    def test_build_rejects_negative_rhs_in_spanish(self):
        method = SimplexMethod()
        problem = _make_problem(
            constraints=[
                {"name": "recurso", "coefficients": ["1", "1"], "op": "<=", "rhs": "-3"}
            ]
        )
        with pytest.raises(MethodNotAdmissibleError) as exc_info:
            method.build(problem)
        msg = str(exc_info.value)
        assert "RHS" in msg or "negativo" in msg.lower()
        assert "Gran M" in msg


class TestSimplexRunAndInterpret:
    def test_optimal_maximization_solution_and_iterations(self):
        method = SimplexMethod()
        problem = _make_problem()
        result = method.run(problem)

        assert result.method == "simplex"
        assert result.status == "optimal"
        assert result.objective == {"sense": "max", "value": "9"}
        # Solution only includes original variables with their units
        assert [(v.name, v.unit, v.value) for v in result.solution] == [
            ("pandesal", "lotes", "1"),
            ("hojaldre", "lotes", "3"),
        ]
        # Iteration 0 (initial) + 2 pivots = 3 snapshots
        assert [it.number for it in result.iterations] == [0, 1, 2]
        assert result.iterations[0].entering is None
        assert result.iterations[1].entering == "pandesal"
        assert result.iterations[1].leaving == "s2"
        assert result.iterations[1].ratios == ["4", "5/2"]
        assert result.iterations[1].ties == []

    def test_optimal_minimization_in_original_sense(self):
        # Min -2 x1 - 3 x2 s.t. x1 + x2 <= 4, x1 <= 2 -> x1=0, x2=4, Z = -12
        method = SimplexMethod()
        problem = _make_problem(
            sense="min",
            obj_coeffs=["-2", "-3"],
            constraints=[
                {"name": "c1", "coefficients": ["1", "1"], "op": "<=", "rhs": "4"},
                {"name": "c2", "coefficients": ["1", "0"], "op": "<=", "rhs": "2"},
            ],
        )
        result = method.run(problem)

        assert result.status == "optimal"
        assert result.objective == {"sense": "min", "value": "-12"}
        assert [(v.name, v.value) for v in result.solution] == [
            ("pandesal", "0"),
            ("hojaldre", "4"),
        ]

    def test_unbounded_problem_reports_special_case(self):
        method = SimplexMethod()
        problem = _make_problem(
            obj_coeffs=["1", "1"],
            constraints=[
                {"name": "c1", "coefficients": ["1", "-1"], "op": "<=", "rhs": "2"},
            ],
        )
        result = method.run(problem)

        assert result.status == "unbounded"
        types = [sc.type for sc in result.special_cases]
        assert "unbounded" in types

    def test_degenerate_tie_reports_special_case(self):
        method = SimplexMethod()
        problem = _make_problem(
            obj_coeffs=["4", "1"],
            constraints=[
                {"name": "c1", "coefficients": ["2", "1"], "op": "<=", "rhs": "6"},
                {"name": "c2", "coefficients": ["3", "1"], "op": "<=", "rhs": "9"},
            ],
        )
        result = method.run(problem)

        assert result.status == "optimal"
        deg_cases = [sc for sc in result.special_cases if sc.type == "degenerate_pivot"]
        assert len(deg_cases) >= 1
        assert deg_cases[0].iteration == 1
        assert set(result.iterations[1].ties) == {"s1", "s2"}

    def test_alternative_optima_reports_special_case(self):
        # Max 2 x1 + 4 x2 s.t. x1 + 2 x2 <= 8, x1 <= 4
        # Objective is parallel to constraint 1 -> non-basic variable has C_j - Z_j = 0
        method = SimplexMethod()
        problem = _make_problem(
            obj_coeffs=["2", "4"],
            constraints=[
                {"name": "c1", "coefficients": ["1", "2"], "op": "<=", "rhs": "8"},
                {"name": "c2", "coefficients": ["1", "0"], "op": "<=", "rhs": "4"},
            ],
        )
        result = method.run(problem)

        assert result.status == "optimal"
        assert result.objective["value"] == "16"
        alt_cases = [sc for sc in result.special_cases if sc.type == "alternative_optima"]
        assert len(alt_cases) == 1


class TestSimplexApiContract:
    def test_api_resolver_simplex_not_admissible_returns_422_code(self):
        body = {
            "method": "simplex",
            "problem": {
                "name": "Infactible para simplex",
                "variables": [{"name": "x1", "unit": "u"}],
                "objective": {"sense": "max", "coefficients": ["1"]},
                "constraints": [
                    {"name": "c1", "coefficients": ["1"], "op": ">=", "rhs": "5"}
                ],
            },
        }
        r = client.post("/api/resolver", json=body)
        assert r.status_code == 422
        data = r.json()
        assert data["code"] == "METHOD_NOT_ADMISSIBLE"
        assert "Gran M" in data["message"]

    def test_api_resolver_simplex_success(self):
        ex = client.get("/api/ejemplos/bakery-real").json()
        r = client.post(
            "/api/resolver", json={"method": "simplex", "problem": ex["problem"]}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["method"] == "simplex"
        assert data["status"] == "optimal"
        assert len(data["solution"]) == 3
        assert data["elapsed_ms"] >= 0
