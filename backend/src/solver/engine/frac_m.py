"""Exact arithmetic over Fraction and a symbolic big-M (contracts section 2).

FracM represents a + b*M with a, b exact Fractions. The total order is
LEXICOGRAPHIC: the M coefficient dominates, then the constant, so
(-M - 30) < (-40). That single rule is what makes the engine pick the right
entering column for Big-M tableaus without knowing Big-M exists.
"""
from dataclasses import dataclass
from fractions import Fraction
from functools import total_ordering
from decimal import Decimal


@dataclass(frozen=True)
@total_ordering
class FracM:
    const: Fraction
    m: Fraction = Fraction(0)
    
    @classmethod
    def parse_decimal(cls, decimal_str: str) -> "FracM":
        """Parse a decimal string into a FracM, preserving exactness."""
        decimal_value = Decimal(decimal_str)
        return cls(Fraction(decimal_value))
    
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
    
    def __mul__(self, other: "FracM | Fraction | int") -> "FracM":
        if isinstance(other, (Fraction, int)):
            other = FracM(Fraction(other))
        if not isinstance(other, FracM):
            return NotImplemented
        if self.m != 0 and other.m != 0:
            raise ValueError("FracM multiplication: M*M is not allowed")
        
        const = self.const * other.const
        m = self.const * other.m + self.m * other.const
        
        return FracM(const, m)

    __rmul__ = __mul__

    def __lt__(self, other: "FracM") -> bool:
        if self.m != other.m:
            return self.m < other.m
        return self.const < other.const
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FracM):
            return False
        
        return self.m == other.m and self.const == other.const
    
    def __str__(self) -> str:
        parts = []
        if self.m != 0:
            if self.m == 1:
                parts.append("M")
            elif self.m == -1:
                parts.append("-M")
            else:
                parts.append(f"{self.m}M")
        
        if self.const != 0:
            if self.const > 0 and parts:
                parts.append(f"+{self.const}")
            else:
                parts.append(str(self.const))
        
        if not parts:
            return "0"
        
        return "".join(parts)
    