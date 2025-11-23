#!/usr/bin/env python3
"""
HTML Content Extractor using Selenium, Readability, and Goose3

This script downloads HTML from a URL using Selenium, cleans it with readability,
and extracts content using goose3, then saves to a text file.
"""

import os
import tempfile
import time
import csv
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

import readability
import goose3
from goose3 import Goose


class HTMLContentExtractor:
    def __init__(self, headless=True, timeout=30):
        """
        Initialize the HTML content extractor.
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Timeout for page loading in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.temp_dir = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better performance and stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Make sure ChromeDriver is installed and in PATH")
            return False
    
    def download_html(self, url):
        """
        Download HTML content from URL using Selenium.
        
        Args:
            url (str): URL to download
            
        Returns:
            str: Path to downloaded HTML file, or None if failed
        """
        if not self.driver:
            if not self.setup_driver():
                return None
        
        try:
            print(f"Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source
            html_content = self.driver.page_source
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(self.temp_dir, "page.html")
            
            # Write HTML to file
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML saved to: {temp_file}")
            return temp_file
            
        except TimeoutException:
            print(f"Timeout loading URL: {url}")
            return None
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return None
        except Exception as e:
            print(f"Error downloading HTML: {e}")
            return None
    
    def clean_html_with_readability(self, html_file_path):
        """
        Clean HTML using readability package.
        
        Args:
            html_file_path (str): Path to HTML file
            
        Returns:
            str: Path to cleaned HTML file, or None if failed
        """
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Apply readability
            doc = readability.Document(html_content)
            cleaned_html = doc.summary()
            
            # Save cleaned HTML
            cleaned_file = html_file_path.replace('.html', '_cleaned.html')
            with open(cleaned_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_html)
            
            print(f"Cleaned HTML saved to: {cleaned_file}")
            return cleaned_file
            
        except Exception as e:
            print(f"Error cleaning HTML with readability: {e}")
            return None
    
    def extract_content_with_goose(self, html_file_path):
        """
        Extract content using goose3.
        
        Args:
            html_file_path (str): Path to HTML file
            
        Returns:
            dict: Extracted content with title, metadata, and body
        """
        try:
            # Initialize Goose
            g = Goose()
            
            # Extract content
            article = g.extract(raw_html=open(html_file_path, 'r', encoding='utf-8').read())
            
            content = {
                'title': article.title,
                'meta_description': article.meta_description,
                'meta_keywords': article.meta_keywords,
                'canonical_link': article.canonical_link,
                'domain': article.domain,
                'body': article.cleaned_text,
                'publish_date': article.publish_date,
                'authors': article.authors,
                'tags': article.tags
            }
            
            print("Content extracted successfully with goose3")
            return content
            
        except Exception as e:
            print(f"Error extracting content with goose3: {e}")
            return None
    
    def clean_text_content(self, text):
        """
        Clean text content by removing excessive whitespace and normalizing line breaks.
        
        Args:
            text (str): Raw text content
            
        Returns:
            str: Cleaned text content
        """
        if not text or not text.strip():
            return text
        
        import re
        
        # Replace multiple consecutive newlines with single newlines
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = cleaned_text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        # Join back with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        return cleaned_text

    def save_to_text_file(self, content, output_path, csv_metadata=None):
        """
        Save extracted content to text file.
        
        Args:
            content (dict): Extracted content
            output_path (str): Path to output text file
            csv_metadata (dict): Additional metadata from CSV file
        """
        try:
            # Clean the body content before saving
            body_content = content.get('body', 'No content extracted')
            cleaned_body = self.clean_text_content(body_content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("EXTRACTED CONTENT\n")
                f.write("=" * 80 + "\n\n")
                
                # Include CSV metadata if provided
                if csv_metadata:
                    f.write("CSV METADATA:\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"URL: {csv_metadata.get('url', 'N/A')}\n")
                    f.write(f"Title: {csv_metadata.get('title', 'N/A')}\n")
                    f.write(f"Date: {csv_metadata.get('date', 'N/A')}\n")
                    f.write(f"Sentiment: {csv_metadata.get('sentiment', 'N/A')}\n\n")
                
                f.write(f"EXTRACTED TITLE: {content.get('title', 'N/A')}\n\n")
                
                f.write("EXTRACTED METADATA:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Description: {content.get('meta_description', 'N/A')}\n")
                f.write(f"Keywords: {content.get('meta_keywords', 'N/A')}\n")
                f.write(f"Canonical Link: {content.get('canonical_link', 'N/A')}\n")
                f.write(f"Domain: {content.get('domain', 'N/A')}\n")
                f.write(f"Publish Date: {content.get('publish_date', 'N/A')}\n")
                f.write(f"Authors: {', '.join(content.get('authors', []))}\n")
                f.write(f"Tags: {', '.join(content.get('tags', []))}\n\n")
                
                f.write("BODY:\n")
                f.write("-" * 40 + "\n")
                f.write(cleaned_body)
            
            print(f"Content saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving to text file: {e}")
            return False
    
    def extract_from_url(self, url, output_path=None, csv_metadata=None):
        """
        Complete extraction process from URL to text file.
        
        Args:
            url (str): URL to extract content from
            output_path (str): Path for output text file (optional)
            csv_metadata (dict): Additional metadata from CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate output path if not provided
            if not output_path:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.replace('www.', '')
                output_path = f"{domain}_extracted_content.txt"
            
            # Step 1: Download HTML
            html_file = self.download_html(url)
            if not html_file:
                return False
            
            # Step 2: Clean HTML with readability
            cleaned_html = self.clean_html_with_readability(html_file)
            if not cleaned_html:
                return False
            
            # Step 3: Extract content with goose3
            content = self.extract_content_with_goose(cleaned_html)
            if not content:
                return False
            
            # Step 4: Save to text file with CSV metadata
            success = self.save_to_text_file(content, output_path, csv_metadata)
            
            return success
            
        except Exception as e:
            print(f"Error in extraction process: {e}")
            return False
    
    def process_csv_file(self, csv_file_path, output_dir="extracted_content", url_column="url", delay=1.0):
        """
        Process all URLs from a CSV file.
        
        Args:
            csv_file_path (str): Path to CSV file
            output_dir (str): Directory to save extracted content
            url_column (str): Name of the column containing URLs
            delay (float): Delay between requests in seconds
            
        Returns:
            dict: Results summary with success/failure counts
        """
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, 1):
                    results['total'] += 1
                    url = row.get(url_column)
                    
                    if not url:
                        error_msg = f"Row {row_num}: No URL found in column '{url_column}'"
                        results['errors'].append(error_msg)
                        results['failed'] += 1
                        print(f"❌ {error_msg}")
                        continue
                    
                    # Create output filename based on row number and domain
                    try:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
                        output_filename = f"row_{row_num:03d}_{domain}_extracted.txt"
                        output_path = os.path.join(output_dir, output_filename)
                    except:
                        output_filename = f"row_{row_num:03d}_extracted.txt"
                        output_path = os.path.join(output_dir, output_filename)
                    
                    print(f"\n{'='*60}")
                    print(f"Processing Row {row_num}: {url}")
                    print(f"{'='*60}")
                    
                    # Extract CSV metadata (all columns except URL)
                    csv_metadata = {k: v for k, v in row.items() if k != url_column}
                    csv_metadata['url'] = url  # Add URL to metadata
                    
                    # Process the URL
                    success = self.extract_from_url(url, output_path, csv_metadata)
                    
                    if success:
                        results['successful'] += 1
                        print(f"✅ Successfully processed: {url}")
                    else:
                        results['failed'] += 1
                        error_msg = f"Row {row_num}: Failed to extract content from {url}"
                        results['errors'].append(error_msg)
                        print(f"❌ {error_msg}")
                    
                    # Small delay between requests
                    time.sleep(delay)
        
        except FileNotFoundError:
            error_msg = f"CSV file not found: {csv_file_path}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        except Exception as e:
            error_msg = f"Error reading CSV file: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        return results
    
    def process_csv_file_sample(self, csv_file_path, output_dir="extracted_content", url_column="url", sample_size=5, delay=1.0):
        """
        Process a sample of URLs from a CSV file.
        
        Args:
            csv_file_path (str): Path to CSV file
            output_dir (str): Directory to save extracted content
            url_column (str): Name of the column containing URLs
            sample_size (int): Number of URLs to process
            delay (float): Delay between requests in seconds
            
        Returns:
            dict: Results summary with success/failure counts
        """
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)[:sample_size]  # Take only first N rows
                
                for row_num, row in enumerate(rows, 1):
                    results['total'] += 1
                    url = row.get(url_column)
                    
                    if not url:
                        error_msg = f"Row {row_num}: No URL found in column '{url_column}'"
                        results['errors'].append(error_msg)
                        results['failed'] += 1
                        print(f"❌ {error_msg}")
                        continue
                    
                    # Create output filename based on row number and domain
                    try:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
                        output_filename = f"sample_{row_num:03d}_{domain}_extracted.txt"
                        output_path = os.path.join(output_dir, output_filename)
                    except:
                        output_filename = f"sample_{row_num:03d}_extracted.txt"
                        output_path = os.path.join(output_dir, output_filename)
                    
                    print(f"\n{'='*60}")
                    print(f"Processing Sample {row_num}: {url}")
                    print(f"{'='*60}")
                    
                    # Extract CSV metadata (all columns except URL)
                    csv_metadata = {k: v for k, v in row.items() if k != url_column}
                    csv_metadata['url'] = url  # Add URL to metadata
                    
                    # Process the URL
                    success = self.extract_from_url(url, output_path, csv_metadata)
                    
                    if success:
                        results['successful'] += 1
                        print(f"✅ Successfully processed sample {row_num}")
                    else:
                        results['failed'] += 1
                        error_msg = f"Sample {row_num}: Failed to extract content from {url}"
                        results['errors'].append(error_msg)
                        print(f"❌ {error_msg}")
                    
                    # Small delay between requests
                    time.sleep(delay)
        
        except FileNotFoundError:
            error_msg = f"CSV file not found: {csv_file_path}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        except Exception as e:
            error_msg = f"Error reading CSV file: {e}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        return results
    
    def print_processing_summary(self, results):
        """Print a summary of the processing results."""
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total URLs processed: {results['total']}")
        print(f"Successful extractions: {results['successful']}")
        print(f"Failed extractions: {results['failed']}")
        
        if results['errors']:
            print(f"\nErrors encountered:")
            for error in results['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(results['errors']) > 10:
                print(f"  ... and {len(results['errors']) - 10} more errors")
        
        success_rate = (results['successful'] / results['total'] * 100) if results['total'] > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            print("Temporary files cleaned up")


def main():
    """Command line interface for HTMLContentExtractor."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="HTML Content Extractor - Extract content from URLs using Selenium, Readability, and Goose3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process CSV file
  python html_content_extractor.py --csv pfof_articles2.csv --output extracted_content
  
  # Process single URL
  python html_content_extractor.py --url "https://example.com" --output single_extract.txt
  
  # Process CSV with custom settings
  python html_content_extractor.py --csv data.csv --output results --timeout 60 --no-headless
  
  # Show help
  python html_content_extractor.py --help
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--csv", help="CSV file containing URLs to process")
    input_group.add_argument("--url", help="Single URL to process")
    
    # Output options
    parser.add_argument("--output", required=True, help="Output directory (for CSV) or file path (for single URL)")
    parser.add_argument("--url-column", default="url", help="Name of URL column in CSV (default: 'url')")
    
    # Processing options
    parser.add_argument("--timeout", type=int, default=30, help="Page load timeout in seconds (default: 30)")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible mode (default: headless)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    
    # Sample processing
    parser.add_argument("--sample", type=int, help="Process only first N URLs from CSV")
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = HTMLContentExtractor(
        headless=not args.no_headless,
        timeout=args.timeout
    )
    
    try:
        if args.csv:
            # Process CSV file
            print(f"📄 Processing CSV file: {args.csv}")
            print(f"📁 Output directory: {args.output}")
            print(f"⏱️  Timeout: {args.timeout}s")
            print(f"🖥️  Headless: {not args.no_headless}")
            print(f"⏳ Delay: {args.delay}s")
            print("=" * 60)
            
            # Process CSV with optional sampling
            if args.sample:
                print(f"🔬 Processing sample of {args.sample} URLs")
                results = extractor.process_csv_file_sample(
                    args.csv, 
                    args.output, 
                    args.url_column, 
                    args.sample,
                    args.delay
                )
            else:
                results = extractor.process_csv_file(
                    args.csv, 
                    args.output, 
                    args.url_column,
                    args.delay
                )
            
            extractor.print_processing_summary(results)
            
        elif args.url:
            # Process single URL
            print(f"🌐 Processing single URL: {args.url}")
            print(f"📄 Output file: {args.output}")
            print("=" * 60)
            
            success = extractor.extract_from_url(args.url, args.output)
            
            if success:
                print(f"✅ Successfully extracted content to: {args.output}")
            else:
                print(f"❌ Failed to extract content from: {args.url}")
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        extractor.cleanup()


if __name__ == "__main__":
    main()
