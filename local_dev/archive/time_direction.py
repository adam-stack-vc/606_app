import re
from datetime import datetime

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

def extract_time_period(user_input: str) -> dict:
    """Extracts year, month, quarter from text like 'January 2024' or 'Q3 2023'"""
    text = user_input.lower()
    current_year = datetime.now().year
    current_month = datetime.now().month
    year, month, quarter = None, None, None

    # --- Explicit year ---
    year_match = re.search(r"\b(20[0-9]{2})\b", text)
    if year_match:
        year = int(year_match.group(1))

    # --- Explicit month ---
    for m_name, m_num in MONTHS.items():
        if m_name in text:
            month = m_num
            break

    # --- Quarter ---
    quarter_match = re.search(r"\bq([1-4])\b", text)
    if quarter_match:
        quarter = int(quarter_match.group(1))

    # --- Relative expressions ---
    if "last year" in text:
        year = current_year - 1
    elif "this year" in text:
        year = current_year

    if "last month" in text:
        if current_month == 1:
            month = 12
            year = (year or current_year) - 1
        else:
            month = current_month - 1
            year = year or current_year

    if "this month" in text:
        month = current_month
        year = year or current_year

    if "last quarter" in text:
        q = (current_month - 1) // 3 + 1
        quarter = q - 1 if q > 1 else 4
        year = current_year if q > 1 else current_year - 1

    if "this quarter" in text:
        quarter = (current_month - 1) // 3 + 1
        year = year or current_year

    return {"year": year, "month": month, "quarter": quarter}
