"""
Enhanced value normalizer with fuzzy matching fallback

Handles typos and misspellings:
- "citadell" → "Citadel Securities LLC"
- "robinood" → "Robinhood Securities, LLC"
- "shwab" → "Charles Schwab"
"""

import json
from pathlib import Path
from typing import Optional, Dict, Tuple

# Try to import rapidfuzz (fast), fallback to difflib (stdlib)
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    import difflib
    FUZZY_AVAILABLE = False

_VALUE_MAPPINGS = None
_FUZZY_THRESHOLD = 85  # Minimum similarity score (0-100)


def _load_value_mappings():
    """Load value mappings from value_mappings.json"""
    global _VALUE_MAPPINGS
    if _VALUE_MAPPINGS is None:
        config_path = Path(__file__).parent / "value_mappings.json"
        with open(config_path, "r") as f:
            _VALUE_MAPPINGS = json.load(f)
    return _VALUE_MAPPINGS


def _fuzzy_match_rapidfuzz(user_value: str, candidates: Dict[str, str], threshold: int) -> Optional[Tuple[str, str, int]]:
    """Use rapidfuzz for fuzzy matching (fast)"""
    if not candidates:
        return None

    # Extract just the keys for matching
    keys = list(candidates.keys())

    # Find best match
    result = process.extractOne(
        user_value.lower(),
        keys,
        scorer=fuzz.ratio,
        score_cutoff=threshold
    )

    if result:
        matched_key, score, _ = result
        canonical_value = candidates[matched_key]
        return (matched_key, canonical_value, score)

    return None


def _fuzzy_match_difflib(user_value: str, candidates: Dict[str, str], threshold: int) -> Optional[Tuple[str, str, int]]:
    """Use difflib for fuzzy matching (stdlib fallback, slower)"""
    if not candidates:
        return None

    user_lower = user_value.lower()
    best_match = None
    best_score = 0

    for candidate_key in candidates.keys():
        # Calculate similarity ratio (0.0 to 1.0)
        ratio = difflib.SequenceMatcher(None, user_lower, candidate_key).ratio()
        score = int(ratio * 100)

        if score >= threshold and score > best_score:
            best_score = score
            best_match = candidate_key

    if best_match:
        return (best_match, candidates[best_match], best_score)

    return None


def normalize_value_fuzzy(field_name: str, user_value: str, enable_fuzzy: bool = True, threshold: int = _FUZZY_THRESHOLD) -> Tuple[str, Optional[str], int]:
    """
    Normalize a user-provided value to its canonical database form with fuzzy matching.

    Args:
        field_name: The filter field name (e.g., "executing_bd", "venues")
        user_value: The value provided by the user (e.g., "citadell", "robinood")
        enable_fuzzy: Enable fuzzy matching fallback
        threshold: Minimum similarity score for fuzzy match (0-100)

    Returns:
        Tuple of (canonical_value, matched_alias, confidence_score)
        - canonical_value: The normalized value to use in SQL
        - matched_alias: The alias that matched (None if no match)
        - confidence_score: 100 for exact match, 0-99 for fuzzy, 0 for no match
    """
    mappings = _load_value_mappings()
    field_mappings = mappings.get(field_name, {})

    if not field_mappings:
        # No mappings for this field
        return (user_value, None, 0)

    user_value_lower = user_value.lower().strip()

    # Try exact match first (fast path)
    canonical_value = field_mappings.get(user_value_lower)
    if canonical_value:
        return (canonical_value, user_value_lower, 100)

    # No exact match - try fuzzy matching if enabled
    if not enable_fuzzy:
        return (user_value, None, 0)

    # Use appropriate fuzzy matcher
    if FUZZY_AVAILABLE:
        match_result = _fuzzy_match_rapidfuzz(user_value_lower, field_mappings, threshold)
    else:
        match_result = _fuzzy_match_difflib(user_value_lower, field_mappings, threshold)

    if match_result:
        matched_key, canonical_value, score = match_result
        return (canonical_value, matched_key, score)

    # No fuzzy match found
    return (user_value, None, 0)


def normalize_value(field_name: str, user_value: str) -> str:
    """
    Backward-compatible wrapper that returns just the canonical value.
    Uses fuzzy matching by default.
    """
    canonical, _, _ = normalize_value_fuzzy(field_name, user_value, enable_fuzzy=True)
    return canonical


if __name__ == "__main__":
    # Test fuzzy matching
    print("=" * 80)
    print("FUZZY VALUE NORMALIZATION TEST")
    print("=" * 80)
    print(f"Fuzzy library: {'rapidfuzz' if FUZZY_AVAILABLE else 'difflib (stdlib)'}")
    print(f"Threshold: {_FUZZY_THRESHOLD}%")
    print()

    test_cases = [
        # (field, user_input, description)
        ("executing_bd", "robinhood", "Exact match"),
        ("executing_bd", "robinood", "Typo: robinood"),
        ("executing_bd", "robinhod", "Typo: robinhod"),
        ("executing_bd", "schwab", "Exact match"),
        ("executing_bd", "shwab", "Typo: shwab"),
        ("executing_bd", "schwabb", "Typo: schwabb"),
        ("venues", "citadel", "Exact match"),
        ("venues", "citadell", "Typo: citadell"),
        ("venues", "cita", "Too short - should not match"),
        ("venues", "virtu", "Exact match"),
        ("venues", "virtu amercias", "Partial typo"),
        ("executing_bd", "xxx", "No match"),
    ]

    for field, value, description in test_cases:
        canonical, matched_alias, score = normalize_value_fuzzy(field, value)

        if score == 100:
            status = "✅ EXACT"
        elif score >= _FUZZY_THRESHOLD:
            status = f"🔍 FUZZY ({score}%)"
        else:
            status = "❌ NO MATCH"

        print(f"{status:20} {description:30}")
        print(f"  Input: '{value}' → Output: '{canonical}'")
        if matched_alias:
            print(f"  Matched via: '{matched_alias}'")
        print()
