"""Tests for the generic Simplex solver loop.

Contracts: docs/contracts.md section 2 and docs/adr/0001-formato-tabular-cj-zj.md.
"""
from fractions import Fraction
import pytest

from solver.engine.frac_m import FracM
from solver.engine.tableau import Row, Tableau
from solver.engine.solver import EngineResult, Iteration, solve


def make_already_optimal_tableau() -> Tableau:
    """Maximization tableau where all C_j - Z_j <= 0."""
    columns = ["x1", "s1", "bj"]
    cj = [FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
    rows = [
        Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(5)]),
    ]
    return Tableau(
        sense="max",
        columns=columns,
        cj=cj,
        rows=rows,
        zj=[FracM(Fraction(3)), FracM(Fraction(0)), FracM(Fraction(0))],
        cj_zj=[FracM(Fraction(-3)), FracM(Fraction(0))],
    )


def make_two_step_max_tableau() -> Tableau:
    """Standard 2-variable LP requiring 2 pivots to reach optimality:

    Max 3 x1 + 2 x2
    s.t.
    x1 + x2 + s1 = 4
    2 x1 + x2 + s2 = 5
    x1, x2, s1, s2 >= 0

    Optimal solution: x1 = 1, x2 = 3, Z = 11.
    """
    columns = ["x1", "x2", "s1", "s2", "bj"]
    cj = [
        FracM(Fraction(3)),
        FracM(Fraction(2)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
    ]
    rows = [
        Row(
            basic="s1",
            cb=FracM(Fraction(0)),
            cells=[Fraction(1), Fraction(1), Fraction(1), Fraction(0), Fraction(4)],
        ),
        Row(
            basic="s2",
            cb=FracM(Fraction(0)),
            cells=[Fraction(2), Fraction(1), Fraction(0), Fraction(1), Fraction(5)],
        ),
    ]
    return Tableau(
        sense="max",
        columns=columns,
        cj=cj,
        rows=rows,
        zj=[],
        cj_zj=[],
    ).evaluate()


def make_unbounded_max_tableau() -> Tableau:
    """Problem where entering variable column has no positive cells:

    Max 2 x1 + 3 x2
    s.t.
    x1 - x2 + s1 = 4
    -2 x1 - x2 + s2 = 2
    When x2 enters, column cells are [-1, -1] <= 0 -> Unbounded.
    """
    columns = ["x1", "x2", "s1", "s2", "bj"]
    cj = [
        FracM(Fraction(2)),
        FracM(Fraction(3)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
    ]
    rows = [
        Row(
            basic="s1",
            cb=FracM(Fraction(0)),
            cells=[Fraction(1), Fraction(-1), Fraction(1), Fraction(0), Fraction(4)],
        ),
        Row(
            basic="s2",
            cb=FracM(Fraction(0)),
            cells=[Fraction(-2), Fraction(-1), Fraction(0), Fraction(1), Fraction(2)],
        ),
    ]
    return Tableau(
        sense="max",
        columns=columns,
        cj=cj,
        rows=rows,
        zj=[],
        cj_zj=[],
    ).evaluate()


def make_degenerate_tie_tableau() -> Tableau:
    """Problem with a tie in minimum ratio test:

    Max 4 x1 + x2
    s.t.
    2 x1 + s1 = 6  -> ratio 6/2 = 3
    3 x1 + s2 = 9  -> ratio 9/3 = 3 (tie!)
    """
    columns = ["x1", "x2", "s1", "s2", "bj"]
    cj = [
        FracM(Fraction(4)),
        FracM(Fraction(1)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
    ]
    rows = [
        Row(
            basic="s1",
            cb=FracM(Fraction(0)),
            cells=[Fraction(2), Fraction(0), Fraction(1), Fraction(0), Fraction(6)],
        ),
        Row(
            basic="s2",
            cb=FracM(Fraction(0)),
            cells=[Fraction(3), Fraction(0), Fraction(0), Fraction(1), Fraction(9)],
        ),
    ]
    return Tableau(
        sense="max",
        columns=columns,
        cj=cj,
        rows=rows,
        zj=[],
        cj_zj=[],
    ).evaluate()


class TestIterationAndEngineResultStructures:
    def test_iteration_defaults(self):
        t = make_already_optimal_tableau()
        it = Iteration(number=0, tableau=t)
        assert it.number == 0
        assert it.tableau is t
        assert it.entering is None
        assert it.leaving is None
        assert it.pivot is None
        assert it.ratios == []
        assert it.ties == []

    def test_engine_result_structure(self):
        t = make_already_optimal_tableau()
        it = Iteration(number=0, tableau=t)
        res = EngineResult(status="optimal", iterations=[it], final=t)
        assert res.status == "optimal"
        assert len(res.iterations) == 1
        assert res.final is t


class TestSolverLoop:
    """Tests the generic Simplex solve loop according to contracts section 2."""

    def test_solve_already_optimal(self):
        t = make_already_optimal_tableau()
        result = solve(t)
        assert result.status == "optimal"
        assert result.iterations == []
        assert result.final is t

    def test_solve_two_step_maximization(self):
        t = make_two_step_max_tableau()
        result = solve(t)
        assert result.status == "optimal"

        # Takes 2 pivots (Iteration 1 and Iteration 2)
        assert len(result.iterations) == 2

        # Iteration 1: enters x1, leaves s2
        assert result.iterations[0].number == 1
        assert result.iterations[0].entering == "x1"
        assert result.iterations[0].leaving == "s2"
        assert result.iterations[0].pivot == "2"

        # Iteration 2: enters x2, leaves s1
        assert result.iterations[1].number == 2
        assert result.iterations[1].entering == "x2"
        assert result.iterations[1].leaving == "s1"
        assert result.iterations[1].pivot == "1/2"

        # Final tableau checks: optimal Z = 11
        bj_idx = result.final.columns.index("bj")
        assert result.final.zj[bj_idx] == FracM(Fraction(9))

        # Basic variables must be x1 and x2
        basics = {r.basic: r.cells[-1] for r in result.final.rows}
        assert basics["x1"] == Fraction(1)
        assert basics["x2"] == Fraction(3)

    def test_solve_unbounded(self):
        t = make_unbounded_max_tableau()
        result = solve(t)
        assert result.status == "unbounded"

    def test_solve_records_degeneracy_ties(self):
        t = make_degenerate_tie_tableau()
        result = solve(t)
        # Iteration 1 enters x1 with tie between s1 and s2
        assert len(result.iterations) >= 1
        it0 = result.iterations[0]
        assert it0.entering == "x1"
        assert len(it0.ties) >= 2
        assert "s1" in it0.ties and "s2" in it0.ties

    def test_solve_max_iter_exceeded_raises_runtime_error(self):
        t = make_two_step_max_tableau()
        with pytest.raises(RuntimeError, match="Maximum iterations"):
            solve(t, max_iter=1)

    def test_solve_exactly_max_iter_pivots_is_not_exceeded(self):
        """Reaching the optimum on the last allowed pivot must not raise."""
        result = solve(make_two_step_max_tableau(), max_iter=2)
        assert result.status == "optimal"
        assert len(result.iterations) == 2

    def test_solve_iteration_snapshots_are_independent(self):
        """Verifies each snapshot in result.iterations is frozen and unaffected by subsequent pivots."""
        t = make_two_step_max_tableau()
        result = solve(t)
        # Snapshot 1 basis is s1, x1
        s1_basics = [r.basic for r in result.iterations[0].tableau.rows]
        assert s1_basics == ["s1", "x1"]

        # Snapshot 2 basis is x2, x1
        s2_basics = [r.basic for r in result.iterations[1].tableau.rows]
        assert s2_basics == ["x2", "x1"]

        # Final basis matches snapshot 2
        final_basics = [r.basic for r in result.final.rows]
        assert set(final_basics) == {"x1", "x2"}
