from typing import Dict

def generate_top_exchange_share_per_quarter_query(query_tags: Dict) -> str:
    """Exchange with largest percentage share per quarter in a given year."""
    year = query_tags.get('year', 2024)
    return f"""
WITH per_exchange_quarter AS (
  SELECT
    EXTRACT(QUARTER FROM day)::int AS quarter,
    market_participant,
    SUM(total_shares) AS mp_shares
  FROM monthly_data
  WHERE EXTRACT(YEAR FROM day) = {year}
    AND market_participant NOT ILIKE '%TRF%'
    AND market_participant NOT ILIKE '%FINRA%'
  GROUP BY EXTRACT(QUARTER FROM day), market_participant
),
quarter_totals AS (
  SELECT quarter, SUM(mp_shares) AS q_shares
  FROM per_exchange_quarter
  GROUP BY quarter
),
with_share AS (
  SELECT
    e.quarter,
    e.market_participant,
    e.mp_shares,
    CASE WHEN t.q_shares > 0
      THEN ROUND((e.mp_shares::numeric / t.q_shares::numeric) * 100, 4)
    END AS share_pct
  FROM per_exchange_quarter e
  JOIN quarter_totals t USING (quarter)
),
ranked AS (
  SELECT
    quarter, market_participant, mp_shares, share_pct,
    ROW_NUMBER() OVER (PARTITION BY quarter ORDER BY share_pct DESC NULLS LAST) AS rn
  FROM with_share
)
SELECT quarter, market_participant AS exchange, mp_shares, share_pct
FROM ranked
WHERE rn = 1
ORDER BY quarter;
"""



