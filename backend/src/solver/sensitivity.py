"""Sensitivity analysis from the optimal tableau (contracts section 4).

analyze() re-solves the problem internally (exact and cheap) - the API receives
only {method, problem}, never a tableau. Uses the final tableau: shadow prices
from the C_B-weighted initial-identity columns (B^-1), reduced costs, and
allowable ranges per c_j and b_i, each with a Spanish decision phrase.
Special cases the course demands: infinite ranges ("-inf"/"+inf") and
restrictions with/without slack.

Only the real (M-free) part of every FracM is used: an artificial left in the
basis at value 0 must not leak M into reported numbers.
"""
from decimal import Decimal
from fractions import Fraction

from .engine.solver import solve
from .methods.base import Method
from .schemas import (
    ObjRange,
    Problem,
    ReducedCost,
    RhsRange,
    SensitivityReport,
    ShadowPrice,
)


class SensitivityNotAvailableError(Exception):
    """The problem has no optimal solution, so there is nothing to analyze."""


def _frac(text: str) -> Fraction:
    return Fraction(Decimal(text))


def _constraint_columns(problem: Problem, method: Method):
    """Per constraint: (id_col, slack_var, flipped).

    id_col is the column that was the unit vector e_i in the initial tableau
    (slack for <=, artificial for >= and =); slack_var is the slack/excess
    whose final value measures the constraint's slack (None for =).
    Mirrors the naming in SimplexMethod.build / BigMMethod.build.
    """
    if method.id != "big_m":
        return [
            (
                f"s{i + 1}",
                f"s{i + 1}",
                constraint.op == ">=" or _frac(constraint.rhs) < 0,
            )
            for i, constraint in enumerate(problem.constraints)
        ]
    out = []
    n_s = n_e = n_a = 0
    for constraint in problem.constraints:
        flipped = _frac(constraint.rhs) < 0
        op = constraint.op
        if flipped:
            op = {"<=": ">=", ">=": "<=", "=": "="}[op]
        if op == "<=":
            n_s += 1
            out.append((f"s{n_s}", f"s{n_s}", flipped))
        elif op == ">=":
            n_e += 1
            n_a += 1
            out.append((f"a{n_a}", f"e{n_e}", flipped))
        else:
            n_a += 1
            out.append((f"a{n_a}", None, flipped))
    return out



def _fmt(base: Fraction, delta: Fraction | None, inf: str) -> str:
    return inf if delta is None else str(base + delta)


def _tighten(lo, hi, bound, is_lower):
    if is_lower:
        return (bound if lo is None or bound > lo else lo), hi
    return lo, (bound if hi is None or bound < hi else hi)


def analyze(problem: Problem, method: Method) -> SensitivityReport:
    initial = method.build(problem)
    engine_result = solve(initial)
    method_result = method.interpret(engine_result, problem)
    if method_result.status != "optimal":
        raise SensitivityNotAvailableError(
            "El análisis de sensibilidad requiere una solución óptima "
            f"(el estado actual es '{method_result.status}')."
        )

    final = (
        method.restore_tableau(engine_result.final, problem)
        if hasattr(method, "restore_tableau")
        else engine_result.final
    )
    sense = problem.objective.sense
    n_vars = len(problem.variables)
    columns = final.columns
    n_cols = len(columns) - 1  # exclude bj
    rows = final.rows
    basic_vars = {r.basic for r in rows}
    row_by_basic = {r.basic: r for r in rows}
    artificial_cols = {
        c for c in columns[n_vars:-1] if c.startswith("a") and c not in
        {v.name for v in problem.variables}
    }

    def c_real(k: int) -> Fraction:
        return final.cj[k].const

    def z_real(k: int) -> Fraction:
        return sum((r.cb.const * r.cells[k] for r in rows), Fraction(0))

    def d_real(k: int) -> Fraction:
        return c_real(k) - z_real(k)

    mapping = _constraint_columns(problem, method)

    # ---- shadow prices and rhs ranges ----
    shadow_prices: list[ShadowPrice] = []
    rhs_ranges: list[RhsRange] = []
    for constraint, (id_col, slack_var, flipped) in zip(problem.constraints, mapping):
        k_id = columns.index(id_col)
        slack_val = (
            row_by_basic[slack_var].cells[-1]
            if slack_var is not None and slack_var in row_by_basic
            else Fraction(0)
        )
        binding = slack_val == 0
        pi = z_real(k_id)
        if flipped:
            pi = -pi
        if not binding:
            pi = Fraction(0)

        name = constraint.name
        if not binding:
            phrase = (
                f"La restricción '{name}' tiene una holgura de {slack_val}: como el "
                "recurso no se agota, su precio sombra es 0 y aumentar su "
                "disponibilidad no mejora Z."
            )
        elif pi == 0:
            phrase = (
                f"La restricción '{name}' es activa (sin holgura), pero su precio "
                "sombra es 0 (óptimo degenerado): una unidad adicional no cambia el "
                "valor óptimo Z."
            )
        else:
            phrase = (
                f"La restricción '{name}' es activa (sin holgura): cada unidad "
                f"adicional en su lado derecho {'aumentaría' if pi > 0 else 'disminuiría'} "
                f"el valor óptimo Z en {abs(pi)} (dentro de su rango admisible)."
            )
        shadow_prices.append(
            ShadowPrice(constraint=name, unit="", value=str(pi), binding=binding, phrase=phrase)
        )

        # rhs range
        b = _frac(constraint.rhs)
        lo = hi = None
        for r in rows:
            beta = r.cells[k_id] * (-1 if flipped else 1)
            b_bar = r.cells[-1]
            if beta > 0:
                lo, hi = _tighten(lo, hi, -b_bar / beta, True)
            elif beta < 0:
                lo, hi = _tighten(lo, hi, -b_bar / beta, False)
        low, high = _fmt(b, lo, "-inf"), _fmt(b, hi, "+inf")
        cur = str(b)
        if low == "-inf" and high == "+inf":
            rp = (f"El lado derecho de '{name}' (actual {cur}) puede variar entre "
                  "-inf y +inf manteniendo la base óptima.")
        elif low == "-inf":
            rp = (f"Mientras el lado derecho de '{name}' (actual {cur}) sea como máximo "
                  f"{high} (desde -inf hasta {high}), la base óptima y los precios "
                  "sombra se mantienen.")
        elif high == "+inf":
            rp = (f"Mientras el lado derecho de '{name}' (actual {cur}) sea al menos "
                  f"{low} (desde {low} hasta +inf), la base óptima y los precios "
                  "sombra se mantienen.")
        else:
            rp = (f"Mientras el lado derecho de '{name}' (actual {cur}) esté entre "
                  f"{low} y {high}, la base óptima y los precios sombra se mantienen.")
        rhs_ranges.append(RhsRange(constraint=name, current=cur, range=(low, high), phrase=rp))

    # ---- reduced costs and objective ranges ---
    nonbasic_cols = [
        k for k in range(n_cols)
        if columns[k] not in basic_vars and columns[k] not in artificial_cols
    ]
    reduced_costs: list[ReducedCost] = []
    objective_ranges: list[ObjRange] = []
    for j, var in enumerate(problem.variables):
        c = _frac(problem.objective.coefficients[j])
        cur = str(c)
        unit = var.unit
        if var.name not in basic_vars:
            d = d_real(j)
            if d == 0:
                phrase = (
                    f"La variable '{var.name}' ({unit}) no es básica y su costo reducido "
                    "es 0: puede entrar a la base sin cambiar el valor óptimo Z "
                    "(existen óptimos alternativos)."
                )
            elif sense == "max":
                phrase = (
                    f"La variable '{var.name}' ({unit}) no conviene producirla "
                    f"actualmente; su coeficiente en el objetivo debería aumentar en al "
                    f"menos {abs(d)} por cada {unit} para que entre al plan óptimo."
                )
            else:
                phrase = (
                    f"La variable '{var.name}' ({unit}) no está en el plan óptimo; su "
                    f"coeficiente de costo debería disminuir en al menos {abs(d)} por "
                    f"cada {unit} para que convenga incluirla."
                )
            reduced_costs.append(
                ReducedCost(variable=var.name, unit=unit, value=str(d), phrase=phrase)
            )
            z = z_real(j)
            low, high = ("-inf", str(z)) if sense == "max" else (str(z), "+inf")
        else:
            row = row_by_basic[var.name]
            lo = hi = None
            for k in nonbasic_cols:
                y = row.cells[k]
                if y == 0:
                    continue
                bound = d_real(k) / y
                # max: y>0 -> lower, y<0 -> upper ; min: reversed
                is_lower = (y > 0) if sense == "max" else (y < 0)
                lo, hi = _tighten(lo, hi, bound, is_lower)
            low, high = _fmt(c, lo, "-inf"), _fmt(c, hi, "+inf")

        if low == "-inf" and high == "+inf":
            op = (f"El coeficiente de '{var.name}' ({unit}, actual {cur}) puede tomar "
                  "cualquier valor real (-inf a +inf) sin que cambie el plan óptimo.")
        elif low == "-inf":
            op = (f"Mientras el coeficiente de '{var.name}' ({unit}, actual {cur}) sea a "
                  f"lo sumo {high} (rango desde -inf hasta {high}), el plan óptimo no cambia.")
        elif high == "+inf":
            op = (f"Mientras el coeficiente de '{var.name}' ({unit}, actual {cur}) sea al "
                  f"menos {low} (rango desde {low} hasta +inf), el plan óptimo no cambia.")
        else:
            op = (f"Mientras el coeficiente de '{var.name}' ({unit}, actual {cur}) se "
                  f"mantenga entre {low} y {high}, el plan óptimo no cambia.")
        objective_ranges.append(
            ObjRange(variable=var.name, current=cur, range=(low, high), phrase=op)
        )

    return SensitivityReport(
        shadow_prices=shadow_prices,
        reduced_costs=reduced_costs,
        objective_ranges=objective_ranges,
        rhs_ranges=rhs_ranges,
    )
