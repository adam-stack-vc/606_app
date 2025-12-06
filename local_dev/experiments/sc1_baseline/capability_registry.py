from __future__ import annotations

"""
capability_registry.py
Defines table-level capabilities used by the planner to validate and build SQL safely.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class TimeInfo:
    year_col: Optional[str] = None
    month_col: Optional[str] = None
    quarter_col: Optional[str] = None
    week_col: Optional[str] = None
    hour_col: Optional[str] = None
    # For raw date columns that require bucketing rules (e.g., monthly_data.day)
    day_col: Optional[str] = None

    def get_temporal_column(self, dimension: str) -> Optional[str]:
        """
        Get the column name for a temporal dimension.

        Args:
            dimension: 'month', 'quarter', 'year', 'week', 'hour', etc.

        Returns:
            Column name if available, None otherwise
        """
        mapping = {
            'year': self.year_col,
            'month': self.month_col,
            'quarter': self.quarter_col,
            'week': self.week_col,
            'hour': self.hour_col,
        }
        return mapping.get(dimension)

    def can_extract_temporal(self, dimension: str) -> bool:
        """
        Check if dimension can be EXTRACTed from day_col.

        Args:
            dimension: 'month', 'quarter', 'year', 'week', etc.

        Returns:
            True if day_col exists and supports this EXTRACT
        """
        if not self.day_col:
            return False

        # PostgreSQL EXTRACT supports these
        extractable = {'year', 'month', 'quarter', 'week', 'day', 'hour'}
        return dimension in extractable

    def supports_dimension(self, dimension: str) -> bool:
        """Check if this dimension is supported at all"""
        return (
            self.get_temporal_column(dimension) is not None or
            self.can_extract_temporal(dimension)
        )


@dataclass(frozen=True)
class TableCapabilities:
    name: str
    columns: Set[str] = field(default_factory=set)
    allowed_dimensions: Set[str] = field(default_factory=set)
    allowed_metrics: Set[str] = field(default_factory=set)  # e.g., {"pfof","volume","rate","date"}
    time: TimeInfo = TimeInfo()
    notes: Optional[str] = None


# Minimal capability registry (can be expanded as needed)
REGISTRY: Dict[str, TableCapabilities] = {
    "executing_bd_606": TableCapabilities(
        name="executing_bd_606",
        columns={
            "executing_bd",
            "venues",
            "stock_group",
            "year",
            "month",
            "netpmtpaidrecvmarketordersusd",
            "netpmtpaidrecvmarketablelimitordersusd",
            "netpmtpaidrecvnonmarketablelimitordersusd",
            "netpmtpaidrecvotherordersusd",
            "netpmtpaidrecvmarketorderscph",
            "netpmtpaidrecvmarketablelimitorderscph",
            "netpmtpaidrecvnonmarketablelimitorderscph",
            "netpmtpaidrecvotherorderscph",
            "data_type",
        },
        allowed_dimensions={"executing_bd", "venues", "stock_group"},
        allowed_metrics={"pfof", "volume", "rate", "date", "pfof_and_volume"},
        time=TimeInfo(year_col="year", month_col="month", quarter_col=None, week_col=None, hour_col=None, day_col=None),
        notes="Primary 606 table; time columns as discrete year/month strings; ensure data_type='venue' for PFOF."
    ),
    "monthly_data": TableCapabilities(
        name="monthly_data",
        columns={
            "day",
            "market_participant",
            "total_shares",
            "total_notional",
            "total_trade_count",
            "tape_a_shares",
            "tape_b_shares",
            "tape_c_shares",
        },
        allowed_dimensions={"market_participant", "day"},
        allowed_metrics={"volume", "date", "trades"},
        time=TimeInfo(year_col=None, month_col=None, quarter_col=None, week_col=None, hour_col=None, day_col="day"),
        notes="Day is a date column; can be used as dimension for daily aggregations or with EXTRACT for bucketing."
    ),
    "finra_ats": TableCapabilities(
        name="finra_ats",
        columns={"year", "quarter", "ats_name", "tier", "total_trades", "total_shares"},
        allowed_dimensions={"ats_name", "tier"},
        allowed_metrics={"volume", "date", "trades"},
        time=TimeInfo(year_col="year", month_col=None, quarter_col="quarter", week_col=None, hour_col=None, day_col=None),
        notes="Quarterly data; use year/quarter for filters and grouping."
    ),
}


def get_capabilities(table: str) -> Optional[TableCapabilities]:
    return REGISTRY.get(table)


def validate_dimensions(table: str, dims: List[str]) -> List[str]:
    caps = get_capabilities(table)
    if not caps:
        return []
    return [d for d in dims if d in caps.allowed_dimensions]


def requires_monthly_data_bucketing(table: str) -> bool:
    caps = get_capabilities(table)
    return bool(caps and caps.time.day_col)


def allowed_metric(table: str, metric: Optional[str]) -> bool:
    caps = get_capabilities(table)
    if not caps or not metric:
        return False
    return metric in caps.allowed_metrics


