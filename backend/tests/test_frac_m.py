"""Unit tests for FracM exact arithmetic and lexicographic ordering.

Contracts: docs/contracts.md section 0 and 2.
"""
from fractions import Fraction
import pytest

from solver.engine.frac_m import FracM


class TestFracMArithmetic:
    def test_add_numeric_constants(self):
        a = FracM(Fraction(3, 4))
        b = FracM(Fraction(1, 2))
        res = a + b
        assert res == FracM(Fraction(5, 4), Fraction(0))

    def test_add_with_symbolic_m(self):
        a = FracM(Fraction(10), Fraction(2))   # 2M + 10
        b = FracM(Fraction(-4), Fraction(-1))  # -M - 4
        res = a + b
        assert res == FracM(Fraction(6), Fraction(1))  # M + 6

    def test_sub_numeric_and_m(self):
        a = FracM(Fraction(5), Fraction(3))    # 3M + 5
        b = FracM(Fraction(2), Fraction(1))    # M + 2
        res = a - b
        assert res == FracM(Fraction(3), Fraction(2))  # 2M + 3

    def test_sub_resulting_in_negative_m(self):
        a = FracM(Fraction(0), Fraction(1))    # M
        b = FracM(Fraction(5), Fraction(2))    # 2M + 5
        res = a - b
        assert res == FracM(Fraction(-5), Fraction(-1))  # -M - 5

    def test_negation(self):
        val = FracM(Fraction(7, 3), Fraction(-2))  # -2M + 7/3
        neg_val = -val
        assert neg_val == FracM(Fraction(-7, 3), Fraction(2))  # 2M - 7/3

    def test_mul_scalar_fraction(self):
        val = FracM(Fraction(3, 2), Fraction(4))   # 4M + 3/2
        scalar = FracM(Fraction(2), Fraction(0))   # 2
        res = val * scalar
        assert res == FracM(Fraction(3), Fraction(8))  # 8M + 3

    def test_mul_with_m_in_one_operand(self):
        a = FracM(Fraction(5), Fraction(0))        # 5
        b = FracM(Fraction(-2), Fraction(3))       # 3M - 2
        res = a * b
        assert res == FracM(Fraction(-10), Fraction(15))  # 15M - 10

    def test_mul_by_plain_fraction(self):
        val = FracM(Fraction(3, 2), Fraction(-4))  # -4M + 3/2
        assert val * Fraction(1, 2) == FracM(Fraction(3, 4), Fraction(-2))
        assert Fraction(1, 2) * val == FracM(Fraction(3, 4), Fraction(-2))
        assert val * 2 == FracM(Fraction(3), Fraction(-8))

    def test_mul_m_by_m_raises_value_error(self):
        a = FracM(Fraction(1), Fraction(1))  # M + 1
        b = FracM(Fraction(2), Fraction(2))  # 2M + 2
        with pytest.raises(ValueError, match="M\\*M is not allowed"):
            _ = a * b


class TestFracMOrdering:
    """Tests the total lexicographic ordering: M coefficient dominates, then constant."""

    def test_lexicographic_order_m_dominates_positive_vs_negative(self):
        # -M - 30 < -40 because m: -1 < 0
        assert FracM(Fraction(-30), Fraction(-1)) < FracM(Fraction(-40), Fraction(0))

    def test_lexicographic_order_large_constant_does_not_override_m(self):
        # -M + 1000000 < 0 because m: -1 < 0
        assert FracM(Fraction(1_000_000), Fraction(-1)) < FracM(Fraction(0), Fraction(0))
        # 1000000 < M because m: 0 < 1
        assert FracM(Fraction(1_000_000), Fraction(0)) < FracM(Fraction(0), Fraction(1))

    def test_lexicographic_order_multiple_m_coefficients(self):
        # 2M + 500 < 3M - 500
        assert FracM(Fraction(500), Fraction(2)) < FracM(Fraction(-500), Fraction(3))
        # -3M < -2M
        assert FracM(Fraction(0), Fraction(-3)) < FracM(Fraction(0), Fraction(-2))

    def test_constant_breaks_tie_when_m_coefficients_equal(self):
        # M + 2 < M + 5
        assert FracM(Fraction(2), Fraction(1)) < FracM(Fraction(5), Fraction(1))
        # -M - 10 < -M - 5
        assert FracM(Fraction(-10), Fraction(-1)) < FracM(Fraction(-5), Fraction(-1))
        # 1/3 < 1/2 (pure constants)
        assert FracM(Fraction(1, 3)) < FracM(Fraction(1, 2))

    def test_comparison_operators_consistency(self):
        smaller = FracM(Fraction(10), Fraction(-1))   # -M + 10
        larger = FracM(Fraction(0), Fraction(0))      # 0
        assert smaller < larger
        assert smaller <= larger
        assert larger > smaller
        assert larger >= smaller
        assert not (smaller > larger)
        assert not (smaller == larger)


class TestFracMEqualityAndHash:
    def test_equality_with_same_values(self):
        assert FracM(Fraction(3, 2), Fraction(5)) == FracM(Fraction(3, 2), Fraction(5))

    def test_inequality_with_different_const(self):
        assert FracM(Fraction(1), Fraction(5)) != FracM(Fraction(2), Fraction(5))

    def test_inequality_with_different_m(self):
        assert FracM(Fraction(1), Fraction(4)) != FracM(Fraction(1), Fraction(5))

    def test_inequality_with_other_types(self):
        assert FracM(Fraction(0), Fraction(0)) != 0
        assert FracM(Fraction(1), Fraction(0)) != Fraction(1)

    def test_hashable_can_be_used_in_set(self):
        s = {FracM(Fraction(1)), FracM(Fraction(1)), FracM(Fraction(2))}
        assert len(s) == 2
        assert FracM(Fraction(1)) in s


class TestFracMFormattingAndParsing:
    """Verifies to_str() canonical strings and parse_decimal() per contracts section 0 and 2."""

    def test_to_str_pure_constants(self):
        if not hasattr(FracM, "__str__"):
            pytest.skip("FracM.__str__ not yet implemented")
        assert str(FracM(Fraction(0))) == "0"
        assert str(FracM(Fraction(5))) == "5"
        assert str(FracM(Fraction(-2))) == "-2"
        assert str(FracM(Fraction(3, 4))) == "3/4"
        assert str(FracM(Fraction(-7, 2))) == "-7/2"

    def test_to_str_pure_m(self):
        if not hasattr(FracM, "__str__"):
            pytest.skip("FracM.__str__ not yet implemented")
        assert str(FracM(Fraction(0), Fraction(1))) == "M"
        assert str(FracM(Fraction(0), Fraction(-1))) == "-M"
        assert str(FracM(Fraction(0), Fraction(2))) == "2M"
        assert str(FracM(Fraction(0), Fraction(-3))) == "-3M"

    def test_to_str_combined_forms(self):
        if not hasattr(FracM, "__str__"):
            pytest.skip("FracM.__str__ not yet implemented")
        assert str(FracM(Fraction(-30), Fraction(-1))) == "-M-30"
        assert str(FracM(Fraction(1, 3), Fraction(2))) == "2M+1/3"
        assert str(FracM(Fraction(-5), Fraction(1))) == "M-5"
        assert str(FracM(Fraction(5), Fraction(1))) == "M+5"

    def test_parse_decimal_exact(self):
        if not hasattr(FracM, "parse_decimal"):
            pytest.skip("FracM.parse_decimal not yet implemented")
        assert FracM.parse_decimal("0.1") == FracM(Fraction(1, 10))
        assert FracM.parse_decimal("-2.5") == FracM(Fraction(-5, 2))
        assert FracM.parse_decimal("40") == FracM(Fraction(40))
        assert FracM.parse_decimal("0") == FracM(Fraction(0))
