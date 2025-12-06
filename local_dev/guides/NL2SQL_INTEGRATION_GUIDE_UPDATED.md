## 606 NL→SQL Integration Guide (Updated)

This guide replaces the original plan with what’s actually implemented now. It captures the current hybrid, deterministic-first pipeline, routing rules, schemas, and extension points.

### What changed vs. the original plan
- **Deterministic-first routing**: We default to deterministic SQL for core analytics and only use LLM for narrative synthesis (and limited fallback), not for final SQL generation.
- **Hybrid path as default**: `ASK_HANDLER=hybrid` is the default; it always uses the complex multi-table router to assemble multiple targeted SQL queries and then synthesize a response.
- **Explicit query classification**: A richer tag set drives routing and query assembly (month/quarter/year, broker/venue, market share, earliest, streak, ATS, etc.).
- **Safer monthly_data queries**: Aggregations are quarter/month aware; day-level GROUP BY pitfalls are guarded with rules/fallbacks.
- **Data typing in 606**: Rows carry `data_type` derived from presence of `venues` (`'venue'` when `venues` has a value, otherwise `'executing_bd'`), aligned with recent backfill.

---

## High-level Architecture

```
Client → POST /ask
        ↓
Classification (query tags)  ← multi_table_query_framework.py
        ↓
Hybrid Router (deterministic segments + orchestration) ← hybrid_query_handler.py
        ↓
Deterministic SQL segments executed against Postgres
        ↓
LLM synthesis for narrative only (no final-SQL authoring)
        ↓
Response { query_results, synthesis, query_classification }
```

### Runtime and Entrypoint
- FastAPI app: `main.py`
  - Health/debug endpoints; POST `/ask`
  - Chooses handler via `ASK_HANDLER` env (default: `hybrid`), importing:
    - `ask606_hybrid.py` (default)
    - `ask606_multi_table.py` (optional)
    - `ask606.py` (legacy single)

---

## Core Components

- `main.py`
  - Wires POST `/ask` to the selected ask-function based on `ASK_HANDLER`.

- `ask606_hybrid.py`
  - `ask_hybrid(question)`:
    - Classifies via `classify_query_enhanced(...)`
    - Delegates to `route_hybrid_query(...)` which orchestrates multiple deterministic SQL segments
    - Returns combined `query_results` plus optional LLM synthesis narrative

- `hybrid_query_handler.py`
  - Deterministic segments and orchestration:
    - PFOF by stock_group (month/quarter aware)
    - PFOF by order_type (market, marketable_limit, nonmarketable_limit, other)
    - Earliest PFOF month (overall and per broker)
    - Longest broker→venue consecutive-month streak
    - Quarterly analytics:
      - Top broker by PFOF per quarter
      - Largest exchange market share per quarter (via `monthly_data`)
      - Top ATS shares per quarter (via `finra_ats`)
  - LLM is used for summarization when helpful; SQL remains deterministic.

- `multi_table_query_framework.py`
  - Schema loading (`schemas/`)
  - Enhanced classification: tags include mentions_volume, mentions_pfof, mentions_order_type, mentions_rate, mentions_cph, mentions_month/year/quarter, mentions_broker/venue, mentions_trend, mentions_ats, mentions_tape, mentions_entity_type, mentions_market_share, mentions_first (earliest), mentions_streak
  - Generation helpers and safety rules (e.g., aggregations by month/quarter, market share exclusions for TRF/FINRA when “exchange” requested)

- Table-specific SQL generators (`handlers/`)
  - `handlers/executing_bd_606_handler.py`: PFOF/CPH/earliest/streak/quarter
  - `handlers/monthly_data_handler.py`: Exchange market share per quarter
  - `handlers/finra_ats_handler.py`: ATS top by quarter

---

## Data Sources and Schemas

- Postgres tables:
  - `executing_bd_606`
    - Includes `data_type` set to `'venue'` when `venues` is present, otherwise `'executing_bd'`
  - `monthly_data`
  - `finra_ats`
  - `entity_types`, `venue_mapping` (reference)
- JSON schemas in `schemas/`:
  - `executing_bd_606_schema.json`, `monthly_data_schema.json`, `finra_ats_schema.json`, `entity_types_schema.json`, `venue_mapping_schema.json`

### Name Resolution and Normalization
- Venue/broker aliasing and categories via JSON data files in repo
- Deterministic treatment for tape/exchange market share and PFOF metric selection (`*_usd`, `*_cph`)

---

## Request Flow in Detail

1) Client sends `{"question": "..."} → POST /ask`
2) `main.py` selects handler (default `ask606_hybrid.py`)
3) `ask_hybrid`:
   - `classify_query_enhanced(...)` → dict of tags
   - `route_hybrid_query(question, tags)` orchestrates:
     - Selects and runs relevant deterministic SQL segments (606, monthly_data, finra_ats)
     - Builds `query_results` map: each key contains `query`, `results`, `row_count`, description
     - Optionally performs LLM narrative synthesis over the results
4) Response includes:
   - `query_results`
   - `synthesis` (when produced)
   - `query_classification`
   - `row_count` (aggregate)

---

## Configuration

- `.env` (see `env.example`)
  - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  - `OPENAI_API_KEY`
  - `ASK_HANDLER=hybrid|multi|single` (default: `hybrid`)
- Local run:
  - `./start_local.sh` (FastAPI + uvicorn)
  - `/health`, `/debug` endpoints for diagnostics

---

## Deterministic Query Segments (Examples)

- PFOF by stock_group (per month/quarter/year)
- PFOF by order_type (market/limit/nonmarketable/other)
- Earliest PFOF month overall / per broker
- Longest broker→venue streak (PFOF > 0, consecutive months)
- Exchange market share by quarter (excludes TRF/FINRA for “exchange”)
- ATS top by quarter

Each segment:
- Is generated by a dedicated function (in `handlers/` or `hybrid_query_handler.py`)
- Executes directly with psycopg2 (autocommit on; rollback upon error)
- Returns rows and a readable query artifact

---

## LLM Usage Policy

- Primary role: narrative summarization over already-fetched results.
- Optional/limited: help with SQL hinting in non-critical flows; not used to author final SQL for core analytics.
- Guardrails:
  - Whitelisted tables and enforced schemas
  - Sanitization of any hint SQL snippets

---

## Extending the System

1) Add or modify a deterministic segment:
   - Implement or update a function in `handlers/` (or `hybrid_query_handler.py`)
   - Ensure the function:
     - Accepts `query_tags` and builds month/quarter/year-aware SQL as needed
     - Returns query string and results in a consistent shape
   - Register the segment in the hybrid router (include it conditionally based on tags)

2) Update schemas and mappings:
   - Edit/add JSON in `schemas/`
   - Update alias/canonicalization files if new venues/brokers are introduced

3) Add a new classification rule:
   - Extend `classify_query_enhanced(...)` in `multi_table_query_framework.py`
   - Tie the new tag to routing conditions in the hybrid router

---

## Troubleshooting & Ops Notes

- Autocommit and targeted rollbacks mitigate “current transaction is aborted”
- Quarterly aggregation paths prevent common GROUP BY day pitfalls
- `data_type` on `executing_bd_606` is now derived from `venues` presence for both new and backfilled rows
- Use `/debug` to confirm module imports and runtime health

---

## Quick Start

1) Configure `.env` (DB and OpenAI)
2) `./start_local.sh`
3) Test:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "In Q2 2025, which broker had the highest PFOF by stock group?"}'
```




