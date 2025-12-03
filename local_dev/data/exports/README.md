# Data Exports

This directory contains CSV exports and data snapshots. These are **not configuration files** - they are actual data records.

## Files

### `executing_bd_606.csv`
- **Type**: Bulk data export from executing_bd_606 table
- **Purpose**: Full table snapshot for offline analysis
- **Size**: ~12MB
- **Last Updated**: October 28, 2024

### `execting_bd_periods.csv` (note: typo in filename)
- **Type**: Date coverage analysis export
- **Purpose**: Shows which brokers reported in which time periods
- **Query**: Lists distinct (executing_bd, month, year, stock_group) combinations
- **Last Updated**: November 23, 2024

### `venue_mapping.csv`
- **Type**: Database table export
- **Purpose**: Canonical venue names and their aliases
- **Note**: This was exported from the `venue_mapping` database table (populated by load_venue_data.py)
- **Last Updated**: December 2, 2024

## Notes

These files are kept for:
- Offline data analysis
- Historical reference
- Backup/recovery
- Documentation of data coverage

They are **not used by the application code** - the live system queries the PostgreSQL database directly.
