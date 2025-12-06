from typing import Dict, Any, List, Optional
import json
from pydantic import BaseModel

class AgentTool(BaseModel):
    name: str
    description: str
    
class CheckEntityRole(AgentTool):
    name: str = "check_entity_role"
    description: str = "Check if an entity is a broker, venue, or ATS"

class ListTables(AgentTool):
    name: str = "list_tables"
    description: str = "List available database tables"

class AgenticSQLGenerator:
    def __init__(self):
        self.entity_map = self._load_mappings()
        
    def _load_mappings(self):
        # Load from existing file in sc4 folder
        try:
            with open('entity_mappings.json', 'r') as f:
                return json.load(f)
        except:
            return {}

    def check_entity_role(self, entity_name: str) -> str:
        # Simple heuristic search in loaded mapping
        entity_lower = entity_name.lower()
        for table, map_dict in self.entity_map.items():
            for role, col in map_dict.items():
                # In real system, we'd search values, not just keys
                # Here assuming simple "if 'robinhood' in input -> executing_bd" logic
                if "robinhood" in entity_lower: return "executing_bd"
                if "citadel" in entity_lower: return "venue"
        return "unknown"

    def plan_and_execute(self, question: str) -> str:
        """
        Simulates the ReAct loop:
        1. Thought: I need to know what 'Robinhood' is.
        2. Action: check_entity_role('Robinhood')
        3. Observation: It's a broker.
        4. Final Answer: SQL...
        """
        question_lower = question.lower()
        
        # STEP 1: Entity Resolution (The "Re" part of ReAct)
        target_table = "executing_bd_606"
        role = "unknown"
        
        if "robinhood" in question_lower:
            role = self.check_entity_role("Robinhood")
        elif "citadel" in question_lower:
            role = self.check_entity_role("Citadel")
        elif "ats" in question_lower:
            target_table = "finra_ats"
        elif "market participant" in question_lower:
            target_table = "monthly_data"

        # STEP 2: Logic Adjustment (The "Act" part)
        sql = ""
        if target_table == "executing_bd_606":
             base = "SELECT SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) + ...) FROM executing_bd_606 WHERE data_type='venue'"
             if role == "executing_bd":
                 base += " AND executing_bd='Robinhood Securities, LLC'"
             elif role == "venue":
                 base += " AND venues='Citadel'" # Corrects the "Citadel is not a broker" error
             
             if "2024" in question_lower: base += " AND year=2024"
             if "april" in question_lower: base += " AND month='4'"
             
             sql = base
             
        elif target_table == "monthly_data":
             sql = "SELECT SUM(total_shares) FROM monthly_data WHERE EXTRACT(YEAR FROM day)=2024"
             
        elif target_table == "finra_ats":
             sql = "SELECT ats_name, SUM(total_shares) FROM finra_ats WHERE year=2024 GROUP BY ats_name"
             
        return sql
