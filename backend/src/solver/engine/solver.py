"""Generic simplex loop - method-agnostic (contracts section 2).

Fixed rules for every method:
1. entering column = most negative z entry (FracM lexicographic order).
2. no negative entries -> optimal.
3. min ratio; column without positive entries -> unbounded (iteration kept).
4. pivot, snapshot, repeat. max_iter exceeded -> RuntimeError (a bug, not a
   special case of the method).

The engine ALWAYS maximizes; min->max normalization belongs to method builders.
"""
from dataclasses import dataclass, field
from typing import Literal

from .tableau import Tableau


@dataclass
class Iteration:
    number: int                 # 0 = initial tableau, before any pivot
    tableau: Tableau            # snapshot AFTER pivot n (n >= 1)
    entering: str | None = None
    leaving: str | None = None
    pivot: str | None = None    # pivot element as string, e.g. "2/3"
    ratios: list[str] = field(default_factory=list)
    ties: list[str] = field(default_factory=list)


@dataclass
class EngineResult:
    status: Literal["optimal", "unbounded"]
    iterations: list[Iteration]
    final: Tableau


def solve(initial: Tableau, max_iter: int = 200) -> EngineResult:
    # TODO(P3 - Niko784): implement the loop per docs/contracts.md section 2
    raise NotImplementedError("engine.solve")
