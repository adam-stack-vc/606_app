# Multi-Table Query Framework Migration Guide

## 🎯 **Overview**

This guide explains how to migrate from the single-table query framework to the new multi-table architecture that can intelligently route queries across multiple database tables.

## 🏗️ **Architecture Changes**

### **Before (Single Table)**
```
User Query → Single Schema → OpenAI → SQL
```

### **After (Multi-Table)**
```
User Query → Query Classification → Table Selection → Targeted Schema → OpenAI → SQL
```

## 📁 **New File Structure**

```
local_dev/
├── schemas/                          # New: Individual table schemas
│   ├── executing_bd_606_schema.json
│   ├── monthly_data_schema.json
│   ├── finra_ats_schema.json
│   ├── entity_types_schema.json
│   └── venue_mapping_schema.json
├── multi_table_query_framework.py    # New: Multi-table framework
├── ask606_multi_table.py            # New: Enhanced ask function
├── query_framework.py               # Existing: Single-table (backup)
├── ask606.py                        # Existing: Single-table
└── main.py                          # Updated to use multi-table
```

## 🔄 **Migration Steps**

### **Step 1: Test the New Framework**

```bash
# Test the multi-table framework
cd /Users/adamsussman/Documents/606_app/local_dev
python ask606_multi_table.py
```

### **Step 2: Update main.py**

Replace the import in `main.py`:

```python
# OLD
from ask606 import ask

# NEW  
from ask606_multi_table import ask
```

### **Step 3: Verify Functionality**

Test with various query types:

```bash
# Volume queries (uses executing_bd_606)
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is the volume for citadel?"}'

# Market data queries (uses monthly_data)
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Show me monthly trends for 2024"}'

# ATS queries (uses finra_ats)
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What ATS venues are available?"}'
```

## 🧠 **How It Works**

### **1. Query Classification**
The system analyzes the user's question to detect:
- **Volume queries**: "volume", "trades", "shares"
- **PFOF queries**: "payment for order flow", "pfof"
- **Time queries**: "monthly", "quarterly", "2024"
- **Entity queries**: "venue", "broker", "exchange"
- **ATS queries**: "ats", "alternative trading system"

### **2. Table Selection**
Based on classification, relevant tables are selected:
- **Volume + PFOF**: `executing_bd_606`, `venue_mapping`
- **Market Data**: `monthly_data`, `venue_mapping`
- **ATS Data**: `finra_ats`, `venue_mapping`
- **Entity Types**: `entity_types`, `venue_mapping`

### **3. Targeted Schema**
Only relevant table schemas are included in the prompt, reducing:
- Token usage
- Confusion
- Irrelevant suggestions

### **4. Smart Routing**
- **Volume queries**: Route to custom volume estimation function
- **Other queries**: Route to OpenAI with targeted schema

## 📊 **Benefits**

### **Performance**
- ✅ Smaller prompts (only relevant tables)
- ✅ Faster response times
- ✅ Lower token costs

### **Accuracy**
- ✅ More focused SQL generation
- ✅ Better table selection
- ✅ Reduced hallucination

### **Scalability**
- ✅ Easy to add new tables
- ✅ Modular schema management
- ✅ Flexible query routing

## 🔧 **Configuration**

### **Adding New Tables**

1. Create schema file in `schemas/`:
```json
{
  "table_name": "new_table",
  "description": "Description of the table",
  "columns": [...],
  "relationships": [...],
  "query_patterns": [...]
}
```

2. Update `get_relevant_tables()` in `multi_table_query_framework.py`

3. Add classification patterns in `classify_query_enhanced()`

### **Custom Query Handlers**

Add new handlers in `ask606_multi_table.py`:

```python
if query_tags.get("mentions_custom_pattern"):
    sql = generate_custom_query(question, query_tags)
else:
    # Use OpenAI
```

## 🚨 **Rollback Plan**

If issues arise, quickly rollback:

```python
# In main.py, change back to:
from ask606 import ask  # Single-table version
```

The original files remain unchanged as backups.

## 🧪 **Testing Checklist**

- [ ] Volume queries work (citadel, cboe)
- [ ] PFOF queries work (payments, rates)
- [ ] Market data queries work (monthly trends)
- [ ] ATS queries work (alternative trading systems)
- [ ] Venue alias resolution works
- [ ] Time-based filtering works
- [ ] Error handling works
- [ ] Performance is acceptable

## 📈 **Next Steps**

1. **Monitor Performance**: Track response times and accuracy
2. **Add More Tables**: Expand to additional data sources
3. **Custom Handlers**: Add specialized query handlers
4. **Analytics**: Track query patterns and table usage
5. **Optimization**: Fine-tune classification and routing

## 🔍 **Debugging**

Enable debug output:

```python
# In ask606_multi_table.py
print(f"🔍 Query Classification: {query_tags}")
print(f"📊 Relevant Tables: {relevant_tables}")
print(f"🤖 System Prompt Length: {len(system_prompt)}")
```

This will help you understand how queries are being classified and routed.
