import json
import re
from typing import List, Dict, Any

def load_benchmark(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, 'r') as f:
        return [json.loads(line) for line in f]

def normalize_sql(sql: str) -> str:
    if not sql:
        return ""
    # Remove whitespace
    sql = re.sub(r'\s+', ' ', sql).strip().lower()
    # Remove trailing semicolon
    if sql.endswith(';'):
        sql = sql[:-1]
    return sql

def evaluate_sql(generated_sql: str, expected_shape: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate generated SQL against expected shape.
    Returns a dict with 'passed': bool, 'score': float, 'details': list
    """
    if not generated_sql:
        return {'passed': False, 'score': 0.0, 'details': ["No SQL generated"]}
    
    gen_norm = normalize_sql(generated_sql)
    details = []
    passed_checks = 0
    total_checks = 0
    
    # Check SELECTs
    if 'selects' in expected_shape:
        total_checks += len(expected_shape['selects'])
        for col in expected_shape['selects']:
            if col.lower() in gen_norm:
                passed_checks += 1
            else:
                details.append(f"Missing SELECT: {col}")
    
    # Check GROUP BY
    if expected_shape.get('group_by'):
        total_checks += 1
        # check if group by clause exists and contains columns
        if "group by" in gen_norm:
            all_found = True
            for col in expected_shape['group_by']:
                if col.lower() not in gen_norm:
                    all_found = False
                    details.append(f"Missing GROUP BY col: {col}")
            if all_found:
                passed_checks += 1
        else:
            details.append("Missing GROUP BY clause")
            
    # Check ORDER BY
    if expected_shape.get('order_by'):
        total_checks += 1
        if "order by" in gen_norm and expected_shape['order_by'].lower() in gen_norm:
            passed_checks += 1
        else:
            details.append(f"Missing/Wrong ORDER BY: {expected_shape['order_by']}")
            
    # Check LIMIT
    if expected_shape.get('limit'):
        total_checks += 1
        if f"limit {expected_shape['limit']}" in gen_norm:
            passed_checks += 1
        else:
             details.append(f"Missing/Wrong LIMIT: {expected_shape['limit']}")

    score = passed_checks / total_checks if total_checks > 0 else 1.0
    
    return {
        'passed': score > 0.8, # Flexible threshold
        'score': score,
        'details': details
    }
