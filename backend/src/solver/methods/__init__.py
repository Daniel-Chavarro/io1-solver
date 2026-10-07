"""Method registry - adapters around the generic engine (contracts section 3)."""
from .base import Method, MethodNotAdmissibleError
from .big_m import BigMMethod
from .simplex import SimplexMethod

REGISTRY = {
    "simplex": SimplexMethod(),
    "big_m": BigMMethod(),
}

__all__ = ["REGISTRY", "Method", "MethodNotAdmissibleError",
           "SimplexMethod", "BigMMethod"]
