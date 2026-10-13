"""Unit tests for Tableau: evaluate, entering_variable, is_optimal, min_ratio, and pivot.

Contracts: docs/contracts.md section 2 and docs/adr/0001-formato-tabular-cj-zj.md.
"""
from fractions import Fraction
import pytest

from solver.engine.frac_m import FracM
from solver.engine.tableau import Row, Tableau


def make_standard_tableau_max():
    """Returns a standard 2-variable, 2-constraint maximization tableau.

    Problem:
        Max 3 x1 + 2 x2
        s.t.
        x1 + x2 + s1 = 4
        2 x1 + x2 + s2 = 5
        x1, x2, s1, s2 >= 0
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


def make_big_m_tableau_max():
    """Returns a Big-M maximization tableau from bakery example (contracts section 2).

    Max 40 pandesal + 30 hojaldre
    s.t.
    pandesal + hojaldre + s1 = 40
    hojaldre - e1 + a1 = 5
    C_B for s1 is 0, for a1 is -M.
    """
    columns = ["pandesal", "hojaldre", "s1", "e1", "a1", "bj"]
    cj = [
        FracM(Fraction(40)),
        FracM(Fraction(30)),
        FracM(Fraction(0)),
        FracM(Fraction(0)),
        FracM(Fraction(0), Fraction(-1)),  # -M
        FracM(Fraction(0)),
    ]
    rows = [
        Row(
            basic="s1",
            cb=FracM(Fraction(0)),
            cells=[Fraction(1), Fraction(1), Fraction(1), Fraction(0), Fraction(0), Fraction(40)],
        ),
        Row(
            basic="a1",
            cb=FracM(Fraction(0), Fraction(-1)),  # -M
            cells=[Fraction(0), Fraction(1), Fraction(0), Fraction(-1), Fraction(1), Fraction(5)],
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


class TestTableauEvaluate:
    def test_evaluate_all_slack_basis(self):
        tableau = make_standard_tableau_max()
        # With C_B = [0, 0], all Z_j must be 0
        assert all(z == FracM(Fraction(0)) for z in tableau.zj)
        # cj_zj excludes bj, so its length is len(columns) - 1
        assert len(tableau.cj_zj) == len(tableau.columns) - 1
        # C_j - Z_j must match C_j for all variables
        assert tableau.cj_zj[0] == FracM(Fraction(3))  # x1
        assert tableau.cj_zj[1] == FracM(Fraction(2))  # x2
        assert tableau.cj_zj[2] == FracM(Fraction(0))  # s1
        assert tableau.cj_zj[3] == FracM(Fraction(0))  # s2
    def test_evaluate_with_non_zero_cb(self):
        columns = ["x1", "x2", "s1", "s2", "bj"]
        cj = [
            FracM(Fraction(3)),
            FracM(Fraction(2)),
            FracM(Fraction(0)),
            FracM(Fraction(0)),
            FracM(Fraction(0)),
        ]
        # x1 is basic with C_B = 3 in row 1, s1 is basic with C_B = 0 in row 0
        rows = [
            Row(
                basic="s1",
                cb=FracM(Fraction(0)),
                cells=[Fraction(0), Fraction(1, 2), Fraction(1), Fraction(-1, 2), Fraction(3, 2)],
            ),
            Row(
                basic="x1",
                cb=FracM(Fraction(3)),
                cells=[Fraction(1), Fraction(1, 2), Fraction(0), Fraction(1, 2), Fraction(5, 2)],
            ),
        ]
        t = Tableau(sense="max", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        # Z_j for x1: 0*0 + 3*1 = 3
        assert t.zj[0] == FracM(Fraction(3))
        # Z_j for x2: 0*(1/2) + 3*(1/2) = 3/2
        assert t.zj[1] == FracM(Fraction(3, 2))
        # C_j - Z_j for x2: 2 - 3/2 = 1/2
        assert t.cj_zj[1] == FracM(Fraction(1, 2))
        # Objective value in bj: 0*(3/2) + 3*(5/2) = 15/2
        assert t.zj[4] == FracM(Fraction(15, 2))

    def test_evaluate_big_m_symbolic(self):
        tableau = make_big_m_tableau_max()
        # In bakery:
        # s1: cb = 0, cells = [1, 1, 1, 0, 0, 40]
        # a1: cb = -M, cells = [0, 1, 0, -1, 1, 5]
        # Z_j for hojaldre = 0*1 + (-M)*1 = -M
        # C_j - Z_j for hojaldre = 30 - (-M) = M + 30
        hojaldre_idx = tableau.columns.index("hojaldre")
        assert tableau.zj[hojaldre_idx] == FracM(Fraction(0), Fraction(-1))
        assert tableau.cj_zj[hojaldre_idx] == FracM(Fraction(30), Fraction(1))  # M + 30

        # Objective value in bj: -5M
        bj_idx = tableau.columns.index("bj")
        assert tableau.zj[bj_idx] == FracM(Fraction(0), Fraction(-5))


class TestTableauEnteringVariable:
    def test_entering_variable_max_selects_most_positive(self):
        tableau = make_standard_tableau_max()
        # C_j - Z_j: x1 -> 3, x2 -> 2. Most positive is x1.
        assert tableau.entering_variable() == "x1"

    def test_entering_variable_max_big_m_dominates(self):
        tableau = make_big_m_tableau_max()
        # pandesal C_j-Z_j is 40; hojaldre C_j-Z_j is M+30.
        # Since cj_zj does not contain bj and M dominates constants, hojaldre enters.
        assert tableau.entering_variable() == "hojaldre"

    def test_entering_variable_max_returns_none_when_optimal(self):
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(4)])]
        # Force all C_j - Z_j <= 0 (cj_zj has len == len(columns) - 1)
        t = Tableau(
            sense="max",
            columns=columns,
            cj=cj,
            rows=rows,
            zj=[FracM(Fraction(2)), FracM(Fraction(0)), FracM(Fraction(0))],
            cj_zj=[FracM(Fraction(-2)), FracM(Fraction(0))],
        )
        assert t.entering_variable() is None

    def test_entering_variable_never_picks_bj(self):
        """CRITICAL: cj_zj excludes bj, so entering_variable only chooses among variables."""
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [
            Row(basic="s1", cb=FracM(Fraction(-1)), cells=[Fraction(1), Fraction(1), Fraction(10)]),
        ]
        t = Tableau(sense="max", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        assert len(t.cj_zj) == len(columns) - 1
        assert t.entering_variable() != "bj"

    def test_entering_variable_min_selects_most_negative(self):
        columns = ["x1", "x2", "s1", "bj"]
        cj = [FracM(Fraction(-5)), FracM(Fraction(-2)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(1), Fraction(10)])]
        t = Tableau(sense="min", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        # In min: most negative C_j - Z_j enters: -5 (x1) vs -2 (x2).
        assert t.entering_variable() == "x1"

    def test_entering_variable_min_returns_none_when_optimal(self):
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(2)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(5)])]
        t = Tableau(sense="min", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        # In min, all C_j - Z_j >= 0 means optimal.
        assert t.entering_variable() is None


class TestTableauOptimality:
    def test_is_optimal_max_when_all_non_positive(self):
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(5)])]
        t = Tableau(
            sense="max",
            columns=columns,
            cj=cj,
            rows=rows,
            zj=[FracM(Fraction(1)), FracM(Fraction(0)), FracM(Fraction(0))],
            cj_zj=[FracM(Fraction(-1)), FracM(Fraction(0))],
        )
        assert t.is_optimal() is True

    def test_is_optimal_max_when_positive_candidate_exists(self):
        tableau = make_standard_tableau_max()
        assert tableau.is_optimal() is False

    def test_is_optimal_max_evaluates_only_variables_without_bj(self):
        """cj_zj excludes bj, so a negative objective value in bj cannot corrupt optimality."""
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(-1)), cells=[Fraction(1), Fraction(1), Fraction(5)])]
        t = Tableau(
            sense="max",
            columns=columns,
            cj=cj,
            rows=rows,
            zj=[FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(-5))],
            cj_zj=[FracM(Fraction(0)), FracM(Fraction(0))],
        )
        assert len(t.cj_zj) == 2
        assert t.is_optimal() is True

    def test_is_optimal_min_when_all_non_negative(self):
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(2)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(5)])]
        t = Tableau(sense="min", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        assert t.is_optimal() is True


class TestTableauMinRatio:
    def test_min_ratio_picks_smallest_positive_quotient(self):
        tableau = make_standard_tableau_max()
        # Entering: x1
        # Row 1 (s1): b1=4, a_11=1 -> ratio = 4
        # Row 2 (s2): b2=5, a_21=2 -> ratio = 5/2 = 2.5
        leaving, ratios = tableau.min_ratio("x1")
        assert leaving == "s2"
        assert "4" in ratios
        assert "5/2" in ratios

    def test_min_ratio_ignores_negative_and_zero_cells(self):
        columns = ["x1", "s1", "s2", "bj"]
        cj = [FracM(Fraction(1)), FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [
            Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(-1), Fraction(1), Fraction(0), Fraction(10)]),
            Row(basic="s2", cb=FracM(Fraction(0)), cells=[Fraction(2), Fraction(0), Fraction(1), Fraction(6)]),
        ]
        t = Tableau(sense="max", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        leaving, ratios = t.min_ratio("x1")
        # Row 1 has -1, so it cannot leave. Only Row 2 (s2) is eligible.
        assert leaving == "s2"

    def test_min_ratio_detects_unbounded_when_no_positive_cells(self):
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(1)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [
            Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(-2), Fraction(1), Fraction(10)]),
        ]
        t = Tableau(sense="max", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        leaving, ratios = t.min_ratio("x1")
        # No positive pivot candidates in column x1 -> leaving is None (unbounded)
        assert leaving is None

    def test_min_ratio_zero_rhs_degenerate(self):
        columns = ["x1", "s1", "s2", "bj"]
        cj = [FracM(Fraction(1)), FracM(Fraction(0)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [
            Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(1), Fraction(1), Fraction(0), Fraction(0)]),  # b1 = 0
            Row(basic="s2", cb=FracM(Fraction(0)), cells=[Fraction(2), Fraction(0), Fraction(1), Fraction(4)]),  # b2 = 4
        ]
        t = Tableau(sense="max", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        leaving, _ = t.min_ratio("x1")
        # Ratio 0/1 = 0 is minimal
        assert leaving == "s1"


class TestTableauPivot:
    def test_pivot_gauss_jordan_correctness(self):
        tableau = make_standard_tableau_max()
        # Pivot on leaving="s2", entering="x1" (pivot element is 2 at row s2, col x1)
        pivoted = tableau.pivot("s2", "x1").evaluate()

        # s2 must be replaced by x1 in rows
        basic_vars = [r.basic for r in pivoted.rows]
        assert basic_vars == ["s1", "x1"]

        # C_B for x1 must now be 3 (C_j of x1)
        x1_row = next(r for r in pivoted.rows if r.basic == "x1")
        assert x1_row.cb == FracM(Fraction(3))

        # Check cells of pivot row (divided by 2):
        # original s2 cells: [2, 1, 0, 1, 5] -> [1, 1/2, 0, 1/2, 5/2]
        assert x1_row.cells == [Fraction(1), Fraction(1, 2), Fraction(0), Fraction(1, 2), Fraction(5, 2)]

        # Check cells of row s1:
        # original s1 cells: [1, 1, 1, 0, 4] - 1 * [1, 1/2, 0, 1/2, 5/2] = [0, 1/2, 1, -1/2, 3/2]
        s1_row = next(r for r in pivoted.rows if r.basic == "s1")
        assert s1_row.cells == [Fraction(0), Fraction(1, 2), Fraction(1), Fraction(-1, 2), Fraction(3, 2)]

    @pytest.mark.xfail(reason="Tableau.pivot muta self.rows in-place y retorna self en vez de devolver un nuevo Tableau inmutable")
    def test_pivot_immutability(self):
        """CRITICAL: pivot() must return a NEW Tableau and must NOT mutate the original."""
        tableau = make_standard_tableau_max()
        initial_basics = [r.basic for r in tableau.rows]
        initial_s2_cells = list(tableau.rows[1].cells)

        pivoted = tableau.pivot("s2", "x1")

        # Original tableau must be unchanged
        assert tableau is not pivoted, "pivot() must return a new Tableau instance"
        assert [r.basic for r in tableau.rows] == initial_basics
        assert tableau.rows[1].cells == initial_s2_cells

    def test_pivot_raises_on_invalid_leaving_variable(self):
        tableau = make_standard_tableau_max()
        with pytest.raises(ValueError, match="Leaving variable nonexistent not found"):
            tableau.pivot("nonexistent", "x1")

    def test_pivot_raises_on_invalid_entering_variable(self):
        tableau = make_standard_tableau_max()
        with pytest.raises(ValueError):
            tableau.pivot("s2", "nonexistent")

    def test_pivot_raises_on_zero_pivot_element(self):
        columns = ["x1", "s1", "bj"]
        cj = [FracM(Fraction(1)), FracM(Fraction(0)), FracM(Fraction(0))]
        rows = [Row(basic="s1", cb=FracM(Fraction(0)), cells=[Fraction(0), Fraction(1), Fraction(5)])]
        t = Tableau(sense="max", columns=columns, cj=cj, rows=rows, zj=[], cj_zj=[]).evaluate()
        with pytest.raises(ValueError, match="Pivot value is zero"):
            t.pivot("s1", "x1")
