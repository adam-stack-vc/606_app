from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Literal, Any

class Period(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None

class Filters(BaseModel):
    data_type: Optional[str] = None
    executing_bd: Optional[str] = None
    venues: Optional[str] = None
    stock_group: Optional[str] = None
    ats_name: Optional[str] = None
    market_participant: Optional[str] = None
    # Allow dynamic filters
    extra: Dict[str, Any] = Field(default_factory=dict)

class StructuredIntent(BaseModel):
    metric: Optional[str] = None
    operation: Literal[
        "aggregate", 
        "topN", 
        "list", 
        "earliest", 
        "latest", 
        "top_per_group", 
        "aggregate_with_count", 
        "multi",
        "string_length",
        "cross_table_list",
        "count",
        "per_entity_average"
    ] = "aggregate"
    
    dimensions: List[str] = Field(default_factory=list)
    period: Period = Field(default_factory=Period)
    filters: Filters = Field(default_factory=Filters)
    
    # Operation specific params
    top_n: Optional[int] = None
    order_by: Optional[str] = None
    order_desc: Optional[bool] = True
    
    count_dimension: Optional[str] = None # For count op
    per_entity: Optional[str] = None # For per_entity_average
    
    # For string_length
    is_longest: Optional[bool] = True
    
    # For multi-table support
    subqueries: Optional[List['StructuredQuery']] = None
    
    # Entities map for flexible filtering (like in original QueryIntent)
    entities: Dict[str, str] = Field(default_factory=dict)

class StructuredQuery(BaseModel):
    name: str
    intent: StructuredIntent
