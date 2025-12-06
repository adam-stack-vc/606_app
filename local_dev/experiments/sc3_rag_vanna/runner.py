import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.dirname(__file__))

from experiments.benchmark_utils import load_benchmark, evaluate_sql
from vanna_mock import MockVanna

def run_rag_vanna():
    # Fix path to be absolute or relative to CWD
    benchmark_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../eval/nl_sql_pairs_additional.jsonl'))
    dataset = load_benchmark(benchmark_path)
    results = []
    vn = MockVanna()
    
    print(f"Running RAG/Vanna (Scenario 3) on {len(dataset)} questions...")
    
    for item in dataset:
        question = item['question']
        
        try:
            # In this scenario, we rely entirely on "retrieval" to find the best SQL pattern
            # and then "generation" (simulated by simple heuristic filling here)
            generated_sql = vn.generate_sql(question)
            
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
    print(f"\nRAG/Vanna Results: {passed}/{len(results)} passed ({passed/len(results)*100:.1f}%)")
    
    with open('results_sc3.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_rag_vanna()
