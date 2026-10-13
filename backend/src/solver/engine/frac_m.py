"""Exact arithmetic over Fraction and a symbolic big-M (contracts section 2).

FracM represents a + b*M with a, b exact Fractions. The total order is
LEXICOGRAPHIC: the M coefficient dominates, then the constant, so
(-M - 30) < (-40). That single rule is what makes the engine pick the right
entering column for Big-M tableaus without knowing Big-M exists.
"""
from dataclasses import dataclass
from fractions import Fraction
from functools import total_ordering


@dataclass(frozen=True)
@total_ordering
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
    
    def __mul__(self, other: "FracM") -> "FracM":
        if self.m != 0 and other.m != 0:
            raise ValueError("FracM multiplication: M*M is not allowed")
        
        const = self.const * other.const
        m = self.const * other.m + self.m * other.const
        
        return FracM(const, m)
    

    def __lt__(self, other: "FracM") -> bool:
        if self.m != other.m:
            return self.m < other.m
        return self.const < other.const
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FracM):
            return False
        
        return self.m == other.m and self.const == other.const