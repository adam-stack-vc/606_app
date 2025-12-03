# Legacy Files

This directory contains files that are **no longer actively used** by the current system. They are kept for reference and backward compatibility with older query systems.

## Legacy Mapping Files

### `executing_bd_aliases.LEGACY.json`
- **Status**: DEPRECATED - Used by old query.py system only
- **Current Replacement**: `value_mappings.json` (executing_bd section)
- **Format**: `{"Canonical Name": ["alias1", "alias2"]}`
- **Purpose**: Mapped broker shortnames to canonical names
- **Last Used By**: query.py, query_framework.py, multi_table_query_framework.py

### `venue_aliases.LEGACY.json`
- **Status**: DEPRECATED - Used by old query.py system only
- **Current Replacement**: `value_mappings.json` (venues section)
- **Format**: `{"Canonical Name": ["alias1", "alias2"]}`
- **Purpose**: Mapped venue shortnames to canonical names
- **Last Used By**: query.py, query_framework.py

### `venue_categories.json`
- **Status**: ARCHIVED - Not referenced by any code
- **Current Replacement**: `value_mappings.json` (_venue_metadata section)
- **Purpose**: Categorized venues into types (exchanges, wholesalers, market_makers, ats, global_investment_banks)
- **Note**: This file was never actually used by the codebase

## Migration Notes

All alias mappings have been **consolidated into `value_mappings.json`** with the following improvements:

1. **Single Source of Truth**: All entity name mappings in one file
2. **Consistent Format**: `{"alias": "Canonical Name"}` (reversed from legacy)
3. **Case Insensitive**: All lookups use lowercase normalization
4. **Conflict Resolution**: When duplicate aliases existed, existing mappings were preserved
5. **Category Metadata**: Venue categories added as `_venue_metadata` section

## Current Active System

The planner-based query system (planner.py, sql_templates.py) uses:
- **entity_mappings.json**: Maps user terms to column names (e.g., "broker" → "executing_bd")
- **value_mappings.json**: Maps user values to canonical database values (e.g., "robinhood" → "Robinhood Securities, LLC")

## Migration Date

Files moved to legacy: December 2, 2024
