from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class QueryIntent:
    """
    Minimal semantic representation for NL→SQL.

    This mirrors the structure described in nl2sql integration docs:
      - topic: high-level subject (optional)
      - metric: e.g., 'pfof', 'volume', 'rate', or 'date'
      - direction: 'exact flow' such as 'executing_bd_to_venue' or 'venue_to_executing_bd'
      - entities: {'executing_bd': str, 'venue': str, ...}
      - period: {'year': int|None, 'month': int|None, 'quarter': int|None}
      - dimensions: list of strings to group by
      - filters: arbitrary key/value filters (reserved for future use)
      - aggregation: e.g., 'MAX'/'MIN' when the user asks for extremes
    """
    topic: Optional[str] = None
    metric: Optional[str] = None
    direction: Optional[str] = None
    entities: Dict[str, str] = field(default_factory=dict)
    period: Dict[str, Optional[int]] = field(default_factory=dict)
    dimensions: List[str] = field(default_factory=list)
    filters: Dict[str, str] = field(default_factory=dict)
    # SQL shaping
    operation: Optional[str] = None          # list | aggregate | topN | top_per_group | earliest | latest | count | per_entity_average
    aggregation: Optional[str] = None        # SUM | COUNT | AVG | MIN | MAX
    order_by: Optional[str] = None           # column/alias to order by
    order_desc: bool = True
    limit: Optional[int] = None
    top_n: Optional[int] = None              # alias for limit when using topN
    count_dimension: Optional[str] = None    # for count operation: what to count (e.g., "venue", "broker")
    per_entity: Optional[str] = None         # for per_entity_average: denominator entity type (e.g., "venue", "broker")

    @classmethod
    def from_tags(cls, tags: Dict) -> "QueryIntent":
        # Build a minimal intent from classification tags
        entities: Dict[str, str] = {}
        for key in ("executing_bd", "venue"):
            if key in tags and tags[key]:
                entities[key] = tags[key]
        period: Dict[str, Optional[int]] = {
            "year": tags.get("year"),
            "month": tags.get("month"),
            "quarter": tags.get("quarter"),
        }

        # Build filters dict from tags - include common filter fields
        filters: Dict[str, str] = dict(tags.get("filters", {})) if isinstance(tags.get("filters", {}), dict) else {}

        # Add stock_group, market_participant, ats_name, tier if present in tags
        for filter_key in ("stock_group", "market_participant", "ats_name", "tier"):
            if filter_key in tags and tags[filter_key]:
                filters[filter_key] = tags[filter_key]

        return cls(
            topic=tags.get("topic"),
            metric=tags.get("metric"),
            direction=tags.get("direction"),
            entities=entities,
            period=period,
            dimensions=list(tags.get("dimensions", [])) if isinstance(tags.get("dimensions", []), list) else [],
            filters=filters,
            operation=tags.get("operation"),
            aggregation=tags.get("aggregation"),
            order_by=tags.get("order_by"),
            order_desc=bool(tags.get("order_desc", True)),
            limit=tags.get("limit"),
            top_n=tags.get("top_n"),
        )

