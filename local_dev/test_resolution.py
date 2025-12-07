import json
import sys
import os

# Add current directory to sys.path to import value_normalizer
sys.path.append(os.getcwd())
from value_normalizer import normalize_value_fuzzy

def resolve_ambiguous_entity(entity_name, context_type=None):
    """
    Resolve an entity name to its canonical form, potentially using context.
    
    Args:
        entity_name: The raw entity name (e.g. "citi")
        context_type: "broker" or "venue" if known, otherwise None
        
    Returns:
        Canonical entity name
    """
    # First try exact normalization for both types
    broker_norm, broker_alias, broker_score = normalize_value_fuzzy("executing_bd", entity_name)
    venue_norm, venue_alias, venue_score = normalize_value_fuzzy("venues", entity_name)
    
    print(f"Resolving '{entity_name}' (Context: {context_type})")
    print(f"  Broker Match: {broker_norm} (Score: {broker_score})")
    print(f"  Venue Match:  {venue_norm} (Score: {venue_score})")
    
    # If context is provided, prefer that type
    if context_type == "broker":
        return broker_norm
    elif context_type == "venue":
        return venue_norm
        
    # If no context, prefer the higher score
    if broker_score > venue_score:
        return broker_norm
    elif venue_score > broker_score:
        return venue_norm
    else:
        # Tie-breaker or ambiguous
        # Default to venue if it's a known venue (often the target of PFOF queries)
        if venue_score > 80: 
            return venue_norm
        return broker_norm

if __name__ == "__main__":
    test_cases = [
        ("citi", "venue"),      # Should be Citigroup (Venue)
        ("citi", "broker"),     # Should be Citigroup Global Markets Inc. (Broker)
        ("citadel", None),      # Should be Citadel Securities LLC (Venue)
        ("robinhood", None),    # Should be Robinhood Securities, LLC (Broker)
        ("schwab", None),       # Should be Charles Schwab (Broker)
        ("virtu", None),        # Should be Virtu Americas LLC (Venue)
    ]
    
    for entity, ctx in test_cases:
        resolved = resolve_ambiguous_entity(entity, ctx)
        print(f"  => Resolved to: {resolved}\n")
