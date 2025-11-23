from typing import Dict

def generate_top_ats_shares_per_quarter_query(query_tags: Dict) -> str:
    """ATS with the highest share volume per quarter for a given year."""
    year = query_tags.get('year', 2024)
    return f"""
WITH per_ats_quarter AS (
  SELECT
    quarter::int AS quarter,
    ats_name,
    SUM(total_shares) AS ats_shares
  FROM finra_ats
  WHERE year = {year}
  GROUP BY quarter, ats_name
),
ranked AS (
  SELECT
    quarter, ats_name, ats_shares,
    ROW_NUMBER() OVER (PARTITION BY quarter ORDER BY ats_shares DESC NULLS LAST) AS rn
  FROM per_ats_quarter
)
SELECT quarter, ats_name, ats_shares
FROM ranked
WHERE rn = 1
ORDER BY quarter;
"""



