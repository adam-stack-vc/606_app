#!/usr/bin/env python3
"""
Pipeline Runner for 606 App
Orchestrates the complete pipeline: html_content_extractor → json_conversion → analysis_pipeline → nms_chunks
"""

import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List
import sys
import os
import pandas as pd

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from html_content_extractor import HTMLContentExtractor
from json_conversion import run_txt_to_json_conversion_pipeline
from analysis_pipeline import analyze_all_documents
from NMS_chunks import chunk_text, load_metadata_json

def run_html_extraction_pipeline(csv_file: str, output_dir: str, timeout: int = 30, headless: bool = True, delay: float = 1.0) -> Dict:
    """
    Run the HTML content extraction pipeline
    
    Args:
        csv_file: Path to input CSV file
        output_dir: Directory to save extracted content and JSON files
        timeout: Page load timeout in seconds
        headless: Run browser in headless mode
        delay: Delay between requests in seconds
        
    Returns:
        Dictionary with extraction results
    """
    print("=" * 60)
    print("STEP 1: HTML CONTENT EXTRACTION")
    print("=" * 60)
    
    # Create output directories
    extracted_dir = Path(output_dir) / "extracted_content"
    json_dir = Path(output_dir) / "json_files"
    json_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input CSV: {csv_file}")
    print(f"Output directory: {output_dir}")
    print(f"Timeout: {timeout}s, Headless: {headless}, Delay: {delay}s")
    
    # Initialize HTML content extractor
    extractor = HTMLContentExtractor(headless=headless, timeout=timeout)
    
    try:
        # Extract content from CSV
        results = extractor.process_csv_file(
            csv_file_path=csv_file,
            output_dir=str(extracted_dir),
            url_column="url",
            delay=delay
        )
        
        # Print extraction summary
        extractor.print_processing_summary(results)
        
        # Convert extracted .txt files to JSON format
        print(f"\nConverting extracted content to JSON format...")
        
        # Check if files exist in the expected directory
        if not extracted_dir.exists() or not any(extracted_dir.glob('*.txt')):
            print(f"⚠️  No .txt files found in {extracted_dir}")
            print(f"🔍 Looking for existing extracted content...")
            
            # Check if there are files in the current directory
            current_dir = Path.cwd() / "extracted_content"
            if current_dir.exists() and any(current_dir.glob('*.txt')):
                print(f"📁 Found existing extracted content in: {current_dir}")
                extracted_dir = current_dir
            else:
                print(f"❌ No extracted content found. Please run HTML extraction first.")
                return {
                    'extraction_results': results,
                    'conversion_results': {'success': False, 'total_files': 0},
                    'json_dir': str(json_dir),
                    'extracted_dir': str(extracted_dir),
                    'summary_file': str(summary_file)
                }
        
        conversion_results = run_txt_to_json_conversion_pipeline(
            str(extracted_dir), 
            str(json_dir)
        )
        
        # Create summary CSV
        summary_file = Path(output_dir) / "extraction_summary.csv"
        create_extraction_summary(results, str(summary_file))
        
        print(f"\nHTML Extraction Statistics:")
        print(f"  Total URLs: {results['total']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Success rate: {(results['successful'] / results['total'] * 100) if results['total'] > 0 else 0:.1f}%")
        print(f"  JSON files created: {conversion_results['total_files']}")
        
        return {
            'extraction_results': results,
            'conversion_results': conversion_results,
            'json_dir': str(json_dir),
            'extracted_dir': str(extracted_dir),
            'summary_file': str(summary_file)
        }
        
    finally:
        extractor.cleanup()

def create_extraction_summary(results: Dict, summary_file: str):
    """
    Create a summary CSV file of the extraction results
    """
    import csv
    
    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total URLs', results['total']])
        writer.writerow(['Successful', results['successful']])
        writer.writerow(['Failed', results['failed']])
        writer.writerow(['Success Rate (%)', f"{(results['successful'] / results['total'] * 100) if results['total'] > 0 else 0:.1f}"])
        
        if results['errors']:
            writer.writerow(['Errors', ''])
            for error in results['errors']:
                writer.writerow(['', error])
    
    print(f"Extraction summary saved to: {summary_file}")

def run_analysis_pipeline(json_dir: str, output_dir: str) -> List[Dict]:
    """
    Run the analysis pipeline to enhance documents
    
    Args:
        json_dir: Directory containing JSON files from fetch_content
        output_dir: Directory to save enhanced documents
        
    Returns:
        List of enhanced documents
    """
    print("\n" + "=" * 60)
    print("STEP 2: ANALYSIS PIPELINE")
    print("=" * 60)
    
    analysis_output_dir = Path(output_dir) / "analysis_output2"
    analysis_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input JSON directory: {json_dir}")
    print(f"Analysis output directory: {analysis_output_dir}")
    
    # Run analysis pipeline
    enhanced_documents = analyze_all_documents(json_dir, str(analysis_output_dir))
    
    print(f"\nAnalysis complete. Enhanced {len(enhanced_documents)} documents.")
    
    return enhanced_documents

def run_nms_chunks_pipeline(analysis_output_dir: str, output_dir: str, chunk_size: int = 6000) -> Dict:
    """
    Run the NMS chunks pipeline to create chunked documents with metadata
    
    Args:
        analysis_output_dir: Directory containing enhanced JSON files
        output_dir: Directory to save chunked output
        chunk_size: Target chunk size in characters
        
    Returns:
        Dictionary with chunking results
    """
    print("\n" + "=" * 60)
    print("STEP 3: NMS CHUNKS PIPELINE")
    print("=" * 60)
    
    chunks_output_dir = Path(output_dir) / "chunks_output"
    chunks_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input analysis directory: {analysis_output_dir}")
    print(f"Chunks output directory: {chunks_output_dir}")
    print(f"Chunk size: {chunk_size} characters")
    
    # Create a combined JSON file with all enhanced documents for NMS chunks
    combined_json_path = chunks_output_dir / "combined_enhanced_documents.json"
    
    # Load all enhanced documents
    enhanced_documents = []
    analysis_path = Path(analysis_output_dir)
    
    for json_file in analysis_path.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            document = json.load(f)
        enhanced_documents.append(document)
    
    print(f"Loaded {len(enhanced_documents)} enhanced documents")
    
    # Save combined JSON for NMS chunks to process
    with open(combined_json_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_documents, f, indent=2, ensure_ascii=False)
    
    # Use the existing NMS chunks logic
    metadata_index = load_metadata_json(str(combined_json_path))
    print(f"Created metadata index for {len(metadata_index)} files")
    
    # Process each record from the metadata index
    all_chunks = []
    manifest_records = []
    
    for original_file, metadata in metadata_index.items():
        filename = metadata['filename']
        text = metadata.get('text', '')
        
        if not text.strip():
            print(f"Warning: Empty text for {filename}")
            continue
        
        # Create manifest record
        manifest_record = {
            'filename': metadata['filename'],
            'url': metadata['url'],
            'date': metadata['date'],
            'value_chains': ', '.join(metadata['value_chains']) if metadata['value_chains'] else '',
            'companies_mentioned': ', '.join(metadata['companies_mentioned']) if metadata['companies_mentioned'] else '',
            'persons_mentioned': ', '.join(metadata['persons_mentioned']) if metadata['persons_mentioned'] else '',
            'asset_classes': metadata['asset_classes'],
            'topic': metadata['topic'],
            'sentiment': metadata['sentiment'],
            'text_length': len(text),
            'total_chunks': 0  # Will be updated after chunking
        }
        
        # Chunk the text
        chunks = chunk_text(text, chunk_size)
        manifest_record['total_chunks'] = len(chunks)
        
        # Create chunk records
        for i, chunk in enumerate(chunks):
            chunk_record = {
                'filename': metadata['filename'],
                'url': metadata['url'],
                'date': metadata['date'],
                'value_chains': ', '.join(metadata['value_chains']) if metadata['value_chains'] else '',
                'companies_mentioned': ', '.join(metadata['companies_mentioned']) if metadata['companies_mentioned'] else '',
                'persons_mentioned': ', '.join(metadata['persons_mentioned']) if metadata['persons_mentioned'] else '',
                'asset_classes': metadata['asset_classes'],
                'topic': metadata['topic'],
                'sentiment': metadata['sentiment'],
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk),
                'text': chunk
            }
            all_chunks.append(chunk_record)
        
        manifest_records.append(manifest_record)
    
    if not all_chunks:
        print("No chunks created!")
        return {'success': False}
    
    # Save outputs
    manifest_path = chunks_output_dir / "nms_manifest.csv"
    manifest_df = pd.DataFrame(manifest_records)
    manifest_df.to_csv(manifest_path, index=False)
    
    # Save chunks as JSONL
    chunks_path = chunks_output_dir / "nms_chunks.jsonl"
    with open(chunks_path, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Save chunks CSV (without text)
    chunks_csv_path = chunks_output_dir / "nms_chunks.csv"
    chunks_df = pd.DataFrame([{k: v for k, v in chunk.items() if k != 'text'} for chunk in all_chunks])
    chunks_df.to_csv(chunks_csv_path, index=False)
    
    print(f"\nChunking complete!")
    print(f"Manifest: {manifest_path}")
    print(f"Chunks (full): {chunks_path}")
    print(f"Chunks CSV: {chunks_csv_path}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Average chunk size: {sum(len(c['text']) for c in all_chunks) / len(all_chunks):.0f} characters")
    
    return {
        'success': True,
        'manifest_path': str(manifest_path),
        'chunks_path': str(chunks_path),
        'chunks_csv_path': str(chunks_csv_path),
        'total_chunks': len(all_chunks),
        'total_documents': len(enhanced_documents)
    }

def main():
    parser = argparse.ArgumentParser(description="Run the complete 606 App pipeline with HTML content extraction")
    parser.add_argument("--csv-file", help="Input CSV file with links (required unless --skip-extraction is used)")
    parser.add_argument("--output-dir", required=True, help="Output directory for all results")
    parser.add_argument("--chunk-size", type=int, default=6000, help="Target chunk size in characters")
    parser.add_argument("--skip-extraction", action="store_true", help="Skip HTML extraction step (use existing JSON files)")
    parser.add_argument("--json-dir", help="Directory containing existing JSON files (used with --skip-extraction)")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip analysis step")
    parser.add_argument("--skip-chunks", action="store_true", help="Skip chunks step")
    
    # HTML extraction options
    parser.add_argument("--timeout", type=int, default=30, help="Page load timeout in seconds")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.skip_extraction and not args.csv_file:
        parser.error("--csv-file is required when not using --skip-extraction")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Starting 606 App Pipeline with HTML Content Extraction")
    if args.csv_file:
        print(f"CSV file: {args.csv_file}")
    print(f"Output directory: {output_dir}")
    print(f"Chunk size: {args.chunk_size}")
    print(f"Timeout: {args.timeout}s, Headless: {not args.no_headless}, Delay: {args.delay}s")
    
    try:
        # Step 1: HTML Content Extraction
        if not args.skip_extraction:
            extraction_results = run_html_extraction_pipeline(
                args.csv_file, 
                str(output_dir),
                timeout=args.timeout,
                headless=not args.no_headless,
                delay=args.delay
            )
            json_dir = extraction_results['json_dir']
        else:
            print("Skipping HTML extraction step - using existing JSON files")
            if args.json_dir:
                json_dir = args.json_dir
                print(f"Using JSON files from: {json_dir}")
            else:
                json_dir = str(output_dir / "json_files")
                print(f"Using JSON files from: {json_dir}")
        
        # Step 2: Analysis Pipeline
        if not args.skip_analysis:
            analysis_output_dir = str(output_dir / "analysis_output")
            enhanced_documents = run_analysis_pipeline(json_dir, str(output_dir))
        else:
            print("Skipping analysis step")
            analysis_output_dir = str(output_dir / "analysis_output")
        
        # Step 3: NMS Chunks
        if not args.skip_chunks:
            chunks_results = run_nms_chunks_pipeline(analysis_output_dir, str(output_dir), args.chunk_size)
            
            if chunks_results['success']:
                print("\n" + "=" * 60)
                print("🎉 PIPELINE COMPLETE!")
                print("=" * 60)
                print(f"Total documents processed: {chunks_results['total_documents']}")
                print(f"Total chunks created: {chunks_results['total_chunks']}")
                print(f"Output files:")
                print(f"  - Manifest: {chunks_results['manifest_path']}")
                print(f"  - Chunks: {chunks_results['chunks_path']}")
                print(f"  - Chunks CSV: {chunks_results['chunks_csv_path']}")
            else:
                print("❌ Pipeline failed at chunks step")
                return 1
        else:
            print("Skipping chunks step")
        
        return 0
        
    except Exception as e:
        print(f"❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
