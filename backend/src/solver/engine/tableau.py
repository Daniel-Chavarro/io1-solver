"""Tableau in the contractual C_j - Z_j format (contracts section 2).

Conventions:
- rows contains only constraint rows; there is no unified z row.
- zj and cj-zj are derived values, recalculated by evaluate().
- The tableau preserves the original and auxiliary columns, including
    artificial columns, so the final basis inverse remains available for
    sensitivity analysis.
- pivot() and evaluate() return NEW Tableaux (immutable snapshots).
"""
from dataclasses import dataclass, field
from typing import Literal
from .frac_m import FracM


@dataclass()
class Row:
    basic: str          # V_B: "x" | "s1" | "e1" | "a1"
    cb: FracM           # C_B: coeficiente del objetivo de la variable básica
    cells: list[FracM]  # len == len(columns)
@dataclass(frozen=True)
class Tableau:
    sense: Literal["max", "min"]
    columns: list[str]       # variables originales + auxiliares + "bj"
    cj: list[FracM]          # C_j originales del objetivo (uno por columna; "" en bj)
    rows: list[Row]          # SOLO filas de restricciones
    zj: list[FracM]          # Z_j = Σ(CB_i · a_ij); bj = valor actual de Z
    cj_zj: list[FracM]       # C_j − Z_j; "" en bj

    def pivot(self, leaving: str, entering: str) -> "Tableau":
        # Gauss-Jordan sobre rows. Actualiza V_B y C_B del leaving row.
        # NO recalcula zj ni cj_zj. Inmutable: devuelve nuevo.
        raise NotImplementedError("pivot() not implemented yet")
    
    def evaluate(self) -> "Tableau":
        # recalcula zj y cj_zj
        raise NotImplementedError("evaluate() not implemented yet")
    def entering_variable(self) -> str | None:
        # max: columna con C_j−Z_j más positivo (> 0; orden FracM)
        # min: columna con C_j−Z_j más negativo (< 0; orden FracM)
        # None → óptimo
        raise NotImplementedError("entering_variable() not implemented yet")
    
    def is_optimal(self) -> bool:
        # max: todos C_j−Z_j ≤ 0; min: todos C_j−Z_j ≥ 0
        raise NotImplementedError("is_optimal() not implemented yet")
    
    def min_ratio(self, col: str) -> tuple[str | None, list[str]]:
        # (fila saliente | None si columna sin positivos, razones como strings)
        raise NotImplementedError("min_ratio() not implemented yet")
