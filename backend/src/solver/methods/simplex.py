"""Simplex method adapter (contracts section 3).

build(): every constraint must be <= and rhs >= 0 (standard form). Slacks s_i
become the initial basis. min->max normalization is done here and undone by
interpret() when reporting.
"""
from time import perf_counter

from ..engine.solver import solve
from ..schemas import MethodResult, Problem
from .base import MethodNotAdmissibleError


class SimplexMethod:
    id = "simplex"
    display_name = "Simplex"

    def build(self, problem: Problem):
        # TODO(P3 - Niko784): validate all-<= and rhs >= 0 (else raise
        # MethodNotAdmissibleError with a Spanish message), normalize min->max,
        # add s_i slacks, build the z row from the objective.
        raise NotImplementedError("simplex.build")

    def interpret(self, engine_result, problem: Problem) -> MethodResult:
        # TODO(P3 - Niko784): unbounded / degenerate pivots / alternative
        # optima (nonbasic with reduced cost 0), solution with original
        # variables/units, z in the original sense.
        raise NotImplementedError("simplex.interpret")

    def run(self, problem: Problem) -> MethodResult:
        t0 = perf_counter()
        result = solve(self.build(problem))
        return self.interpret(result, problem)
