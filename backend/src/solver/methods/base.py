"""Shared method protocol (contracts section 3)."""
from typing import Protocol

from ..schemas import MethodResult, Problem


class MethodNotAdmissibleError(Exception):
    """Raised by build() when the problem cannot be handled by this method."""


class Method(Protocol):
    id: str
    display_name: str

    def build(self, problem: Problem):
        ...

    def interpret(self, engine_result, problem: Problem) -> MethodResult:
        ...

    def run(self, problem: Problem) -> MethodResult:
        ...
