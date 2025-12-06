"""
Test synonym mappings for entities and values
"""
import os
os.environ["USE_LLM_INTENT"] = "true"

from planner import plan_single_sql

# Test queries using synonyms
test_queries = [
    # Stock group / category synonyms
    "Total PFOF for S&P 500 stocks in 2024",
    "Total PFOF for S&P stocks in 2024",
    "PFOF by category in 2024",
    "PFOF by stock type in 2024",

    # Venue/wholesaler/market maker synonyms
    "How many wholesalers did Robinhood use in 2024",
    "Top market maker by PFOF for Robinhood",
    "PFOF by liquidity provider for Charles Schwab",

    # Broker synonyms
    "Top retail broker by PFOF in 2024",
    "PFOF for routing brokers in Q2 2024",
    "Count of online brokers in 2024",

    # Participant/exchange synonyms
    "Top trading venue by volume in 2024",
    "Volume by market center in Q2",
    "Top stock exchange by total shares",

    # ATS/dark pool synonyms
    "Top dark pool by volume in 2024",
    "Volume for alternative trading systems in Q2",
    "Count of ECNs in the data",

    # Tape synonyms (metric detection)
    "Total NYSE stocks volume in 2024",
    "NASDAQ listed stocks by market participant",
    "ETF volume by exchange in Q2 2024",
]

print("Testing Synonym Mappings")
print("=" * 80)

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print("-" * 80)
    sql = plan_single_sql(query, {})
    if sql:
        # Show just the key parts of the SQL
        lines = sql.split("\n")
        select_line = [l for l in lines if "SELECT" in l.upper()]
        from_line = [l for l in lines if "FROM" in l.upper()]
        where_lines = [l for l in lines if "WHERE" in l.upper() or "stock_group" in l or "data_type" in l]

        if select_line:
            print(f"✅ {select_line[0].strip()}")
        if from_line:
            print(f"   {from_line[0].strip()}")
        if where_lines:
            for wl in where_lines[:3]:  # First 3 WHERE conditions
                print(f"   {wl.strip()}")
    else:
        print("❌ Failed to generate SQL")
    print()
