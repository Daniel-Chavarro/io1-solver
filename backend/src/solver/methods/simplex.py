"""Simplex method adapter (contracts section 3).

build(): every constraint must be <= and rhs >= 0 (standard form). Slacks s_i
become the initial basis (C_B = 0) and evaluate() populates Z_j and C_j - Z_j
in the problem's original sense (max or min, per ADR 0001).
"""
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _AffineTransform:
    x0: list[Fraction]              # punto base factible (len == n)
    t_mat: list[list[Fraction]]     # matriz T (n x n): x = x0 + T @ y
    t_inv: list[list[Fraction]]     # inversa exacta T^-1 (n x n): y = T^-1 @ (x - x0)
    z0: Fraction                    # constante del objetivo c^T @ x0
    c_y: list[Fraction]             # coeficientes transformados T^T @ c
    a_y: list[list[Fraction]]       # matriz de restricciones (A @ T) en forma <= (m x n)
    b_y: list[Fraction]             # lados derechos transformados b - A @ x0 >= 0 (len == m)
    flipped: list[bool]             # True si la restricción i era >= y se multiplicó por -1
    sub_cons: dict[int, int]        # col k -> índice i de la restricción cuyo exceso define y_k
    detail: str                     # explicación en español del cambio de variables aplicado


def _build_affine_transform(problem: Problem) -> _AffineTransform | None:
    if not 1 <= len(problem.variables) <= 8:
        raise MethodNotAdmissibleError("El problema admite entre 1 y 8 variables.")
    if not 1 <= len(problem.constraints) <= 13:
        raise MethodNotAdmissibleError("El problema admite entre 1 y 13 restricciones.")

    for constraint in problem.constraints:
        if constraint.op == "=":
            raise MethodNotAdmissibleError(
                f"El método Simplex solo admite restricciones <= "
                f"(la restricción '{constraint.name}' usa '='). Usa el método de la Gran M."
            )
        if constraint.op == "<=":
            rhs_val = Fraction(Decimal(constraint.rhs))
            if rhs_val < 0:
                raise MethodNotAdmissibleError(
                    f"El método Simplex requiere lados derechos (RHS) no negativos "
                    f"(la restricción '{constraint.name}' tiene RHS = {constraint.rhs}). "
                    f"Usa el método de la Gran M."
                )

    if all(constraint.op == "<=" for constraint in problem.constraints):
        return None

    if not any(constraint.op == "<=" for constraint in problem.constraints):
        first_ge = next(c for c in problem.constraints if c.op == ">=")
        raise MethodNotAdmissibleError(
            f"El método Simplex solo admite restricciones <= "
            f"(la restricción '{first_ge.name}' usa '{first_ge.op}'). Usa el método de la Gran M."
        )

    n = len(problem.variables)
    m = len(problem.constraints)

    A: list[list[Fraction]] = []
    b: list[Fraction] = []
    flipped: list[bool] = []
    for constraint in problem.constraints:
        coeffs = [Fraction(Decimal(co)) for co in constraint.coefficients]
        rhs = Fraction(Decimal(constraint.rhs))
        if constraint.op == "<=":
            A.append(coeffs)
            b.append(rhs)
            flipped.append(False)
        else:  # >=
            A.append([-co for co in coeffs])
            b.append(-rhs)
            flipped.append(True)

    x0 = [Fraction(0)] * n
    t_mat = [[Fraction(1) if r == c else Fraction(0) for c in range(n)] for r in range(n)]
    single_lb_cols: set[int] = set()
    pivoted_cols: set[int] = set()
    sub_cons: dict[int, int] = {}

    # Paso 1: cotas inferiores de una sola variable
    for i, (row, bi) in enumerate(zip(A, b)):
        nz = [r for r in range(n) if row[r] != 0]
        if len(nz) == 1:
            k = nz[0]
            if row[k] < 0 and bi < 0:
                lb = bi / row[k]
                if lb > x0[k]:
                    x0[k] = lb
                    single_lb_cols.add(k)
                    sub_cons[k] = i

    # Paso 2: sustitución gaussiana de exceso en restricciones >= multivariables activas
    for i in range(m):
        deficit = sum(A[i][r] * x0[r] for r in range(n)) - b[i]
        if deficit > 0:
            row_y = [sum(-A[i][r] * t_mat[r][j] for r in range(n)) for j in range(n)]
            candidates = [k for k in range(n) if row_y[k] > 0 and k not in pivoted_cols]
            if not candidates:
                raise MethodNotAdmissibleError(
                    f"El método Simplex solo admite restricciones <= "
                    f"(la restricción '{problem.constraints[i].name}' no admite transformación equivalente factible). "
                    f"Usa el método de la Gran M."
                )
            free_candidates = [k for k in candidates if k not in single_lb_cols]
            k = free_candidates[-1] if free_candidates else candidates[-1]
            rk = row_y[k]
            for r in range(n):
                t_rk = t_mat[r][k]
                if t_rk != 0:
                    x0[r] += t_rk * (deficit / rk)
                    for j in range(n):
                        if j != k:
                            t_mat[r][j] -= t_rk * (row_y[j] / rk)
                    t_mat[r][k] = t_rk / rk
            pivoted_cols.add(k)
            sub_cons[k] = i

    # Verificación de factibilidad del punto base x0
    b_y = [b[i] - sum(A[i][r] * x0[r] for r in range(n)) for i in range(m)]
    if any(x < 0 for x in x0) or any(val < 0 for val in b_y):
        raise MethodNotAdmissibleError(
            "El método Simplex solo admite restricciones <= "
            "(las restricciones >= no admiten transformación factible a forma estándar). "
            "Usa el método de la Gran M."
        )

    t_inv = [[Fraction(1) if r == c else Fraction(0) for c in range(n)] for r in range(n)]
    for k, i_con in sub_cons.items():
        t_inv[k] = [-v for v in A[i_con]]

    a_y = [[sum(A[i][r] * t_mat[r][k] for r in range(n)) for k in range(n)] for i in range(m)]
    c_orig = [Fraction(Decimal(co)) for co in problem.objective.coefficients]
    z0 = sum(c_orig[r] * x0[r] for r in range(n))
    c_y = [sum(c_orig[r] * t_mat[r][k] for r in range(n)) for k in range(n)]

    detail = (
        "Se aplicó transformación al problema equivalente por cambio de variables (x = x⁰ + T·y) "
        "para resolver restricciones >= con Simplex estándar: vértice inicial ("
        + ", ".join(f"{problem.variables[r].name}={x0[r]}" for r in range(n))
        + f") y Z inicial = {z0}."
    )

    return _AffineTransform(
        x0=x0,
        t_mat=t_mat,
        t_inv=t_inv,
        z0=z0,
        c_y=c_y,
        a_y=a_y,
        b_y=b_y,
        flipped=flipped,
        sub_cons=sub_cons,
        detail=detail,
    )


def uses_equivalent_transform(problem: Problem) -> bool:
    """Indica si el problema requiere y admite transformación afín al problema equivalente."""
    try:
        return _build_affine_transform(problem) is not None
    except MethodNotAdmissibleError:
        return False


def _tableau_to_out(tableau: Tableau, z_offset: Fraction = Fraction(0)) -> TableauOut:
    """Serialize an immutable engine Tableau into the API TableauOut contract."""
    zj_out = [str(z) for z in tableau.zj]
    if z_offset != 0 and tableau.zj:
        zj_out[-1] = str(tableau.zj[-1] + FracM(z_offset))
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
        zj=zj_out,
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
        if self.id == "simplex":
            tf = _build_affine_transform(problem)
            if tf is not None:
                n_cons = len(problem.constraints)
                var_names = [v.name for v in problem.variables]
                slack_names = [f"s{i + 1}" for i in range(n_cons)]
                columns = var_names + slack_names + ["bj"]
                cj = (
                    [FracM(c) for c in tf.c_y]
                    + [FracM(Fraction(0)) for _ in range(n_cons)]
                    + [FracM(Fraction(0))]
                )
                rows: list[Row] = []
                for i in range(n_cons):
                    var_cells = tf.a_y[i]
                    slack_cells = [
                        Fraction(1) if j == i else Fraction(0) for j in range(n_cons)
                    ]
                    rhs_cell = tf.b_y[i]
                    rows.append(
                        Row(
                            basic=slack_names[i],
                            cb=FracM(Fraction(0)),
                            cells=var_cells + slack_cells + [rhs_cell],
                        )
                    )
                assert len(cj) == len(columns)
                return Tableau(
                    sense=problem.objective.sense,
                    columns=columns,
                    cj=cj,
                    rows=rows,
                    zj=[],
                    cj_zj=[],
                ).evaluate()

        if not 1 <= len(problem.variables) <= 8:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 8 variables."
            )
        if not 1 <= len(problem.constraints) <= 13:
            raise MethodNotAdmissibleError(
                "El problema admite entre 1 y 13 restricciones."
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

    def restore_tableau(self, final_tableau: Tableau, problem: Problem) -> Tableau:
        if self.id != "simplex":
            return final_tableau
        tf = _build_affine_transform(problem)
        if tf is None:
            return final_tableau

        n = len(problem.variables)
        m = len(problem.constraints)

        basic_vals_y = {r.basic: r.cells[-1] for r in final_tableau.rows}
        y_opt = [basic_vals_y.get(v.name, Fraction(0)) for v in problem.variables]
        x_opt = [
            tf.x0[j] + sum(tf.t_mat[j][k] * y_opt[k] for k in range(n))
            for j in range(n)
        ]

        rows_x: list[Row] = []
        for r in final_tableau.rows:
            m_x = [
                sum(r.cells[k] * tf.t_inv[k][j] for k in range(n))
                for j in range(n)
            ]
            rhs_x = r.cells[-1] + sum(m_x[j] * tf.x0[j] for j in range(n))
            cells_x = m_x + r.cells[n:-1] + [rhs_x]
            rows_x.append(Row(basic=r.basic, cb=FracM(Fraction(0)), cells=cells_x))

        cj_x = (
            [FracM.parse_decimal(c) for c in problem.objective.coefficients]
            + [FracM(Fraction(0))] * (m + 1)
        )
        tab_x = Tableau(
            sense=problem.objective.sense,
            columns=list(final_tableau.columns),
            cj=cj_x,
            rows=rows_x,
            zj=[],
            cj_zj=[],
        )

        for k, v in enumerate(problem.variables):
            v_name = v.name
            found_row = next(
                (r_idx for r_idx, r in enumerate(tab_x.rows) if r.basic == v_name),
                None,
            )
            if found_row is not None:
                tab_x = tab_x.pivot(tab_x.rows[found_row].basic, v_name)
            elif x_opt[k] > 0 and k in tf.sub_cons:
                s_name = f"s{tf.sub_cons[k] + 1}"
                found_s_row = next(
                    (r_idx for r_idx, r in enumerate(tab_x.rows) if r.basic == s_name),
                    None,
                )
                if found_s_row is not None:
                    tab_x = tab_x.pivot(s_name, v_name)

        return tab_x.evaluate()
    def interpret(self, engine_result: EngineResult, problem: Problem) -> MethodResult:
        tf = _build_affine_transform(problem) if self.id == "simplex" else None
        z_offset = tf.z0 if tf is not None else Fraction(0)
        sub_slacks = (
            {f"s{i_con + 1}" for i_con in tf.sub_cons.values()}
            if tf is not None
            else set()
        )

        initial_tableau = self.build(problem)
        final_tableau = engine_result.final

        iterations_out: list[IterationOut] = [
            IterationOut(
                number=0,
                tableau=_tableau_to_out(initial_tableau, z_offset=z_offset),
                entering=None,
                leaving=None,
                pivot=None,
                ratios=[],
                ties=[],
            )
        ]

        special_cases: list[SpecialCase] = []
        if tf is not None:
            special_cases.append(
                SpecialCase(
                    type="normalized_constraint",
                    iteration=0,
                    detail=tf.detail,
                )
            )

        # Check initial tableau for basic variables at 0 if no pivots occur
        if not engine_result.iterations:
            zero_basics = [
                r.basic
                for r in initial_tableau.rows
                if r.cells[-1] == Fraction(0) and r.basic not in sub_slacks
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
                    tableau=_tableau_to_out(it.tableau, z_offset=z_offset),
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
                    r.basic
                    for r in it.tableau.rows
                    if r.cells[-1] == Fraction(0) and r.basic not in sub_slacks
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
            if tf is not None:
                final_tableau = self.restore_tableau(engine_result.final, problem)
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
            final_table=_tableau_to_out(
                final_tableau,
                z_offset=z_offset
                if tf is not None and engine_result.status != "optimal"
                else Fraction(0),
            ),
        )
    def run(self, problem: Problem) -> MethodResult:
        initial = self.build(problem)
        result = solve(initial)
        return self.interpret(result, problem)

