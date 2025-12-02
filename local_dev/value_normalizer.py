"""
value_normalizer.py
Normalizes filter values to canonical database values using value_mappings.json

Example:
  User says "S&P 500" → normalized to "SP500" (database value)
  User says "S&P" → normalized to "SP500"
"""

import json
from pathlib import Path
from typing import Optional, Dict

_VALUE_MAPPINGS = None


def _load_value_mappings():
    """Load value mappings from value_mappings.json"""
    global _VALUE_MAPPINGS
    if _VALUE_MAPPINGS is None:
        config_path = Path(__file__).parent / "value_mappings.json"
        with open(config_path, "r") as f:
            _VALUE_MAPPINGS = json.load(f)
    return _VALUE_MAPPINGS


def normalize_value(field_name: str, user_value: str) -> str:
    """
    Normalize a user-provided value to its canonical database form.

    Args:
        field_name: The filter field name (e.g., "stock_group", "tier")
        user_value: The value provided by the user (e.g., "S&P 500")

    Returns:
        Canonical database value (e.g., "SP500") or original value if no mapping exists
    """
    mappings = _load_value_mappings()

    # Get mappings for this field
    field_mappings = mappings.get(field_name, {})

    # Try exact match (case-insensitive)
    user_value_lower = user_value.lower().strip()
    canonical_value = field_mappings.get(user_value_lower)

    if canonical_value:
        return canonical_value

    # No mapping found, return original
    return user_value


def normalize_filters(filters: Dict[str, str]) -> Dict[str, str]:
    """
    Normalize all filter values in a dictionary.

    Args:
        filters: Dictionary of filter_name -> user_value

    Returns:
        Dictionary with normalized values
    """
    normalized = {}
    for field_name, user_value in filters.items():
        if isinstance(user_value, str):
            normalized[field_name] = normalize_value(field_name, user_value)
        else:
            normalized[field_name] = user_value

    return normalized


if __name__ == "__main__":
    # Test value normalization
    test_cases = [
        ("stock_group", "S&P 500"),
        ("stock_group", "s&p"),
        ("stock_group", "SP500"),
        ("stock_group", "S&P500"),
        ("stock_group", "Other"),  # No mapping
    ]

    print("Testing Value Normalization")
    print("=" * 60)
    for field, value in test_cases:
        normalized = normalize_value(field, value)
        status = "✓" if normalized != value else "→"
        print(f"{status} {field}: '{value}' → '{normalized}'")
