class MockVanna:
    """
    Mock Vanna class to simulate RAG retrieval without needing a live vector DB/OpenAI key.
    In a real implementation, this would use vanna.ai package.
    """
    def __init__(self):
        # Minimal training data simulation
        self.training_data = [
            {
                "question": "PFOF for Robinhood in April 2024",
                "sql": "SELECT SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) + COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) + ...) FROM executing_bd_606 WHERE executing_bd='Robinhood Securities, LLC' AND year=2024 AND month='4' AND data_type='venue'"
            },
             {
                "question": "Total shares by quarter in 2024",
                "sql": "SELECT EXTRACT(QUARTER FROM day) as quarter, SUM(total_shares) FROM monthly_data WHERE EXTRACT(YEAR FROM day)=2024 GROUP BY quarter"
            }
        ]

    def generate_sql(self, question: str) -> str:
        # Simple keyword matching to simulate "retrieval"
        question_lower = question.lower()
        
        # 1. Match PFOF patterns
        if "pfof" in question_lower:
            base_sql = "SELECT SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) + COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) + COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) + COALESCE(netpmtpaidrecvotherordersusd, 0)) as total_pfof_usd FROM executing_bd_606 WHERE data_type='venue'"
            
            if "robinhood" in question_lower:
                base_sql += " AND executing_bd='Robinhood Securities, LLC'"
            
            if "2024" in question_lower:
                 base_sql += " AND year=2024"
                 
            if "april" in question_lower:
                 base_sql += " AND month='4'"
                 
            if "stock group" in question_lower:
                 base_sql = base_sql.replace("SELECT SUM", "SELECT stock_group, SUM").replace("WHERE", "WHERE").replace(";", "") + " GROUP BY stock_group"

            return base_sql

        # 2. Match Volume/Monthly patterns
        if "total shares" in question_lower or "volume" in question_lower:
            if "monthly_data" in question_lower or "market participant" in question_lower or "quarter" in question_lower:
                 base_sql = "SELECT SUM(total_shares) FROM monthly_data"
                 
                 if "2024" in question_lower:
                     base_sql += " WHERE EXTRACT(YEAR FROM day)=2024"
                     
                 if "quarter" in question_lower:
                     base_sql = base_sql.replace("SELECT SUM", "SELECT EXTRACT(QUARTER FROM day) as quarter, SUM") + " GROUP BY quarter"
                     
                 return base_sql

        # 3. Match ATS patterns
        if "ats" in question_lower:
             return "SELECT ats_name, SUM(total_shares) FROM finra_ats WHERE year=2024 GROUP BY ats_name"

        return "SELECT 'Unable to generate SQL via RAG' as error"
