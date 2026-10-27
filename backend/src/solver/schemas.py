"""Pydantic contracts (docs/contracts.md sections 1-5).

Mirrored by frontend/src/types.ts. Numbers travel as decimal strings and are
parsed to Fraction inside the domain - never floats. All user-facing error
messages are Spanish.
"""
import re
from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator
from pydantic_core import PydanticCustomError

Sense = Literal["max", "min"]
Op = Literal["<=", ">=", "="]
NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def _error(code: str, message: str) -> PydanticCustomError:
    """Validation error whose pydantic `type` is the API error code.

    main.py's RequestValidationError handler turns it into {code, message}.
    `message` must be fully built (no template context): user text such as
    "{where}" must never be interpreted as a placeholder.
    """
    return PydanticCustomError(code, message)


def check_number(value: str, where: str) -> str:
    if isinstance(value, str) and not value.strip():
        raise _error("EMPTY_FIELD", f"Falta un valor numerico en {where}")
    if not isinstance(value, str) or not NUMBER.match(value.strip()):
        raise _error("INVALID_NUMBER", f"'{value}' no es un numero valido en {where}")
    return value


class Variable(BaseModel):
    name: str
    unit: str


class Constraint(BaseModel):
    name: str
    coefficients: list[str]
    op: Op
    rhs: str


class Objective(BaseModel):
    sense: Sense
    coefficients: list[str]


class Problem(BaseModel):
    name: str
    variables: list[Variable]
    objective: Objective
    constraints: list[Constraint]

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not v.strip():
            raise _error("EMPTY_FIELD", "El problema necesita un nombre")
        return v

    @model_validator(mode="after")
    def _consistency(self) -> "Problem":
        names = [v.name for v in self.variables]
        if any(not n.strip() for n in names):
            raise _error("EMPTY_FIELD", "Toda variable necesita nombre")
        if len(set(names)) != len(names):
            raise _error("DUPLICATE_NAME", "Hay nombres de variables duplicados")
        if not 1 <= len(names) <= 8:
            raise _error("SIZE_LIMIT", "El problema admite entre 1 y 8 variables")
        if len(self.objective.coefficients) != len(names):
            raise _error(
                "INVALID_INPUT",
                "La funcion objetivo necesita un coeficiente por variable",
            )
        for x in self.objective.coefficients:
            check_number(x, "la funcion objetivo")
        if not 1 <= len(self.constraints) <= 13:
            raise _error("SIZE_LIMIT", "El problema admite entre 1 y 13 restricciones")
        for c in self.constraints:
            if not c.name.strip():
                raise _error("EMPTY_FIELD", "Toda restriccion necesita nombre")
            if len(c.coefficients) != len(names):
                raise _error(
                    "INVALID_INPUT",
                    f"La restriccion '{c.name}' necesita {len(names)} coeficientes",
                )
            for x in c.coefficients:
                check_number(x, f"la restriccion '{c.name}'")
            check_number(c.rhs, f"la restriccion '{c.name}'")
        return self


class ResolverRequest(BaseModel):
    method: str
    problem: Problem


class SensitivityRequest(BaseModel):
    method: str
    problem: Problem


class ComparisonRequest(BaseModel):
    problem: Problem


# ---- response models ----

class TableauRow(BaseModel):
    basic: str
    cb: str
    cells: list[str]


class TableauOut(BaseModel):
    sense: Sense
    columns: list[str]
    cj: list[str]
    rows: list[TableauRow]
    zj: list[str]
    cj_zj: list[str]


class IterationOut(BaseModel):
    number: int                 # 0 = initial tableau, before any pivot
    tableau: TableauOut
    entering: Optional[str] = None
    leaving: Optional[str] = None
    pivot: Optional[str] = None
    ratios: list[str] = []
    ties: list[str] = []


class VariableValue(BaseModel):
    name: str
    unit: str
    value: str


class SpecialCase(BaseModel):
    type: str
    iteration: Optional[int] = None
    detail: str


class MethodResult(BaseModel):
    method: str
    status: str
    solution: list[VariableValue]
    objective: dict
    special_cases: list[SpecialCase]
    iterations: list[IterationOut]
    final_table: TableauOut
    elapsed_ms: float = 0.0


class ShadowPrice(BaseModel):
    constraint: str
    unit: str
    value: str
    binding: bool
    phrase: str


class ReducedCost(BaseModel):
    variable: str
    unit: str
    value: str
    phrase: str


class ObjRange(BaseModel):
    variable: str
    current: str
    range: tuple[str, str]
    phrase: str


class RhsRange(BaseModel):
    constraint: str
    current: str
    range: tuple[str, str]
    phrase: str


class SensitivityReport(BaseModel):
    shadow_prices: list[ShadowPrice]
    reduced_costs: list[ReducedCost]
    objective_ranges: list[ObjRange]
    rhs_ranges: list[RhsRange]


class MethodSummary(BaseModel):
    method: str
    status: str
    iterations: Optional[int] = None
    elapsed_ms: Optional[float] = None
    tableau_shape: Optional[str] = None


class Comparison(BaseModel):
    results: dict[str, MethodSummary]
    same_objective: Optional[bool] = None
    verdict: str