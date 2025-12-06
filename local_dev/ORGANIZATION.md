# Project Organization Summary

**Date:** December 5, 2025
**Organized by:** Claude Code

---

## Overview

The local_dev directory has been reorganized to separate core system files from documentation, scripts, and archived materials. This improves maintainability and makes it clear which files are actively used in the text-to-sql process.

---

## Directory Structure

### Root Directory (15 Python files, 5 JSON files)

**Core Query System Files:**
- `main.py` - FastAPI application entry point
- `ask606_hybrid.py` - Hybrid query router (calls planner or multi-table handler)
- `hybrid_query_handler.py` - Multi-table query handler with LLM synthesis
- `planner.py` - Single-table query planner (deterministic SQL generation)
- `sql_templates.py` - SQL template builders (build_aggregate, build_top_n, etc.)
- `multi_table_query_framework.py` - Query classification (classify_query_enhanced)
- `llm_intent_extractor.py` - LLM-based intent extraction (optional)
- `query_intent.py` - QueryIntent dataclass
- `capability_registry.py` - Table capabilities metadata (TimeInfo, TableCapabilities)
- `value_normalizer.py` - Entity value normalization and fuzzy matching
- `semantic_sql_adapter.py` - Legacy semantic SQL adapter
- `db.py` - Database connection wrapper

**Supporting Files:**
- `auth.py` - Authentication (if used)
- `aws_config.py` - AWS configuration

**Streamlit App:**
- `streamlit_app.py` - Interactive testing UI

**Configuration Files (JSON):**
- `entity_mappings.json` - Entity synonym mappings (broker → executing_bd, venue → venues)
- `value_mappings.json` - Value normalization mappings (fuzzy matching rules)
- `direction_map.json` - Query direction mappings (pfof → venue_to_executing_bd)
- `schema_registry.json` - Table schema registry
- `test_suite.json` - Test suite configuration

**Other Root Files:**
- `.env` - Environment variables
- `env.example` - Environment template
- `README.md` - Main documentation (newly created)
- `ORGANIZATION.md` - This file

---

### guides/ (23 documentation files)

All markdown documentation files:

**Session Summaries:**
- `SESSION_SUMMARY.md` - General session summary
- `SESSION_SUMMARY_DEC3.md` - December 3, 2025 session (temporal dimension fix)

**Feature Documentation:**
- `TEMPORAL_DIMENSION_SOLUTION.md` - Generic temporal dimension design
- `TEMPORAL_DIMENSION_FIX_COMPLETE.md` - Implementation details
- `TEMPORAL_DIMENSION_BUG.md` - Bug analysis
- `FIXES_IMPLEMENTED.md` - P0/P1 fixes for count queries
- `FIXES_SUMMARY.md` - Round 1 fixes summary
- `FIXES_SUMMARY_ROUND2.md` - Round 2 fixes summary
- `VENUE_RESOLUTION_FIX.md` - Venue resolution improvements

**Implementation Guides:**
- `NL2SQL_INTEGRATION_GUIDE_UPDATED.md` - Query planning guide
- `MULTI_TABLE_MIGRATION_GUIDE.md` - Multi-table architecture
- `CROSS_TABLE_ENRICHMENT.md` - Cross-table enrichment patterns
- `VENUE_MAPPING_GUIDE.md` - Venue alias resolution
- `FINRA_ATS_UPLOAD_GUIDE.md` - FINRA ATS data upload

**Testing & Usage:**
- `TESTING_APP_INTEGRATION.md` - Testing app integration
- `QUICK_START.md` - Quick start guide
- `QUERY_FEEDBACK_DIAGNOSTIC.md` - Query feedback analysis
- `README_STREAMLIT.md` - Streamlit app documentation
- `README.md` - Original README (moved to guides)
- `TECHNICAL_OVERVIEW.md` - Technical overview

---

### scripts/ (27 utility scripts)

**Test Scripts:**
- `test_query_fixes.py` - Test count query fixes
- `test_temporal_dimension_fix.py` - Test temporal dimension fixes
- `test_feedback_issues.py` - Test feedback query issues
- `test_final_two_fixes.py` - Test final two fixes
- `test_llm_planner.py` - Test LLM intent extraction
- `test_new_operations.py` - Test count and per_entity_average operations
- `test_synonyms.py` - Test entity synonym mapping

**Data Loading Scripts:**
- `load_venue_aliases.py` - Load venue aliases into database
- `load_venue_data.py` - Load venue data
- `filter_q2_2025_pfof.py` - Filter Q2 2025 PFOF data
- `prune_xml_by_pfof.py` - Prune XML files by PFOF threshold

**Database Setup:**
- `setup_database.sh` - Database initialization script
- `create_ats_n_filings_table.sh` - Create ATS N filings table

**Deployment Scripts:**
- `deploy.sh` - General deployment
- `deploy-ec2.sh` - EC2 deployment
- `deploy-ec2-simple.sh` - Simplified EC2 deployment
- `deploy_to_aws.sh` - AWS deployment
- `start_local.sh` - Start local development server
- `upload_finra_ats.sh` - Upload FINRA ATS data

**Utilities:**
- `show_llm_prompt.py` - Display LLM prompt for debugging
- `debug_db.py` - Database debugging utilities

---

### archive/ (34 old/unused files)

**Old Implementations:**
- `ask606.py` - Old single-table version (replaced by hybrid)
- `ask606_multi_table.py` - Old multi-table version (replaced by hybrid)
- `query_framework.py` - Old query framework
- `query_framework_backup.py` - Backup of old framework
- `multi_table_query_handler.py` - Old multi-table handler
- `query.py` - Old query handler
- `main_b1.py` - Backup of main.py
- `context_direction.py` - Old direction detection (replaced)
- `time_direction.py` - Old time direction logic (replaced)
- `cross_table_enrichment.py` - Old enrichment logic
- `value_normalizer_exact_only.py.bak` - Backup file

**SQL Setup Files:**
- `create_tables.sql` - Table creation SQL
- `create_finra_ats_table.sql` - FINRA ATS table
- `create_venue_mapping_table.sql` - Venue mapping table
- `create_venue_mapping_with_aliases.sql` - Enhanced venue mapping
- `create_ats_n_filings_table.sql` - ATS N filings table
- `create_ats_n_flat_table.sql` - ATS N flat table
- `ats_n_filings_dump.sql` - Data dump

**Data Files:**
- `606_queries.txt` - Query examples
- `FirmCRD-XMLLink.csv` - Firm CRD data
- Various CSV files from query feedback

**Configuration/Schema:**
- `606_schema.json` - Old schema
- `broker_categories.json` - Broker categories

**Deployment Artifacts:**
- `dockerfile` - Docker configuration
- `fastapi-606-amd64.tar.gz` - Docker image archive
- `ec2-trust-policy.json` - AWS EC2 trust policy
- `ec2-additional-permissions.json` - AWS EC2 permissions

**Miscellaneous:**
- `nsql.yaml` - NSQL configuration
- `query analysis.xlsx` - Query analysis spreadsheet
- `processed_Q3_2025/` - Processed Q3 2025 data

---

### Other Directories (kept in place)

**schemas/** - JSON table schema files (7 files)
- Individual table schemas for OpenAI context

**eval/** - Test query JSONL files
- `nl_sql_pairs_additional.jsonl` - Test queries (IDs 16-83)

**data/** - Data files and exports
- Various data files used by the system

**table_data/** - Table data exports
- Exported table data for backup/testing

**tests/** - Test directory (4 files)
- Legacy test files

**handlers/** - Handler modules (7 files)
- Legacy handler code

**legacy/** - Legacy code (6 files)
- Old implementation files

**venv/** - Python virtual environment
- Not version controlled

**__pycache__/** - Python bytecode cache
- Generated files

**.claude/** - Claude Code configuration
- Agent configuration files

---

## File Count Summary

| Location | Count | Purpose |
|----------|-------|---------|
| Root *.py | 15 | Core text-to-sql system |
| Root *.json | 5 | Configuration files |
| guides/ | 23 | Documentation |
| scripts/ | 27 | Utilities, tests, deployment |
| archive/ | 34 | Old/unused files |
| schemas/ | 7 | Table schemas |
| eval/ | 1+ | Test queries |
| data/ | varies | Data files |
| table_data/ | varies | Table exports |

**Total organized:** ~100+ files

---

## Benefits of This Organization

### 1. **Clarity**
- Easy to see which files are actively used in text-to-sql
- Clear separation of concerns (code vs docs vs scripts)

### 2. **Maintainability**
- Scripts are isolated and easy to find
- Documentation is organized in one place
- Old files are preserved but out of the way

### 3. **Onboarding**
- New developers can quickly understand the system
- README.md provides clear entry point
- Documentation is centralized

### 4. **Development**
- Faster file search in IDEs
- Less clutter in root directory
- Clear distinction between prod and dev files

---

## Key Files for Text-to-SQL Process

If you need to understand or modify the text-to-sql system, focus on these files:

1. **Entry:** `main.py` → `ask606_hybrid.py`
2. **Classification:** `multi_table_query_framework.py` (classify_query_enhanced)
3. **Routing:** `hybrid_query_handler.py` (route_hybrid_query)
4. **Single-table SQL:** `planner.py` + `sql_templates.py`
5. **Multi-table SQL:** `hybrid_query_handler.py` (generate_complex_multi_table_query)
6. **Metadata:** `capability_registry.py`
7. **Config:** `entity_mappings.json`, `value_mappings.json`

---

## What Was Moved Where

### To guides/
- All `*.md` files (documentation)

### To scripts/
- All `test_*.py` files (test scripts)
- All `load_*.py` files (data loading)
- All `*deploy*.sh` files (deployment)
- All `setup*.sh` files (setup scripts)
- Utility scripts: `show_llm_prompt.py`, `debug_db.py`

### To archive/
- Old implementations: `ask606.py`, `ask606_multi_table.py`, `query.py`
- Backup files: `*_backup.py`, `*_b1.py`, `*.bak`
- SQL files: `*.sql`
- Old logic: `context_direction.py`, `time_direction.py`, `cross_table_enrichment.py`
- Docker/AWS: `dockerfile`, `*.tar.gz`, `ec2-*.json`
- Data files: `*.csv`, `*.txt`, `*.xlsx`
- Old configs: `606_schema.json`, `broker_categories.json`

### Kept in Root
- Core system Python files (15 files)
- Configuration JSON files (5 files)
- Streamlit app
- Environment files (.env, env.example)
- README files

---

## Next Steps

1. **Update imports** if any scripts reference moved files
2. **Update documentation links** in guides to reference new locations
3. **Clean up archive/** periodically - delete truly obsolete files
4. **Add new files** to appropriate directories (not root)

---

## Notes

- The organization preserves all files - nothing was deleted
- Git history is preserved
- Virtual environment (venv/) was not moved
- Hidden files (.env, .claude) remain in root
- Subdirectories (schemas/, eval/, data/) remain unchanged as they're already organized
