"""Sensitivity analysis from the optimal tableau (contracts section 4).

analyze() re-solves the problem internally (exact and cheap) - the API receives
only {method, problem}, never a tableau. Uses the final tableau: shadow prices
from the z row over slack/excess/artificial columns, reduced costs, and
allowable ranges per c_j and b_i, each with a Spanish decision phrase.
Special cases the course demands: infinite ranges ("-inf"/"+inf") and
restrictions with/without slack.
"""
from .methods.base import Method
from .schemas import Problem, SensitivityReport


def analyze(problem: Problem, method: Method) -> SensitivityReport:
    # TODO(P4): per docs/contracts.md section 4
    raise NotImplementedError("sensitivity.analyze")
