
"""
Function 6: Analysis Pipeline
This function will analyze the JSON files against bigrams and ontologies
to extract insights and patterns. Currently commented out as requested.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

# spaCy setup
nlp = spacy.load("en_core_web_sm", disable=["parser", "textcat"])  # Keep NER enabled for entity extraction
STOPWORDS = STOP_WORDS  # spaCy's stopwords

# Configuration variables
WINDOW_SIZE = 3  # Window size for skipgram matching (ignoring stopwords)

# Load lemma overrides from external file
def load_lemma_overrides():
    """Load lemma overrides from lemma_overrides.json file"""
    try:
        with open('/Users/adamsussman/Documents/Form-D/lemma_overrides.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Warning: lemma_overrides.json not found, using default overrides")
        return {
            "securities": "securities", 
            "fixed income": "fixed income", 
            "outsourcing": "outsourcing",
            "screening": "screening",
            "monitoring": "monitoring",
            "equities": "equities",
            "data": "data",
            "data science": "data science",
            "markets": "markets",
            "listed": "listed",
            "crossing": "crossing",
            "e-trading": "e-trading",
            "trade": "trade",
            "futures": "futures",
            "indexing": "indexing",
            "indices": "indices"
        }
    except Exception as e:
        print(f"Error loading lemma_overrides.json: {e}")
        return {}

# Load lemma overrides
LEMMA_OVERRIDES = load_lemma_overrides()

# Load financial bigrams from external file
def load_financial_bigrams():
    """Load financial bigrams from bigram_anchors.json file"""
    try:
        with open('/Users/adamsussman/Documents/ontology_builder/ontology_repo/configs/bigram_anchors.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Warning: bigram_anchors.json not found, using empty list")
        return []
    except Exception as e:
        print(f"Error loading bigram_anchors.json: {e}")
        return []

# Load financial bigrams
FINANCIAL_BIGRAMS = load_financial_bigrams()

# Load value chain data from CSV
def load_value_chain_data():
    """Load value chain data from bigrams_with_value_chain.csv file"""
    import csv
    value_chain_data = {}
    try:
        # Try the first CSV file
        csv_file = '/Users/adamsussman/Documents/ontology_builder/ontology_repo/configs/bigrams_with_value_chain.csv'
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                bigram = row['bigram']
                value_chain_data[bigram] = {
                    'value_chain': row.get('value_chain', ''),
                    'function': row.get('function', ''),
                    'function_id': row.get('function_id', '')
                }
        print(f"Loaded {len(value_chain_data)} bigrams with value chain mappings from {csv_file}")
        return value_chain_data
    except FileNotFoundError:
        print(f"Warning: {csv_file} not found, trying alternative file")
        try:
            # Try the second CSV file
            csv_file2 = '/Users/adamsussman/Documents/ontology_builder/ontology_repo/configs/bigrams_with_value_chain2.csv'
            with open(csv_file2, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    bigram = row['bigram']
                    value_chain_data[bigram] = {
                        'value_chain': row.get('value_chain', ''),
                        'function': row.get('function', ''),
                        'function_id': row.get('function_id', '')
                    }
            print(f"Loaded {len(value_chain_data)} bigrams with value chain mappings from {csv_file2}")
            return value_chain_data
        except FileNotFoundError:
            print("Warning: No value chain CSV files found, using empty dict")
            return {}
    except Exception as e:
        print(f"Error loading value chain CSV: {e}")
        return {}

# Load value chain data
VALUE_CHAIN_DATA = load_value_chain_data()

# spaCy utility functions
def tokenize(text):
    """Use spaCy to tokenize + lemmatize with custom lemma overrides."""
    doc = nlp(text)
    tokens = []
    
    for token in doc:
        if not (token.is_space or token.is_punct):
            # Check for lemma overrides first
            original_text = token.text.lower()
            if original_text in LEMMA_OVERRIDES:
                lemma = LEMMA_OVERRIDES[original_text]
            else:
                lemma = token.lemma_.lower()
            tokens.append(lemma)
    return tokens

def match_skipgram(tokens, anchor_tokens, window=3):
    """True if anchor tokens appear in order within given window, ignoring stopwords."""
    if len(anchor_tokens) < 2:
        return False
    toks = [t for t in tokens if t not in STOPWORDS]
    for i in range(len(toks)):
        if toks[i] == anchor_tokens[0]:
            end = min(len(toks), i + window)
            for j in range(i+1, end):
                if toks[j] == anchor_tokens[1]:
                    return True
    return False

def find_financial_bigrams(text: str) -> Dict[str, int]:
    """
    Find financial bigrams and single words in text using spaCy-based matching
    """
    tokens = tokenize(text)
    found_bigrams = {}
    
    for bigram in FINANCIAL_BIGRAMS:
        bigram_tokens = tokenize(bigram.lower())
        
        # Handle single words (1 token)
        if len(bigram_tokens) == 1:
            word = bigram_tokens[0]
            count = tokens.count(word)
            if count > 0:
                found_bigrams[bigram] = count
        
        # Handle bigrams (2+ tokens) using skipgram matching
        elif len(bigram_tokens) >= 2:
            if match_skipgram(tokens, bigram_tokens, window=WINDOW_SIZE):
                # Count occurrences by checking multiple windows
                count = 0
                toks = [t for t in tokens if t not in STOPWORDS]
                for i in range(len(toks)):
                    if toks[i] == bigram_tokens[0]:
                        end = min(len(toks), i + WINDOW_SIZE)
                        for j in range(i+1, end):
                            if toks[j] == bigram_tokens[1]:
                                count += 1
                                break
                if count > 0:
                    found_bigrams[bigram] = count
    
    return found_bigrams

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract companies and persons mentioned in the text using spaCy NER
    """
    # Process text with spaCy
    doc = nlp(text)
    
    # Extract entities (filtering to PERSON and ORG)
    companies_mentioned = []
    persons_mentioned = []
    
    for ent in doc.ents:
        if ent.label_ == "ORG":
            # Clean up organization names
            clean_name = ent.text.strip()
            if clean_name and len(clean_name) > 1:  # Filter out single characters
                companies_mentioned.append(clean_name)
        elif ent.label_ == "PERSON":
            # Clean up person names
            clean_name = ent.text.strip()
            if clean_name and len(clean_name) > 1:  # Filter out single characters
                persons_mentioned.append(clean_name)
    
    # Remove duplicates while preserving order
    companies_mentioned = list(dict.fromkeys(companies_mentioned))
    persons_mentioned = list(dict.fromkeys(persons_mentioned))
    
    return {
        'companies_mentioned': companies_mentioned,
        'persons_mentioned': persons_mentioned
    }

def analyze_value_chain_coverage(text: str) -> Dict[str, any]:
    """
    Analyze text against value chain data using spaCy-based skipgram matching
    """
    tokens = tokenize(text)
    coverage = {
        'value_chains': defaultdict(list),
        'functions': defaultdict(list),
        'function_ids': defaultdict(list),
        'found_bigrams': []
    }
    
    for bigram, data in VALUE_CHAIN_DATA.items():
        bigram_tokens = tokenize(bigram.lower())
        if match_skipgram(tokens, bigram_tokens, window=WINDOW_SIZE):
            coverage['found_bigrams'].append(bigram)
            
            value_chain = data.get('value_chain', '')
            if value_chain:
                coverage['value_chains'][value_chain].append(bigram)
            
            function = data.get('function', '')
            if function:
                coverage['functions'][function].append(bigram)
            
            function_id = data.get('function_id', '')
            if function_id:
                coverage['function_ids'][function_id].append(bigram)
    
    # Convert defaultdicts to regular dicts
    coverage['value_chains'] = dict(coverage['value_chains'])
   # coverage['functions'] = dict(coverage['functions'])
   # coverage['function_ids'] = dict(coverage['function_ids'])
    
    return coverage

"""
def extract_key_metrics(text: str) -> Dict[str, any]:
    
    Extract key business metrics from text
    
    metrics = {}
    
    # Look for funding amounts
    funding_pattern = r'\$(\d+(?:\.\d+)?)\s*(?:million|billion|m|b)'
    funding_matches = re.findall(funding_pattern, text, re.IGNORECASE)
    if funding_matches:
        metrics['funding_mentioned'] = funding_matches
    
    # Look for employee counts
    employee_pattern = r'(\d+)\s*(?:employees|staff|team members)'
    employee_matches = re.findall(employee_pattern, text, re.IGNORECASE)
    if employee_matches:
        metrics['employee_count_mentioned'] = employee_matches
    
    # Look for customer counts
    customer_pattern = r'(\d+)\s*(?:customers|clients|users)'
    customer_matches = re.findall(customer_pattern, text, re.IGNORECASE)
    if customer_matches:
        metrics['customer_count_mentioned'] = customer_matches
    
    return metrics
"""
def analyze_document_json(json_file_path: str) -> Dict:
    """
    Analyze a single document JSON file and enhance it with analysis
    """
    with open(json_file_path, 'r', encoding='utf-8') as file:
        document = json.load(file)
    
    # Get the text content for analysis
    text_content = document.get('text', '')
    
    if not text_content:
        print(f"Warning: No text content found in {json_file_path}")
        return document
    
    # Perform analysis
    entities = extract_entities(text_content)
    value_chain_coverage = analyze_value_chain_coverage(text_content)
    
    # Enhance the document with analysis results
    document['companies_mentioned'] = entities['companies_mentioned']
    document['persons_mentioned'] = entities['persons_mentioned']
    document['value_chains'] = list(value_chain_coverage.get('value_chains', {}).keys())
    
    # Add analysis metadata (optional)
    document['analysis_metadata'] = {
        'value_chain_coverage': value_chain_coverage,
        'content_length': len(text_content),
        'word_count': len(text_content.split())
    }
    
    return document

def analyze_all_documents(json_dir: str, output_dir: str) -> List[Dict]:
    """
    Analyze all document JSON files and enhance them with analysis
    
    Args:
        json_dir: Directory containing JSON files
        output_dir: Directory to save enhanced documents
        
    Returns:
        List of enhanced documents
    """
    json_path = Path(json_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Looking for JSON files in: {json_path}")
    print(f"📁 Output directory: {output_path}")
    
    # Debug: List all files in the directory
    all_files = list(json_path.glob('*'))
    print(f"📄 Found {len(all_files)} files in directory:")
    for file in all_files:
        print(f"  - {file.name} ({'file' if file.is_file() else 'directory'})")
    
    # Look specifically for .json files
    json_files = list(json_path.glob('*.json'))
    print(f"📄 Found {len(json_files)} .json files:")
    for json_file in json_files:
        print(f"  - {json_file.name}")
    
    enhanced_documents = []
    
    for json_file in json_files:
        print(f"Analyzing {json_file.name}...")
        
        # Analyze and enhance document
        enhanced_document = analyze_document_json(str(json_file))
        enhanced_documents.append(enhanced_document)
        
        # Save enhanced document (overwrite original)
        output_file = output_path / json_file.name
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(enhanced_document, file, indent=2, ensure_ascii=False)
        
        print(f"Enhanced document saved: {json_file.name}")
    
    print(f"Analysis complete. Enhanced {len(enhanced_documents)} documents.")
    return enhanced_documents

def create_aggregate_analysis(analyses: List[Dict], output_file: str):
    """
    Create aggregate analysis across all companies
    """
    # Aggregate financial bigrams
    all_bigrams = Counter()
    for analysis in analyses:
        for bigram, count in analysis['financial_bigrams'].items():
            all_bigrams[bigram] += count
    
    # Aggregate value chain coverage
    value_chain_stats = defaultdict(int)
    #function_stats = defaultdict(int)
    #function_id_stats = defaultdict(int)
    
    for analysis in analyses:
        value_chain_data = analysis.get('value_chain_coverage', {})
        
        # Count value chains
        for value_chain, bigrams in value_chain_data.get('value_chains', {}).items():
            value_chain_stats[value_chain] += len(bigrams)
        
        # Count functions
        #for function, bigrams in value_chain_data.get('functions', {}).items():
         #   function_stats[function] += len(bigrams)
        
        # Count function IDs
        #for function_id, bigrams in value_chain_data.get('function_ids', {}).items():
        #    function_id_stats[function_id] += len(bigrams)
    
    # Aggregate metrics
    total_companies = len(analyses)
    total_sections = sum(a['content_stats']['total_sections'] for a in analyses)
    total_content_length = sum(a['content_stats']['total_content_length'] for a in analyses)
    
    aggregate = {
        'summary': {
            'total_companies': total_companies,
            'total_sections': total_sections,
            'total_content_length': total_content_length,
            'average_sections_per_company': total_sections / total_companies if total_companies > 0 else 0
        },
        'top_financial_bigrams': dict(all_bigrams.most_common(20)),
        'value_chain_coverage_stats': {
            'value_chains': dict(value_chain_stats),
            #'functions': dict(function_stats),
            #'function_ids': dict(function_id_stats)
        },
        'company_analyses': analyses
    }
    
    # Save aggregate analysis
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(aggregate, file, indent=2, ensure_ascii=False)
    
    print(f"Aggregate analysis saved to {output_file}")

# ============================================================================
# COMMENTED OUT SECTION - ANALYSIS PIPELINE
# ============================================================================
# This section contains the main pipeline function that would be called
# to analyze all JSON files against bigrams and ontologies. It's commented out as requested.

"""
def run_analysis_pipeline():
    # Main pipeline function for analysis
    json_dir = "/Users/adamsussman/Documents/Form-D/company_jsons"
    analysis_output_dir = "/Users/adamsussman/Documents/Form-D/company_analyses"
    aggregate_output_file = "/Users/adamsussman/Documents/Form-D/aggregate_analysis.json"
    
    print("Starting analysis pipeline...")
    
    # Analyze all companies
    analyses = analyze_all_companies(json_dir, analysis_output_dir)
    
    # Create aggregate analysis
    create_aggregate_analysis(analyses, aggregate_output_file)
    
    # Print summary
    print(f"Analysis complete:")
    print(f"Companies analyzed: {len(analyses)}")
    print(f"Individual analyses: {analysis_output_dir}")
    print(f"Aggregate analysis: {aggregate_output_file}")
    
    return analyses

# Uncomment the line below to run the analysis pipeline
# run_analysis_pipeline()
"""

# Example usage (commented out since this should be a function, not executable)
# if __name__ == "__main__":
#     json_dir = "/Users/adamsussman/Documents/Form-D/company_jsons"
#     analysis_output_dir = "/Users/adamsussman/Documents/Form-D/company_analyses"
#     
#     analyses = analyze_all_companies(json_dir, analysis_output_dir)
#     create_aggregate_analysis(analyses, "/Users/adamsussman/Documents/Form-D/aggregate_analysis.json")
