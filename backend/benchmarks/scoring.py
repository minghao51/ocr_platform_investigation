"""
Accuracy scoring for benchmark results.
Compares VLM output against ground truth with smart matching.
"""

import re
from datetime import datetime
from typing import Any, Dict, Tuple


def normalize_number(value: Any) -> float | None:
    """Try to parse a value as a number."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("¥", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def normalize_date(value: str) -> datetime | None:
    """Try to parse a date string into a datetime object."""
    if not isinstance(value, str):
        return None
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%Y.%m.%d",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Compute normalized Levenshtein similarity ratio between two strings."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    dp = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, len2 + 1):
            temp = dp[j]
            if s1[i - 1].lower() == s2[j - 1].lower():
                dp[j] = prev
            else:
                dp[j] = 1 + min(dp[j], dp[j - 1], prev)
            prev = temp
    distance = dp[len2]
    return 1.0 - distance / max(len1, len2)


def normalize_string(value: str) -> str:
    """Normalize a string for comparison: lowercase, remove spaces, punctuation, and modifiers."""
    if not isinstance(value, str):
        return str(value)
    result = value.strip().lower()
    # Remove CORD modifier patterns: +, ++, and text after them
    result = re.sub(r'\s*\+\s*', '', result)
    result = result.replace(" ", "").replace("-", "").replace("_", "")
    return result


def name_contains_match(exp_name: str, act_name: str) -> Tuple[float, str]:
    """
    Check if one name contains the other, handling CORD modifiers.

    CORD ground truth often includes modifiers: `VietMilkCoffee++Hot++M`
    VLMs extract base names: `Viet Milk Coffee`

    Returns (score, match_type).
    """
    exp_norm = normalize_string(exp_name)
    act_norm = normalize_string(act_name)

    if exp_norm == act_norm:
        return (1.0, "name_exact")

    # Check if one is a substring of the other
    if exp_norm in act_norm:
        ratio = len(exp_norm) / len(act_norm)
        return (0.7 + 0.3 * ratio, "name_contains_actual")
    if act_norm in exp_norm:
        ratio = len(act_norm) / len(exp_norm)
        return (0.7 + 0.3 * ratio, "name_contains_expected")

    # Fallback to Levenshtein
    ratio = levenshtein_ratio(exp_norm, act_norm)
    return (ratio, "name_fuzzy")


def score_field(expected: Any, actual: Any, field_name: str = "") -> Tuple[float, str]:
    """
    Score a single field comparison.

    For string fields (especially names), normalizes by removing spaces
    before comparison to handle CORD's concatenated annotation format.

    Returns:
        (score 0-1, match_type description)
    """
    if expected is None and actual is None:
        return (1.0, "both_null")
    if expected is None or actual is None:
        return (0.0, "null_mismatch")

    num_expected = normalize_number(expected)
    num_actual = normalize_number(actual)
    if num_expected is not None and num_actual is not None:
        if num_expected == 0 and num_actual == 0:
            return (1.0, "numeric_exact")
        tolerance = abs(num_expected) * 0.01
        if abs(num_expected - num_actual) <= tolerance:
            return (1.0, "numeric_within_1pct")
        max_val = max(abs(num_expected), abs(num_actual))
        return (1.0 - abs(num_expected - num_actual) / max_val, "numeric_partial")

    date_expected = normalize_date(str(expected))
    date_actual = normalize_date(str(actual))
    if date_expected is not None and date_actual is not None:
        if date_expected == date_actual:
            return (1.0, "date_exact")
        diff_days = abs((date_expected - date_actual).days)
        if diff_days == 0:
            return (1.0, "date_same_day")
        if diff_days <= 1:
            return (0.8, "date_within_1day")
        if diff_days <= 7:
            return (0.5, "date_within_week")
        return (0.0, "date_mismatch")

    # For string comparison, check modifier-aware match first
    str_expected = str(expected)
    str_actual = str(actual)
    name_score, match_type = name_contains_match(str_expected, str_actual)
    if name_score >= 0.85:
        return (name_score, match_type)
    if name_score > 0.5:
        return (name_score * 0.7, f"{match_type}_partial")
    return (0.0, "string_mismatch")


def score_results(expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score all fields in expected vs actual.

    Only scores fields that exist in the expected data (ground truth).
    Extra fields in actual are noted but not penalized.
    Missing fields in actual are scored as 0.

    Returns:
        {
            "overall_score": float (0-1),
            "field_scores": {field_name: {"score": float, "match_type": str}},
            "total_fields": int,
            "matched_fields": int,
        }
    """
    field_scores: Dict[str, Dict[str, Any]] = {}

    for field_name in expected:
        exp_val = expected[field_name]
        act_val = actual.get(field_name)
        score, match_type = score_field(exp_val, act_val, field_name)
        field_scores[field_name] = {"score": score, "match_type": match_type}

    total = len(field_scores)
    if total == 0:
        return {
            "overall_score": 0.0,
            "field_scores": field_scores,
            "total_fields": 0,
            "matched_fields": 0,
        }

    overall = sum(fs["score"] for fs in field_scores.values()) / total
    matched = sum(1 for fs in field_scores.values() if fs["score"] >= 0.85)

    return {
        "overall_score": round(overall, 4),
        "field_scores": field_scores,
        "total_fields": total,
        "matched_fields": matched,
    }


def score_items_list(
    expected_items: list, actual_items: list
) -> Dict[str, Any]:
    """Score a list of items (e.g. menu items on a receipt).

    Uses best-match bipartite matching. An item is considered matched
    if its name matches (normalized) — price/quantity mismatches reduce
    the score but don't zero it out.
    """
    if not expected_items and not actual_items:
        return {"score": 1.0, "matched": 0, "total": 0}
    if not expected_items or not actual_items:
        return {"score": 0.0, "matched": 0, "total": max(len(expected_items), len(actual_items))}

    matched = 0
    total = len(expected_items)
    used_actual = set()

    for exp_item in expected_items:
        best_score = 0.0
        best_idx = -1
        for j, act_item in enumerate(actual_items):
            if j in used_actual:
                continue
            # Use specialized name matching that handles CORD modifiers
            exp_name = exp_item.get("name", "")
            act_name = act_item.get("name", "")
            if exp_name and act_name:
                name_score, _ = name_contains_match(exp_name, act_name)
            elif not exp_name and not act_name:
                name_score = 1.0
            else:
                name_score = 0.0

            if name_score < 0.7:
                continue

            # Score other fields
            other_scores = []
            for key in exp_item:
                if key == "name":
                    continue
                s, _ = score_field(exp_item[key], act_item.get(key), key)
                other_scores.append(s)

            # Weight: name is 60%, other fields average 40%
            if other_scores:
                item_score = 0.6 * name_score + 0.4 * (sum(other_scores) / len(other_scores))
            else:
                item_score = name_score

            if item_score > best_score:
                best_score = item_score
                best_idx = j

        if best_score >= 0.7:
            matched += 1
            if best_idx >= 0:
                used_actual.add(best_idx)

    return {
        "score": round(matched / total, 4) if total > 0 else 0.0,
        "matched": matched,
        "total": total,
    }
