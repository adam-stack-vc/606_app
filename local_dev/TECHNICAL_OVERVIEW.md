Technical Overview - 606 Local Dev Chatbot

Overview
- Purpose: Natural language to SQL over 606 PFOF data, monthly market data, and FINRA ATS, with deterministic query paths and LLM synthesis.
- Runtime: FastAPI (uvicorn) with optional OpenAI calls for narrative synthesis or SQL generation fallback.
- Data sources (Postgres):
  - executing_bd_606 (606 PFOF data)
  - monthly_data (market volume by day/participant)
  - finra_ats (quarterly ATS data)
  - entity_types, venue_mapping (reference)

How to Run
- Setup DB: ./setup_database.sh (uses .env)
- Start API: ./start_local.sh
- Environment (.env):
  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  - OPENAI_API_KEY
  - ASK_HANDLER=hybrid|multi|single (default hybrid)

FastAPI App
- File: main.py
  - Endpoints: GET / (health), GET /health, GET /debug, POST /ask
  - Handler selection by ASK_HANDLER:
    - single → ask606.py
    - multi → ask606_multi_table.py
    - hybrid (default) → ask606_hybrid.py
  - Error handling: try/except around ask(); returns HTTP 500 with error details; logging enabled.

Core Handlers
1) Hybrid (preferred): local_dev/ask606_hybrid.py
   - Classifies, executes multiple deterministic SQL queries where applicable, then synthesizes a narrative.
   - Autocommit on, with rollback where needed.
   - Deterministic synthesis (no “insufficient data” when results present):
     - CPH per stock_group
     - PFOF per stock_group
     - PFOF per order_type
     - Earliest PFOF month (overall, and per broker)
     - Longest broker→venue streak (monthly consecutive PFOF > 0)
     - Quarter-based:
       - Top broker by PFOF per quarter
       - Largest exchange market share per quarter
       - Top ATS shares per quarter

2) Multi-table: local_dev/ask606_multi_table.py
   - Similar to hybrid, but executes deterministic SQL paths directly and returns a query_results map plus a light synthesis.
   - Includes monthly_data fallback when LLM-generated SQL hits GROUP BY/day errors.
   - Deterministic segments mirror hybrid for parity (CPH, per stock_group, per order_type, earliest, streak, quarterly).

Shared Table-Specific SQL Generators (handlers/)
- handlers/executing_bd_606_handler.py
  - generate_top_cph_brokers_query(query_tags): top 3 brokers by max *_cph within each stock_group (month/year-aware)
  - generate_top_pfof_broker_per_stock_group_query(query_tags): top PFOF per stock_group (month/year-aware)
  - generate_top_pfof_broker_per_order_type_query(query_tags): top PFOF per order type (market, marketable_limit, nonmarketable_limit, other)
  - generate_earliest_pfof_month_query(): earliest month/year with PFOF > 0
  - generate_earliest_pfof_by_broker_query(): earliest month/year with PFOF > 0 per broker
  - generate_longest_broker_venue_streak_query(): longest consecutive-month streak (PFOF > 0) per broker→venue pair
  - generate_top_pfof_broker_per_quarter_query(query_tags): top PFOF broker per quarter in given year

- handlers/monthly_data_handler.py
  - generate_top_exchange_share_per_quarter_query(query_tags): top exchange market share per quarter (excludes TRF/FINRA)

- handlers/finra_ats_handler.py
  - generate_top_ats_shares_per_quarter_query(query_tags): top ATS by total_shares per quarter

Classification & Prompting Framework
- File: local_dev/multi_table_query_framework.py
  - Schema loading: load_all_schemas(schemas/)
  - Classification: classify_query_enhanced(user_input) sets flags used for routing:
    - mentions_volume, mentions_pfof, mentions_order_type, mentions_rate, mentions_cph, mentions_max,
      mentions_month, mentions_year, mentions_quarter, mentions_broker, mentions_venue, mentions_trend,
      mentions_ats, mentions_tape, mentions_entity_type, mentions_market_share,
      mentions_first (earliest), mentions_streak (longest run)
  - Non-NLP fallback:
    - Month-name parsing without SpaCy
    - Year regex
  - Guidance rules:
    - monthly_data aggregation safety (EXTRACT, GROUP BY, avoid raw day)
    - Market share rules (compute share within period; tape-aware if requested)
    - PFOF rules (use *_usd directly; do not route to volume estimation unless “orders/volume” explicitly requested)
  - SQL helpers:
    - generate_volume_estimation_query(user_input, tags) [used only if query implies volume/orders]
    - generate_market_data_query(tags): month/quarter/year aware, returns totals or top participants
    - generate_ats_query(tags)
    - sanitize_sql_output(sql): strip backticks/fences, fix common syntax issues

Hybrid Query Router
- File: local_dev/hybrid_query_handler.py
  - route_hybrid_query(): always uses complex multi-table path (deterministic segments + LLM synthesis)
  - Deterministic query assembly based on classification flags:
    - PFOF: *_usd aggregates (top by month/quarter, by stock_group, by order_type, earliest, streak)
    - monthly_data: totals, market share by quarter; tape handling via rules
    - finra_ats: quarterly totals, top ATS
  - Synthesis:
    - Deterministic text for known results; otherwise LLM summarization with system prompt
    - Errors are included in data_summary for context, not hidden

LLM Usage
- When ASK_HANDLER=hybrid:
  - SQL generally deterministic; LLM used for synthesis narrative only.
- When ASK_HANDLER=multi:
  - LLM can be used to draft SQL for generic cases, but deterministic queries execute in parallel for critical flows.
  - Fallback path for monthly_data GROUP BY/day errors.

Schemas, Mapping, and Data Files
- Schemas (local_dev/schemas/):
  - executing_bd_606_schema.json (structure and columns for 606 table)
  - monthly_data_schema.json
  - finra_ats_schema.json
  - entity_types_schema.json
  - venue_mapping_schema.json
- Data files (referenced by load_data_robust.sql):
  - executing_bd_606.csv
  - monthly_data.csv
  - finra_ats.csv
  - venue_mapping.csv

Database & Setup Scripts
- create_tables.sql: tables, indexes, triggers
- load_data_robust.sql: robust COPY/load with temp tables; inserts into canonical tables
- setup_database.sh: reads .env, creates tables, loads all data, verifies counts (psql)

Configuration & Secrets
- aws_config.py: loads secrets from AWS Secrets Manager if AWS_EXECUTION_ENV is set; otherwise .env
- db.py: get_db_connection() via aws_config

Error Handling & Logging
- Autocommit enabled for DB connections
- On SQL error: rollback() attempted, error returned with context
- /debug endpoint imports key modules and returns import status

Endpoints & Examples
- POST /ask
  - Body: {"question": "In April 2024, which broker received the most PFOF per stock group?"}
  - Response: {
      "query_results": {
        "pfof_by_stock_group": { "query": "...", "results": [...], "row_count": n },
        "exchange_share_by_quarter": {...},
        "ats_top_by_quarter": {...},
        ...
      },
      "synthesis": "Human readable summary...",
      "query_classification": {...}
    }

Key Design Choices
- Deterministic-first for correctness and debuggability; LLM used for narrative
- Explicit routing via classification flags; no hidden magic
- Market share uses quarterly aggregation and excludes TRF/FINRA for “exchange”
- PFOF uses *_usd columns; volume estimation (USD/CPH) only when specifically requested as “orders/volume”

Troubleshooting
- “current transaction is aborted” → already mitigated via autocommit + rollback on errors
- GROUP BY day errors → deterministic monthly_data fallback path
- NameError for new handler functions → ensure handlers/__init__.py present and imports included (done)

File Index (Primary)
- main.py (FastAPI, /ask endpoint)
- ask606_hybrid.py (hybrid handler with deterministic + synthesis)
- ask606_multi_table.py (multi-table handler with deterministic segments)
- multi_table_query_framework.py (classification, rules, schema, helpers)
- handlers/
  - executing_bd_606_handler.py (PFOF/CPH/earliest/streak/quarter queries)
  - monthly_data_handler.py (exchange market share per quarter)
  - finra_ats_handler.py (ATS top per quarter)
- schemas/* (table schema JSON)
- create_tables.sql, load_data_robust.sql (DB setup/load)
- setup_database.sh, start_local.sh (local run)


