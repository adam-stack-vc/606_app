#!/usr/bin/env python3
"""
Test broker and venue alias resolution
"""
from query import resolve_aliases_in_sql

# Test cases
test_sqls = [
    # Broker aliases
    ("SELECT * FROM executing_bd_606 WHERE executing_bd = 'robinhood'", 
     "Robinhood Securities, LLC"),
    
    ("SELECT * FROM executing_bd_606 WHERE executing_bd = 'Robinhood'", 
     "Robinhood Securities, LLC"),
    
    ("SELECT * FROM executing_bd_606 WHERE executing_bd = 'schwab'", 
     "Charles Schwab"),
    
    # Venue aliases
    ("SELECT * FROM executing_bd_606 WHERE venues = 'citadel'", 
     "Citadel Securities, LLC"),
    
    ("SELECT * FROM executing_bd_606 WHERE venues = 'virtu'", 
     "Virtu Americas, LLC"),
    
    # Combined
    ("SELECT * FROM executing_bd_606 WHERE executing_bd = 'robinhood' AND venues = 'citadel'", 
     ["Robinhood Securities, LLC", "Citadel Securities, LLC"]),
]

print("=" * 80)
print("Testing Alias Resolution")
print("=" * 80)
print()

for sql, expected in test_sqls:
    print(f"Input SQL:")
    print(f"  {sql}")
    print()
    
    resolved = resolve_aliases_in_sql(sql)
    
    print(f"Resolved SQL:")
    print(f"  {resolved}")
    print()
    
    if isinstance(expected, list):
        checks = [exp in resolved for exp in expected]
        if all(checks):
            print("✅ All expected values found")
        else:
            print(f"❌ Expected values not found: {expected}")
    else:
        if expected in resolved:
            print(f"✅ Found expected value: {expected}")
        else:
            print(f"❌ Expected '{expected}' not found in result")
    
    print("-" * 80)
    print()

