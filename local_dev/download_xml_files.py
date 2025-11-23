#!/usr/bin/env python3
"""
Script to download XML files from URLs in a CSV file
"""

import csv
import requests
import zipfile
import os
import glob
from urllib.parse import urlparse, urljoin
import time
from pathlib import Path
import re
from bs4 import BeautifulSoup
import argparse

def get_files_from_directory(url):
    """Get list of files from a directory URL"""
    try:
        print(f"  📁 Detected directory, scanning for files...")
        response = requests.get(url)
        response.raise_for_status()
        
        file_urls = []
        
        # Parse the HTML content to find links
        lines = response.text.split('\n')
        for line in lines:
            # Look for href patterns in the HTML
            matches = re.findall(r'href="([^"]+)"', line)
            for href in matches:
                if href and not href.startswith('?') and not href.startswith('#') and href != '..':
                    # Make it a full URL
                    full_url = urljoin(url, href)
                    
                    # Only include files (not parent directories)
                    if not href.endswith('/'):
                        file_urls.append(full_url)
        
        print(f"    Found {len(file_urls)} files in directory")
        return file_urls
        
    except Exception as e:
        print(f"    ❌ Error scanning directory {url}: {e}")
        return []

def download_file(url, destination_folder):
    """Download a file from URL to destination folder"""
    try:
        # Get filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename or filename.endswith('/'):
            # If it's a directory or no filename, create a timestamped name
            filename = f"download_{int(time.time())}.zip"
        
        filepath = os.path.join(destination_folder, filename)
        
        print(f"  Downloading: {filename}")
        
        # Download with progress
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        print(f"    Content-Type: {content_type}")
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"    Progress: {percent:.1f}%", end='\r')
        
        print(f"    ✓ Downloaded: {filename}")
        return filepath, content_type
        
    except Exception as e:
        print(f"    ❌ Error downloading {url}: {e}")
        return None, None

def process_downloaded_file(file_path, destination_folder, content_type):
    """Process downloaded file - extract XML from zip or copy if it's already XML"""
    try:
        filename = os.path.basename(file_path)
        xml_files_extracted = []
        
        # Check if it's already an XML file
        if filename.lower().endswith('.xml'):
            print(f"    ✓ File is already XML: {filename}")
            xml_files_extracted.append(file_path)
            return xml_files_extracted
        
        # Check if it's a zip file
        if filename.lower().endswith('.zip') or 'zip' in content_type:
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # List all files in zip
                    file_list = zip_ref.namelist()
                    
                    # Find XML files
                    xml_files = [f for f in file_list if f.lower().endswith('.xml')]
                    
                    if not xml_files:
                        print(f"    ⚠️  No XML files found in {filename}")
                        os.remove(file_path)  # Delete the zip
                        return []
                    
                    print(f"    Found {len(xml_files)} XML files:")
                    
                    # Extract only XML files
                    for xml_file in xml_files:
                        # Get just the filename (remove path)
                        xml_filename = os.path.basename(xml_file)
                        xml_dest_path = os.path.join(destination_folder, xml_filename)
                        
                        # Extract the file
                        with zip_ref.open(xml_file) as source, open(xml_dest_path, 'wb') as target:
                            target.write(source.read())
                        
                        xml_files_extracted.append(xml_dest_path)
                        print(f"      ✓ Extracted: {xml_filename}")
                
                # Delete the zip file
                os.remove(file_path)
                print(f"    🗑️  Deleted: {filename}")
                
            except zipfile.BadZipFile:
                print(f"    ⚠️  File is not a valid zip: {filename}")
                # Check if it might be an XML file with wrong extension
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(100)  # Read first 100 chars
                        if content.strip().startswith('<?xml'):
                            # It's an XML file with wrong extension
                            new_name = filename.replace('.zip', '.xml')
                            new_path = os.path.join(destination_folder, new_name)
                            os.rename(file_path, new_path)
                            xml_files_extracted.append(new_path)
                            print(f"      ✓ Renamed to XML: {new_name}")
                        else:
                            print(f"    ❌ Unknown file type: {filename}")
                            os.remove(file_path)
                except:
                    print(f"    ❌ Unknown file type: {filename}")
                    os.remove(file_path)
        else:
            print(f"    ⚠️  Unknown file type: {filename} (Content-Type: {content_type})")
            os.remove(file_path)
        
        return xml_files_extracted
        
    except Exception as e:
        print(f"    ❌ Error processing {file_path}: {e}")
        return []

def process_csv_urls(csv_file, destination_folder="Q3_2025", max_rows=None):
    """Process URLs from CSV file and download XML files"""
    
    # Create destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)
    
    print(f"Processing URLs from: {csv_file}")
    print(f"Destination folder: {destination_folder}")
    print("=" * 60)
    
    # Statistics
    total_urls = 0
    successful_downloads = 0
    failed_downloads = 0
    total_xml_files = 0
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            # Find the URL column (try common names)
            url_column = None
            if reader.fieldnames:
                for col in reader.fieldnames:
                    if 'url' in col.lower() or 'link' in col.lower() or 'file' in col.lower():
                        url_column = col
                        break
            
            if not url_column:
                print("❌ Could not find URL column in CSV. Available columns:")
                if reader.fieldnames:
                    for col in reader.fieldnames:
                        print(f"  - {col}")
                return
            
            print(f"Using URL column: {url_column}")
            print()
            
            # Process each row
            processed_rows = 0
            for i, row in enumerate(reader, 1):
                if max_rows is not None and processed_rows >= max_rows:
                    break
                url = row.get(url_column, '').strip()
                
                if not url:
                    print(f"[{i}] ⚠️  Empty URL, skipping")
                    continue
                
                print(f"[{i}] Processing: {url}")
                
                # Check if this is a directory (ends with /)
                if url.endswith('/'):
                    # Get all files from directory
                    file_urls = get_files_from_directory(url)
                    
                    if not file_urls:
                        print(f"    ⚠️  No files found in directory")
                        failed_downloads += 1
                        total_urls += 1
                        processed_rows += 1
                        continue
                    
                    # Download each file from the directory
                    for j, file_url in enumerate(file_urls, 1):
                        print(f"    [{j}/{len(file_urls)}] Downloading: {os.path.basename(urlparse(file_url).path)}")
                        
                        download_result = download_file(file_url, destination_folder)
                        
                        if download_result[0]:  # file_path
                            file_path, content_type = download_result
                            # Process the downloaded file
                            xml_files = process_downloaded_file(file_path, destination_folder, content_type)
                            
                            if xml_files:
                                total_xml_files += len(xml_files)
                        
                        # Small delay between files
                        time.sleep(0.5)
                    
                    successful_downloads += 1
                else:
                    # Single file download
                    download_result = download_file(url, destination_folder)
                    
                    if download_result[0]:  # file_path
                        file_path, content_type = download_result
                        # Process the downloaded file
                        xml_files = process_downloaded_file(file_path, destination_folder, content_type)
                        
                        if xml_files:
                            successful_downloads += 1
                            total_xml_files += len(xml_files)
                        else:
                            failed_downloads += 1
                    else:
                        failed_downloads += 1
                
                total_urls += 1
                processed_rows += 1
                
                # Small delay to be nice to servers
                time.sleep(1)
    
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file}")
        return
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return
    
    # Final summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Total URLs processed: {total_urls}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total XML files extracted: {total_xml_files}")
    
    # List all XML files in destination
    xml_files_in_dest = glob.glob(os.path.join(destination_folder, "*.xml"))
    print(f"XML files in {destination_folder}: {len(xml_files_in_dest)}")
    
    if xml_files_in_dest:
        print("\nXML files ready for processing:")
        for xml_file in xml_files_in_dest:
            print(f"  - {os.path.basename(xml_file)}")

def main():
    """Main function"""
    print("XML File Downloader")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(description="Download XML files from URLs listed in a CSV.")
    parser.add_argument("--csv", dest="csv_file", default="Q3_2025_606.csv", help="CSV file containing URLs (default: Q3_2025_606.csv)")
    parser.add_argument("--dest", dest="destination", default="Q3_2025", help="Destination folder (default: Q3_2025)")
    parser.add_argument("--max-rows", dest="max_rows", type=int, default=None, help="Process only the first N rows (default: all)")
    args = parser.parse_args()
    
    # Resolve CSV file
    csv_path = args.csv_file
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        # Fallback: look for default in current dir
        if os.path.exists("Q3_2025_606.csv"):
            csv_path = "Q3_2025_606.csv"
            print(f"Using fallback CSV: {csv_path}")
        else:
            print("Place Q3_2025_606.csv in the current directory or pass --csv.")
            return
    
    destination = args.destination or "Q3_2025"
    max_rows = args.max_rows
    
    # Start downloading
    process_csv_urls(csv_path, destination, max_rows=max_rows)

if __name__ == "__main__":
    main()  