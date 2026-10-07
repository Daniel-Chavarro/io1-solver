"""Big-M method adapter (contracts section 3).

build(): handles <=, >= and =. Negative rhs flips the row (reported). >= gets
excess e_i plus an artificial a_i with cost -M in the z row; = gets the same
artificial. The M stays SYMBOLIC (FracM) so tables display "M" and comparisons
are exact.
"""
from time import perf_counter

from ..engine.solver import solve
from ..schemas import MethodResult, Problem
from .base import MethodNotAdmissibleError


class BigMMethod:
    id = "big_m"
    display_name = "Gran M"

    def build(self, problem: Problem):
        # TODO(P4): per docs/contracts.md section 3 - artificials with -M cost,
        # excess columns, z row with FracM, record normalized constraints.
        raise NotImplementedError("big_m.build")

    def interpret(self, engine_result, problem: Problem) -> MethodResult:
        # TODO(P4): everything simplex reports PLUS infeasibility when an
        # artificial stays basic > 0 at the end (value 0 -> degenerate note).
        raise NotImplementedError("big_m.interpret")

    def run(self, problem: Problem) -> MethodResult:
        t0 = perf_counter()
        result = solve(self.build(problem))
        return self.interpret(result, problem)
