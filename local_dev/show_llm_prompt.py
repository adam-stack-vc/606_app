"""
Show the exact prompt sent to the LLM for intent extraction
"""
from llm_intent_extractor import _build_schema_context, _build_examples, SYSTEM_PROMPT

# Build the full prompt
schema_context = _build_schema_context()
examples = _build_examples()

system_prompt = SYSTEM_PROMPT.format(
    schema_context=schema_context,
    examples=examples
)

print("=" * 80)
print("SYSTEM PROMPT SENT TO LLM")
print("=" * 80)
print(system_prompt)
print("\n" + "=" * 80)
print("USER MESSAGE EXAMPLE")
print("=" * 80)
print("Who paid Robinhood PFOF in June 2024")
print("\n" + "=" * 80)
print("LLM RESPONSE FORMAT")
print("=" * 80)
print("""Expected JSON response:
{
  "table": "executing_bd_606",
  "operation": "aggregate",
  "metric": "pfof",
  "aggregation": "SUM",
  "dimensions": ["venues"],
  "entities": {"executing_bd": "Robinhood"},
  "period": {"year": 2024, "month": 6},
  "filters": {"data_type": "venue"}
}
""")
