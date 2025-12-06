from __future__ import annotations

"""
planner.py
Maps natural language queries to SQL using a Neuro-Symbolic approach.
Uses LLM for intent extraction (StructuredIntent) and a deterministic Compiler for SQL generation.
"""

import os
from typing import Dict, Optional

# Import Neuro-Symbolic components
from query_models import StructuredIntent
from query_compiler import compile_sql
from llm_intent_extractor import extract_intent_with_llm

def plan_single_sql(user_input: str, tags: Dict) -> Optional[str]:
    """
    Plan a single-shot SQL query using the Neuro-Symbolic engine.
    
    1. Uses LLM to extract a StructuredIntent (Pydantic model).
    2. Uses the Compiler to generate valid SQL from that intent.
    
    Falls back to legacy manual logic if intent extraction fails (though legacy logic is deprecated).
    """
    
    # Step 1: Intent Extraction
    try:
        # We can pass the raw user input directly to the extractor
        # The extractor uses the same capabilities as before but now returns a StructuredIntent
        structured_intent = extract_intent_with_llm(user_input)
        
        if structured_intent:
            print(f"🧠 Structured Intent Extracted: {structured_intent.operation} on {structured_intent.metric}")
            
            # Step 2: Compilation
            sql = compile_sql(structured_intent)
            
            if sql and not sql.startswith("--"):
                print(f"✅ Compiled SQL: {sql[:50]}...")
                return sql
            else:
                print("⚠️ Compilation returned comment or empty string")
                
    except Exception as e:
        print(f"❌ Planner Error: {e}")
        # In a real production system, we might want a fallback here, 
        # but for this refactor we rely on the robust new engine.
        pass
        
    return None
