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

    @pytest.mark.xfail(raises=NotImplementedError, reason="solve() implementation in progress (Niko784)")
    def test_solve_already_optimal(self):
        t = make_already_optimal_tableau()
        result = solve(t)
        assert result.status == "optimal"
        assert len(result.iterations) == 1
        assert result.iterations[0].number == 0
        assert result.iterations[0].entering is None
        assert result.iterations[0].leaving is None
        assert result.final is not None

    @pytest.mark.xfail(raises=NotImplementedError, reason="solve() implementation in progress (Niko784)")
    def test_solve_two_step_maximization(self):
        t = make_two_step_max_tableau()
        result = solve(t)
        assert result.status == "optimal"

        # Should take 2 pivots: Iteration 0 (initial), Iteration 1 (after pivot 1), Iteration 2 (final optimal)
        assert len(result.iterations) == 3

        # Iteration 0: enters x1, leaves s2
        assert result.iterations[0].number == 0
        assert result.iterations[0].entering == "x1"
        assert result.iterations[0].leaving == "s2"
        assert result.iterations[0].pivot == "2"

        # Iteration 1: enters x2, leaves s1
        assert result.iterations[1].number == 1
        assert result.iterations[1].entering == "x2"
        assert result.iterations[1].leaving == "s1"

        # Iteration 2: optimal
        assert result.iterations[2].number == 2
        assert result.iterations[2].entering is None
        assert result.iterations[2].leaving is None

        # Final tableau checks: optimal Z = 11
        bj_idx = result.final.columns.index("bj")
        assert result.final.zj[bj_idx] == FracM(Fraction(11))

        # Basic variables must be x1 and x2
        basics = {r.basic: r.cells[-1] for r in result.final.rows}
        assert basics["x1"] == Fraction(1)
        assert basics["x2"] == Fraction(3)

    @pytest.mark.xfail(raises=NotImplementedError, reason="solve() implementation in progress (Niko784)")
    def test_solve_unbounded(self):
        t = make_unbounded_max_tableau()
        result = solve(t)
        assert result.status == "unbounded"
        # Must retain the iteration where unboundedness was detected
        last_it = result.iterations[-1]
        assert last_it.entering == "x2"
        assert last_it.leaving is None

    @pytest.mark.xfail(raises=NotImplementedError, reason="solve() implementation in progress (Niko784)")
    def test_solve_records_degeneracy_ties(self):
        t = make_degenerate_tie_tableau()
        result = solve(t)
        # Iteration 0 enters x1 with tie between s1 and s2
        it0 = result.iterations[0]
        assert it0.entering == "x1"
        assert len(it0.ties) >= 2
        assert "s1" in it0.ties and "s2" in it0.ties
    @pytest.mark.xfail(raises=NotImplementedError, reason="solve() implementation in progress (Niko784)")
    def test_solve_max_iter_exceeded_raises_runtime_error(self):
        t = make_two_step_max_tableau()
        # Requires 2 pivots; with max_iter=1 it must raise RuntimeError
        try:
            solve(t, max_iter=1)
        except NotImplementedError:
            raise
        except RuntimeError as exc:
            assert "max_iter" in str(exc)
        else:
            pytest.fail("Expected RuntimeError when max_iter is exceeded")

    @pytest.mark.xfail(raises=NotImplementedError, reason="solve() implementation in progress (Niko784)")
    def test_solve_iteration_snapshots_are_independent(self):
        """Verifies each snapshot in result.iterations is frozen and unaffected by subsequent pivots."""
        t = make_two_step_max_tableau()
        result = solve(t)
        # Snapshot 0 basis must still be s1, s2
        s0_basics = [r.basic for r in result.iterations[0].tableau.rows]
        assert s0_basics == ["s1", "s2"]

        # Snapshot 1 basis must be s1, x1
        s1_basics = [r.basic for r in result.iterations[1].tableau.rows]
        assert s1_basics == ["s1", "x1"]

        # Final basis must be x2, x1
        final_basics = [r.basic for r in result.final.rows]
        assert set(final_basics) == {"x1", "x2"}
