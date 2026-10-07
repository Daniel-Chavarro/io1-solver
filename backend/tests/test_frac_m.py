"""FracM unit tests - flip the skip when engine/frac_m.py lands (contracts section 2)."""
from fractions import Fraction

import pytest

from solver.engine.frac_m import FracM

pytestmark = pytest.mark.skip(reason="TODO(P3 - Niko784): implementar FracM (contracts section 2)")


def test_lexicographic_order_m_dominates():
    assert FracM(Fraction(-30), Fraction(-1)) < FracM(Fraction(-40))   # -M-30 < -40


def test_to_str_forms():
    assert FracM(Fraction(5)).to_str() == "5"
    assert FracM(Fraction(3, 4)).to_str() == "3/4"
    assert FracM(Fraction(0), Fraction(1)).to_str() == "M"
    assert FracM(Fraction(-30), Fraction(-1)).to_str() == "-M-30"
    assert FracM(Fraction(1, 3), Fraction(2)).to_str() == "2M+1/3"


def test_parse_decimal_is_exact():
    assert FracM.parse_decimal("0.1") == FracM(Fraction(1, 10))
