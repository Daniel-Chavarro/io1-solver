"""Exact arithmetic over Fraction and a symbolic big-M (contracts section 2).

FracM represents a + b*M with a, b exact Fractions. The total order is
LEXICOGRAPHIC: the M coefficient dominates, then the constant, so
(-M - 30) < (-40). That single rule is what makes the engine pick the right
entering column for Big-M tableaus without knowing Big-M exists.
"""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class FracM:
    const: Fraction
    m: Fraction = Fraction(0)

    # TODO(P3 - Niko784): implement per docs/contracts.md section 2:
    #   add / sub / neg / mul_fraction, __lt__/__eq__ (lexicographic),
    #   to_str() -> "5" | "3/4" | "M" | "-3M" | "-M-30" | "2M+1/3"
    #   parse_decimal(s) -> FracM  (via Decimal, exact)
    def __lt__(self, other: "FracM") -> bool:
        raise NotImplementedError("frac_m.FracM.__lt__")
