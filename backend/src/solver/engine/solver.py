"""Generic simplex loop - method-agnostic (contracts section 2).

Fixed rules for every method:
1. entering column = most positive C_j - Z_j (max) or most negative (min),
   compared with the FracM lexicographic order.
2. no candidate -> optimal.
3. min ratio; column without positive entries -> unbounded.
4. pivot, evaluate, snapshot, repeat. More than max_iter pivots ->
   RuntimeError (a bug, not a special case of the method).

The engine works in the tableau's original sense (max or min); it never
normalizes min->max and knows nothing about artificial variables.
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
    """
    Solve a linear programming problem using the simplex method.
    
    It asumes that the tableau is already in canonical form and that the problem is feasible.
    Also that the tableau is complete, i.e. all columns are present, including the artificial variables.
    """
    
    tableau: Tableau = initial
    iterations: list[Iteration] = []
    
    for i in range(max_iter + 1):
        if tableau.is_optimal():
            return EngineResult(status="optimal", iterations=iterations, final=tableau)
        
        entering = tableau.get_entering_variable()
        if entering is None:
            return EngineResult(status="optimal", iterations=iterations, final=tableau)
        
        leaving, ratios, ties = tableau.get_leaving_variable(entering)
        
        if leaving is None:
            return EngineResult(status="unbounded", iterations=iterations, final=tableau)
        
        # One more pivot would exceed the budget
        if i == max_iter:
            break
        
        pivot_value = tableau.get_pivot_value(leaving, entering)
        
        tableau = tableau.pivot(leaving, entering).evaluate()
        
        iteration = Iteration(
            number=i + 1,
            tableau=tableau,
            entering=entering,
            leaving=leaving,
            pivot=str(pivot_value),
            ratios=[str(r) for r in ratios],
            ties=ties
        )
        iterations.append(iteration)
    
    raise RuntimeError(f"Maximum iterations ({max_iter}) exceeded. Possible cycling or bug in the algorithm.")