"""Tableau: rows of FracM cells with an always-first z row (contracts section 2).

Conventions:
- rows[0] is the z row; it stores z_j - c_j and its rhs cell is the current z.
- Aux columns keep their identity columns forever (never dropped): the final
  basis inverse lives there and sensitivity needs it.
- pivot() returns a NEW Tableau (immutable) so iteration snapshots are free.
"""
from dataclasses import dataclass, field

from .frac_m import FracM


@dataclass
class Row:
    basic: str                      # "x1" | "s1" | "e1" | "a1" | "z"
    cells: list[FracM] = field(default_factory=list)


@dataclass
class Tableau:
    columns: list[str] = field(default_factory=list)   # vars + aux + "rhs"
    rows: list[Row] = field(default_factory=list)     # rows[0] = z row

    # TODO(P3 - Niko784): implement per docs/contracts.md section 2
    def pivot(self, basic_row: str, col: str) -> "Tableau":
        raise NotImplementedError("tableau.pivot")

    def most_negative_z_entry(self) -> str | None:
        raise NotImplementedError("tableau.most_negative_z_entry")

    def is_optimal(self) -> bool:
        raise NotImplementedError("tableau.is_optimal")

    def min_ratio(self, col: str) -> tuple[str | None, list[str]]:
        raise NotImplementedError("tableau.min_ratio")
