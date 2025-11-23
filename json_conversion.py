"""
JSON Schema Conversion for HTML Content Extractor
This function converts .txt files from the HTML content extractor into structured JSON schema.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

def extract_txt_metadata(txt_content: str) -> Dict[str, str]:
    """
    Extract metadata from HTML content extractor .txt files
    """
    lines = txt_content.split('\n')
    metadata = {}
    
    # Parse CSV metadata section
    in_csv_metadata = False
    in_extracted_metadata = False
    in_body = False
    
    for line in lines:
        line = line.strip()
        
        if line == "CSV METADATA:":
            in_csv_metadata = True
            continue
        elif line == "EXTRACTED METADATA:":
            in_csv_metadata = False
            in_extracted_metadata = True
            continue
        elif line == "BODY:":
            in_extracted_metadata = False
            in_body = True
            continue
        elif line.startswith("=") or line.startswith("-"):
            continue
        
        # Parse CSV metadata
        if in_csv_metadata and ":" in line:
            try:
                if line.startswith("URL:"):
                    metadata['url'] = line.split("URL: ", 1)[1]
                elif line.startswith("Title:"):
                    metadata['csv_title'] = line.split("Title: ", 1)[1]
                elif line.startswith("Date:"):
                    metadata['date'] = line.split("Date: ", 1)[1]
                elif line.startswith("Sentiment:"):
                    metadata['sentiment'] = line.split("Sentiment: ", 1)[1]
            except IndexError:
                print(f"⚠️  Warning: Could not parse line: {line}")
                continue
        
        # Parse extracted metadata (we're not using these fields anymore, but keeping for compatibility)
        elif in_extracted_metadata and ":" in line:
            try:
                if line.startswith("Description:"):
                    metadata['description'] = line.split("Description: ", 1)[1]
                elif line.startswith("Keywords:"):
                    metadata['keywords'] = line.split("Keywords: ", 1)[1]
                elif line.startswith("Canonical Link:"):
                    metadata['canonical_link'] = line.split("Canonical Link: ", 1)[1]
                elif line.startswith("Domain:"):
                    metadata['domain'] = line.split("Domain: ", 1)[1]
                elif line.startswith("Publish Date:"):
                    metadata['publish_date'] = line.split("Publish Date: ", 1)[1]
                elif line.startswith("Authors:"):
                    metadata['authors'] = line.split("Authors: ", 1)[1]
                elif line.startswith("Tags:"):
                    metadata['tags'] = line.split("Tags: ", 1)[1]
            except IndexError:
                print(f"⚠️  Warning: Could not parse line: {line}")
                continue
    
    return metadata

def extract_txt_body(txt_content: str) -> str:
    """
    Extract body content from HTML content extractor .txt files
    """
    lines = txt_content.split('\n')
    body_lines = []
    in_body = False
    
    for line in lines:
        if line.strip() == "BODY:":
            in_body = True
            continue
        elif in_body:
            body_lines.append(line)
    
    # Join lines and clean up the text
    body_text = '\n'.join(body_lines).strip()
    
    # Clean up the text: remove excessive whitespace and normalize line breaks
    import re
    
    # Replace multiple consecutive newlines with single newlines
    body_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', body_text)
    
    # Remove leading/trailing whitespace from each line
    lines = body_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    # Join back with single newlines
    cleaned_body = '\n'.join(cleaned_lines)
    
    return cleaned_body

def extract_txt_title(txt_content: str) -> str:
    """
    Extract the extracted title from HTML content extractor .txt files
    """
    lines = txt_content.split('\n')
    
    for line in lines:
        if line.startswith("EXTRACTED TITLE:"):
            return line.split("EXTRACTED TITLE: ", 1)[1]
    
    return ""

def convert_txt_to_json(txt_file_path: str) -> Dict:
    """
    Convert a single .txt file from HTML content extractor to JSON schema
    """
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if file has content
        if not content.strip():
            print(f"⚠️  Warning: Empty file {txt_file_path}")
            return create_empty_json_data(txt_file_path)
        
        # Extract metadata and content
        metadata = extract_txt_metadata(content)
        body = extract_txt_body(content)
        extracted_title = extract_txt_title(content)
        
        # Validate that we have essential data
        if not body.strip():
            print(f"⚠️  Warning: No body content found in {txt_file_path}")
            body = "No content extracted"
        
        # Create JSON structure compatible with analysis pipeline
        json_data = {
            'filename': Path(txt_file_path).stem,
            'url': metadata.get('url', ''),
            'title': metadata.get('csv_title', ''),
            'date': metadata.get('date', ''),
            'sentiment': metadata.get('sentiment', ''),
            'text': body,
            'text_length': len(body),
            'source': 'html_extractor',
            'processing_info': {
                'converted_at': datetime.now().isoformat(),
                'source_file': txt_file_path
            }
        }
        
        return json_data
        
    except Exception as e:
        print(f"❌ Error reading file {txt_file_path}: {e}")
        return create_empty_json_data(txt_file_path)

def create_empty_json_data(txt_file_path: str) -> Dict:
    """
    Create empty JSON data for files that couldn't be processed
    """
    return {
        'filename': Path(txt_file_path).stem,
        'url': '',
        'title': '',
        'date': '',
        'sentiment': '',
        'text': 'Error: Could not extract content',
        'text_length': 0,
        'source': 'html_extractor',
        'processing_info': {
            'converted_at': datetime.now().isoformat(),
            'source_file': txt_file_path
        }
    }

def convert_all_txts_to_json(txt_dir: str, output_dir: str) -> List[str]:
    """
    Convert all .txt files from HTML content extractor to JSON format
    
    Args:
        txt_dir: Directory containing .txt files from HTML content extractor
        output_dir: Directory to save JSON files
        
    Returns:
        List of created JSON file paths
    """
    txt_path = Path(txt_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Looking for .txt files in: {txt_path}")
    print(f"📁 Output directory: {output_path}")
    
    # Debug: List all files in the directory
    all_files = list(txt_path.glob('*'))
    print(f"📄 Found {len(all_files)} files in directory:")
    for file in all_files:
        print(f"  - {file.name} ({'file' if file.is_file() else 'directory'})")
    
    # Look specifically for .txt files
    txt_files = list(txt_path.glob('*.txt'))
    print(f"📄 Found {len(txt_files)} .txt files:")
    for txt_file in txt_files:
        print(f"  - {txt_file.name}")
    
    created_files = []
    
    for txt_file in txt_files:
        print(f"Converting {txt_file.name} to JSON...")
        
        try:
            # Convert to JSON
            json_data = convert_txt_to_json(str(txt_file))
            
            # Save JSON file
            json_filename = txt_file.stem + '.json'
            json_file_path = output_path / json_filename
            
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            
            created_files.append(str(json_file_path))
            print(f"✅ Created: {json_file_path}")
            
        except Exception as e:
            print(f"❌ Error converting {txt_file.name}: {e}")
    
    return created_files

def create_json_schema() -> Dict:
    """
    Define the JSON schema for the converted data from HTML content extractor
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "url": {"type": "string"},
            "title": {"type": "string"},
            "date": {"type": "string"},
            "sentiment": {"type": "string"},
            "text": {"type": "string"},
            "text_length": {"type": "integer"},
            "source": {"type": "string"},
            "processing_info": {
                "type": "object",
                "properties": {
                    "converted_at": {"type": "string"},
                    "source_file": {"type": "string"}
                },
                "required": ["converted_at", "source_file"]
            }
        },
        "required": ["filename", "url", "text", "source", "processing_info"]
    }
    
    return schema

def save_json_schema(schema: Dict, output_file: str):
    """
    Save the JSON schema to a file
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(schema, file, indent=2)
    
    print(f"JSON schema saved to {output_file}")

def run_txt_to_json_conversion_pipeline(txt_dir: str, output_dir: str) -> Dict:
    """
    Main pipeline function to convert .txt files from HTML content extractor to JSON format
    
    Args:
        txt_dir: Directory containing .txt files from HTML content extractor
        output_dir: Directory to save JSON files
        
    Returns:
        Dictionary with conversion results
    """
    print("=" * 60)
    print("TXT TO JSON CONVERSION PIPELINE")
    print("=" * 60)
    
    print(f"Input directory: {txt_dir}")
    print(f"Output directory: {output_dir}")
    
    # Convert all .txt files to JSON
    created_files = convert_all_txts_to_json(txt_dir, output_dir)
    
    # Create and save JSON schema
    schema = create_json_schema()
    schema_file = Path(output_dir) / "conversion_schema.json"
    save_json_schema(schema, str(schema_file))
    
    # Print summary
    print(f"\nJSON conversion complete:")
    print(f"Files converted: {len(created_files)}")
    print(f"Output directory: {output_dir}")
    print(f"Schema file: {schema_file}")
    
    return {
        'success': len(created_files) > 0,
        'converted_files': created_files,
        'total_files': len(created_files),
        'output_dir': output_dir,
        'schema_file': str(schema_file)
    }


if __name__ == "__main__":
    """Example usage for command line execution."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python json_conversion.py <txt_directory> <output_directory>")
        print("Example: python json_conversion.py extracted_content/ json_output/")
        sys.exit(1)
    
    txt_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    results = run_txt_to_json_conversion_pipeline(txt_dir, output_dir)
    
    if results['success']:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"Converted {results['total_files']} files")
    else:
        print(f"\n❌ Conversion failed")
        sys.exit(1)
