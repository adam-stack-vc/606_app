import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.dirname(__file__))

from experiments.benchmark_utils import load_benchmark, evaluate_sql
from models import StructuredIntent
from compiler import compile_sql

def run_neuro_symbolic():
    # Fix path to be absolute or relative to CWD
    benchmark_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../eval/nl_sql_pairs_additional.jsonl'))
    dataset = load_benchmark(benchmark_path)
    results = []
    
    print(f"Running Neuro-Symbolic (Scenario 2) on {len(dataset)} questions...")
    
    for item in dataset:
        question = item['question']
        
        try:
            # SIMULATION: In a real system, an LLM would generate this JSON.
            # Here, we use the 'intent' field from the benchmark as the "Perfect LLM Extraction".
            # This tests the *Compiler's* ability to generate valid SQL from valid Intent.
            intent_dict = item.get('intent')
            if not intent_dict:
                raise ValueError("No ground truth intent found for simulation")
                
            intent_model = StructuredIntent(**intent_dict)
            generated_sql = compile_sql(intent_model)
            
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
    print(f"\nNeuro-Symbolic Results: {passed}/{len(results)} passed ({passed/len(results)*100:.1f}%)")
    
    with open('results_sc2.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_neuro_symbolic()
