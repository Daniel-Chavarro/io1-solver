"""Simplex method adapter (contracts section 3).

build(): every constraint must be <= and rhs >= 0 (standard form). Slacks s_i
become the initial basis (C_B = 0) and evaluate() populates Z_j and C_j - Z_j
in the problem's original sense (max or min, per ADR 0001).
"""
from decimal import Decimal
from fractions import Fraction

from ..engine.frac_m import FracM
from ..engine.solver import EngineResult, solve
from ..engine.tableau import Row, Tableau
from ..schemas import (
    IterationOut,
    MethodResult,
    Problem,
    SpecialCase,
    TableauOut,
    TableauRow,
    VariableValue,
)
from .base import MethodNotAdmissibleError


def _tableau_to_out(tableau: Tableau) -> TableauOut:
    """Serialize an immutable engine Tableau into the API TableauOut contract."""
    return TableauOut(
        sense=tableau.sense,
        columns=list(tableau.columns),
        cj=[str(c) for c in tableau.cj[:-1]] + [""],
        rows=[
            TableauRow(
                basic=r.basic,
                cb=str(r.cb),
                cells=[str(cell) for cell in r.cells],
            )
            for r in tableau.rows
        ],
        zj=[str(z) for z in tableau.zj],
        cj_zj=[str(cz) for cz in tableau.cj_zj],
    )


def _row_ratios_str(tableau: Tableau, entering: str) -> list[str]:
    """Return per-row minimum-ratio strings ('-' when cell <= 0) for a step."""
    col_idx = tableau.columns.index(entering)
    ratios: list[str] = []
    for row in tableau.rows:
        coeff = row.cells[col_idx]
        if coeff > 0:
            ratios.append(str(row.cells[-1] / coeff))
        else:
            ratios.append("-")
    return ratios


class SimplexMethod:
    id = "simplex"
    display_name = "Simplex"

    def build(self, problem: Problem) -> Tableau:
        if not 1 <= len(problem.variables) <= 8:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 8 variables."
            )
        if not 1 <= len(problem.constraints) <= 8:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 8 restricciones."
            )

        for constraint in problem.constraints:
            if constraint.op != "<=":
                raise MethodNotAdmissibleError(
                    f"El método Simplex solo admite restricciones <= "
                    f"(la restricción '{constraint.name}' usa '{constraint.op}'). "
                    f"Usa el método de la Gran M."
                )
            rhs_val = Fraction(Decimal(constraint.rhs))
            if rhs_val < 0:
                raise MethodNotAdmissibleError(
                    f"El método Simplex requiere lados derechos (RHS) no negativos "
                    f"(la restricción '{constraint.name}' tiene RHS = {constraint.rhs}). "
                    f"Usa el método de la Gran M."
                )

        n_vars = len(problem.variables)
        n_cons = len(problem.constraints)

        var_names = [v.name for v in problem.variables]
        slack_names = [f"s{i + 1}" for i in range(n_cons)]
        columns = var_names + slack_names + ["bj"]

        cj: list[FracM] = (
            [FracM.parse_decimal(c) for c in problem.objective.coefficients]
            + [FracM(Fraction(0)) for _ in range(n_cons)]
            + [FracM(Fraction(0))]  # placeholder for bj column
        )

        rows: list[Row] = []
        for i, constraint in enumerate(problem.constraints):
            var_cells = [Fraction(Decimal(c)) for c in constraint.coefficients]
            slack_cells = [
                Fraction(1) if j == i else Fraction(0) for j in range(n_cons)
            ]
            rhs_cell = Fraction(Decimal(constraint.rhs))
            rows.append(
                Row(
                    basic=slack_names[i],
                    cb=FracM(Fraction(0)),
                    cells=var_cells + slack_cells + [rhs_cell],
                )
            )

        assert len(cj) == len(columns) and len(columns) == n_vars + n_cons + 1

        return Tableau(
            sense=problem.objective.sense,
            columns=columns,
            cj=cj,
            rows=rows,
            zj=[],
            cj_zj=[],
        ).evaluate()

    def interpret(self, engine_result: EngineResult, problem: Problem) -> MethodResult:
        initial_tableau = self.build(problem)
        final_tableau = engine_result.final

        iterations_out: list[IterationOut] = [
            IterationOut(
                number=0,
                tableau=_tableau_to_out(initial_tableau),
                entering=None,
                leaving=None,
                pivot=None,
                ratios=[],
                ties=[],
            )
        ]

        special_cases: list[SpecialCase] = []

        # Check initial tableau for basic variables at 0 if no pivots occur
        if not engine_result.iterations:
            zero_basics = [
                r.basic for r in initial_tableau.rows if r.cells[-1] == Fraction(0)
            ]
            if zero_basics:
                special_cases.append(
                    SpecialCase(
                        type="degenerate_pivot",
                        iteration=0,
                        detail=(
                            f"Solución básica degenerada en la tabla inicial: "
                            f"{', '.join(zero_basics)} tiene valor 0."
                        ),
                    )
                )

        prev_tableau = initial_tableau
        for it in engine_result.iterations:
            has_tie = len(it.ties) > 1
            ties_out = list(it.ties) if has_tie else []
            ratios_out = (
                _row_ratios_str(prev_tableau, it.entering)
                if it.entering is not None
                else list(it.ratios)
            )

            iterations_out.append(
                IterationOut(
                    number=it.number,
                    tableau=_tableau_to_out(it.tableau),
                    entering=it.entering,
                    leaving=it.leaving,
                    pivot=it.pivot,
                    ratios=ratios_out,
                    ties=ties_out,
                )
            )

            if has_tie:
                special_cases.append(
                    SpecialCase(
                        type="degenerate_pivot",
                        iteration=it.number,
                        detail=(
                            f"Empate en la razón mínima entre {', '.join(it.ties)} "
                            f"al entrar '{it.entering}'."
                        ),
                    )
                )
            else:
                zero_basics = [
                    r.basic for r in it.tableau.rows if r.cells[-1] == Fraction(0)
                ]
                if zero_basics:
                    special_cases.append(
                        SpecialCase(
                            type="degenerate_pivot",
                            iteration=it.number,
                            detail=(
                                f"Solución básica degenerada: la variable básica "
                                f"'{zero_basics[0]}' tomó valor 0."
                            ),
                        )
                    )

            prev_tableau = it.tableau

        if engine_result.status == "unbounded":
            entering = final_tableau.get_entering_variable()
            unbounded_iter_num = len(engine_result.iterations) + 1
            special_cases.append(
                SpecialCase(
                    type="unbounded",
                    iteration=unbounded_iter_num,
                    detail=(
                        f"El problema no está acotado: la variable que entra "
                        f"'{entering}' no tiene coeficientes positivos en su columna."
                    ),
                )
            )
        elif engine_result.status == "optimal":
            basic_vars = {r.basic for r in final_tableau.rows}
            alt_vars: list[str] = []
            for j, col_name in enumerate(final_tableau.columns[:-1]):
                if col_name not in basic_vars and final_tableau.cj_zj[j] == FracM(
                    Fraction(0)
                ):
                    alt_vars.append(col_name)
            if alt_vars:
                special_cases.append(
                    SpecialCase(
                        type="alternative_optima",
                        iteration=len(engine_result.iterations),
                        detail=(
                            f"Existen óptimos alternativos: "
                            f"{', '.join(alt_vars)} no está en la base y su "
                            f"criterio C_j - Z_j es 0 en la tabla final."
                        ),
                    )
                )

        basic_values = {r.basic: r.cells[-1] for r in final_tableau.rows}
        solution = [
            VariableValue(
                name=v.name,
                unit=v.unit,
                value=str(basic_values.get(v.name, Fraction(0))),
            )
            for v in problem.variables
        ]

        z_value = str(final_tableau.zj[-1]) if final_tableau.zj else "0"

        return MethodResult(
            method=self.id,
            status=engine_result.status,
            solution=solution,
            objective={"sense": problem.objective.sense, "value": z_value},
            special_cases=special_cases,
            iterations=iterations_out,
            final_table=_tableau_to_out(final_tableau),
        )

    def run(self, problem: Problem) -> MethodResult:
        initial = self.build(problem)
        result = solve(initial)
        return self.interpret(result, problem)

