# 606 PFOF Query System - Local Development

Natural language to SQL query system for SEC Rule 606 Payment for Order Flow data.

## Directory Structure

```
local_dev/
├── Core Query System (text-to-sql)
│   ├── main.py                          # FastAPI entry point
│   ├── ask606_hybrid.py                 # Hybrid query router
│   ├── hybrid_query_handler.py          # Multi-table query handler
│   ├── planner.py                       # Single-table query planner
│   ├── sql_templates.py                 # SQL generation templates
│   ├── multi_table_query_framework.py   # Query classification
│   ├── llm_intent_extractor.py          # LLM-based intent extraction
│   ├── query_intent.py                  # QueryIntent dataclass
│   ├── capability_registry.py           # Table capabilities metadata
│   ├── semantic_sql_adapter.py          # Legacy semantic SQL adapter
│   ├── value_normalizer.py              # Entity value normalization
│   └── db.py                            # Database connection
│
├── Configuration Files
│   ├── .env                             # Environment variables
│   ├── entity_mappings.json             # Entity synonym mappings
│   ├── value_mappings.json              # Value normalization mappings
│   ├── direction_map.json               # Query direction mappings
│   ├── schema_registry.json             # Table schema registry
│   └── test_suite.json                  # Test suite configuration
│
├── Streamlit App
│   └── streamlit_app.py                 # Testing UI
│
├── Data & Schemas
│   ├── schemas/                         # JSON table schemas
│   ├── eval/                            # Test query JSONL files
│   ├── data/                            # Data files
│   ├── table_data/                      # Table data exports
│   └── handlers/                        # Legacy handler code
│
├── scripts/                             # Utility scripts
│   ├── test_*.py                        # Test scripts
│   ├── load_*.py                        # Data loading scripts
│   ├── deploy*.sh                       # Deployment scripts
│   └── setup_database.sh                # Database setup
│
├── guides/                              # Documentation
│   ├── README.md                        # Main README
│   ├── SESSION_SUMMARY*.md              # Session summaries
│   ├── TEMPORAL_DIMENSION*.md           # Temporal dimension docs
│   ├── FIXES*.md                        # Fix documentation
│   └── *_GUIDE.md                       # Various guides
│
└── archive/                             # Old/unused files
    ├── Old implementations
    ├── SQL setup files
    ├── Backup files
    └── Deployment artifacts
```

## Core Text-to-SQL Flow

### 1. Entry Point
```
User Query → main.py → ask606_hybrid.ask()
```

### 2. Query Classification
```
classify_query_enhanced() in multi_table_query_framework.py
  ↓
Extracts: year, month, entities, metric, direction, etc.
```

### 3. Query Routing (in hybrid_query_handler.py)
```
route_hybrid_query()
  ├─→ plan_single_sql() → Single-table query (deterministic templates)
  └─→ generate_complex_multi_table_query() → Multi-table (deterministic + LLM synthesis)
```

### 4. SQL Generation
```
Single-table: planner.py + sql_templates.py (deterministic)
Multi-table: hybrid_query_handler.py (deterministic per-table queries)
```

### 5. Execution & Response
```
Database execution → Results → Narrative generation
```

## Key Features

- **Deterministic SQL Generation**: Template-based, no SQL hallucination
- **LLM Intent Extraction**: Optional (USE_LLM_INTENT env var)
- **Semantic Hints**: Optional LangChain hints for complex patterns (USE_SEMANTIC_HINTS env var)
- **Multi-Table Support**: Automatic routing and synthesis
- **Entity Normalization**: Synonym mapping and fuzzy matching
- **Temporal Dimensions**: Generic capability-driven approach
- **Streamlit Testing UI**: Interactive query testing and feedback with semantic hints toggle

## Environment Variables

- `USE_LLM_INTENT=false` - Use deterministic classification (recommended)
- `USE_SEMANTIC_HINTS=false` - Use LangChain semantic hints for complex patterns (optional)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database config
- `OPENAI_API_KEY` - For narrative synthesis and semantic hints

## Quick Start

### Start FastAPI Server
```bash
uvicorn main:app --reload --port 8000
```

### Start Streamlit App
```bash
streamlit run streamlit_app.py
```

### Run Tests
```bash
cd scripts
USE_LLM_INTENT=false python test_query_fixes.py
```

## Recent Updates

**December 5, 2025**
- Fixed temporal dimension bug (GROUP BY month/quarter/year)
- Enhanced entity detection ("for X" pattern, interrogatives)
- Cleaned invalid entity filters in COUNT queries
- Organized project structure (guides/, scripts/, archive/)
- Added semantic hints feature with Streamlit toggle and CSV tracking

See `guides/SESSION_SUMMARY_DEC3.md` for complete details.

## Documentation

- **Query Planning**: `guides/NL2SQL_INTEGRATION_GUIDE_UPDATED.md`
- **Temporal Dimensions**: `guides/TEMPORAL_DIMENSION_SOLUTION.md`
- **Multi-Table**: `guides/MULTI_TABLE_MIGRATION_GUIDE.md`
- **Semantic Hints**: `guides/SEMANTIC_HINTS_FEATURE.md`
- **Fixes**: `guides/FIXES_IMPLEMENTED.md`
- **Streamlit**: `guides/README_STREAMLIT.md`

## Architecture Decisions

1. **Deterministic SQL Templates** - Prevents hallucination, enables debugging
2. **Capability Registry** - Table metadata drives SQL generation
3. **Hybrid Routing** - Single-table for simple, multi-table for complex
4. **LLM Only for Synthesis** - SQL generation is deterministic, narratives use LLM

## Contributing

When adding new features:
1. Update capability_registry.py for new tables/columns
2. Add SQL templates to sql_templates.py
3. Update classification in multi_table_query_framework.py
4. Add tests to scripts/test_*.py
5. Document in guides/

## Support

For issues or questions, check the guides/ directory or create an issue with query examples and expected SQL.
