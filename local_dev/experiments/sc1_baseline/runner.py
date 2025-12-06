import sys
import os
import json
# Add parent dir to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.dirname(__file__))

from experiments.benchmark_utils import load_benchmark, evaluate_sql
from planner import plan_single_sql
from capability_registry import get_capabilities # Ensure this is loaded

def run_baseline():
    # Fix path to be absolute or relative to CWD
    benchmark_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../eval/nl_sql_pairs_additional.jsonl'))
    dataset = load_benchmark(benchmark_path)
    results = []
    
    print(f"Running Baseline (Scenario 1) on {len(dataset)} questions...")
    
    for item in dataset:
        question = item['question']
        print(f" Processing: {question[:50]}...")
        
        # Simulate tag extraction (basic keywords) used by planner.py normally
        # But here we might need to rely on planner's internal extraction or just pass raw dict
        # planner.plan_single_sql expects tags dict. 
        # The planner.py in this folder has the manual tagging logic inside `plan_single_sql` 
        # if we pass minimal tags.
        
        try:
            # Minimal tags to trigger planner's internal logic
            tags = {"_text": question}
            
            generated_sql = plan_single_sql(question, tags)
            
            eval_result = evaluate_sql(generated_sql, item.get('expected_sql_shape', {}))
            
            results.append({
                'id': item.get('id'),
                'question': question,
                'generated_sql': generated_sql,
                'passed': eval_result['passed'],
                'score': eval_result['score'],
                'details': eval_result['details']
            })
        except Exception as e:
             results.append({
                'id': item.get('id'),
                'question': question,
                'generated_sql': None,
                'passed': False,
                'score': 0.0,
                'details': [str(e)]
            })

    # Output summary
    passed = sum(1 for r in results if r['passed'])
    print(f"\nBaseline Results: {passed}/{len(results)} passed ({passed/len(results)*100:.1f}%)")
    
    with open('results_sc1.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_baseline()
