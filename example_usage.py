#!/usr/bin/env python3
"""
Example usage of the HTML Content Extractor
"""

from html_content_extractor import HTMLContentExtractor


def extract_single_url():
    """Extract content from a single URL."""
    url = "https://example.com"
    output_file = "example_extracted.txt"
    
    extractor = HTMLContentExtractor(headless=True, timeout=30)
    
    try:
        print(f"Extracting content from: {url}")
        success = extractor.extract_from_url(url, output_file)
        
        if success:
            print(f"✅ Content successfully extracted to: {output_file}")
        else:
            print("❌ Failed to extract content")
    
    finally:
        extractor.cleanup()


def extract_multiple_urls():
    """Extract content from multiple URLs."""
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://www.wikipedia.org"
    ]
    
    extractor = HTMLContentExtractor(headless=True, timeout=30)
    
    try:
        for i, url in enumerate(urls, 1):
            output_file = f"extracted_content_{i}.txt"
            print(f"\nExtracting from URL {i}: {url}")
            
            success = extractor.extract_from_url(url, output_file)
            
            if success:
                print(f"✅ Content saved to: {output_file}")
            else:
                print(f"❌ Failed to extract from: {url}")
    
    finally:
        extractor.cleanup()


if __name__ == "__main__":
    print("HTML Content Extractor - Example Usage")
    print("=" * 50)
    
    # Choose which example to run
    choice = input("Choose example:\n1. Single URL\n2. Multiple URLs\nEnter choice (1 or 2): ")
    
    if choice == "1":
        extract_single_url()
    elif choice == "2":
        extract_multiple_urls()
    else:
        print("Invalid choice. Running single URL example...")
        extract_single_url()
