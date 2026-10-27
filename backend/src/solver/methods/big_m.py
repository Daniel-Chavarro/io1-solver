"""Big-M method adapter (contracts section 3).

build(): handles <=, >= and =. Negative rhs flips the row (reported). >= gets
excess e_i plus an artificial a_i; = gets the same artificial. Artificials cost
-M when maximizing and +M when minimizing. The M stays SYMBOLIC (FracM) so
tables display "M" and comparisons are exact.

interpret(): everything simplex reports (inherited) PLUS infeasibility when an
artificial stays basic with value > 0 at the optimum (value 0 -> degenerate
note, not infeasible).
"""
from decimal import Decimal
from fractions import Fraction

from ..engine.frac_m import FracM
from ..engine.solver import EngineResult
from ..engine.tableau import Row, Tableau
from ..schemas import MethodResult, Problem, SpecialCase
from .base import MethodNotAdmissibleError
from .simplex import SimplexMethod

_FLIP = {"<=": ">=", ">=": "<=", "=": "="}


def _normalized_rows(problem: Problem) -> list[tuple[list[Fraction], str, Fraction, bool]]:
    """Return (coefficients, op, rhs, flipped) per constraint with rhs >= 0."""
    rows = []
    for constraint in problem.constraints:
        coeffs = [Fraction(Decimal(c)) for c in constraint.coefficients]
        op = constraint.op
        rhs = Fraction(Decimal(constraint.rhs))
        flipped = rhs < 0
        if flipped:
            coeffs = [-c for c in coeffs]
            op = _FLIP[op]
            rhs = -rhs
        rows.append((coeffs, op, rhs, flipped))
    return rows


class BigMMethod(SimplexMethod):
    id = "big_m"
    display_name = "Gran M"

    def build(self, problem: Problem) -> Tableau:
        if not 1 <= len(problem.variables) <= 8:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 8 variables."
            )
        if not 1 <= len(problem.constraints) <= 13:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 13 restricciones."
            )

        normalized = _normalized_rows(problem)
        n_cons = len(normalized)

        # Auxiliary names are numbered per kind, in constraint order:
        # [<=, >=, <=, =] -> s1, e1, a1, s2, a2
        slack_of: dict[int, str] = {}
        excess_of: dict[int, str] = {}
        artificial_of: dict[int, str] = {}
        for i, (_, op, _, _) in enumerate(normalized):
            if op == "<=":
                slack_of[i] = f"s{len(slack_of) + 1}"
            else:
                if op == ">=":
                    excess_of[i] = f"e{len(excess_of) + 1}"
                artificial_of[i] = f"a{len(artificial_of) + 1}"

        var_names = [v.name for v in problem.variables]
        aux_names = (
            list(slack_of.values())
            + list(excess_of.values())
            + list(artificial_of.values())
        )
        columns = var_names + aux_names + ["bj"]

        penalty = FracM(Fraction(0), Fraction(-1 if problem.objective.sense == "max" else 1))
        zero = FracM(Fraction(0))
        cj: list[FracM] = (
            [FracM.parse_decimal(c) for c in problem.objective.coefficients]
            + [zero] * (len(slack_of) + len(excess_of))
            + [penalty] * len(artificial_of)
            + [zero]  # placeholder for bj column
        )

        rows: list[Row] = []
        for i, (coeffs, _, rhs, _) in enumerate(normalized):
            aux_cells = []
            for name in aux_names:
                if name == slack_of.get(i) or name == artificial_of.get(i):
                    aux_cells.append(Fraction(1))
                elif name == excess_of.get(i):
                    aux_cells.append(Fraction(-1))
                else:
                    aux_cells.append(Fraction(0))
            if i in slack_of:
                basic, cb = slack_of[i], zero
            else:
                basic, cb = artificial_of[i], penalty
            rows.append(Row(basic=basic, cb=cb, cells=coeffs + aux_cells + [rhs]))

        assert len(cj) == len(columns) and all(len(r.cells) == len(columns) for r in rows)
        assert len(rows) == n_cons

        return Tableau(
            sense=problem.objective.sense,
            columns=columns,
            cj=cj,
            rows=rows,
            zj=[],
            cj_zj=[],
        ).evaluate()

    def interpret(self, engine_result: EngineResult, problem: Problem) -> MethodResult:
        base = super().interpret(engine_result, problem)
        status = base.status
        special_cases: list[SpecialCase] = []

        for (_, op, _, flipped), constraint in zip(_normalized_rows(problem), problem.constraints):
            if flipped:
                special_cases.append(
                    SpecialCase(
                        type="normalized_constraint",
                        iteration=0,
                        detail=(
                            f"La restricción '{constraint.name}' tenía lado derecho "
                            f"negativo ({constraint.rhs}); se multiplicó por -1 y pasó "
                            f"de '{constraint.op}' a '{op}'."
                        ),
                    )
                )

        special_cases.extend(base.special_cases)

        if engine_result.status == "optimal":
            final = engine_result.final
            n_vars = len(problem.variables)
            artificials = {c for c in final.columns[n_vars:-1] if c.startswith("a")}
            last_iter = len(engine_result.iterations)
            for row in final.rows:
                if row.basic not in artificials:
                    continue
                if row.cells[-1] > 0:
                    status = "infeasible"
                    special_cases.append(
                        SpecialCase(
                            type="infeasible",
                            iteration=last_iter,
                            detail=(
                                f"El problema no tiene solución factible: la artificial "
                                f"{row.basic} quedó en la base con valor {row.cells[-1]}."
                            ),
                        )
                    )
                else:
                    special_cases.append(
                        SpecialCase(
                            type="degenerate_pivot",
                            iteration=last_iter,
                            detail=(
                                f"La artificial {row.basic} quedó en la base con valor 0: "
                                f"la solución es degenerada pero factible."
                            ),
                        )
                    )
            if status == "infeasible":
                # An "alternative optimum" of an infeasible tableau means nothing.
                special_cases = [c for c in special_cases if c.type != "alternative_optima"]

        return base.model_copy(update={"status": status, "special_cases": special_cases})
