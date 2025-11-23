#!/usr/bin/env python3
"""
Process pfof_articles2.csv with HTML Content Extractor

This script processes the pfof_articles2.csv file to extract content from all URLs
and save the results with CSV metadata included.
"""

from html_content_extractor import HTMLContentExtractor
import os


def process_pfof_articles():
    """Process the pfof_articles2.csv file."""
    csv_file = "pfof_articles2.csv"
    output_dir = "pfof_extracted_content"
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("Please make sure pfof_articles2.csv is in the current directory.")
        return
    
    print("🚀 Starting PFOF Articles Processing")
    print("=" * 60)
    print(f"CSV file: {csv_file}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    
    # Initialize extractor
    extractor = HTMLContentExtractor(headless=True, timeout=30)
    
    try:
        # Process the CSV file
        results = extractor.process_csv_file(
            csv_file_path=csv_file,
            output_dir=output_dir,
            url_column="url"
        )
        
        # Print summary
        extractor.print_processing_summary(results)
        
        # Additional info
        print(f"\n📁 Extracted content saved to: {output_dir}/")
        print("Each file contains:")
        print("  - CSV metadata (URL, title, date, sentiment)")
        print("  - Extracted title from the webpage")
        print("  - Extracted metadata (description, keywords, etc.)")
        print("  - Full article body text")
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"❌ Error during processing: {e}")
    
    finally:
        extractor.cleanup()
        print("\n🧹 Cleanup completed")


def process_sample_articles(num_articles=5):
    """Process only the first N articles for testing."""
    csv_file = "pfof_articles2.csv"
    output_dir = f"pfof_sample_extracted_{num_articles}"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print(f"🧪 Processing Sample of {num_articles} Articles")
    print("=" * 60)
    
    extractor = HTMLContentExtractor(headless=True, timeout=30)
    
    try:
        # Read CSV and process only first N rows
        import csv
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)[:num_articles]
        
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        os.makedirs(output_dir, exist_ok=True)
        
        for i, row in enumerate(rows, 1):
            results['total'] += 1
            url = row.get('url')
            
            if not url:
                continue
            
            # Create output filename
            from urllib.parse import urlparse
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
                output_filename = f"sample_{i:02d}_{domain}_extracted.txt"
            except:
                output_filename = f"sample_{i:02d}_extracted.txt"
            
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"\nProcessing Sample {i}: {url}")
            
            # Extract CSV metadata
            csv_metadata = {k: v for k, v in row.items() if k != 'url'}
            csv_metadata['url'] = url
            
            # Process the URL
            success = extractor.extract_from_url(url, output_path, csv_metadata)
            
            if success:
                results['successful'] += 1
                print(f"✅ Successfully processed sample {i}")
            else:
                results['failed'] += 1
                print(f"❌ Failed to process sample {i}")
        
        extractor.print_processing_summary(results)
        print(f"\n📁 Sample content saved to: {output_dir}/")
        
    finally:
        extractor.cleanup()


if __name__ == "__main__":
    import sys
    
    print("PFOF Articles Content Extractor")
    print("=" * 40)
    print("1. Process all articles")
    print("2. Process sample (first 5 articles)")
    print("3. Process custom sample size")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        process_pfof_articles()
    elif choice == "2":
        process_sample_articles(5)
    elif choice == "3":
        try:
            num = int(input("Enter number of articles to process: "))
            process_sample_articles(num)
        except ValueError:
            print("Invalid number. Processing 5 articles instead.")
            process_sample_articles(5)
    else:
        print("Invalid choice. Processing sample of 5 articles.")
        process_sample_articles(5)
