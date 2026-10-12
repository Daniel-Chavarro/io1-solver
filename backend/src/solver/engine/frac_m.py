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
    
    def __add__(self, other: "FracM") -> "FracM":
        const = self.const + other.const
        m = self.m + other.m
        return FracM(const, m)
    
    def __sub__(self, other: "FracM") -> "FracM":
        const = self.const - other.const
        m = self.m - other.m
        return FracM(const, m)
    
    def __neg__(self) -> "FracM":
        return FracM(-self.const, -self.m)
    
    def __mult__(self, other: "FracM") -> "FracM":
        const =  

    def __lt__(self, other: "FracM") -> bool:
        raise NotImplementedError("frac_m.FracM.__lt__")
    
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("frac_m.FracM.__eq__")