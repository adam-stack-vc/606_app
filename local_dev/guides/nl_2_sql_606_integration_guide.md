# 606 NL2SQL Integration Guide
### Hybrid Pipeline: QueryIntent → LangChain SQL Hints → Deterministic SQL Builder
### For Cursor + GPT-5.1 Development Workflow

---

## 🎯 Overview

This guide describes the recommended architecture for integrating:

- **Rule-based classification**
- **Context disambiguation (direction, entities, metrics)**
- **Time period extraction**
- **QueryIntent abstraction**
- **LangChain SQLDatabaseChain (safe, restricted use)**
- **Deterministic SQL builder**
- **Postgres execution**

for the Market Structure / 606 app.

The goal is to combine **domain control** with **LLM semantic reasoning** *without sacrificing safety or correctness*.

---

# 🧪 System Architecture

```
Natural language input
        ↓
Query Classification (keyword/regex)
        ↓
Context Disambiguation (direction, entities, metric)
        ↓
Time Extraction (year, month, quarter)
        ↓
QueryIntent (semantic representation)
        ↓
LangChain SQL Hint (OPTIONAL semantic help)
        ↓
Deterministic SQL Builder (final, secure SQL)
        ↓
Postgres Query Execution
        ↓
LLM Summarizer (optional)
```

---

# 🧠 Component Architecture

## 1. Query Classification
Rule-based detection of query attributes:
- mentions_volume
- mentions_pfof
- mentions_broker / mentions_venue
- mentions_time (year/month)
- stock_group detection
- venue/broker canonical resolution

Outputs a `tags` dictionary.

---

## 2. Context Disambiguation
Uses:
- `direction_map.json` (semantic flows)
- spaCy dependency parsing
- passive/active voice handling
- agent/recipient extraction
- metric inference
- subject_role / object_role assignment

Determines query semantics such as:
- executing_bd → venue (volume flow)
- venue → executing_bd (PFOF flow)
- ats → market (liquidity/disclosure)

---

## 3. Time Extraction
Parses:
- Explicit: “January 2024”, “Q1 2023”
- Relative: “last month”, “this quarter”, “last year”
- Partial: “2024”, “January”

Normalizes into:
```
{"year": Y, "month": M, "quarter": Q}
```

---

## 4. QueryIntent Model
Semantic representation for NL queries:

```
QueryIntent(
    topic,
    metric,
    direction,
    entities,
    period,
    dimensions,
    filters,
    subject_role,
    object_role
)
```

Provides a stable abstraction for SQL generation and RAG.

---

## 5. LangChain SQLDatabaseChain (Semantic Hint Only)
Restricted usage:
- Help with MIN/MAX (earliest/latest)
- Help with GROUP BY reasoning
- Help with ORDER BY superlatives (largest, highest)
- Help with LIMIT (top/bottom N)

Not allowed to:
- Execute SQL
- Create final SQL
- Invent tables/columns

Safe usage:
- Only whitelisted tables in DB connection
- Used to produce intermediate `sql_hint`

---

## 6. Deterministic SQL Builder
Combines:
- QueryIntent
- optional SQL hint
- schema_registry
- allowed joins
- allowed columns

Produces fully validated SQL.

---

## 7. Execution & Summarization
- SQL executed with psycopg2 or asyncpg
- Response optionally summarized by GPT-5.1

---

# 📂 Core Files

```
nl2sql_606_integration_guide.md
schema_registry.json
schema_metadata.json
metric_map.json

context_direction.py
time_direction.py
query_intent.py
semantic_sql_adapter.py
multi_table_query_framework.py

/tools
    join_graph_generator.py
    synthetic_nl_sql_generator.py
    rag_index_schema.py

eval/nl_sql_pairs.jsonl
/tests
```

---

# 📁 0. Suggested Directory Layout
```
project_root/
  schema_registry.json
  schema_metadata.json
  metric_map.json

  eval/
    nl_sql_pairs.jsonl

  tools/
    join_graph_generator.py
    synthetic_nl_sql_generator.py
    rag_index_schema.py

  tests/
    __init__.py
    test_nl_to_intent.py
    test_intent_to_sql.py
    conftest.py
```

You can adjust names/paths, but this gives a clean mental model.

---

# 📘 1. schema_registry.json (Template + Example)
This is the single source of truth for tables, columns, and types.

```
{ ... }
```

*(Schema content omitted here for brevity — it remains in the full guide.)*

---

# 🧩 2. schema_metadata.json (Join Rules, Roles, Time Columns)
Defines semantic table metadata.

```
{ ... }
```

---

# 📊 3. metric_map.json (Metric DSL)
Defines derived metrics, formulas, triggers, and supported tables.

```
{ ... }
```

---

# 🧪 4. Evaluation Dataset Seed – eval/nl_sql_pairs.jsonl
Stores NL→SQL golden pairs.

```
{ ... }
```

---

# 🧪 5. Pytest Scaffolding
Unit tests for NL→Intent and Intent→SQL.

```
{ ... }
```

---

# 🕸 6. Join Graph Generator – tools/join_graph_generator.py
Builds a graph of joinable tables.

```
{ ... }
```

---

# 🤖 7. Synthetic NL→SQL Generator – tools/synthetic_nl_sql_generator.py
Generates training/evaluation pairs via GPT.

```
{ ... }
```

---

# 📚 8. RAG Index for Schema & Metrics – tools/rag_index_schema.py
Embeds schema+metrics into a vector DB.

```
{ ... }
```

---

# 🧱 Best Practices for Adding New Tables & Schemas
1. Update `schema_registry.json`
2. Update `schema_metadata.json`
3. Update `metric_map.json`
4. Add table descriptions
5. Extend QueryIntent routing
6. Extend SQL builder
7. Add NL→SQL eval cases
8. Add unit tests
9. Update join graph
10. Update RAG embeddings

---

# 🧠 Philosophy
- Deterministic SQL = Safety
- QueryIntent = Abstraction
- LangChain = Semantic hint layer
- Schema Registry = Source of truth
- Direction/Time maps = Domain reasoning

---

# ✔ This guide will be expanded as features mature.


