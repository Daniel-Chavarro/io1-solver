"""Fixture-driven tests over examples/*.json (contracts section 7).

The same JSON feeds the UI (/api/ejemplos) and pytest. Skips come off as each
method lands: simplex -> TODO(P3), big_m + infeasible -> TODO(P4).
"""
import json
from pathlib import Path

import pytest

from solver.methods import REGISTRY, MethodNotAdmissibleError
from solver.schemas import Problem

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
CASES = [
    pytest.param(
        eid,
        method,
        marks=pytest.mark.skip(reason="TODO(P4): quitar cuando big_m este implementado")
        if method == "big_m"
        else (),
    )
    for eid in ("bakery-real", "test-unbounded", "test-infeasible")
    for method in ("simplex", "big_m")
]


def _load(example_id):
    return json.loads((EXAMPLES / f"{example_id}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(("example_id", "method_id"), CASES)
def test_fixture(example_id, method_id):
    ex = _load(example_id)
    expected = ex["expected"][method_id]
    problem = Problem(**ex["problem"])
    if expected.get("admissible") is False:
        with pytest.raises(MethodNotAdmissibleError):
            REGISTRY[method_id].build(problem)
        return
    result = REGISTRY[method_id].run(problem)
    assert result.status == expected["status"]
    if "objective_value" in expected:
        assert result.objective["value"] == expected["objective_value"]
