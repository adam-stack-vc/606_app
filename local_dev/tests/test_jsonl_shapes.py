import json
from pathlib import Path
from typing import Any, Dict, List, Optional


ALLOWED_TABLES = {"executing_bd_606", "monthly_data", "finra_ats", "multi"}
ALLOWED_OPERATIONS = {
    "list",
    "aggregate",
    "topN",
    "top_per_group",
    "earliest",
    "latest",
    "multi",
}
ALLOWED_METRICS = {None, "pfof", "volume", "avg_trade_size", "trades"}
ALLOWED_PERIOD_KEYS = {"year", "month", "quarter"}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def _validate_period(period: Dict[str, Any]) -> None:
    assert isinstance(period, dict)
    for k in period.keys():
        assert k in ALLOWED_PERIOD_KEYS
    if "year" in period:
        assert isinstance(period["year"], int)
    if "month" in period:
        assert isinstance(period["month"], int)
        assert 1 <= period["month"] <= 12
    if "quarter" in period:
        assert isinstance(period["quarter"], int)
        assert 1 <= period["quarter"] <= 4


def _validate_expected_sql_shape(shape: Dict[str, Any]) -> None:
    assert isinstance(shape, dict)
    assert "selects" in shape and isinstance(shape["selects"], list)
    assert "group_by" in shape and isinstance(shape["group_by"], list)
    # order_by can be None or str
    assert "order_by" in shape
    if shape["order_by"] is not None:
        assert isinstance(shape["order_by"], str)
    # order_desc can be None or bool
    assert "order_desc" in shape
    if shape["order_desc"] is not None:
        assert isinstance(shape["order_desc"], bool)
    # limit can be None or int
    assert "limit" in shape
    if shape["limit"] is not None:
        assert isinstance(shape["limit"], int) and shape["limit"] > 0


def _validate_result_shape(shape: Dict[str, Any]) -> None:
    assert isinstance(shape, dict)
    assert "columns" in shape or "blocks" in shape
    if "columns" in shape:
        assert isinstance(shape["columns"], list)
        assert len(shape["columns"]) >= 1
        for c in shape["columns"]:
            assert isinstance(c, str) and c
    if "blocks" in shape:
        assert isinstance(shape["blocks"], list)
        assert len(shape["blocks"]) >= 1
        for b in shape["blocks"]:
            assert isinstance(b, str) and b


def _validate_intent(intent: Dict[str, Any]) -> None:
    assert isinstance(intent, dict)
    # metric can be None for list/distinct
    metric = intent.get("metric", None)
    assert metric in ALLOWED_METRICS

    op = intent.get("operation")
    assert op in ALLOWED_OPERATIONS

    dims = intent.get("dimensions", [])
    assert isinstance(dims, list)
    for d in dims:
        assert isinstance(d, str) and d

    period = intent.get("period", {})
    _validate_period(period)

    filters = intent.get("filters", {})
    assert isinstance(filters, dict)

    # topN should include top_n
    if op == "topN":
        assert "top_n" in intent and isinstance(intent["top_n"], int) and intent["top_n"] > 0

    # list operation should have metric None
    if op == "list":
        assert metric is None


def _validate_entry(entry: Dict[str, Any]) -> None:
    assert isinstance(entry.get("id"), int)
    assert isinstance(entry.get("question"), str) and entry["question"]
    table = entry.get("table_hint")
    assert table in ALLOWED_TABLES

    intent = entry.get("intent")
    assert isinstance(intent, dict)
    _validate_intent(intent)

    if intent.get("operation") == "multi":
        # multi requires subqueries
        subs = entry.get("subqueries")
        assert isinstance(subs, list) and len(subs) >= 1
        for s in subs:
            assert "intent" in s
            _validate_intent(s["intent"])
            assert "expected_sql_shape" in s
            _validate_expected_sql_shape(s["expected_sql_shape"])
        assert "expected_result_shape" in entry
        _validate_result_shape(entry["expected_result_shape"])
    else:
        assert "expected_sql_shape" in entry
        _validate_expected_sql_shape(entry["expected_sql_shape"])
        assert "expected_result_shape" in entry
        _validate_result_shape(entry["expected_result_shape"])


def test_nl_sql_pairs_additional_jsonl_structure() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    jsonl_path = base_dir / "eval" / "nl_sql_pairs_additional.jsonl"
    assert jsonl_path.exists(), f"Missing file: {jsonl_path}"
    entries = _read_jsonl(jsonl_path)
    # Expect at least 30 entries
    assert len(entries) >= 30
    for e in entries:
        _validate_entry(e)


