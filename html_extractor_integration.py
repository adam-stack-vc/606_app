#!/usr/bin/env python3
"""
HTML Content Extractor Integration for Pipeline

This module provides integration functions to use the HTML Content Extractor
within the existing pipeline_runner.py workflow.
"""

import os
import json
from pathlib import Path
from html_content_extractor import HTMLContentExtractor


def extract_content_for_pipeline(csv_file_path, output_dir, timeout=30, headless=True, delay=1.0):
    """
    Extract content from URLs in CSV file for pipeline integration.
    
    Args:
        csv_file_path (str): Path to CSV file with URLs
        output_dir (str): Directory to save extracted content
        timeout (int): Page load timeout in seconds
        headless (bool): Run browser in headless mode
        delay (float): Delay between requests in seconds
        
    Returns:
        dict: Results summary with paths and statistics
    """
    print("=" * 60)
    print("HTML CONTENT EXTRACTION")
    print("=" * 60)
    
    # Initialize extractor
    extractor = HTMLContentExtractor(headless=headless, timeout=timeout)
    
    try:
        # Process CSV file
        results = extractor.process_csv_file(
            csv_file_path=csv_file_path,
            output_dir=output_dir,
            url_column="url",
            delay=delay
        )
        
        # Print summary
        extractor.print_processing_summary(results)
        
        # Return results for pipeline integration
        return {
            'success': results['successful'] > 0,
            'total_processed': results['total'],
            'successful': results['successful'],
            'failed': results['failed'],
            'success_rate': (results['successful'] / results['total'] * 100) if results['total'] > 0 else 0,
            'output_dir': output_dir,
            'errors': results['errors']
        }
        
    finally:
        extractor.cleanup()


def convert_extracted_to_json(extracted_dir, json_output_dir):
    """
    Convert extracted text files to JSON format compatible with pipeline.
    
    Args:
        extracted_dir (str): Directory containing extracted text files
        json_output_dir (str): Directory to save JSON files
        
    Returns:
        dict: Conversion results
    """
    print("\n" + "=" * 60)
    print("CONVERTING TO JSON FORMAT")
    print("=" * 60)
    
    extracted_path = Path(extracted_dir)
    json_path = Path(json_output_dir)
    json_path.mkdir(parents=True, exist_ok=True)
    
    converted_files = []
    errors = []
    
    # Process each extracted text file
    for txt_file in extracted_path.glob("*.txt"):
        try:
            # Read the text file
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the content to extract metadata and body
            lines = content.split('\n')
            metadata = {}
            body_start = False
            body_content = []
            
            for line in lines:
                if line.startswith("CSV METADATA:"):
                    continue
                elif line.startswith("URL:"):
                    metadata['url'] = line.split("URL: ", 1)[1]
                elif line.startswith("Title:"):
                    metadata['title'] = line.split("Title: ", 1)[1]
                elif line.startswith("Date:"):
                    metadata['date'] = line.split("Date: ", 1)[1]
                elif line.startswith("Sentiment:"):
                    metadata['sentiment'] = line.split("Sentiment: ", 1)[1]
                elif line.startswith("EXTRACTED TITLE:"):
                    metadata['extracted_title'] = line.split("EXTRACTED TITLE: ", 1)[1]
                elif line.startswith("BODY:"):
                    body_start = True
                    continue
                elif body_start and line.strip():
                    body_content.append(line)
            
            # Create JSON structure compatible with pipeline
            json_data = {
                'filename': txt_file.stem,
                'url': metadata.get('url', ''),
                'title': metadata.get('title', ''),
                'extracted_title': metadata.get('extracted_title', ''),
                'date': metadata.get('date', ''),
                'sentiment': metadata.get('sentiment', ''),
                'text': '\n'.join(body_content),
                'text_length': len('\n'.join(body_content)),
                'source': 'html_extractor'
            }
            
            # Save JSON file
            json_filename = txt_file.stem + '.json'
            json_file_path = json_path / json_filename
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            converted_files.append(str(json_file_path))
            print(f"✅ Converted: {txt_file.name} -> {json_filename}")
            
        except Exception as e:
            error_msg = f"Error converting {txt_file.name}: {e}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    print(f"\nConversion complete:")
    print(f"  Converted files: {len(converted_files)}")
    print(f"  Errors: {len(errors)}")
    
    return {
        'success': len(converted_files) > 0,
        'converted_files': converted_files,
        'errors': errors,
        'json_output_dir': str(json_path)
    }


def run_html_extraction_pipeline(csv_file_path, output_dir, timeout=30, headless=True, delay=1.0):
    """
    Complete HTML extraction pipeline: extract content and convert to JSON.
    
    Args:
        csv_file_path (str): Path to CSV file with URLs
        output_dir (str): Base output directory
        timeout (int): Page load timeout in seconds
        headless (bool): Run browser in headless mode
        delay (float): Delay between requests in seconds
        
    Returns:
        dict: Complete pipeline results
    """
    # Step 1: Extract content
    extracted_dir = os.path.join(output_dir, "extracted_content")
    extraction_results = extract_content_for_pipeline(
        csv_file_path, extracted_dir, timeout, headless, delay
    )
    
    if not extraction_results['success']:
        return {
            'success': False,
            'error': 'Content extraction failed',
            'extraction_results': extraction_results
        }
    
    # Step 2: Convert to JSON
    json_output_dir = os.path.join(output_dir, "json_files")
    conversion_results = convert_extracted_to_json(extracted_dir, json_output_dir)
    
    return {
        'success': extraction_results['success'] and conversion_results['success'],
        'extraction_results': extraction_results,
        'conversion_results': conversion_results,
        'output_dirs': {
            'extracted_content': extracted_dir,
            'json_files': json_output_dir
        }
    }


if __name__ == "__main__":
    """Example usage for pipeline integration."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python html_extractor_integration.py <csv_file> <output_dir>")
        print("Example: python html_extractor_integration.py pfof_articles2.csv results/")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    print("🚀 Starting HTML Extraction Pipeline")
    print(f"CSV file: {csv_file}")
    print(f"Output directory: {output_dir}")
    
    results = run_html_extraction_pipeline(csv_file, output_dir)
    
    if results['success']:
        print("\n🎉 Pipeline completed successfully!")
        print(f"Extracted content: {results['output_dirs']['extracted_content']}")
        print(f"JSON files: {results['output_dirs']['json_files']}")
    else:
        print("\n❌ Pipeline failed")
        sys.exit(1)
