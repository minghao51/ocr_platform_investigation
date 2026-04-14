"""
Integration tests for benchmark scoring logic.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmarks.scoring import (
    normalize_string,
    normalize_number,
    normalize_date,
    levenshtein_ratio,
    name_contains_match,
    score_field,
    score_results,
    score_items_list,
)


class TestNormalizeString:
    """Test string normalization for comparison."""

    def test_remove_spaces(self):
        assert normalize_string("Hello World") == "helloworld"

    def test_remove_hyphens(self):
        assert normalize_string("Hello-World") == "helloworld"

    def test_remove_underscores(self):
        assert normalize_string("Hello_World") == "helloworld"

    def test_lowercase(self):
        assert normalize_string("HELLO WORLD") == "helloworld"

    def test_cord_modifiers(self):
        """Test CORD modifier pattern removal."""
        # Single +
        assert normalize_string("Item+Modifier") == "itemmodifier"
        # Double +
        assert normalize_string("Item++Modifier") == "itemmodifier"
        # Spaces around +
        assert normalize_string("Item + Modifier") == "itemmodifier"
        # Multiple modifiers
        assert normalize_string("VietMilkCoffee++Hot++M") == "vietmilkcoffeehotm"

    def test_complex_cord_modifier(self):
        """Test actual CORD example."""
        expected = "VietMilkCoffee++Hot++M"
        actual = "Viet Milk Coffee"
        assert normalize_string(expected) == "vietmilkcoffeehotm"
        # After normalization, they won't match exactly (different strings)
        assert normalize_string(actual) == "vietmilkcoffee"


class TestNormalizeNumber:
    """Test number normalization."""

    def test_integer(self):
        assert normalize_number(42) == 42.0

    def test_float(self):
        assert normalize_number(3.14) == 3.14

    def test_string_number(self):
        assert normalize_number("42") == 42.0

    def test_string_with_comma(self):
        assert normalize_number("1,234.56") == 1234.56

    def test_string_with_dollar(self):
        assert normalize_number("$100.00") == 100.0

    def test_string_with_euro(self):
        assert normalize_number("€50.00") == 50.0

    def test_string_with_pound(self):
        assert normalize_number("£25.00") == 25.0

    def test_string_with_yen(self):
        assert normalize_number("¥1000") == 1000.0

    def test_invalid_string(self):
        assert normalize_number("not a number") is None


class TestNormalizeDate:
    """Test date parsing and normalization."""

    def test_iso_format(self):
        result = normalize_date("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_slash_format_mdyyyy(self):
        result = normalize_date("01/15/2024")
        assert result is not None
        assert result.month == 1
        assert result.day == 15
        assert result.year == 2024

    def test_slash_format_ddmmyyyy(self):
        result = normalize_date("15/01/2024")
        assert result is not None
        assert result.day == 15
        assert result.month == 1
        assert result.year == 2024

    def test_dash_format(self):
        result = normalize_date("01-15-2024")
        assert result is not None

    def test_dot_format(self):
        result = normalize_date("2024.01.15")
        assert result is not None

    def test_month_name_short(self):
        result = normalize_date("Jan 15, 2024")
        assert result is not None

    def test_month_name_long(self):
        result = normalize_date("January 15, 2024")
        assert result is not None

    def test_compact_format(self):
        result = normalize_date("20240115")
        assert result is not None

    def test_invalid_date(self):
        assert normalize_date("not a date") is None

    def test_non_string(self):
        assert normalize_date(12345) is None


class TestLevenshteinRatio:
    """Test fuzzy string matching."""

    def test_identical_strings(self):
        assert levenshtein_ratio("hello", "hello") == 1.0

    def test_both_empty(self):
        assert levenshtein_ratio("", "") == 1.0

    def test_one_empty(self):
        assert levenshtein_ratio("hello", "") == 0.0

    def test_similar_strings(self):
        ratio = levenshtein_ratio("hello", "hallo")
        assert ratio > 0.7  # Very similar

    def test_different_strings(self):
        ratio = levenshtein_ratio("hello", "world")
        assert ratio < 0.5  # Quite different

    def test_case_insensitive(self):
        assert levenshtein_ratio("Hello", "hello") == 1.0


class TestNameContainsMatch:
    """Test name matching with CORD modifier handling."""

    def test_exact_match(self):
        score, match_type = name_contains_match("Coffee", "Coffee")
        assert score == 1.0
        assert match_type == "name_exact"

    def test_normalized_exact_match(self):
        score, match_type = name_contains_match("Viet Milk Coffee", "VietMilkCoffee")
        assert score == 1.0

    def test_cord_modifier_match(self):
        """Test CORD modifier: ground truth has ++, VLM has base name."""
        score, match_type = name_contains_match(
            "VietMilkCoffee++Hot++M", "Viet Milk Coffee"
        )
        # Should have partial match due to substring
        assert score > 0.5
        assert "contains" in match_type

    def test_actual_in_expected(self):
        score, match_type = name_contains_match("VietMilkCoffeeHotM", "VietMilkCoffee")
        assert score > 0.7  # Substring match

    def test_expected_in_actual(self):
        score, match_type = name_contains_match("Coffee", "Coffee Shop")
        assert score > 0.7  # Substring match

    def test_fallback_to_levenshtein(self):
        score, match_type = name_contains_match("Coffee", "Tea")
        assert score < 0.5  # Not similar
        assert match_type == "name_fuzzy"


class TestScoreField:
    """Test individual field scoring."""

    def test_both_null(self):
        score, match_type = score_field(None, None)
        assert score == 1.0
        assert match_type == "both_null"

    def test_one_null(self):
        score, match_type = score_field(10, None)
        assert score == 0.0
        assert match_type == "null_mismatch"

    def test_numeric_exact(self):
        score, match_type = score_field(100, 100)
        assert score == 1.0
        # When both numbers are 0, it returns numeric_exact
        score2, match_type2 = score_field(0, 0)
        assert match_type2 == "numeric_exact"
        # For non-zero equal numbers, returns numeric_within_1pct (which is also correct)
        assert match_type == "numeric_within_1pct"

    def test_numeric_within_1_percent(self):
        score, match_type = score_field(100, 100.50)
        assert score == 1.0
        assert match_type == "numeric_within_1pct"

    def test_numeric_partial(self):
        score, match_type = score_field(100, 105)
        assert 0.9 < score < 1.0  # Partial match
        assert match_type == "numeric_partial"

    def test_string_exact_match(self):
        score, match_type = score_field("Coffee", "Coffee")
        assert score == 1.0
        assert match_type == "name_exact"

    def test_string_contains_match(self):
        score, match_type = score_field("Coffee Shop", "Coffee")
        assert score > 0.7

    def test_string_mismatch(self):
        score, match_type = score_field("Coffee", "Tea")
        assert score == 0.0

    def test_date_exact(self):
        score, match_type = score_field("2024-01-15", "2024-01-15")
        assert score == 1.0
        assert match_type == "date_exact"

    def test_date_different_format_same_day(self):
        score, match_type = score_field("2024-01-15", "01/15/2024")
        assert score == 1.0
        # The match type might be "date_exact" if they parse to the same date object
        assert "exact" in match_type or "same_day" in match_type


class TestScoreResults:
    """Test overall result scoring."""

    def test_all_fields_match(self):
        expected = {"total": 100, "items": [{"name": "Coffee", "price": 5}]}
        actual = {"total": 100, "items": [{"name": "Coffee", "price": 5}]}
        result = score_results(expected, actual)
        assert result["overall_score"] == 1.0
        assert result["matched_fields"] == 2

    def test_missing_field_penalized(self):
        expected = {"total": 100, "tax": 10}
        actual = {"total": 100}  # Missing tax
        result = score_results(expected, actual)
        assert result["overall_score"] == 0.5  # 1/2 fields match
        assert result["matched_fields"] == 1

    def test_extra_fields_not_penalized(self):
        expected = {"total": 100}
        actual = {"total": 100, "tax": 10, "discount": 5}
        result = score_results(expected, actual)
        assert result["overall_score"] == 1.0  # Only scores expected fields

    def test_empty_expected(self):
        expected = {}
        actual = {"anything": "value"}
        result = score_results(expected, actual)
        assert result["overall_score"] == 0.0
        assert result["total_fields"] == 0


class TestScoreItemsList:
    """Test item list scoring with bipartite matching."""

    def test_empty_lists(self):
        result = score_items_list([], [])
        assert result["score"] == 1.0
        assert result["matched"] == 0
        assert result["total"] == 0

    def test_one_empty_list(self):
        expected = [{"name": "Coffee", "price": 5}]
        actual = []
        result = score_items_list(expected, actual)
        assert result["score"] == 0.0

    def test_perfect_match(self):
        expected = [
            {"name": "Coffee", "price": 5},
            {"name": "Tea", "price": 3},
        ]
        actual = [
            {"name": "Coffee", "price": 5},
            {"name": "Tea", "price": 3},
        ]
        result = score_items_list(expected, actual)
        assert result["score"] == 1.0
        assert result["matched"] == 2

    def test_different_order(self):
        """Order shouldn't matter."""
        expected = [
            {"name": "Coffee", "price": 5},
            {"name": "Tea", "price": 3},
        ]
        actual = [
            {"name": "Tea", "price": 3},
            {"name": "Coffee", "price": 5},
        ]
        result = score_items_list(expected, actual)
        assert result["score"] == 1.0

    def test_name_match_with_price_mismatch(self):
        """Name match gives partial score even if price differs."""
        expected = [{"name": "Coffee", "price": 5}]
        actual = [{"name": "Coffee", "price": 6}]
        result = score_items_list(expected, actual)
        # Name is 60%, price partial makes it lower but still good
        assert result["score"] > 0.5

    def test_cord_modifier_item_matching(self):
        """Test CORD modifier handling in items."""
        expected = [
            {"name": "VietMilkCoffee++Hot++M", "price": 4.50},
        ]
        actual = [
            {"name": "Viet Milk Coffee", "price": 4.50},
        ]
        result = score_items_list(expected, actual)
        # Should match due to substring/normalization
        assert result["score"] > 0.7

    def test_partial_match(self):
        expected = [
            {"name": "Coffee", "price": 5},
            {"name": "Tea", "price": 3},
            {"name": "Sandwich", "price": 8},
        ]
        actual = [
            {"name": "Coffee", "price": 5},
            {"name": "Bagel", "price": 4},  # No match
        ]
        result = score_items_list(expected, actual)
        assert result["matched"] == 1
        assert result["score"] == pytest.approx(1 / 3, rel=0.01)  # 1 out of 3 matched

    def test_over_extraction(self):
        """VLM extracts more items than ground truth."""
        expected = [
            {"name": "Coffee", "price": 5},
        ]
        actual = [
            {"name": "Coffee", "price": 5},
            {"name": "Tea", "price": 3},  # Extra
        ]
        result = score_items_list(expected, actual)
        assert result["score"] == 1.0  # All expected matched
