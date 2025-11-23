# 606 NL2SQL Integration Guide  
### Hybrid Pipeline: QueryIntent → LangChain SQL Hints → Deterministic SQL Builder  
### For Cursor + GPT-5.1 Development Workflow

---

## 🎯 Overview

This guide describes the recommended architecture for integrating:

- **Rule-based classification**
- **Context disambiguation (direction, entities, metrics)**
- **Time period extraction**
- **QueryIntent abstraction**
- **LangChain SQLDatabaseChain (safe, restricted use)**
- **Deterministic SQL builder**
- **Postgres execution**

for the Market Structure / 606 app.

The goal is to combine **domain control** with **LLM semantic reasoning** *without sacrificing safety or correctness*.

---

# 🧩 System Architecture

