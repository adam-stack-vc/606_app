#!/usr/bin/env python3
"""
Send Markdown files to OpenAI using the Responses API with structured outputs.
Processes all files in batch and outputs a single JSON file with all results.
Uses function calling to get structured JSON responses with strict/flexible processing modes.
"""

import os
import time
import argparse
from typing import Dict, List, Optional
import logging
from pathlib import Path
import re
import io
import json
import copy

try:
    import openai
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Missing packages. Install with: pip install openai python-dotenv")
    import sys
    sys.exit(1)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURATION - API key should be in .env file or provided via command line 

class MarkdownToAssistantMD:
    def __init__(self, api_key: str = None, input_dir: str = None, output_dir: str = None, debug: bool = False, 
                 model: str = "gpt-4o", temperature: float = 0.1):
        """Initialize the markdown to assistant processor."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided via parameter or OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        
        # Input and output directories
        self.input_dir = Path(input_dir) if input_dir else Path("/Users/adamsussman/Documents/606_app/markdowns/")
        
        # Generate output directory based on input directory structure
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # Fallback to default
            self.output_dir = Path("/Users/adamsussman/Documents/606_app/output")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Debug mode - save raw responses to files
        self.debug = debug
        if self.debug:
            self.debug_dir = self.output_dir / "debug_responses"
            self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up configs directory for schema and prompt files
        self.configs_dir = Path("configs")
        if not self.configs_dir.exists():
            self.configs_dir.mkdir(exist_ok=True)

    def load_schema(self, filename: str = "pfof_response_schema.json") -> Dict:
        """Load JSON schema."""
        schema_path = self.configs_dir / filename
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Schema file {filename} not found, using default schema")
            return self._get_default_schema()
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            return self._get_default_schema()

    def _get_default_schema(self) -> Dict:
        """Get default schema for structured response."""
        return {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "date": {"type": "string"},
                "author": {"type": "string"},
                "author_role": {"type": "string"},
                "company": {"type": "string"},
                "company_role": {"type": "string"},
                "date": {"type": "string"},
                "pfof_stance": {"type": "string"},
                "pfof_evidence": {"type": "string"},
            },
            "required": ["filename", "date", "author", "author_role", "company", "company_role", "pfof_stance", "pfof_evidence"]
        }

    def load_prompt(self, filename: str = "prompt_improved.txt") -> str:
        """Load prompt file."""
        prompt_path = self.configs_dir / filename
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning(f"Prompt file {filename} not found, using default prompt")
            return self._get_default_prompt()
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default prompt for analysis."""
        return """Analyze the provided markdown content and extract the following information:

1. **filename**: The name of the file being analyzed
2. **date**: The date of the document
3. **author**: The author of the document
4. **author_role**: The role of the author
5. **company**: The company or organization
6. **company_role**: The role of the company in the industry
7. **date**: The date of the document
8. **pfof stance **: documents has a positive, neutral, or negative stance on PFOF
9. **pfof evidence**: evidence for the pfof stance


Please provide a structured response with all the requested information."""

    def load_control_vocabulary(self, filename: str = "pfof_ont.json") -> Dict:
        """Load controlled vocabulary from ontology file."""
        vocab_path = self.configs_dir / filename
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Vocabulary file {filename} not found, using empty vocabulary")
            return {}
        except Exception as e:
            logger.error(f"Error loading vocabulary: {e}")
            return {}

    def apply_strict_constraints(self, schema: Dict, vocab: Dict) -> Dict:
        """
        Return a copy of schema with enum constraints applied based on the controlled vocabulary.
        Only used in method == "strict". If vocab is empty, returns the original schema.
        """
        if not vocab:
            return schema

        modified = copy.deepcopy(schema)

        # Extract function IDs from the ontology
        function_ids = []
        if "functions" in vocab:
            for func in vocab["functions"]:
                if isinstance(func, dict) and "function_id" in func:
                    function_ids.append(func["function_id"])

        # Extract entity lists
        persons_mentioned = vocab.get("persons_mentioned", [])
        companies_mentioned = vocab.get("companies_mentioned", [])
        cryptos_mentioned = vocab.get("cryptos_mentioned", [])

        def add_enum_constraints(props: Dict, path: str = "") -> None:
            """Recursively add enum constraints to matching fields."""
            for field, prop in props.items():
                field_lc = field.lower()
                
                # Strings
                if prop.get("type") == "string":
                    if "function_id" in field_lc and function_ids:
                        prop["enum"] = function_ids
                    elif "crypto_persona" in field_lc:
                        prop["enum"] = ["TradFi", "Crypto Native", "NA"]
                    elif "pfof_stance" in field_lc:
                        prop["enum"] = ["positive", "neutral, negative"]
                    elif "guiding_principles" in field_lc:
                        prop["enum"] = ["investor protection", "capital formation", "fair and orderly markets", 
                                      "investor choice", "technology modernization", "lack of trust with intermediaries"]

                # Arrays
                elif prop.get("type") == "array" and "items" in prop:
                    items = prop["items"]
                    if items.get("type") == "string":
                        if "function_id" in field_lc and function_ids:
                            items["enum"] = function_ids
                        elif "persons" in field_lc and persons_mentioned:
                            items["enum"] = persons_mentioned
                        elif "companies" in field_lc and companies_mentioned:
                            items["enum"] = companies_mentioned
                        elif "cryptos" in field_lc and cryptos_mentioned:
                            items["enum"] = cryptos_mentioned
                        elif "guiding_principles" in field_lc:
                            items["enum"] = ["investor protection", "capital formation", "fair and orderly markets", 
                                           "investor choice", "technology modernization", "lack of trust with intermediaries"]
                    elif items.get("type") == "object" and "properties" in items:
                        add_enum_constraints(items["properties"], f"{path}.{field}")

                # Objects
                elif prop.get("type") == "object" and "properties" in prop:
                    add_enum_constraints(prop["properties"], f"{path}.{field}")

        # Apply constraints to the schema
        if "properties" in modified:
            add_enum_constraints(modified["properties"])

        return modified

    def enhance_prompt_with_vocabulary(self, base_prompt: str, vocab: Dict, method: str = "flexible") -> str:
        """Enhance prompt with controlled vocabulary information."""
        if not vocab:
            return base_prompt

        appendix_lines = []

        # Add function IDs
        if "functions" in vocab:
            function_ids = [func.get("function_id", "") for func in vocab["functions"] 
                          if isinstance(func, dict) and "function_id" in func]
            if function_ids:
                appendix_lines.append(f"- function_id options: {', '.join(function_ids)}")

        # Add entity lists
        if vocab.get("persons_mentioned"):
            appendix_lines.append(f"- persons_mentioned options: {', '.join(vocab['persons_mentioned'])}")
        if vocab.get("companies_mentioned"):
            appendix_lines.append(f"- companies_mentioned options: {', '.join(vocab['companies_mentioned'])}")
        if vocab.get("cryptos_mentioned"):
            appendix_lines.append(f"- cryptos_mentioned options: {', '.join(vocab['cryptos_mentioned'])}")

        # Add method-specific instructions
        if method == "strict":
            appendix_lines.append(
                "- STRICT mode: prefer values from the lists above; avoid inventing new labels unless unavoidable."
            )

        return base_prompt.strip() + "\n" + "\n".join(appendix_lines) + "\n"

    def verify_client(self) -> bool:
        """Verify that the OpenAI client is working."""
        try:
            # Test the client with a simple request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.info(f"✅ OpenAI client verified with model: {self.model}")
            return True
        except Exception as e:
            logger.error(f"❌ Error verifying OpenAI client: {e}")
            return False

    def read_markdown_file(self, filepath: Path) -> str:
        """Read markdown file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            raise

    def parse_structured_response(self, response_data: Dict, filename: str) -> Dict:
        """Parse structured JSON response from OpenAI and extract data."""
        result = {
            'filename': filename,
            'author': '',
            'company': '',
            'date': '',
            'function_ids': '',
            'persons': '',
            'cryptos': '',
            'companies': '',
            'crypto_persona': '',
            'reg_summary': '',
            'disclosure_summary': '',
            'is_valid': False,
            'errors': []
        }
        
        logger.info(f"=== PARSING STRUCTURED RESPONSE FOR {filename} ===")
        
        try:
            logger.info(f"Response data: {response_data}")
            
            # Validate that we have the expected fields
            expected_fields = ['filename', 'author', 'company', 'date', 'function_ids', 'persons', 'cryptos', 'companies', 'crypto_persona', 'reg_summary', 'disclosure_summary']
            missing_fields = [field for field in expected_fields if field not in response_data]
            if missing_fields:
                result['errors'].append(f"Missing fields: {', '.join(missing_fields)}")
                logger.warning(f"Missing fields for {filename}: {missing_fields}")
                # Don't return early, try to extract what we can
            
            # Map response data to our result structure
            result['filename'] = response_data.get('filename', filename)
            result['author'] = response_data.get('author', '')
            result['company'] = response_data.get('company', '')
            result['date'] = response_data.get('date', '')
            result['function_ids'] = response_data.get('function_ids', '')
            result['persons'] = response_data.get('persons', '')
            result['cryptos'] = response_data.get('cryptos', '')
            result['companies'] = response_data.get('companies', '')
            result['crypto_persona'] = response_data.get('crypto_persona', '')
            result['reg_summary'] = response_data.get('reg_summary', '')
            result['disclosure_summary'] = response_data.get('disclosure_summary', '')
            
            # Consider it valid if we have at least some key fields
            if result['author'] or result['company'] or result['reg_summary']:
                result['is_valid'] = True
            
            logger.info(f"Successfully parsed structured response for {filename}: {result}")
            
        except Exception as e:
            result['errors'].append(f"Error parsing structured response: {str(e)}")
            logger.warning(f"Failed to parse structured response for {filename}: {e}")
        
        return result
    
        
 
    def process_markdown_file(self, filepath: Path, schema: Dict = None, prompt: str = None) -> Dict:
        """Process a single markdown file using the Responses API."""
        logger.info(f"Processing file: {filepath}")
        
        # Read the markdown file
        content = self.read_markdown_file(filepath)
        
        # Load schema and prompt if not provided
        if schema is None:
            schema = self.load_schema()
        if prompt is None:
            prompt = self.load_prompt()
        
        try:
            # Create tool definition
            tool = {
                "type": "function",
                "function": {
                    "name": "structured_response",
                    "description": "Generate structured response according to schema",
                    "parameters": schema,
                },
            }

            # Build full prompt
            full_prompt = f"""{prompt}

Analyze this markdown content:

```markdown
{content}
```

Use the structured_response function to provide your analysis."""

            # Call API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analyze content and respond using the provided function."},
                    {"role": "user", "content": full_prompt},
                ],
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": "structured_response"}},
                temperature=self.temperature,
            )

            # Extract result
            tool_call = response.choices[0].message.tool_calls[0]
            response_data = json.loads(tool_call.function.arguments)
            
            # DEBUG: Log the raw response data
            logger.info(f"=== RAW RESPONSE FOR {filepath.name} ===")
            logger.info(f"Response data: {response_data}")
            logger.info(f"=== END RAW RESPONSE ===")
            
            # Save raw response to debug file if debug mode is enabled
            if self.debug:
                debug_file = self.debug_dir / f"{filepath.stem}_response.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== RAW RESPONSE FOR {filepath.name} ===\n")
                    f.write(f"Response data: {json.dumps(response_data, indent=2)}\n")
                    f.write(f"=== END RAW RESPONSE ===\n")
                    
                    # Also save the original markdown content for reference
                    f.write(f"\n=== ORIGINAL MARKDOWN CONTENT ===\n")
                    f.write(content)
                    f.write(f"\n=== END ORIGINAL CONTENT ===\n")
                    
                logger.info(f"Debug response saved to: {debug_file}")
            
            # Parse structured response
            parsed_data = self.parse_structured_response(response_data, filepath.name)
            
            return {
                'original_file': str(filepath),
                'response': response_data,
                'parsed_data': parsed_data,
                'status': 'success' if parsed_data['is_valid'] else 'validation_failed'
            }
            
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return {
                'original_file': str(filepath),
                'error': str(e),
                'status': 'failed'
            }

    def process_all_markdown_files(self, schema_filename: str = "response_schema.json", 
                                  prompt_filename: str = "prompt_improved.txt", 
                                  method: str = "flexible", ontology_filename: str = "sec_crypto_ont.json") -> List[Dict]:
        """Process all markdown files in the input directory."""
        results = []
        
        # Load resources
        vocab = self.load_control_vocabulary(ontology_filename)
        base_schema = self.load_schema(schema_filename)
        base_prompt = self.load_prompt(prompt_filename)
        
        # Apply method-specific modifications
        prompt = self.enhance_prompt_with_vocabulary(base_prompt, vocab, method)
        schema = self.apply_strict_constraints(base_schema, vocab) if method == "strict" else base_schema
        
        # Find all markdown files
        markdown_files = list(self.input_dir.glob("*.md"))
        
        if not markdown_files:
            logger.warning(f"No markdown files found in {self.input_dir}")
            return results
        
        logger.info(f"Found {len(markdown_files)} markdown files to process")
        
        for i, filepath in enumerate(markdown_files, 1):
            logger.info(f"Processing file {i}/{len(markdown_files)}: {filepath.name}")
            
            try:
                # Process the file
                result = self.process_markdown_file(filepath, schema, prompt)
                results.append(result)
                
                # Small delay between requests to be respectful to the API
                if i < len(markdown_files):
                    logger.info("Waiting 2 seconds before next request...")
                    time.sleep(15)
                    
            except Exception as e:
                logger.error(f"Failed to process {filepath}: {e}")
                results.append({
                    'original_file': str(filepath),
                    'error': str(e),
                    'status': 'failed'
                })
        
        return results

    def save_json_results(self, results: List[Dict]) -> Path:
        """Save all successful results to a single JSON file."""
        json_path = self.output_dir / "assistant_responses.json"
        
        # Include results that have response data
        successful_results = [r for r in results if r.get('response') is not None]
        
        logger.info(f"Total results: {len(results)}")
        logger.info(f"Results with response data: {len(successful_results)}")
        
        # Create structured output with all results
        output_data = {
            "processing_summary": {
                "total_files": len(results),
                "successful": len([r for r in results if r['status'] == 'success']),
                "validation_failed": len([r for r in results if r['status'] == 'validation_failed']),
                "failed": len([r for r in results if r['status'] == 'failed'])
            },
            "results": results
        }
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(output_data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON results saved to: {json_path}")
        logger.info(f"Successfully processed {len(successful_results)} files to JSON")
        return json_path

    def generate_summary_report(self, results: List[Dict]) -> Path:
        """Generate a summary report of all processing results."""
        summary_path = self.output_dir / "processing_summary.md"
        
        successful = [r for r in results if r['status'] == 'success']
        validation_failed = [r for r in results if r['status'] == 'validation_failed']
        failed = [r for r in results if r['status'] == 'failed']
        
        summary = f"# Processing Summary\n\n"
        summary += f"**Processing Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        summary += f"**Total Files:** {len(results)}\n\n"
        summary += f"**Successful:** {len(successful)} ✅\n\n"
        summary += f"**Validation Failed:** {len(validation_failed)} ⚠️\n\n"
        summary += f"**Failed:** {len(failed)} ❌\n\n"
        
        if validation_failed:
            summary += f"## Validation Errors\n\n"
            for result in validation_failed:
                parsed_data = result.get('parsed_data', {})
                summary += f"### {Path(result['original_file']).name}\n\n"
                for error in parsed_data.get('errors', []):
                    summary += f"- {error}\n"
                summary += f"\n"
        
        summary += f"## Results\n\n"
        for result in results:
            if result['status'] == 'success':
                status_icon = "✅"
            elif result['status'] == 'validation_failed':
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            
            summary += f"- {status_icon} {Path(result['original_file']).name}\n"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Summary report saved to: {summary_path}")
        return summary_path


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Process markdown files using OpenAI Responses API")
    parser.add_argument("--input_dir", required=True, help="Input directory containing markdown files")
    parser.add_argument("--output_dir", help="Output directory for processed files (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode - save raw responses to files")
    parser.add_argument("--schema", default="response_schema.json", help="Schema filename in configs/")
    parser.add_argument("--prompt", default="prompt_improved.txt", help="Prompt filename in configs/")
    parser.add_argument("--method", choices=["strict", "flexible"], default="flexible", 
                       help="strict=enforce vocabulary, flexible=allow new categories")
    parser.add_argument("--ontology", default="sec_crypto_ont.json", help="Ontology filename for controlled vocabulary")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model")
    parser.add_argument("--temperature", type=float, default=0.1, help="Response temperature")
    parser.add_argument("--api-key", help="OpenAI API key (or use OPENAI_API_KEY env var)")
    args = parser.parse_args()
    
    # Check for required credentials
    api_key = os.getenv('OPENAI_API_KEY') or args.api_key
    
    # If not found in environment, prompt user for input
    if not api_key:
        print("OpenAI API key not found in environment variables.")
        api_key = input("Please enter your OpenAI API key: ").strip()
        if not api_key:
            print("ERROR: API key is required to proceed.")
            return
    
    # Initialize processor
    processor = MarkdownToAssistantMD(
        api_key=api_key, 
        input_dir=args.input_dir, 
        output_dir=args.output_dir, 
        debug=args.debug,
        model=args.model,
        temperature=args.temperature
    )
    
    # Verify client works before proceeding
    print("Verifying OpenAI client...")
    if not processor.verify_client():
        print("❌ OpenAI client verification failed. Cannot proceed.")
        print("\nTroubleshooting tips:")
        print("1. Check your API key")
        print("2. Verify your API key has access to the specified model")
        print("3. Check your internet connection")
        return
    
    print("Starting markdown processing with Responses API...")
    print(f"Input directory: {processor.input_dir}")
    print(f"Output directory: {processor.output_dir}")
    print(f"Model: {processor.model}")
    print(f"Schema: {args.schema}")
    print(f"Prompt: {args.prompt}")
    print(f"Method: {args.method}")
    print(f"Ontology: {args.ontology}")
    if args.debug:
        print(f"Debug mode enabled - raw responses will be saved to: {processor.debug_dir}")
    
    # Process all files
    results = processor.process_all_markdown_files(args.schema, args.prompt, args.method, args.ontology)
    
    # Save JSON results
    json_path = processor.save_json_results(results)
    
    # Generate summary
    summary_path = processor.generate_summary_report(results)
    
    # Print results
    successful = [r for r in results if r['status'] == 'success']
    validation_failed = [r for r in results if r['status'] == 'validation_failed']
    failed = [r for r in results if r['status'] == 'failed']
    
    print(f"\n✅ Processing completed!")
    print(f"Processed {len(results)} files")
    print(f"Successful: {len(successful)} ✅")
    print(f"Validation Failed: {len(validation_failed)} ⚠️")
    print(f"Failed: {len(failed)} ❌")
    print(f"Output directory: {processor.output_dir}")
    print(f"JSON results: {json_path}")
    print(f"Summary report: {summary_path}")
    
    # Show individual results
    print(f"\nIndividual results:")
    for result in results:
        if result['status'] == 'success':
            status_icon = "✅"
        elif result['status'] == 'validation_failed':
            status_icon = "⚠️"
        else:
            status_icon = "❌"
        
        print(f"  {status_icon} {Path(result['original_file']).name}")


if __name__ == "__main__":
    main()
