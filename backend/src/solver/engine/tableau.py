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
from fractions import Fraction


@dataclass()
class Row:
    basic: str          # V_B: "x" | "s1" | "e1" | "a1"
    cb: FracM           # C_B: coeficiente del objetivo de la variable básica
    cells: list[Fraction]  # len == len(columns)
@dataclass(frozen=True)
class Tableau:
    sense: Literal["max", "min"]
    columns: list[str]       # variables originales + auxiliares + "bj"
    cj: list[FracM]          # C_j originales del objetivo (uno por columna; "" en bj)
    rows: list[Row]          # SOLO filas de restricciones
    zj: list[FracM]          # Z_j = Σ(CB_i · a_ij); bj = valor actual de Z
    cj_zj: list[FracM]       # C_j − Z_j; sin incluir la columna de bj (última columna)

    def pivot(self, leaving: str, entering: str) -> "Tableau":
        # Search for the pivot row corresponding to the leaving variable
        pivot_row = next((r for r in self.rows if r.basic == leaving), None)
        if pivot_row is None:
            raise ValueError(f"Leaving variable {leaving} not found in tableau rows")
        
        # Search for the pivot column index corresponding to the entering variable
        if entering not in self.columns:
            raise ValueError(f"Entering variable {entering} not found in tableau columns")
        pivot_col_index = self.columns.index(entering)
        
        # Check if the pivot value is zero to avoid division by zero
        pivot_value = pivot_row.cells[pivot_col_index]
        if pivot_value == 0:
            raise ValueError(f"Pivot value is zero for leaving variable {leaving} and entering variable {entering}")
        
        new_rows = []
        
        for row in self.rows:
            if row.basic == leaving:
                # Update the pivot row
                new_cells = [cell / pivot_value for cell in row.cells]
                new_cb = self.cj[pivot_col_index]  # New C_B is the C_j of the entering variable
                new_row = Row(basic=entering, cb=new_cb, cells=new_cells)
            else:
                # Update other rows
                factor = row.cells[pivot_col_index] / pivot_value
                new_cells = [
                    cell - factor * pivot_row.cells[j] for j, cell in enumerate(row.cells)
                ]
                new_row = Row(basic=row.basic, cb=row.cb, cells=new_cells)
            
            # Replace the old row with the new row in the tableau
            new_rows.append(new_row)
        
        return Tableau(
            sense=self.sense,
            columns=self.columns,
            cj=self.cj,
            rows=new_rows,
            zj=self.zj,  # Will be recalculated in evaluate()
            cj_zj=self.cj_zj,  # Will be recalculated in evaluate()
        )
    
    def evaluate(self) -> "Tableau":
        # Recalculate Z_j and C_j - Z_j for all columns
        new_zj: list[FracM] = []
        new_cj_zj: list[FracM] = []
        
        for j, col in enumerate(self.columns):
            zj_value: FracM = sum(
                (row.cb * row.cells[j] for row in self.rows),
                FracM(Fraction(0), Fraction(0)),
            )
            new_zj.append(zj_value)
            if col != "bj":
                new_cj_zj.append(self.cj[j] - zj_value)
        
        return Tableau(
            sense=self.sense,
            columns=self.columns,
            cj=self.cj,
            rows=self.rows,
            zj=new_zj,
            cj_zj=new_cj_zj,
        )
    
    def get_entering_variable(self) -> str | None:
        # max: column with the largest positive C_j - Z_j; min: column with the smallest negative C_j - Z_j
        # min: column with the smallest negative C_j - Z_j
        # None → finished (optimal) or unbounded (no positive ratios)
        
        if self.sense == "max":
            candidates = [(j, cj_zj) for j, cj_zj in enumerate(self.cj_zj) if cj_zj > FracM(Fraction(0), Fraction(0))]
            if not candidates:
                return None
            entering_index = max(candidates, key=lambda x: x[1])[0]
            return self.columns[entering_index]
        else:
            candidates = [(j, cj_zj) for j, cj_zj in enumerate(self.cj_zj) if cj_zj < FracM(Fraction(0), Fraction(0))]
            if not candidates:
                return None
            entering_index = min(candidates, key=lambda x: x[1])[0]
            return self.columns[entering_index]

    def is_optimal(self) -> bool:
        # max: all C_j−Z_j ≤ 0; min: all C_j−Z_j ≥ 0
        if self.sense == "max":
            return all(cj_zj <= FracM(Fraction(0), Fraction(0)) for cj_zj in self.cj_zj)
        else:
            return all(cj_zj >= FracM(Fraction(0), Fraction(0)) for cj_zj in self.cj_zj)
    
    def get_leaving_variable(self, col: str) -> tuple[str | None, list[str], list[str]]:
        # (entering row | None if column has no positives, ratios as strings, ties as strings)
        
        col_index = self.columns.index(col)
        ratios: list[tuple[Fraction, str]] = []
        ties: list[str] = []
        
        for row in self.rows:
            if row.cells[col_index] > 0:
                ratio = row.cells[-1] / row.cells[col_index]
                ratios.append((ratio, row.basic))
        
        if not ratios:
            return (None, [], [])

        min_ratio = min(ratios, key=lambda x: x[0])
        for ratio, basic in ratios:
            if ratio == min_ratio[0]:
                ties.append(basic)

        return (min_ratio[1], [str(r[0]) for r in ratios], ties)
    
    def get_pivot_value(self, leaving: str, entering: str) -> Fraction:
        pivot_row = next((r for r in self.rows if r.basic == leaving), None)
        if pivot_row is None:
            raise ValueError(f"Leaving variable {leaving} not found in tableau rows")
        
        if entering not in self.columns:
            raise ValueError(f"Entering variable {entering} not found in tableau columns")
        pivot_col_index = self.columns.index(entering)
        
        return pivot_row.cells[pivot_col_index]