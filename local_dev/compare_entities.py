import json
import difflib

# Data from the previous step (I will paste the JSON output here to avoid re-querying or just re-query in the script)
# To be self-contained and robust, I'll just re-query or hardcode the lists if they were small, but they are large.
# Actually, I can just import from db in the script.

from db import get_db_connection

def get_entities():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT executing_bd FROM executing_bd_606")
    brokers = [r[0] for r in cur.fetchall() if r[0]]
    
    cur.execute("SELECT DISTINCT venues FROM executing_bd_606")
    venues = [r[0] for r in cur.fetchall() if r[0]]
    
    conn.close()
    return sorted(brokers), sorted(venues)

def find_overlaps(brokers, venues):
    brokers_set = set(brokers)
    venues_set = set(venues)
    
    # Exact matches
    exact_matches = sorted(list(brokers_set.intersection(venues_set)))
    
    print(f"--- Exact Matches ({len(exact_matches)}) ---")
    for m in exact_matches:
        print(f"  {m}")
    print("\n")
    
    # Fuzzy matches
    # We want to find broker B and venue V where B ~ V but B != V
    print(f"--- Fuzzy Matches (Similiarity > 0.8) ---")
    
    # Optimization: Don't compare everything to everything if lists are huge, but 100x500 is 50,000 comparisons, which is instant.
    
    matches = []
    for b in brokers:
        # exact matches already covered
        if b in venues_set:
            continue
            
        # Find close matches in venues
        # get_close_matches returns list, but doesn't give score. 
        # Let's use SequenceMatcher for more control
        for v in venues:
            if b == v: continue
            
            ratio = difflib.SequenceMatcher(None, b.lower(), v.lower()).ratio()
            if ratio > 0.85: # High threshold
                matches.append((ratio, b, v))
                
    # Sort by score
    matches.sort(key=lambda x: x[0], reverse=True)
    
    for score, b, v in matches:
        print(f"  [{score:.2f}] Broker: '{b}'  <-->  Venue: '{v}'")
        
    print("\n")
    
    # Check specific "Citi" case
    print("--- Citi Analysis ---")
    citi_brokers = [b for b in brokers if "citi" in b.lower()]
    citi_venues = [v for v in venues if "citi" in v.lower()]
    print(f"Brokers with 'citi': {citi_brokers}")
    print(f"Venues with 'citi': {citi_venues}")

if __name__ == "__main__":
    brokers, venues = get_entities()
    find_overlaps(brokers, venues)
