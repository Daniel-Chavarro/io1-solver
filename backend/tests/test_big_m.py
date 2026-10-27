"""Unit and integration tests for BigMMethod (contracts section 3)."""
from fractions import Fraction

from fastapi.testclient import TestClient

from solver.engine.frac_m import FracM
from solver.main import app
from solver.methods.big_m import BigMMethod
from solver.schemas import Problem

client = TestClient(app)

M = FracM(Fraction(0), Fraction(1))


def _problem(sense, obj, constraints, variables=None) -> Problem:
    n = len(obj)
    return Problem(
        name="Problema de prueba",
        variables=variables or [{"name": f"x{i + 1}", "unit": "u"} for i in range(n)],
        objective={"sense": sense, "coefficients": obj},
        constraints=[
            {"name": f"c{i + 1}", "coefficients": co, "op": op, "rhs": rhs}
            for i, (co, op, rhs) in enumerate(constraints)
        ],
    )


def _bakery() -> Problem:
    """The worked example of docs/contracts.md section 5."""
    return _problem(
        "max",
        ["40", "30"],
        [(["1", "1"], "<=", "40"), (["0", "1"], ">=", "5")],
        variables=[
            {"name": "pandesal", "unit": "lotes"},
            {"name": "hojaldre", "unit": "lotes"},
        ],
    )


def _values(result) -> dict[str, str]:
    return {v.name: v.value for v in result.solution}


def _types(result) -> list[str]:
    return [c.type for c in result.special_cases]


class TestBigMBuild:
    def test_contract_example_initial_tableau(self):
        t = BigMMethod().build(_bakery())

        assert t.columns == ["pandesal", "hojaldre", "s1", "e1", "a1", "bj"]
        assert [str(c) for c in t.cj[:-1]] == ["40", "30", "0", "0", "-M"]
        assert [(r.basic, str(r.cb)) for r in t.rows] == [("s1", "0"), ("a1", "-M")]
        assert [str(c) for c in t.rows[1].cells] == ["0", "1", "0", "-1", "1", "5"]
        assert [str(z) for z in t.zj] == ["0", "-M", "0", "M", "-M", "-5M"]
        assert [str(c) for c in t.cj_zj] == ["40", "M+30", "0", "-M", "0"]

    def test_min_uses_plus_m(self):
        t = BigMMethod().build(_problem("min", ["2", "3"], [(["1", "1"], ">=", "4")]))
        assert t.cj[t.columns.index("a1")] == M
        assert t.rows[0].cb == M

    def test_equality_gets_only_artificial(self):
        t = BigMMethod().build(_problem("max", ["1", "1"], [(["1", "2"], "=", "6")]))
        assert t.columns == ["x1", "x2", "a1", "bj"]

    def test_aux_names_numbered_per_kind(self):
        t = BigMMethod().build(
            _problem(
                "max",
                ["1", "1"],
                [
                    (["1", "0"], "<=", "4"),
                    (["0", "1"], ">=", "1"),
                    (["1", "1"], "<=", "9"),
                    (["1", "-1"], "=", "0"),
                ],
            )
        )
        assert t.columns == ["x1", "x2", "s1", "s2", "e1", "a1", "a2", "bj"]
        assert [r.basic for r in t.rows] == ["s1", "a1", "s2", "a2"]

    def test_negative_rhs_flips_row(self):
        # -x1 - x2 <= -2  ->  x1 + x2 >= 2
        t = BigMMethod().build(_problem("min", ["1", "1"], [(["-1", "-1"], "<=", "-2")]))
        assert t.columns == ["x1", "x2", "e1", "a1", "bj"]
        assert t.rows[0].cells == [Fraction(1), Fraction(1), Fraction(-1), Fraction(1), Fraction(2)]


class TestBigMRun:
    def test_contract_example_optimum(self):
        r = BigMMethod().run(_bakery())
        assert r.method == "big_m"
        assert r.status == "optimal"
        assert _values(r) == {"pandesal": "35", "hojaldre": "5"}
        assert r.objective == {"sense": "max", "value": "1550"}
        # M dominates: the artificial column enters first.
        assert r.iterations[1].entering == "hojaldre"
        assert r.iterations[1].leaving == "a1"

    def test_min_with_ge_constraints(self):
        # min 2x1 + 3x2  s.t. x1 + x2 >= 4, x1 + 3x2 >= 6  ->  x1=3, x2=1, z=9
        r = BigMMethod().run(
            _problem("min", ["2", "3"], [(["1", "1"], ">=", "4"), (["1", "3"], ">=", "6")])
        )
        assert r.status == "optimal"
        assert _values(r) == {"x1": "3", "x2": "1"}
        assert r.objective["value"] == "9"

    def test_equality_constraint(self):
        # max 3x1 + 2x2  s.t. x1 + x2 = 4, x1 <= 3  ->  x1=3, x2=1, z=11
        r = BigMMethod().run(
            _problem("max", ["3", "2"], [(["1", "1"], "=", "4"), (["1", "0"], "<=", "3")])
        )
        assert r.status == "optimal"
        assert _values(r) == {"x1": "3", "x2": "1"}
        assert r.objective["value"] == "11"

    def test_negative_rhs_is_reported(self):
        r = BigMMethod().run(_problem("min", ["1", "1"], [(["-1", "-1"], "<=", "-2")]))
        assert r.status == "optimal"
        assert r.objective["value"] == "2"
        normalized = [c for c in r.special_cases if c.type == "normalized_constraint"]
        assert len(normalized) == 1
        assert "'<=' a '>='" in normalized[0].detail

    def test_infeasible_when_artificial_stays_positive(self):
        r = BigMMethod().run(
            _problem("max", ["1"], [(["1"], "<=", "2"), (["1"], ">=", "5")])
        )
        assert r.status == "infeasible"
        infeasible = [c for c in r.special_cases if c.type == "infeasible"]
        assert len(infeasible) == 1
        assert "a1" in infeasible[0].detail
        assert "alternative_optima" not in _types(r)

    def test_artificial_at_zero_is_degenerate_not_infeasible(self):
        # The second equality is redundant (2x the first): once a1 leaves, the
        # a2 row becomes all zeros and a2 stays basic at 0 - feasible.
        r = BigMMethod().run(
            _problem(
                "max",
                ["1", "2"],
                [(["1", "1"], "=", "2"), (["2", "2"], "=", "4")],
            )
        )
        assert r.status == "optimal"
        assert _values(r) == {"x1": "0", "x2": "2"}
        assert r.objective["value"] == "4"
        assert "infeasible" not in _types(r)
        assert any("a2" in c.detail and "valor 0" in c.detail for c in r.special_cases)
        assert any(row.basic == "a2" for row in r.final_table.rows)

    def test_unbounded(self):
        r = BigMMethod().run(_problem("max", ["1", "1"], [(["1", "-1"], ">=", "1")]))
        assert r.status == "unbounded"
        assert "unbounded" in _types(r)

    def test_solution_excludes_auxiliaries(self):
        r = BigMMethod().run(_bakery())
        assert [v.name for v in r.solution] == ["pandesal", "hojaldre"]


def test_api_resolver_big_m():
    resp = client.post(
        "/api/resolver", json={"method": "big_m", "problem": _bakery().model_dump()}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "optimal"
    assert body["objective"]["value"] == "1550"
    assert body["iterations"][0]["tableau"]["cj_zj"] == ["40", "M+30", "0", "-M", "0"]
