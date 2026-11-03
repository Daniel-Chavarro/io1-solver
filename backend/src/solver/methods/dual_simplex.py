"""Dual Simplex method adapter.

build(): converts every constraint to <= form:
- <= constraints keep (coeffs, rhs)
- >= constraints are multiplied by -1 -> ([-coeffs], -rhs)
- = constraints are split into two <= constraints:
    first (coeffs, rhs) and second ([-coeffs], -rhs)
Slacks s_1..s_m are added, forming the initial basis with C_B = 0.

solve_dual(): dual simplex pivots (leaving row with most negative RHS, entering
column with minimum dual ratio |(C_j - Z_j)/a_rj| over a_rj < 0) until the tableau
is primal feasible, then continues with primal simplex pivots if not yet optimal.

interpret(): serializes iterations, reporting normalized constraint conversions,
dual degenerate pivots, infeasibility, unboundedness, and alternative optima.
"""
from decimal import Decimal
from fractions import Fraction

from ..engine.frac_m import FracM
from ..engine.solver import EngineResult, solve_dual
from ..engine.tableau import Row, Tableau
from ..schemas import (
    IterationOut,
    MethodResult,
    Problem,
    SpecialCase,
    VariableValue,
)
from .base import MethodNotAdmissibleError
from .simplex import _row_ratios_str, _tableau_to_out


def _expand_constraints(
    problem: Problem,
) -> tuple[list[tuple[list[Fraction], Fraction]], set[str]]:
    """
    Expand problem constraints into <= rows and track equality-split slack pairs.
    Returns (rows_data, eq_split_slacks).
    """
    rows_data: list[tuple[list[Fraction], Fraction]] = []
    eq_split_slacks: set[str] = set()
    slack_idx = 1
    for constraint in problem.constraints:
        coeffs = [Fraction(Decimal(c)) for c in constraint.coefficients]
        rhs_val = Fraction(Decimal(constraint.rhs))
        if constraint.op == "<=":
            rows_data.append((coeffs, rhs_val))
            slack_idx += 1
        elif constraint.op == ">=":
            rows_data.append(([-c for c in coeffs], -rhs_val))
            slack_idx += 1
        elif constraint.op == "=":
            s_pos = f"s{slack_idx}"
            s_neg = f"s{slack_idx + 1}"
            eq_split_slacks.add(s_pos)
            eq_split_slacks.add(s_neg)
            rows_data.append((coeffs, rhs_val))
            rows_data.append(([-c for c in coeffs], -rhs_val))
            slack_idx += 2
        else:
            raise MethodNotAdmissibleError(
                f"Operador no soportado '{constraint.op}' en la restricción '{constraint.name}'."
            )
    return rows_data, eq_split_slacks


class DualSimplexMethod:
    id = "dual_simplex"
    display_name = "Simplex Dual"

    def build(self, problem: Problem) -> Tableau:
        if not 1 <= len(problem.variables) <= 8:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 8 variables."
            )
        if not 1 <= len(problem.constraints) <= 13:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 13 restricciones."
            )

        rows_data, _ = _expand_constraints(problem)
        m = len(rows_data)
        n_vars = len(problem.variables)
        var_names = [v.name for v in problem.variables]
        slack_names = [f"s{i + 1}" for i in range(m)]
        columns = var_names + slack_names + ["bj"]

        cj: list[FracM] = (
            [FracM.parse_decimal(c) for c in problem.objective.coefficients]
            + [FracM(Fraction(0)) for _ in range(m)]
            + [FracM(Fraction(0))]
        )

        rows: list[Row] = []
        for i, (coeffs, rhs_val) in enumerate(rows_data):
            slack_cells = [Fraction(1) if j == i else Fraction(0) for j in range(m)]
            rows.append(
                Row(
                    basic=slack_names[i],
                    cb=FracM(Fraction(0)),
                    cells=coeffs + slack_cells + [rhs_val],
                )
            )

        assert len(cj) == len(columns) and len(columns) == n_vars + m + 1

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
        _, eq_split_slacks = _expand_constraints(problem)

        special_cases: list[SpecialCase] = []

        # Record normalized constraint transformations
        for constraint in problem.constraints:
            rhs_val = Fraction(Decimal(constraint.rhs))
            if constraint.op == ">=":
                special_cases.append(
                    SpecialCase(
                        type="normalized_constraint",
                        iteration=0,
                        detail=(
                            f"La restricción '{constraint.name}' era '>=' y se multiplicó "
                            f"por -1 para pasar a '<=' (lado derecho {-rhs_val})."
                        ),
                    )
                )
            elif constraint.op == "=":
                special_cases.append(
                    SpecialCase(
                        type="normalized_constraint",
                        iteration=0,
                        detail=(
                            f"La restricción de igualdad '{constraint.name}' se desdobló "
                            f"en dos restricciones '<=' (con lados derechos {rhs_val} y {-rhs_val})."
                        ),
                    )
                )

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

        if not engine_result.iterations:
            zero_basics = [
                r.basic
                for r in initial_tableau.rows
                if r.cells[-1] == Fraction(0) and r.basic not in eq_split_slacks
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

            leaving_row = next(
                (r for r in prev_tableau.rows if r.basic == it.leaving), None
            )
            is_dual_step = leaving_row is not None and leaving_row.cells[-1] < Fraction(0)

            if is_dual_step:
                ratios_out = list(it.ratios)
                if has_tie:
                    special_cases.append(
                        SpecialCase(
                            type="degenerate_pivot",
                            iteration=it.number,
                            detail=(
                                f"Empate en la razón dual mínima entre {', '.join(it.ties)} "
                                f"al salir '{it.leaving}'."
                            ),
                        )
                    )
            else:
                ratios_out = (
                    _row_ratios_str(prev_tableau, it.entering)
                    if it.entering is not None
                    else list(it.ratios)
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

            if not has_tie:
                zero_basics = [
                    r.basic
                    for r in it.tableau.rows
                    if r.cells[-1] == Fraction(0) and r.basic not in eq_split_slacks
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
            prev_tableau = it.tableau

        if engine_result.status == "infeasible":
            bad_rows = [
                r
                for r in final_tableau.rows
                if r.cells[-1] < Fraction(0)
                and all(c >= Fraction(0) for c in r.cells[:-1])
            ]
            if not bad_rows:
                bad_rows = [r for r in final_tableau.rows if r.cells[-1] < Fraction(0)]
            bad_row = min(bad_rows, key=lambda r: r.cells[-1])
            special_cases.append(
                SpecialCase(
                    type="infeasible",
                    iteration=len(engine_result.iterations),
                    detail=(
                        f"El problema no tiene solución factible: la variable básica "
                        f"'{bad_row.basic}' tiene lado derecho negativo ({bad_row.cells[-1]}) "
                        f"y su fila no tiene coeficientes negativos para pivotear."
                    ),
                )
            )
        elif engine_result.status == "unbounded":
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
                if (
                    col_name not in basic_vars
                    and col_name not in eq_split_slacks
                    and final_tableau.cj_zj[j] == FracM(Fraction(0))
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
        result = solve_dual(initial)
        return self.interpret(result, problem)
